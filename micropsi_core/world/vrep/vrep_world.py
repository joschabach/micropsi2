import math
import time
import logging
import numpy as np
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt

import os
import shlex
import subprocess
import signal
import threading
import base64
import random
import sys
from io import BytesIO

from scipy.misc import toimage, fromimage, imresize
from PIL import Image


import vrep
from micropsi_core.world.world import World
from micropsi_core.world.worldadapter import ArrayWorldAdapter, WorldAdapterMixin

from micropsi_core.tools import pid_exists


class VREPConnection(threading.Thread):
    wait = 2
    current_try = 0
    ping_interval = 1

    def __init__(self, host, port, synchronous_mode=False, connection_listeners=[]):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.clientID = -1
        self.daemon = True
        self.stop = threading.Event()
        self.is_connected = False
        self.logger = logging.getLogger("world")
        self.state = threading.Condition()
        self.is_active = True
        self.synchronous_mode = synchronous_mode
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
                if self.synchronous_mode:
                    result = vrep.simxSynchronous(self.clientID, True)
                    if result == vrep.simx_return_ok:
                        self.logger.info("VREP set to synchronous mode")
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


def preexec_function():
    # Ignore the SIGINT signal by setting the handler to the standard
    # signal handler SIG_IGN.
    signal.signal(signal.SIGINT, signal.SIG_IGN)


class VREPWatchdog(threading.Thread):

    def __init__(self, binary, flags, scene, listeners):
        threading.Thread.__init__(self)
        self.binary_path = os.path.expanduser(binary)
        self.scene_path = os.path.expanduser(scene)
        self.flags = flags
        self.args = shlex.split(self.binary_path + flags + self.scene_path)
        self.daemon = True
        self.paused = False
        self.stop = threading.Event()
        self.state = threading.Condition()
        self.logger = logging.getLogger("world")
        self.initial_spawn = True
        self.pid = None
        self.escalate = None
        self.is_active = True
        self.vrep_listeners = listeners
        self.process = None
        self.start()

    def run(self):
        self.spawn_vrep()
        while self.is_active:
            with self.state:
                if self.paused:
                    self.state.wait()

            if self.process and self.process.poll():
                self.kill_vrep()
                self.stop.wait(5)
            if self.process is None or not pid_exists(self.pid):
                self.logger.info("Vrep process gone, respawning.")
                self.spawn_vrep()
                self.stop.wait(1)
        self.pause()

    def spawn_vrep(self):
        fp = open('/tmp/vrep.log', 'a')
        self.process = subprocess.Popen(self.args, stdout=fp, preexec_fn=preexec_function)
        self.escalate = None
        self.pid = self.process.pid
        self.logger.info("VREP PID is " + str(self.pid))
        if not self.initial_spawn:
            for item in self.vrep_listeners:
                item.on_vrep_respawn()
        self.initial_spawn = False

    def kill_vrep(self):
        if self.process is not None:
            while self.pid is not None and pid_exists(self.pid):
                self.logger.info("killing vrep with pid " + str(self.pid))
                try:
                    if self.escalate is None:
                        self.logger.info("sending SIGTERM to vrep")
                        os.kill(self.pid, signal.SIGTERM)
                        self.escalate = 'terminate'
                    elif self.escalate == 'terminate':
                        self.logger.info("sending SIGINT to vrep")
                        os.kill(self.pid, signal.SIGINT)
                        self.escalate = 'kill'
                    elif self.escalate == 'kill':
                        self.logger.info("sending SIGKILL to vrep")
                        os.kill(self.pid, signal.SIGKILL)
                        self.escalate = 'experiment'
                    elif self.escalate == 'experiment':
                        self.logger.info("sending SIGSYS to vrep")
                        os.kill(self.pid, signal.SIGSYS)
                        self.escalate = 'nuke'
                    elif self.escalate == 'nuke':
                        self.logger.info("ok, vrep just does not want to go away. no idea what we can do other than restarting the whole toolkit.")
                        self.pid = None
                        self.terminate()
                        import _thread
                        _thread.interrupt_main()
                        sys.exit(1)
                except Exception:
                    self.logger.info("Exception: %s" % sys.exc_info()[0])
                self.logger.info("waiting max 10 sec for vrep to quit")
                try:
                    self.process.wait(10)
                except subprocess.TimeoutExpired:
                    pass
            self.logger.debug("vrep with pid %s should be dead" % str(self.pid))
            self.process = None
            self.pid = None

    def resume(self):
        with self.state:
            self.paused = False
            self.state.notify()

    def pause(self):
        with self.state:
            self.paused = True

    def terminate(self):
        self.is_active = False
        self.stop.set()
        self.kill_vrep()


class VrepCallMixin():

    block_runner_if_connection_lost = True

    def on_vrep_connect(self):
        """ is called by the world, if a connection was established """
        self.initialize()

    def call_vrep(self, method, params, empty_result_ok=False, debugprint=False):
        """ error handling wrapper for calls to the vrep API """
        result = method(*params)
        if debugprint:
            print(self.world.current_step, ' vrep wrap called', method, 'with parameters', params, '. result was', result)
        code = result if type(result) == int else result[0]
        if code != vrep.simx_return_ok:
            if (code == vrep.simx_return_novalue_flag or code == vrep.simx_return_split_progress_flag) and not empty_result_ok:
                    # streaming mode did not return data. wait a bit, try again
                    self.logger.info("Did not receive data from vrep when calling %s, trying again in 500 ms" % method.__name__)
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
            rval = result[1]
            if np.any(np.isnan(np.array(rval, dtype=float))):
                raise Exception('VREP returned invalid value')
            return rval
        else:
            rval = result[1:]
            if np.any(np.isnan(np.array(rval, dtype=float))):
                raise Exception('VREP returned invalid value')
            return rval


class VREPWorld(World):
    """ A vrep robot simulator environment
        In V-REP, the following setup has to be performed:
        - simExtRemoteApiStart(19999) has to have been run
        - the simulation must have been started
    """
    supported_worldadapters = ['Robot', 'OneBallRobot', 'Objects6D', 'IKRobotWithGreyscaleVision', 'IKRobot']

    assets = {
        'template': 'vrep/vrep.tpl',
        'js': "vrep/vrep.js",
    }

    def __init__(self, filename, world_type="VREPWorld", name="", owner="", engine=None, uid=None, version=1, config={}):
        World.__init__(self, filename, world_type=world_type, name=name, owner=owner, uid=uid, version=version, config=config)

        self.simulation_speed = float(config['simulation_speed'])
        self.synchronous_mode = self.simulation_speed > 0

        self.vrep_watchdog = None

        if config['vrep_host'] == 'localhost' or config['vrep_host'] == '127.0.0.1':
            if config.get('vrep_binary') and config.get('vrep_scene'):
                if config.get('run_headless', 'true') == 'true':
                    flags = " -h -s -gREMOTEAPISERVERSERVICE_%s_TRUE_TRUE " % config['vrep_port']
                else:
                    flags = " -s -gREMOTEAPISERVERSERVICE_%s_TRUE_TRUE " % config['vrep_port']
                self.logger.info("Spawning local vrep process")
                self.vrep_watchdog = VREPWatchdog(config['vrep_binary'], flags, config['vrep_scene'], listeners=[self])

        self.connection_daemon = VREPConnection(config['vrep_host'], int(config['vrep_port']), synchronous_mode=self.synchronous_mode, connection_listeners=[self])

        time.sleep(5)  # wait for the daemon to get started before continuing.

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

    def step(self):
        if not self.synchronous_mode:
            super().step()
        else:
            if self.current_step % self.simulation_speed == 0:
                super().step()
            else:
                self.current_step += 1

    def on_vrep_respawn(self):
        self.connection_daemon.resume()

    def signal_handler(self, *args):
        if hasattr(self, "connection_daemon"):
            if self.connection_daemon:
                self.connection_daemon.is_active = False
                self.connection_daemon.resume()
                self.connection_daemon.terminate()
                self.connection_daemon.join()
            if self.vrep_watchdog is not None:
                self.vrep_watchdog.is_active = False
                self.vrep_watchdog.resume()
                self.vrep_watchdog.terminate()
                self.vrep_watchdog.join()

    def __del__(self):
        self.signal_handler()

    @staticmethod
    def get_config_options():
        return [
            {'name': 'vrep_host',
             'default': '127.0.0.1'},
            {'name': 'vrep_port',
             'default': 19999},
            {'name': 'simulation_speed',
             'default': '0',
             'description': 'nodenet steps per vrep step. 0 for vrep realtime'},
            {'name': 'vrep_binary',
             'default': '~/Applications/vrep/vrep.app/Contents/MacOS/vrep',
             'description': 'path to the vrep binary. leave empty if you launch vrep yourself.'},
            {'name': 'vrep_scene',
             'default': '~/micropsi-nodenets/vrep-scenes/iiwa-scene-ik.ttt',
             'description': 'path to the vrep scene file. leave empty if you launch vrep yourself'},
            {'name': 'run_headless',
             'default': 'true',
             'options': ['true', 'false'],
             'description': 'launch vrep without GUI (only if you gave binary & scene)'}
        ]


class VrepCollisionsMixin(WorldAdapterMixin):

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

    def read_from_world(self):
        super().read_from_world()
        if self.collision_name:
            collision_state = self.call_vrep(vrep.simxReadCollision, [self.clientID, self.collision_handle,
                                                          vrep.simx_opmode_buffer])
            self._set_datasource_value("collision", 1 if collision_state else 0)


class VrepGreyscaleVisionMixin(WorldAdapterMixin):

    @staticmethod
    def get_config_options():
        return [{'name': 'downscale',
             'description': 'shrink the image by a factor of 2^k, using anti aliasing. specify `1` to halve the image in each dimension, `2` to quarter it, `0` to leave it unscaled (default)',
             'default': 0}]

    def initialize(self):
        super().initialize()
        self.observer_handle = self.call_vrep(vrep.simxGetObjectHandle, [self.clientID, "Observer", vrep.simx_opmode_blocking])
        if self.observer_handle < 1:
            self.logger.warn("Could not get handle for Observer vision sensor, vision will not be available.")
        else:
            resolution, image = self.call_vrep(vrep.simxGetVisionSensorImage, [self.clientID, self.observer_handle, 0, vrep.simx_opmode_streaming]) # _split+4000)
            if len(resolution) != 2:
                self.logger.error("Could not determine vision resolution.")
            elif self.downscale == 0:
                self.vision_resolution = resolution
                self.logger.info("Vision resolution is %s, greyscale" % str(self.vision_resolution))
            else:
                self.vision_resolution = (int(resolution[0] / 2**self.downscale), int(resolution[1] / 2**self.downscale))
                self.logger.info("Vision resolution is {} (greyscale) after downscaling by 2**{}".format(self.vision_resolution, self.downscale))
        for y in range(self.vision_resolution[1]):
            for x in range(self.vision_resolution[0]):
                self.add_datasource("px_%03d_%03d" % (x, y))

        self.image = plt.imshow(np.zeros(shape=(self.vision_resolution[0], self.vision_resolution[1])), cmap="bone", interpolation='nearest')
        self.image.norm.vmin = 0
        self.image.norm.vmax = 1

    def read_from_world(self):
        super().read_from_world()
        resolution, image = self.call_vrep(vrep.simxGetVisionSensorImage, [self.clientID, self.observer_handle, 0, vrep.simx_opmode_buffer])
        rgb_image = np.reshape(np.asarray(image, dtype=np.uint8), (resolution[0] * resolution[1], 3)).astype(np.float32)

        luminance = np.sum(rgb_image * np.asarray([.2126, .7152, .0722]), axis=1)
        y_image = luminance.astype(np.float32).reshape((resolution[0], resolution[1]))[::-1, :]   # todo: npyify and make faster

        if self.downscale != 0:
            y_image = imresize(y_image*255, size=1./(2**self.downscale), interp='bilinear')  # for greyscale images, scipy.misc.imresize is enough.

        y_image = y_image/255.0

        self._set_datasource_values('px_000_000', y_image.flatten())
        self.image.set_data(y_image)
        # print('vrep vision image sum', np.sum(abs(y_image)))


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

    def read_from_world(self):
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


class VrepOneBallGameMixin(WorldAdapterMixin):

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

    def write_to_world(self):
        super().write_to_world()
        if self.ball_handle > 0:
            # position the transparent sphere:
            rx = self._get_datatarget_value('sphere_x')
            ry = self._get_datatarget_value('sphere_y')
            self.call_vrep(vrep.simxSetObjectPosition, [self.clientID, self.sphere_handle, self.robot_handle, [-rx, -ry], vrep.simx_opmode_oneshot], empty_result_ok=True)

    def read_from_world(self):
        super().read_from_world()
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
        parameters.extend(VrepGreyscaleVisionMixin.get_config_options())
        return parameters

    def initialize(self):
        super().initialize()

        self.object_names = [name.strip() for name in self.objects.split(',')]
        self.object_handles = []
        for name in self.object_names:
            handle = self.call_vrep(vrep.simxGetObjectHandle, [self.clientID, name, vrep.simx_opmode_blocking])
            if handle < 1:
                self.logger.critical("There seems to be no object with the name %s in the v-rep simulation." % name)
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
                # execution target
                self.add_datatarget("execute-%s" % name)

    def write_to_world(self):
        super().write_to_world()
        self.call_vrep(vrep.simxPauseCommunication, [self.clientID, True], empty_result_ok=True)
        for i, (name, handle) in enumerate(zip(self.object_names, self.object_handles)):
            if self._get_datatarget_value('execute-%s' % name) > 0.9:
                # set position:
                tx = self._get_datatarget_value("%s-x" % name)
                ty = self._get_datatarget_value("%s-y" % name)
                tz = self._get_datatarget_value("%s-z" % name)
                self.call_vrep(vrep.simxSetObjectPosition, [self.clientID, handle, -1, [tx, ty, tz], vrep.simx_opmode_streaming], empty_result_ok=True)
                # set angles:
                talpha = self._get_datatarget_value("%s-alpha" % name)
                tbeta = self._get_datatarget_value("%s-beta" % name)
                tgamma = self._get_datatarget_value("%s-gamma" % name)
                self.call_vrep(vrep.simxSetObjectOrientation, [self.clientID, handle, -1, [talpha, tbeta, tgamma], vrep.simx_opmode_streaming], empty_result_ok=True)
        self.call_vrep(vrep.simxPauseCommunication, [self.clientID, False])

    def read_from_world(self):
        execute = self._get_datatarget_value('execute') > 0.9

        for i, (name, handle) in enumerate(zip(self.object_names, self.object_handles)):
            tx, ty, tz = self.call_vrep(vrep.simxGetObjectPosition, [self.clientID, handle, -1, vrep.simx_opmode_streaming], empty_result_ok=False)
            self._set_datasource_value("%s-x" % name, tx)
            self._set_datasource_value("%s-y" % name, ty)
            self._set_datasource_value("%s-z" % name, tz)

            talpha, tbeta, tgamma = self.call_vrep(vrep.simxGetObjectOrientation, [self.clientID, handle, -1, vrep.simx_opmode_streaming], empty_result_ok=False)
            self._set_datasource_value("%s-alpha" % name, talpha)
            self._set_datasource_value("%s-beta" % name, tbeta)
            self._set_datasource_value("%s-gamma" % name, tgamma)

            # if name == 'fork':
            #     print('fetch: step={}, object {}, name={}, handle={}\nx={} y={} z={}\nalpha={} beta={} gamma={}\n'.format(self.world.current_step, i, name, handle, tx, ty, tz, talpha, tbeta, tgamma))


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
             'options': ["force/torque", "force/torque-sync", "ik", "angles", "movements"]},
            {'name': 'randomize_arm',
             'description': 'Initialize the robot arm randomly',
             'default': 'False',
             'options': ["False", "True"]},
        ]

    def __init__(self, world, uid=None, **data):
        super().__init__(world, uid, **data)
        self.initialize()

    def initialize(self):
        self.tvals = None

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

        if self.control_type == "ik":
            self.ik_target_handle = self.call_vrep(vrep.simxGetObjectHandle, [self.clientID, "ik_target", vrep.simx_opmode_blocking])
            self.ik_follower_handle = self.call_vrep(vrep.simxGetObjectHandle, [self.clientID, "ik_follower", vrep.simx_opmode_blocking])
            self.call_vrep(vrep.simxGetObjectPosition, [self.clientID, self.ik_target_handle, -1, vrep.simx_opmode_streaming], empty_result_ok=True)
            self.call_vrep(vrep.simxGetObjectPosition, [self.clientID, self.ik_follower_handle, -1, vrep.simx_opmode_streaming], empty_result_ok=True)

        self.add_datasource("tip-x")
        self.add_datasource("tip-y")
        self.add_datasource("tip-z")

        self.add_datatarget("restart")
        self.add_datatarget("execute")

        for i in range(len(self.joints)):
            self.add_datasource("joint_angle_%s" % str(i + 1))
            self.add_datasource("joint_force_%s" % str(i + 1))

        if self.control_type != "ik":
            for i in range(len(self.joints)):
                self.add_datatarget("joint_%s" % str(i + 1))
        else:
            self.add_datatarget("ik_x")
            self.add_datatarget("ik_y")
            self.add_datatarget("ik_z")

        self.call_vrep(vrep.simxGetObjectGroupData, [self.clientID, vrep.sim_object_joint_type, 15, vrep.simx_opmode_streaming], empty_result_ok=True)

        self.last_restart = 0

        self.current_angle_target_values = np.zeros_like(self.joints)

        if self.nodenet:
            self.nodenet.worldadapter_instance = self
        self.initialized = True

        self.reset_simulation_state()

    def update_data_sources_and_targets(self):
        self.write_to_world()
        if self.world.synchronous_mode:
            self.call_vrep(vrep.simxSynchronousTrigger, [self.clientID])
            self.call_vrep(vrep.simxGetPingTime, [self.clientID])
        self.read_from_world()

    def write_to_world(self):
        old_datasource_values = np.array(self.datasource_values)
        self.datatarget_feedback_values = np.zeros_like(self.datatarget_values)
        self.datasource_values = np.zeros_like(self.datasource_values)

        self.tvals = None

        restart = self._get_datatarget_value('restart') > 0.9 and self.world.current_step - self.last_restart >= 5
        execute = self._get_datatarget_value('execute') > 0.9

        # simulation restart
        if restart:
            return self.reset_simulation_state()

        super().write_to_world()
        # execute movement, send new target angles
        if execute:

            self.call_vrep(vrep.simxPauseCommunication, [self.clientID, True], empty_result_ok=True)

            if self.control_type != "ik":
                self.tvals = [0] * len(self.datatarget_values)
                self.current_angle_target_values = np.array(self._get_datatarget_values('joint_1', len(self.joints)))
                joint_angle_offset = self.get_datasource_index("joint_angle_1")
                for i, joint_handle in enumerate(self.joints):
                    tval = self.current_angle_target_values[i] * math.pi
                    if self.control_type == "force/torque" or self.control_type == "force/torque-sync":
                        tval += (old_datasource_values[joint_angle_offset + i]) * math.pi
                        self.tvals[i] = tval
                        self.call_vrep(vrep.simxSetJointTargetPosition,
                                       [self.clientID, joint_handle, tval, vrep.simx_opmode_oneshot],
                                       empty_result_ok=True)
                    elif self.control_type == "angles":
                        self.call_vrep(vrep.simxSetJointPosition,
                                       [self.clientID, joint_handle, tval, vrep.simx_opmode_oneshot],
                                       empty_result_ok=True)
                    elif self.control_type == "movements":
                        tval += (old_datasource_values[joint_angle_offset + i]) * math.pi
                        self.call_vrep(vrep.simxSetJointPosition,
                                       [self.clientID, joint_handle, tval, vrep.simx_opmode_oneshot],
                                       empty_result_ok=True)

            else:
                tpos = self.call_vrep(vrep.simxGetObjectPosition,
                                           [self.clientID, self.ik_follower_handle, -1,
                                            vrep.simx_opmode_buffer])

                tx = tpos[0] + self._get_datatarget_value("ik_x")
                ty = tpos[1] + self._get_datatarget_value("ik_y")
                tz = tpos[2] + self._get_datatarget_value("ik_z")

                self.call_vrep(vrep.simxSetObjectPosition,
                               [self.clientID, self.ik_target_handle, -1, [tx, ty, tz],
                                vrep.simx_opmode_oneshot], empty_result_ok=True, debugprint=False)

            self.call_vrep(vrep.simxPauseCommunication, [self.clientID, False])

    def read_from_world(self):
        super().read_from_world()
        self.fetch_sensor_and_feedback_values_from_simulation(self.tvals, include_feedback=True)

    def reset_simulation_state(self):
        self.call_vrep(vrep.simxStopSimulation, [self.clientID, vrep.simx_opmode_oneshot], debugprint=False)

        def state():
            returnvalue = None
            attempt_nr = 1
            while returnvalue is None:
                call_result = self.call_vrep(vrep.simxCallScriptFunction, [self.clientID, "Open_Port", vrep.sim_scripttype_customizationscript, 'getsimstate', [], [], [], bytearray(), vrep.simx_opmode_blocking])
                try:
                    returnvalue = call_result[0][0]
                except:
                    print('couldnt get simulation state. got this instead:', call_result, ' (trying again in 0.5 s)')
                    if attempt_nr > 10:
                        if self.world.vrep_watchdog is not None:
                            print('killing vrep before trying again.')
                            self.world.vrep_watchdog.pause()
                            print("state() paused watchdog")
                            self.world.vrep_watchdog.kill_vrep()
                            print("state() called kill, waiting 5 secs, then resuming")
                            time.sleep(5)  # wait a bit before resuming watchdog.
                            self.world.vrep_watchdog.resume()
                            print("state() resumed watchdog")
                            print("stopping simulation reset")
                        else:
                            self.logger.error("VREP does not react. Please restart")
                        return None
                    else:
                        attempt_nr += 1
                        time.sleep(0.5)
            return returnvalue

        _state = state()
        while _state != vrep.sim_simulation_stopped:
            if _state is None:
                return
            time.sleep(0.01)
            _state = state()

        if self.world.synchronous_mode:
            self.call_vrep(vrep.simxSynchronous, [self.clientID, True])

        self.call_vrep(vrep.simxStartSimulation, [self.clientID, vrep.simx_opmode_oneshot], debugprint=False)

        _state = state()
        readystate = vrep.sim_simulation_advancing if self.world.synchronous_mode else vrep.sim_simulation_advancing_running
        while _state != readystate:
            if _state is None:
                return
            time.sleep(0.01)
            _state = state()

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

        if self.world.synchronous_mode:
            self.call_vrep(vrep.simxSynchronousTrigger, [self.clientID])

        self.read_from_world()
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

        joint_ids, something, data, se = self.call_vrep(vrep.simxGetObjectGroupData, [self.clientID, vrep.sim_object_joint_type, 15, vrep.simx_opmode_streaming])

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
                                                                                  vrep.simx_opmode_streaming])


class OneBallRobot(Robot, VrepGreyscaleVisionMixin, VrepCollisionsMixin, VrepOneBallGameMixin):
    """ A Worldadapter to play the one-ball-reaching-task """

    @classmethod
    def get_config_options(cls):
        """ I've found no way around this yet """
        parameters = []
        parameters.extend(Robot.get_config_options())
        parameters.extend(VrepCollisionsMixin.get_config_options())
        parameters.extend(VrepGreyscaleVisionMixin.get_config_options())
        parameters.extend(VrepOneBallGameMixin.get_config_options())
        return parameters


class IKRobotWithGreyscaleVision(Robot, VrepGreyscaleVisionMixin, Vrep6DObjectsMixin):
    """ A Worldadapter to control a robot with IK + arbitrary scene objects, based on a greyscale vision stream """

    @classmethod
    def get_config_options(cls):
        """ I've found no way around this yet """
        parameters = []
        parameters.extend(Robot.get_config_options())
        parameters.extend(VrepGreyscaleVisionMixin.get_config_options())
        parameters.extend(Vrep6DObjectsMixin.get_config_options())
        return parameters

class IKRobot(Robot, Vrep6DObjectsMixin):
    """ A Worldadapter to control a robot with IK + arbitrary scene objects """

    @classmethod
    def get_config_options(cls):
        """ I've found no way around this yet """
        parameters = []
        parameters.extend(Robot.get_config_options())
        parameters.extend(Vrep6DObjectsMixin.get_config_options())
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

    def write_to_world(self):
        restart = self._get_datatarget_value('restart') > 0.9 and self.world.current_step - self.last_restart >= 5
        # simulation restart
        if restart:
            return self.reset_simulation_state()
        super().write_to_world()

    def fetch_sensor_and_feedback_values_from_simulation(self, targets, include_feedback=False):
        if not self.world.connection_daemon.is_connected:
            if self.block_runner_if_connection_lost:
                while not self.world.connection_daemon.is_connected:
                    time.sleep(0.5)
            else:
                return

        if self.world.connection_daemon.clientID != self.clientID:
            self.initialize()
