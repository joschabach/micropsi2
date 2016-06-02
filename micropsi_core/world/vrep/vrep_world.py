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

import vrep
from micropsi_core.world.world import World
from micropsi_core.world.worldadapter import ArrayWorldAdapter


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
    supported_worldadapters = ['Robot']

    assets = {
        'template': 'vrep/vrep.tpl',
        'js': "vrep/vrep.js",
    }

    def __init__(self, filename, world_type="VREPWorld", name="", owner="", engine=None, uid=None, version=1, config={}):
        World.__init__(self, filename, world_type=world_type, name=name, owner=owner, uid=uid, version=version)

        self.robot_name = config['robot_name']
        self.vision_type = config['vision_type']
        self.control_type = config['control_type']
        self.collision_name = config.get('collision_name', '')

        self.randomize_arm = config['randomize_arm']
        self.randomize_ball = config['randomize_ball']

        self.connection_daemon = VREPConnection(config['vrep_host'], int(config['vrep_port']), connection_listeners=[self])

        from micropsi_core.runtime import add_signal_handler
        add_signal_handler(self.kill_vrep_connection)

    def get_world_view(self, step):
        data = {
            'objects': self.get_world_objects(),
            'agents': self.data.get('agents', {}),
            'current_step': self.current_step,
        }
        if self.vision_type == "grayscale":
            plots = {}
            for uid in self.agents:
                image = self.agents[uid].image
                if image:
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
             'default': 19999},
            {'name': 'robot_name',
             'description': 'The name of the robot object in V-REP',
             'default': 'LBR_iiwa_7_R800',
             'options': ["LBR_iiwa_7_R800", "MTB_Robot"]},
            {'name': 'collision_name',
             'default': 'Collision',
             'description': 'The name of the robot\'s collision handle'},
            {'name': 'control_type',
             'description': 'The type of input sent to the robot',
             'default': 'force/torque',
             'options': ["force/torque", "force/torque-sync", "angles", "movements"]},
            {'name': 'vision_type',
             'description': 'Type of vision information to receive',
             'default': 'none',
             'options': ["none", "grayscale"]},
            {'name': 'randomize_arm',
             'description': 'Initialize the robot arm randomly',
             'default': 'False',
             'options': ["False", "True"]},
            {'name': 'randomize_ball',
             'description': 'Initialize the ball position randomly',
             'default': 'False',
             'options': ["False", "True"]}
        ]


class Robot(ArrayWorldAdapter):

    block_runner_if_connection_lost = True

    def __init__(self, world, uid=None, **data):
        self.available_datatargets = []
        self.available_datasources = []
        super().__init__(world, uid, **data)

        self.get_vrep_data()

    def handle_res(self, res):
        if res != vrep.simx_return_ok:
            self.logger.warn("vrep call returned error, reconnecting instance")
            self.world.connection_daemon.resume()

    def on_vrep_connect(self):
        """ is called by the world, if a connection was established """
        self.get_vrep_data()

    def get_vrep_data(self):

        self.clientID = self.world.connection_daemon.clientID

        self.joints = []
        self.vision_resolution = []
        self.collision_handle = -1
        self.robot_handle = -1
        self.ball_handle = -1
        self.robot_position = []

        res, self.robot_handle = vrep.simxGetObjectHandle(self.clientID, self.world.robot_name, vrep.simx_opmode_blocking)
        self.handle_res(res)
        if self.robot_handle < 1:
            self.logger.critical("There seems to be no robot with the name %s in the v-rep simulation." % self.world.robot_name)

        res, self.joints = vrep.simxGetObjects(self.clientID, vrep.sim_object_joint_type, vrep.simx_opmode_blocking)
        self.handle_res(res)
        self.logger.info("Found robot with %d joints" % len(self.joints))

        if self.world.collision_name:
            res, self.collision_handle = vrep.simxGetCollisionHandle(self.clientID, self.world.collision_name, vrep.simx_opmode_blocking)
            self.handle_res(res)
            if self.collision_handle > 0:
                res, collision_state = vrep.simxReadCollision(self.clientID, self.collision_handle, vrep.simx_opmode_streaming)
            else:
                self.logger.warning("Collision handle %s not found, not tracking collisions" % self.collision_name)

        res, self.ball_handle = vrep.simxGetObjectHandle(self.clientID, "Ball", vrep.simx_opmode_blocking)
        self.handle_res(res)
        if self.ball_handle < 1:
            self.logger.warn("Could not get handle for Ball object, distance values will not be available.")
        else:
            res, _ = vrep.simxGetObjectPosition(self.clientID, self.ball_handle, -1, vrep.simx_opmode_streaming)
            if res != 0 and res != 1:
                self.handle_res(res)
            res, _ = vrep.simxGetObjectPosition(self.clientID, self.joints[len(self.joints) - 1], -1, vrep.simx_opmode_streaming)
            if res != 0 and res != 1:
                self.handle_res(res)
            res, robot_position = vrep.simxGetObjectPosition(self.clientID, self.robot_handle, -1, vrep.simx_opmode_blocking)
            if res != 0 and res != 1:
                self.handle_res(res)
            self.robot_position = robot_position

        if self.world.vision_type == "grayscale":
            res, self.observer_handle = vrep.simxGetObjectHandle(self.clientID, "Observer", vrep.simx_opmode_blocking)
            self.handle_res(res)
            if self.observer_handle < 1:
                self.logger.warn("Could not get handle for Observer vision sensor, vision will not be available.")
            else:
                res, resolution, image = vrep.simxGetVisionSensorImage(self.clientID, self.observer_handle, 0, vrep.simx_opmode_streaming) # _split+4000)
                if res != 0 and res != 1:
                    self.handle_res(res)
                else:
                    time.sleep(1)
                    res, resolution, image = vrep.simxGetVisionSensorImage(self.clientID, self.observer_handle, 0, vrep.simx_opmode_buffer)
                    self.vision_resolution = resolution
                    if len(resolution) != 2:
                        self.logger.error("Could not determine vision resolution after 1 second wait time.")
                    else:
                        self.logger.info("Vision resolution is %s" % str(self.vision_resolution))

        self.available_datatargets = []
        self.available_datasources = []
        self.available_datasources.append("ball-distance")
        self.available_datasources.append("collision")
        self.available_datasources.append("ball-x")
        self.available_datasources.append("ball-y")

        self.available_datasources.append("tip-x")
        self.available_datasources.append("tip-y")
        self.available_datasources.append("tip-z")

        self.available_datatargets.append("restart")
        self.available_datatargets.append("execute")

        for i in range(len(self.joints)):
            self.available_datatargets.append("joint_%s" % str(i + 1))

        for i in range(len(self.joints)):
            self.available_datasources.append("joint_angle_%s" % str(i + 1))

        for i in range(len(self.joints)):
            self.available_datasources.append("joint_force_%s" % str(i + 1))

        self.last_restart = 0

        self.current_angle_target_values = np.zeros_like(self.joints)

        self.restart_offset = 0
        self.execute_offset = 1
        self.joint_offset = 2

        self.distance_offset = 0
        self.collision_offset = 1
        self.ball_position_offset = 2
        self.tip_position_offset = self.ball_position_offset + 2  # because ball_x, ball_y
        self.joint_angle_offset = self.tip_position_offset + 3  # because tipx tipy tipz
        self.joint_force_offset = self.joint_angle_offset + len(self.joints)

        if self.world.vision_type == "grayscale":
            self.image_offset = self.joint_force_offset + len(self.joints)
            self.image_length = self.vision_resolution[0] * self.vision_resolution[1]

            for y in range(self.vision_resolution[1]):
                for x in range(self.vision_resolution[0]):
                    self.available_datasources.append("px_%d_%d" % (x, y))

            self.image = plt.imshow(np.zeros(shape=(self.vision_resolution[0], self.vision_resolution[1])), cmap="bone")
            self.image.norm.vmin = 0
            self.image.norm.vmax = 1

        if self.nodenet:
            self.nodenet.worldadapter_instance = self
        self.datasource_values = [0] * len(self.available_datasources)
        self.datatarget_values = [0] * len(self.available_datatargets)
        self.datatarget_feedback_values = [0] * len(self.available_datatargets)
        self.fetch_sensor_and_feedback_values_from_simulation(None, initial=True)

    def get_available_datasources(self):
        return self.available_datasources

    def get_available_datatargets(self):
        return self.available_datatargets

    def update_data_sources_and_targets(self):

        old_datasource_values = np.array(self.datasource_values)

        self.datatarget_feedback_values = [0] * len(self.available_datatargets)
        self.datasource_values = [0] * len(self.available_datasources)
        tvals = None

        restart = self.datatarget_values[self.restart_offset] > 0.9 and self.world.current_step - self.last_restart >= 5
        execute = self.datatarget_values[self.execute_offset] > 0.9

        # simulation restart
        if restart:
            vrep.simxStopSimulation(self.clientID, vrep.simx_opmode_oneshot)
            time.sleep(0.5)
            res = vrep.simxStartSimulation(self.clientID, vrep.simx_opmode_oneshot)
            self.handle_res(res)
            time.sleep(0.5)

            if self.world.randomize_arm == "True":
                vrep.simxPauseCommunication(self.clientID, True)
                for i, joint_handle in enumerate(self.joints):
                    self.datatarget_values[self.joint_offset + i] = random.uniform(-0.8, 0.8)
                    self.current_angle_target_values[i] = self.datatarget_values[self.joint_offset + i]
                    tval = self.current_angle_target_values[i] * math.pi
                    vrep.simxSetJointPosition(self.clientID, joint_handle, tval, vrep.simx_opmode_oneshot)
                vrep.simxPauseCommunication(self.clientID, False)

            if self.world.randomize_ball == "True":
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

                vrep.simxSetObjectPosition(self.clientID, self.ball_handle, self.robot_handle, [rx, ry], vrep.simx_opmode_blocking)

            self.fetch_sensor_and_feedback_values_from_simulation(None)
            self.last_restart = self.world.current_step
            return

        # execute movement, send new target angles
        if execute:
            tvals = [0] * len(self.available_datatargets)
            self.current_angle_target_values = np.array(self.datatarget_values[self.joint_offset:self.joint_offset+len(self.joints)])
            vrep.simxPauseCommunication(self.clientID, True)
            for i, joint_handle in enumerate(self.joints):
                tval = self.current_angle_target_values[i] * math.pi
                if self.world.control_type == "force/torque" or self.world.control_type == "force/torque-sync":
                    tval += (old_datasource_values[self.joint_angle_offset + i]) * math.pi
                    tvals[i] = tval
                    vrep.simxSetJointTargetPosition(self.clientID, joint_handle, tval, vrep.simx_opmode_oneshot)
                elif self.world.control_type == "angles":
                    vrep.simxSetJointPosition(self.clientID, joint_handle, tval, vrep.simx_opmode_oneshot)
                elif self.world.control_type == "movements":
                    tval += (old_datasource_values[self.joint_angle_offset + i]) * math.pi
                    vrep.simxSetJointPosition(self.clientID, joint_handle, tval, vrep.simx_opmode_oneshot)
            vrep.simxPauseCommunication(self.clientID, False)

        # read joint angle and force values
        self.fetch_sensor_and_feedback_values_from_simulation(tvals, True)

        # read vision data
        # if no observer present, don't query vision data
        if self.world.vision_type != "grayscale":
            return

        res, resolution, image = vrep.simxGetVisionSensorImage(self.clientID, self.observer_handle, 0, vrep.simx_opmode_buffer)
        self.handle_res(res)
        if len(image):
            rgb_image = np.reshape(np.asarray(image, dtype=np.uint8), (self.vision_resolution[0] * self.vision_resolution[1], 3)).astype(np.float32)
            rgb_image /= 255.
            y_image = np.asarray([.2126 * px[0] + .7152 * px[1] + .0722 * px[2] for px in rgb_image]).astype(np.float32).reshape((self.vision_resolution[0], self.vision_resolution[1]))[::-1,:]   # todo: npyify and make faster
            self.datasource_values[self.image_offset:len(self.datasource_values)-1] = y_image.flatten()

            self.image.set_data(y_image)

            return self.image

    def fetch_sensor_and_feedback_values_from_simulation(self, targets, include_feedback=False, initial=False):

        res, joint_pos = vrep.simxGetObjectPosition(self.clientID, self.joints[len(self.joints)-1], -1, vrep.simx_opmode_streaming)
        self.datasource_values[self.tip_position_offset + 0] = joint_pos[0] - self.robot_position[0]
        self.datasource_values[self.tip_position_offset + 1] = joint_pos[1] - self.robot_position[1]
        self.datasource_values[self.tip_position_offset + 2] = joint_pos[2] - self.robot_position[2]
        # get data and feedback
        # read distance value

        if not self.world.connection_daemon.is_connected:
            if self.block_runner_if_connection_lost and not initial:
                while not self.world.connection_daemon.is_connected:
                    time.sleep(0.5)
            else:
                return

        if self.world.connection_daemon.clientID != self.clientID:
            self.get_vrep_data()

        if self.ball_handle > 0:
            res, ball_pos = vrep.simxGetObjectPosition(self.clientID, self.ball_handle, -1, vrep.simx_opmode_buffer)
            res, joint_pos = vrep.simxGetObjectPosition(self.clientID, self.joints[len(self.joints)-1], -1, vrep.simx_opmode_streaming)

            relative_pos = [0,0]
            relative_pos[0] = ball_pos[0] - self.robot_position[0]
            relative_pos[1] = ball_pos[1] - self.robot_position[1]

            dist = np.linalg.norm(np.array(ball_pos) - np.array(joint_pos))
            self.datasource_values[self.distance_offset] = dist
            self.datasource_values[self.ball_position_offset + 0] = relative_pos[0]
            self.datasource_values[self.ball_position_offset + 1] = relative_pos[1]

        res, joint_ids, something, data, se = vrep.simxGetObjectGroupData(self.clientID, vrep.sim_object_joint_type, 15, vrep.simx_opmode_blocking)
        self.handle_res(res)

        if len(data) == 0:
            self.logger.warning("No data from vrep received. Sleeping for 5secs, the retrying.")
            time.sleep(1)

            res, joint_ids, something, data, se = vrep.simxGetObjectGroupData(self.clientID,
                                                                              vrep.sim_object_joint_type, 15,
                                                                              vrep.simx_opmode_blocking)
            self.handle_res(res)

            if len(data) == 0:
                self.logger.error("No data from vrep received on retry. Giving up and returning no data.")
            return

        movement_finished = False
        count = 0
        while not movement_finished:
            allgood = True
            for i, joint_handle in enumerate(self.joints):
                angle = 0
                force = 0
                if self.world.control_type == "force/torque" or self.world.control_type == "force/torque-sync":
                    angle = data[i*2]
                    force = data[i*2 + 1]
                    if targets is not None:
                        target_angle = targets[i]
                        if abs(abs(angle) - abs(target_angle)) < .001 and include_feedback:
                            self.datatarget_feedback_values[self.joint_offset + i] = 1
                        else:
                            allgood = False
                elif self.world.control_type == "angles":
                    angle = data[i * 2]
                elif self.world.control_type == "movements":
                    angle = data[i * 2]
                self.datasource_values[self.joint_angle_offset + i] = angle / math.pi
                self.datasource_values[self.joint_force_offset + i] = force

            movement_finished = allgood
            if not movement_finished:
                joint_positions = []
                for i, joint_handle in enumerate(self.joints):
                    joint_positions.append(data[i*2])

                count += 1
                if count == 10:
                    self.logger.warning("Robot did not complete movement in time, giving up.");
                    self.logger.warning("Joint   targets: %s" % str(targets));
                    self.logger.warning("Joint positions: %s" % str(joint_positions));
                    movement_finished = True
                time.sleep(0.2)
                res, joint_ids, something, data, se = vrep.simxGetObjectGroupData(self.clientID,
                                                                                  vrep.sim_object_joint_type, 15,
                                                                                  vrep.simx_opmode_blocking)
                self.handle_res(res)

        if self.collision_handle > 0:
            res, collision_state = vrep.simxReadCollision(self.clientID, self.collision_handle,
                                                          vrep.simx_opmode_buffer)
            self.datasource_values[self.collision_offset] = 1 if collision_state else 0
