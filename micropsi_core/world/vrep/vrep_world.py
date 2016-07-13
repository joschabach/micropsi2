import math
import time
import logging
import numpy as np
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt

import threading
from io import BytesIO
import base64
import random
import math


from scipy.misc import toimage, fromimage
from PIL import Image

import vrep
from micropsi_core.world.world import World
from micropsi_core.world.worldadapter import ArrayWorldAdapter, WorldAdapterMixin


class VREPConnection(threading.Thread):
    wait = 2
    current_try = 0
    ping_interval = 1

    def __init__(self, host, port, connection_listeners=[]):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.clientID = -1
        self.daemon = True
        self.stop  = threading.Event()
        self.is_connected = False
        self.logger = logging.getLogger("world")
        self.state = threading.Condition()
        self.is_active = True
        self.connection_listeners = connection_listeners
        self.start()

    def run(self):
        self.reconnect()
        while self.is_active:
            with self.state:
                if self.paused:
                    self.state.wait()
            self.reconnect()
        vrep.simxFinish(-1)

    def reconnect(self):
        self.is_connected = False
        self.current_try = 0
        self.clientID = -1
        vrep.simxFinish(-1)  # just in case, close all opened connections
        while self.clientID < 0 and self.is_active:
            self.clientID = vrep.simxStart(self.host, self.port, True, False, 5000, 4)  # Connect to V-REP
            if self.clientID == -1:
                self.logger.error("Could not connect to v-rep, trying again in %d seconds", self.current_try * self.wait)
                self.stop.wait(self.current_try * self.wait)
                self.current_try += 1
            else:
                self.is_connected = True
                self.logger.info("Connected to local V-REP at port %d" % self.port)
                for item in self.connection_listeners:
                    item.on_vrep_connect()
        self.pause()

    def resume(self):
        with self.state:
            self.paused = False
            self.state.notify()

    def pause(self):
        with self.state:
            self.paused = True

    def terminate(self):
        self.stop.set()


class VREPWorld(World):
    """ A vrep robot simulator environment
        In V-REP, the following setup has to be performed:
        - simExtRemoteApiStart(19999) has to have been run
        - the simulation must have been started
    """
    supported_worldadapters = ['Robot', 'OneBallRobot', 'Objects6D']

    assets = {
        'template': 'vrep/vrep.tpl',
        'js': "vrep/vrep.js",
    }

    def __init__(self, filename, world_type="VREPWorld", name="", owner="", engine=None, uid=None, version=1, config={}):
        World.__init__(self, filename, world_type=world_type, name=name, owner=owner, uid=uid, version=version, config=config)

        self.connection_daemon = VREPConnection(config['vrep_host'], int(config['vrep_port']), connection_listeners=[self])

        time.sleep(1)  # wait for the daemon to get started before continuing.

        from micropsi_core.runtime import add_signal_handler
        add_signal_handler(self.kill_vrep_connection)

    def get_world_view(self, step):
        data = {
            'objects': self.get_world_objects(),
            'agents': self.data.get('agents', {}),
            'current_step': self.current_step,
        }
        plots = {}
        for uid in self.agents:
            if hasattr(self.agents[uid], 'image'):
                image = self.agents[uid].image
                bio = BytesIO()
                image.figure.savefig(bio, format="png")
                plots[uid] = base64.encodebytes(bio.getvalue()).decode("utf-8")
        data['plots'] = plots
        return data

    def on_vrep_connect(self):
        """ is called by the connection_daemon, if a connection was established """
        for uid in self.agents:
            self.agents[uid].on_vrep_connect()

    def kill_vrep_connection(self, *args):
        if hasattr(self, "connection_daemon"):
            self.connection_daemon.is_active = False
            if self.connection_daemon:
                self.connection_daemon.resume()
                self.connection_daemon.terminate()
                self.connection_daemon.join()
                vrep.simxFinish(-1)

    def __del__(self):
        self.kill_vrep_connection()

    @staticmethod
    def get_config_options():
        return [
            {'name': 'vrep_host',
             'default': '127.0.0.1'},
            {'name': 'vrep_port',
             'default': 19999}
        ]


class VrepCollisions(WorldAdapterMixin):

    @staticmethod
    def get_config_options():
        return [{'name': 'collision_name',
             'default': 'Collision',
             'description': 'The name of the robot\'s collision handle'}]

    def initialize(self):
        super().initialize()
        if self.collision_name:
            self.collision_handle = self.call_vrep(vrep.simxGetCollisionHandle, [self.clientID, self.collision_name, vrep.simx_opmode_blocking])
            if self.collision_handle < 1:
                self.logger.warning("Collision handle %s not found, not tracking collisions" % self.collision_name)
            else:
                self.call_vrep(vrep.simxReadCollision, [self.clientID, self.collision_handle, vrep.simx_opmode_streaming], empty_result_ok=True)
            self.add_datasource("collision")

    def update_data_sources_and_targets(self):
        super().update_data_sources_and_targets()
        if self.collision_name:
            collision_state = self.call_vrep(vrep.simxReadCollision, [self.clientID, self.collision_handle,
                                                          vrep.simx_opmode_buffer])
            self._set_datasource_value("collision", 1 if collision_state else 0)


class VrepGreyscaleVision(WorldAdapterMixin):

    def initialize(self):
        super().initialize()
        self.observer_handle = self.call_vrep(vrep.simxGetObjectHandle, [self.clientID, "Observer", vrep.simx_opmode_blocking])
        if self.observer_handle < 1:
            self.logger.warn("Could not get handle for Observer vision sensor, vision will not be available.")
        else:
            resolution, image = self.call_vrep(vrep.simxGetVisionSensorImage, [self.clientID, self.observer_handle, 0, vrep.simx_opmode_streaming]) # _split+4000)
            self.vision_resolution = resolution
            if len(resolution) != 2:
                self.logger.error("Could not determine vision resolution.")
            else:
                self.logger.info("Vision resolution is %s, greyscale" % str(self.vision_resolution))
        for y in range(self.vision_resolution[1]):
            for x in range(self.vision_resolution[0]):
                self.add_datasource("px_%03d_%03d" % (x, y))

        self.image = plt.imshow(np.zeros(shape=(self.vision_resolution[0], self.vision_resolution[1])), cmap="bone", interpolation='nearest')
        self.image.norm.vmin = 0
        self.image.norm.vmax = 1

    def update_data_sources_and_targets(self):
        super().update_data_sources_and_targets()
        resolution, image = self.call_vrep(vrep.simxGetVisionSensorImage, [self.clientID, self.observer_handle, 0, vrep.simx_opmode_buffer])
        rgb_image = np.reshape(np.asarray(image, dtype=np.uint8), (self.vision_resolution[0] * self.vision_resolution[1], 3)).astype(np.float32)
        rgb_image /= 255.
        luminance = np.sum(rgb_image * np.asarray([.2126, .7152, .0722]), axis=1)
        y_image = luminance.astype(np.float32).reshape((self.vision_resolution[0], self.vision_resolution[1]))[::-1,:]   # todo: npyify and make faster

        self._set_datasource_values('px_000_000', y_image.flatten())
        self.image.set_data(y_image)
        print('vrep vision image sum', np.sum(abs(y_image)))


class VrepRGBVisionMixin(WorldAdapterMixin):

    downscale_factor = 2**2  # rescale the image before sending it to the toolkit. use a power of two.

    def initialize(self):
        super().initialize()
        self.observer_handle = self.call_vrep(vrep.simxGetObjectHandle, [self.clientID, "Observer", vrep.simx_opmode_blocking])
        if self.observer_handle < 1:
            self.logger.warn("Could not get handle for Observer vision sensor, vision will not be available.")
        else:
            resolution, image = self.call_vrep(vrep.simxGetVisionSensorImage, [self.clientID, self.observer_handle, 0, vrep.simx_opmode_streaming]) # _split+4000)
            if len(resolution) != 2:
                self.logger.error("Could not determine vision resolution.")
            else:
                self.vision_resolution = (int(resolution[0] / self.downscale_factor), int(resolution[1] / self.downscale_factor))
                self.logger.info("Vision resolution is %s (RGB)" % str(self.vision_resolution))

        for x in range(self.vision_resolution[0]):
            for y in range(self.vision_resolution[1]):
                for c in range(3):
                    self.add_datasource("px_%03d_%03d_%d" % (x, y, c))

        self.logger.info("added %d vision data sources." % (self.vision_resolution[1]*self.vision_resolution[0]*3))

        self.image = plt.imshow(np.zeros(shape=(self.vision_resolution[0], self.vision_resolution[1], 3)), interpolation='nearest')
        self.image.norm.vmin = 0
        self.image.norm.vmax = 1

    def update_data_sources_and_targets(self):
        super().update_data_sources_and_targets()
        resolution, image = self.call_vrep(vrep.simxGetVisionSensorImage, [self.clientID, self.observer_handle, 0, vrep.simx_opmode_buffer])
        rgb_image = np.reshape(np.asarray(image, dtype=np.uint8), (
                               self.vision_resolution[0]*self.downscale_factor, self.vision_resolution[1]*self.downscale_factor, 3)).astype(np.float32)
        # rgb_image /= 255.

        # smooth & resize the image.
        # it would be nice to use scipy.ndimage.zoom for that since that doesnt require PIL.
        # but it doesnt correctly downsample rgb images (i.e., colors go wrong at sharp edges)
        pil_img = toimage(rgb_image, high=255, low=0, mode='RGB')
        scaled_image = fromimage(pil_img.resize(self.vision_resolution, resample=Image.LANCZOS), mode='RGB') / 255

        # import ipdb; ipdb.set_trace()
        # plt.imshow(scaled_image)
        # plt.savefig('/tmp/upsi/vision_worldadapter{}.png'.format(self.world.current_step))
        # plt.close('all')

        self._set_datasource_values('px_000_000_0', scaled_image.flatten())
        self.image.set_data(scaled_image)


# class VrepRGBDVision(WorldAdapterMixin):
#    ...


class VrepOneBallGame(WorldAdapterMixin):

    @staticmethod
    def get_config_options():
        return [{'name': 'randomize_ball',
             'description': 'Initialize the ball position randomly',
             'default': 'False',
             'options': ["False", "True"]}]

    def initialize(self):
        super().initialize()
        self.ball_handle = self.call_vrep(vrep.simxGetObjectHandle, [self.clientID, "Ball", vrep.simx_opmode_blocking])
        if self.ball_handle < 1:
            self.logger.warn("Could not get handle for Ball object, distance values will not be available.")
        else:
            self.call_vrep(vrep.simxGetObjectPosition, [self.clientID, self.ball_handle, -1, vrep.simx_opmode_streaming], empty_result_ok=True)
        self.sphere_handle = self.call_vrep(vrep.simxGetObjectHandle, [self.clientID, "Sphere", vrep.simx_opmode_blocking])
        print('sphere handle:', str(self.sphere_handle))

        self.add_datasource("ball-distance")
        self.add_datasource("ball-x")
        self.add_datasource("ball-y")
        self.add_datatarget("sphere_x")
        self.add_datatarget("sphere_y")

    def update_data_sources_and_targets(self):
        super().update_data_sources_and_targets()
        if self.ball_handle > 0:
            ball_pos = self.call_vrep(vrep.simxGetObjectPosition, [self.clientID, self.ball_handle, -1, vrep.simx_opmode_buffer])
            joint_pos = self.call_vrep(vrep.simxGetObjectPosition, [self.clientID, self.joints[len(self.joints)-1], -1, vrep.simx_opmode_streaming])

            relative_pos = [0,0]
            relative_pos[0] = ball_pos[0] - self.robot_position[0]
            relative_pos[1] = ball_pos[1] - self.robot_position[1]

            dist = np.linalg.norm(np.array(ball_pos) - np.array(joint_pos))
            self._set_datasource_value('ball-distance', dist)
            self._set_datasource_value('ball-x', relative_pos[0])
            self._set_datasource_value('ball-y', relative_pos[1])
            # position the transparent sphere:
            rx = self._get_datatarget_value('sphere_x')
            ry = self._get_datatarget_value('sphere_y')
            self.call_vrep(vrep.simxSetObjectPosition, [self.clientID, self.sphere_handle, self.robot_handle, [-rx, -ry], vrep.simx_opmode_oneshot], empty_result_ok=True)

    def reset_simulation_state(self):
        super().reset_simulation_state()
        if self.randomize_ball == "True":
            # max_dist = 0.8
            # rx = random.uniform(-max_dist, max_dist)
            # max_y = math.sqrt((max_dist ** 2) - (rx ** 2))
            # ry = random.uniform(-max_y, max_y)
            max_dist = 0.8
            min_dist = 0.2
            k = max_dist**2 - min_dist**2
            a = np.random.rand() * 2 * np.pi
            r = np.sqrt(np.random.rand() * k + min_dist**2)
            rx = r*np.cos(a)
            ry = r*np.sin(a)

            self.call_vrep(vrep.simxSetObjectPosition, [self.clientID, self.ball_handle, self.robot_handle, [rx, ry], vrep.simx_opmode_blocking])


class Vrep6DObjectsMixin(WorldAdapterMixin):

    @staticmethod
    def get_config_options():
        parameters = [{'name': 'objects',
                      'description': 'comma-separated names of objects in the vrep scene',
                      'default': 'fork,ghost_fork'}]
        parameters.extend(VrepGreyscaleVision.get_config_options())
        return parameters

    def initialize(self):
        super().initialize()

        self.object_names = [name.strip() for name in self.objects.split(',')]
        self.object_handles = []
        for name in self.object_names:
            handle = self.call_vrep(vrep.simxGetObjectHandle, [self.clientID, name, vrep.simx_opmode_blocking])
            if handle < 1:
                self.logger.critical("There seems to be no object with the name %s in the v-rep simulation." % self.name)
            else:
                self.object_handles.append(handle)
                self.logger.info("Found object %s" % name)

                # position:
                self.add_datasource("%s-x" % name)
                self.add_datasource("%s-y" % name)
                self.add_datasource("%s-z" % name)
                # angle:
                self.add_datasource("%s-alpha" % name)
                self.add_datasource("%s-beta" % name)
                self.add_datasource("%s-gamma" % name)

                # target position:
                self.add_datatarget("%s-x" % name)
                self.add_datatarget("%s-y" % name)
                self.add_datatarget("%s-z" % name)
                # target angle:
                self.add_datatarget("%s-alpha" % name)
                self.add_datatarget("%s-beta" % name)
                self.add_datatarget("%s-gamma" % name)

    def update_data_sources_and_targets(self):
        # self.datatarget_feedback_values = np.zeros_like(self.datatarget_values)
        super().update_data_sources_and_targets()

        execute = self._get_datatarget_value('execute') > 0.9

        if execute:
            self.call_vrep(vrep.simxPauseCommunication, [self.clientID, True], empty_result_ok=True)
            for i, (name, handle) in enumerate(zip(self.object_names, self.object_handles)):
                # set position:
                tx = self._get_datatarget_value("%s-x" % name)
                ty = self._get_datatarget_value("%s-y" % name)
                tz = self._get_datatarget_value("%s-z" % name)
                self.call_vrep(vrep.simxSetObjectPosition, [self.clientID, handle, -1, [tx, ty, tz], vrep.simx_opmode_oneshot], empty_result_ok=True)
                # set angles:
                talpha = self._get_datatarget_value("%s-alpha" % name)
                tbeta = self._get_datatarget_value("%s-beta" % name)
                tgamma = self._get_datatarget_value("%s-gamma" % name)
                self.call_vrep(vrep.simxSetObjectOrientation, [self.clientID, handle, -1, [talpha, tbeta, tgamma], vrep.simx_opmode_oneshot], empty_result_ok=True)
            self.call_vrep(vrep.simxPauseCommunication, [self.clientID, False])

        for i, (name, handle) in enumerate(zip(self.object_names, self.object_handles)):
            tx, ty, tz = self.call_vrep(vrep.simxGetObjectPosition, [self.clientID, handle, -1, vrep.simx_opmode_oneshot], empty_result_ok=True)
            self._set_datasource_value("%s-x" % name, tx)
            self._set_datasource_value("%s-y" % name, ty)
            self._set_datasource_value("%s-z" % name, tz)

            talpha, tbeta, tgamma = self.call_vrep(vrep.simxGetObjectOrientation, [self.clientID, handle, -1, vrep.simx_opmode_oneshot], empty_result_ok=True)
            self._set_datasource_value("%s-alpha" % name, talpha)
            self._set_datasource_value("%s-beta" % name, tbeta)
            self._set_datasource_value("%s-gamma" % name, tgamma)

            # if name == 'fork':
            #     print('fetch: step={}, object {}, name={}, handle={}\nx={} y={} z={}\nalpha={} beta={} gamma={}\n'.format(self.world.current_step, i, name, handle, tx, ty, tz, talpha, tbeta, tgamma))

    def reset_simulation_state(self):
        pass


class VrepCallMixin():

    block_runner_if_connection_lost = True

    def on_vrep_connect(self):
        """ is called by the world, if a connection was established """
        self.initialize()

    def call_vrep(self, method, params, empty_result_ok=False):
        """ error handling wrapper for calls to the vrep API """
        result = method(*params)
        code = result if type(result) == int else result[0]
        if code != vrep.simx_return_ok:
            if (code == vrep.simx_return_novalue_flag or code == vrep.simx_return_split_progress_flag) and not empty_result_ok:
                    # streaming mode did not return data. wait a bit, try again
                    self.logger.debug("Did not receive data from vrep when calling %s, trying again in 500 ms" % method.__name__)
                    time.sleep(0.5)
                    result = method(*params)
                    code = result if type(result) == int else result[0]
            if code == vrep.simx_return_illegal_opmode_flag:
                self.logger.error("Illegal opmode for VREP call %s" % method.__name)
            if code == vrep.simx_return_remote_error_flag:
                self.logger.error("VREP internal error when calling %s. Invalid handle specified?" % method.__name__)
            elif code == vrep.simx_return_local_error_flag:
                self.logger.error("Client error for VREP call %s" % method.__name)
            elif code == vrep.simx_return_initialize_error_flag:
                self.logger.error("VREP Simulation is not running")
            elif code == vrep.simx_return_timeout_flag or ((code == vrep.simx_return_novalue_flag or code == vrep.simx_return_split_progress_flag) and not empty_result_ok):
                self.logger.warning("Vrep returned code %d when calling %s, attempting a reconnect" % (code, method.__name__))
                self.world.connection_daemon.resume()
                self.initialized = False
                while not self.world.connection_daemon.is_connected or not self.initialized:
                    time.sleep(0.2)
                return self.call_vrep(method, params)
        if type(result) == int:
            return True
        if len(result) == 2:
            return result[1]
        else:
            return result[1:]


class Robot(WorldAdapterMixin, ArrayWorldAdapter, VrepCallMixin):
    """ The basic worldadapter to control a robot in vrep.
    Combine this with the Vrep Mixins for a useful robot simulation"""

    @staticmethod
    def get_config_options():
        return [
            {'name': 'robot_name',
             'description': 'The name of the robot object in V-REP',
             'default': 'LBR_iiwa_7_R800',
             'options': ["LBR_iiwa_7_R800", "MTB_Robot"]},
            {'name': 'control_type',
             'description': 'The type of input sent to the robot',
             'default': 'force/torque',
             'options': ["force/torque", "force/torque-sync", "angles", "movements"]},
            {'name': 'randomize_arm',
             'description': 'Initialize the robot arm randomly',
             'default': 'False',
             'options': ["False", "True"]},
        ]

    def __init__(self, world, uid=None, **data):
        super().__init__(world, uid, **data)
        self.initialize()

    def initialize(self):

        self.clientID = self.world.connection_daemon.clientID

        self.datasource_names = []
        self.datatarget_names = []
        self.datasource_values = np.zeros(0)
        self.datatarget_values = np.zeros(0)
        self.datatarget_feedback_values = np.zeros(0)

        super().initialize()

        self.joints = []
        self.robot_handle = -1
        self.robot_position = []

        self.robot_handle = self.call_vrep(vrep.simxGetObjectHandle, [self.clientID, self.robot_name, vrep.simx_opmode_blocking])

        if self.robot_handle < 1:
            self.logger.critical("There seems to be no robot with the name %s in the v-rep simulation." % self.robot_name)
        else:
            self.robot_position = self.call_vrep(vrep.simxGetObjectPosition, [self.clientID, self.robot_handle, -1, vrep.simx_opmode_blocking])

        self.joints = self.call_vrep(vrep.simxGetObjects, [self.clientID, vrep.sim_object_joint_type, vrep.simx_opmode_blocking])
        self.call_vrep(vrep.simxGetObjectPosition, [self.clientID, self.joints[len(self.joints) - 1], -1, vrep.simx_opmode_streaming], empty_result_ok=True)

        self.logger.info("Found robot with %d joints" % len(self.joints))

        self.add_datasource("tip-x")
        self.add_datasource("tip-y")
        self.add_datasource("tip-z")

        self.add_datatarget("restart")
        self.add_datatarget("execute")

        for i in range(len(self.joints)):
            self.add_datasource("joint_angle_%s" % str(i + 1))
            self.add_datatarget("joint_%s" % str(i + 1))

        for i in range(len(self.joints)):
            self.add_datasource("joint_force_%s" % str(i + 1))

        self.last_restart = 0

        self.current_angle_target_values = np.zeros_like(self.joints)

        if self.nodenet:
            self.nodenet.worldadapter_instance = self
        self.initialized = True

        self.reset_simulation_state()

    def update_data_sources_and_targets(self):
        old_datasource_values = np.array(self.datasource_values)
        self.datatarget_feedback_values = [0] * len(self.datatarget_values)
        self.datasource_values = [0] * len(self.datasource_values)
        super().update_data_sources_and_targets()

        tvals = None

        restart = self._get_datatarget_value('restart') > 0.9 and self.world.current_step - self.last_restart >= 5
        execute = self._get_datatarget_value('execute') > 0.9

        # simulation restart
        if restart:
            return self.reset_simulation_state()

        # execute movement, send new target angles
        if execute:
            tvals = [0] * len(self.datatarget_values)
            self.current_angle_target_values = np.array(self._get_datatarget_values('joint_1', len(self.joints)))
            self.call_vrep(vrep.simxPauseCommunication, [self.clientID, True], empty_result_ok=True)
            joint_angle_offset = self.get_datasource_index("joint_angle_1")
            for i, joint_handle in enumerate(self.joints):
                tval = self.current_angle_target_values[i] * math.pi
                if self.control_type == "force/torque" or self.control_type == "force/torque-sync":
                    tval += (old_datasource_values[joint_angle_offset + i]) * math.pi
                    tvals[i] = tval
                    self.call_vrep(vrep.simxSetJointTargetPosition, [self.clientID, joint_handle, tval, vrep.simx_opmode_oneshot], empty_result_ok=True)
                elif self.control_type == "angles":
                    self.call_vrep(vrep.simxSetJointPosition, [self.clientID, joint_handle, tval, vrep.simx_opmode_oneshot], empty_result_ok=True)
                elif self.control_type == "movements":
                    tval += (old_datasource_values[joint_angle_offset + i]) * math.pi
                    self.call_vrep(vrep.simxSetJointPosition, [self.clientID, joint_handle, tval, vrep.simx_opmode_oneshot], empty_result_ok=True)

            self.call_vrep(vrep.simxPauseCommunication, [self.clientID, False])

        # read joint angle and force values
        self.fetch_sensor_and_feedback_values_from_simulation(tvals, True)

    def reset_simulation_state(self):
        self.call_vrep(vrep.simxStopSimulation, [self.clientID, vrep.simx_opmode_oneshot], empty_result_ok=True)
        time.sleep(0.3)
        self.call_vrep(vrep.simxStartSimulation, [self.clientID, vrep.simx_opmode_oneshot])
        time.sleep(0.5)
        super().reset_simulation_state()
        if self.randomize_arm == "True":
            self.call_vrep(vrep.simxPauseCommunication, [self.clientID, True], empty_result_ok=True)
            for i, joint_handle in enumerate(self.joints):
                self._set_datatarget_value("joint_%d" % (i + 1), random.uniform(-0.8, 0.8))
                self.current_angle_target_values[i] = self._get_datatarget_value("joint_%d" % (i + 1))
                tval = self.current_angle_target_values[i] * math.pi
                self.call_vrep(vrep.simxSetJointPosition, [self.clientID, joint_handle, tval, vrep.simx_opmode_oneshot], empty_result_ok=True)
            # hack: noeppel down
            self.call_vrep(vrep.simxSetJointPosition, [self.clientID, self.joints[-2], math.pi/2, vrep.simx_opmode_oneshot], empty_result_ok=True)
            # /hack
            self.call_vrep(vrep.simxPauseCommunication, [self.clientID, False])

        self.fetch_sensor_and_feedback_values_from_simulation(None)
        self.last_restart = self.world.current_step

    def fetch_sensor_and_feedback_values_from_simulation(self, targets, include_feedback=False):

        if not self.world.connection_daemon.is_connected:
            if self.block_runner_if_connection_lost:
                while not self.world.connection_daemon.is_connected:
                    time.sleep(0.5)
            else:
                return

        if self.world.connection_daemon.clientID != self.clientID:
            self.initialize()

        joint_pos = self.call_vrep(vrep.simxGetObjectPosition, [self.clientID, self.joints[len(self.joints)-1], -1, vrep.simx_opmode_streaming])

        self._set_datasource_value('tip-x', joint_pos[0] - self.robot_position[0])
        self._set_datasource_value('tip-y', joint_pos[1] - self.robot_position[1])
        self._set_datasource_value('tip-z', joint_pos[2] - self.robot_position[2])

        joint_ids, something, data, se = self.call_vrep(vrep.simxGetObjectGroupData, [self.clientID, vrep.sim_object_joint_type, 15, vrep.simx_opmode_blocking])

        movement_finished = False
        count = 0
        while not movement_finished:
            allgood = True
            for i, joint_handle in enumerate(self.joints):
                angle = 0
                force = 0
                if self.control_type == "force/torque" or self.control_type == "force/torque-sync":
                    angle = data[i*2]
                    force = data[i*2 + 1]
                    if targets is not None:
                        target_angle = targets[i]
                        if abs(abs(angle) - abs(target_angle)) < .001 and include_feedback:
                            self._set_datatarget_feedback_value("joint_%s" % (i + 1), 1)
                        else:
                            allgood = False
                elif self.control_type == "angles":
                    angle = data[i * 2]
                elif self.control_type == "movements":
                    angle = data[i * 2]
                self._set_datasource_value("joint_angle_%s" % (i + 1), angle / math.pi)
                self._set_datasource_value("joint_force_%s" % (i + 1), force)

            movement_finished = allgood
            if not movement_finished:
                joint_positions = []
                for i, joint_handle in enumerate(self.joints):
                    joint_positions.append(data[i*2])

                count += 1
                if count == 10:
                    self.logger.info("Robot did not complete movement in time, giving up.")
                    self.logger.info("Joint   targets: %s" % str(targets))
                    self.logger.info("Joint positions: %s" % str(joint_positions))
                    movement_finished = True
                time.sleep(0.1)
                joint_ids, something, data, se = self.call_vrep(vrep.simxGetObjectGroupData, [self.clientID,
                                                                                  vrep.sim_object_joint_type, 15,
                                                                                  vrep.simx_opmode_blocking])


class OneBallRobot(Robot, VrepGreyscaleVision, VrepCollisions, VrepOneBallGame):
    """ A Worldadapter to play the one-ball-reaching-task """

    @classmethod
    def get_config_options(cls):
        """ I've found no way around this yet """
        parameters = []
        parameters.extend(Robot.get_config_options())
        parameters.extend(VrepCollisions.get_config_options())
        parameters.extend(VrepGreyscaleVision.get_config_options())
        parameters.extend(VrepOneBallGame.get_config_options())
        return parameters


class Objects6D(VrepRGBVisionMixin, Vrep6DObjectsMixin, VrepCallMixin, ArrayWorldAdapter):
    """ worldadapter to observe and control 6D poses of arbitrary objects in a vrep scene
    (i.e. their positons and orientations)"""
    block_runner_if_connection_lost = True

    @staticmethod
    def get_config_options():
        parameters = []
        parameters.extend(VrepRGBVisionMixin.get_config_options())
        parameters.extend(Vrep6DObjectsMixin.get_config_options())
        return parameters

    def __init__(self, world, uid=None, **data):
        super().__init__(world, uid, **data)

        self.initialize()

    def initialize(self):
        self.clientID = self.world.connection_daemon.clientID

        self.datasource_names = []
        self.datatarget_names = []
        self.datasource_values = np.zeros(0)
        self.datatarget_values = np.zeros(0)
        self.datatarget_feedback_values = np.zeros(0)

        super().initialize()

        self.add_datatarget("restart")
        self.add_datatarget("execute")

        self.last_restart = 0

        if self.nodenet:
            self.nodenet.worldadapter_instance = self
        self.initialized = True
        # print('objects6D initialize: self.datasources=',self.datasources)
        self.reset_simulation_state()

    def update_data_sources_and_targets(self):
        # self.datatarget_feedback_values = np.zeros_like(self.datatarget_values)
        self.datasource_values = np.zeros_like(self.datasource_values, dtype='float64')  # need to override self.datasource_values' dtype to float. why?
        super().update_data_sources_and_targets()

        restart = self._get_datatarget_value('restart') > 0.9 and self.world.current_step - self.last_restart >= 5
        execute = self._get_datatarget_value('execute') > 0.9

        # simulation restart
        if restart:
            return self.reset_simulation_state()

        # send new target positions and angles
        if execute:
            self.call_vrep(vrep.simxPauseCommunication, [self.clientID, True], empty_result_ok=True)
            for i, (name, handle) in enumerate(zip(self.object_names, self.object_handles)):
                # set position:
                tx = self._get_datatarget_value("%s-x" % name)
                ty = self._get_datatarget_value("%s-y" % name)
                tz = self._get_datatarget_value("%s-z" % name)
                self.call_vrep(vrep.simxSetObjectPosition, [self.clientID, handle, -1, [tx, ty, tz], vrep.simx_opmode_oneshot], empty_result_ok=True)
                # set angles:
                talpha = self._get_datatarget_value("%s-alpha" % name)
                tbeta = self._get_datatarget_value("%s-beta" % name)
                tgamma = self._get_datatarget_value("%s-gamma" % name)
                self.call_vrep(vrep.simxSetObjectOrientation, [self.clientID, handle, -1, [talpha, tbeta, tgamma], vrep.simx_opmode_oneshot], empty_result_ok=True)
            self.call_vrep(vrep.simxPauseCommunication, [self.clientID, False])

        self.fetch_sensor_and_feedback_values_from_simulation(None)

    def reset_simulation_state(self):
        self.call_vrep(vrep.simxStopSimulation, [self.clientID, vrep.simx_opmode_oneshot], empty_result_ok=True)
        time.sleep(0.3)
        self.call_vrep(vrep.simxStartSimulation, [self.clientID, vrep.simx_opmode_oneshot])
        time.sleep(0.5)
        super().reset_simulation_state()

        self.fetch_sensor_and_feedback_values_from_simulation(None)
        self.last_restart = self.world.current_step

    def fetch_sensor_and_feedback_values_from_simulation(self, targets, include_feedback=False):
        if not self.world.connection_daemon.is_connected:
            if self.block_runner_if_connection_lost:
                while not self.world.connection_daemon.is_connected:
                    time.sleep(0.5)
            else:
                return

        if self.world.connection_daemon.clientID != self.clientID:
            self.initialize()