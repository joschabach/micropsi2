import math
import time
import logging
import numpy as np
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt

from io import BytesIO
import base64
import random

import vrep
from micropsi_core.world.world import World
from micropsi_core.world.worldadapter import ArrayWorldAdapter


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

        vrep.simxFinish(-1)  # just in case, close all opened connections
        self.clientID = vrep.simxStart('127.0.0.1', 19999, True, 0, 5000, 5)  # Connect to V-REP
        if self.clientID == -1:
            raise Exception("Could not connect to v-rep.")

        self.logger.info("Connected to local V-REP at port 19999")

        res, pingtime = vrep.simxGetPingTime(self.clientID)
        self.handle_res(res)

        self.logger.info('Ping time to v-rep: %dms' % pingtime)

        res, self.iiwa_handle = vrep.simxGetObjectHandle(self.clientID, self.robot_name, vrep.simx_opmode_blocking)
        self.handle_res(res)
        if self.iiwa_handle < 1:
            raise Exception("There seems to be no robot with the name %s in the v-rep simulation." % self.robot_name)

        res, self.joints = vrep.simxGetObjects(self.clientID, vrep.sim_object_joint_type, vrep.simx_opmode_blocking)
        self.handle_res(res)
        self.logger.info("Found robot with %d joints" % len(self.joints))

        res, self.ball_handle = vrep.simxGetObjectHandle(self.clientID, "Ball", vrep.simx_opmode_blocking)
        self.handle_res(res)
        if self.ball_handle < 1:
            self.logger.warn("Could not get handle for Ball object, distance values will not be available.")
        else:
            res, _ = vrep.simxGetObjectPosition(self.clientID, self.ball_handle, -1, vrep.simx_opmode_streaming)
            if res != 0 and res != 1:
                self.handle_res(res)
            res, _ = vrep.simxGetObjectPosition(self.clientID, self.joints[len(self.joints)-1], -1, vrep.simx_opmode_streaming)
            if res != 0 and res != 1:
                self.handle_res(res)

        if self.vision_type == "grayscale":
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
                        raise Exception("Could not determine vision resolution after 1 second wait time.")
                    else:
                        self.logger.info("Vision resolution is %s" % str(self.vision_resolution))

        from micropsi_core.runtime import add_signal_handler
        add_signal_handler(self.kill_vrep_connection)


    def handle_res(self, res):
        if res != vrep.simx_return_ok:
            error = vrep.simxGetLastErrors(self.clientID, vrep.simx_opmode_blocking)
            self.logger.warn("v-rep call returned error code %d, error: %s" % (res, error))

    def get_world_view(self, step):
        if self.vision_type == "grayscale":
            plots = {}
            for uid in self.agents:
                image = self.agents[uid].image
                if image:
                    bio = BytesIO()
                    image.figure.savefig(bio, format="png")
                    plots[uid] = base64.encodebytes(bio.getvalue()).decode("utf-8")

            return {
                'objects': self.get_world_objects(),
                'agents': self.data.get('agents', {}),
                'current_step': self.current_step,
                'plots': plots
            }
        else:
            return None

    def kill_vrep_connection(self, *args):
        vrep.simxFinish(-1)

    def __del__(self):
        self.kill_vrep_connection()


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
             'options': ["force/torque", "angles", "movements"]},
            {'name': 'vision_type',
             'description': 'Type of vision information to receive',
             'default': 'none',
             'options': ["none", "grayscale"]}
        ]


class Robot(ArrayWorldAdapter):

    def __init__(self, world, uid=None, **data):

        self.available_datatargets = []
        self.available_datasources = []

        self.available_datasources.append("distance")

        self.available_datatargets.append("restart")
        self.available_datatargets.append("execute")

        for i in range(len(world.joints)):
            self.available_datatargets.append("joint_%s" % str(i + 1))

        for i in range(len(world.joints)):
            self.available_datasources.append("joint_angle_%s" % str(i + 1))

        for i in range(len(world.joints)):
            self.available_datasources.append("joint_force_%s" % str(i + 1))

        super().__init__(world, uid, **data)

        self.current_angle_target_values = np.zeros_like(self.world.joints)

        self.restart_offset = 0
        self.execute_offset = 1
        self.joint_offset = 2

        self.distance_offset = 0
        self.joint_angle_offset = 1
        self.joint_force_offset = self.joint_angle_offset + len(self.world.joints)

        if self.world.vision_type == "grayscale":
            self.image_offset = self.joint_force_offset + len(self.world.joints)
            self.image_length = self.world.vision_resolution[0] * self.world.vision_resolution[1]

            for y in range(self.world.vision_resolution[1]):
                for x in range(self.world.vision_resolution[0]):
                    self.available_datasources.append("px_%d_%d" % (x, y))

            self.image = plt.imshow(np.zeros(shape=(self.world.vision_resolution[0],self.world.vision_resolution[1])), cmap="bone")
            self.image.norm.vmin = 0
            self.image.norm.vmax = 1

        self.fetch_sensor_and_feedback_values_from_simulation()

    def get_available_datasources(self):
        return self.available_datasources

    def get_available_datatargets(self):
        return self.available_datatargets

    def update_data_sources_and_targets(self):

        old_datasource_values = np.array(self.datasource_values)

        self.datatarget_feedback_values = [0] * len(self.available_datatargets)
        self.datasource_values = [0] * len(self.available_datasources)

        restart = self.datatarget_values[self.restart_offset] > 0.9
        execute = self.datatarget_values[self.execute_offset] > 0.9

        # simulation restart
        if restart:
            vrep.simxStopSimulation(self.world.clientID, vrep.simx_opmode_oneshot)
            time.sleep(1)
            vrep.simxStartSimulation(self.world.clientID, vrep.simx_opmode_oneshot)

            vrep.simxPauseCommunication(self.world.clientID, True)
            for i, joint_handle in enumerate(self.world.joints):
                self.datatarget_values[self.joint_offset + i] = random.uniform(-0.8, 0.8)
                self.current_angle_target_values[i] = self.datatarget_values[self.joint_offset + i]
                tval = self.current_angle_target_values[i] * math.pi
                vrep.simxSetJointPosition(self.world.clientID, joint_handle, tval, vrep.simx_opmode_oneshot)
            vrep.simxPauseCommunication(self.world.clientID, False)

            self.fetch_sensor_and_feedback_values_from_simulation()
            return

        # execute movement, send new target angles
        if execute:
            self.current_angle_target_values = np.array(self.datatarget_values[self.joint_offset:self.joint_offset+len(self.world.joints)])
            vrep.simxPauseCommunication(self.world.clientID, True)
            for i, joint_handle in enumerate(self.world.joints):
                tval = self.current_angle_target_values[i] * math.pi
                if self.world.control_type == "force/torque":
                    vrep.simxSetJointTargetPosition(self.world.clientID, joint_handle, tval, vrep.simx_opmode_oneshot)
                elif self.world.control_type == "angles":
                    vrep.simxSetJointPosition(self.world.clientID, joint_handle, tval, vrep.simx_opmode_oneshot)
                elif self.world.control_type == "movements":
                    tval += (old_datasource_values[self.joint_angle_offset + i]) * math.pi
                    vrep.simxSetJointPosition(self.world.clientID, joint_handle, tval, vrep.simx_opmode_oneshot)
            vrep.simxPauseCommunication(self.world.clientID, False)

        # read joint angle and force values
        self.fetch_sensor_and_feedback_values_from_simulation(True)

        # read vision data
        # if no observer present, don't query vision data
        if self.world.vision_type != "grayscale":
            return

        res, resolution, image = vrep.simxGetVisionSensorImage(self.world.clientID, self.world.observer_handle, 0, vrep.simx_opmode_buffer)
        rgb_image = np.reshape(np.asarray(image, dtype=np.uint8), (self.world.vision_resolution[0] * self.world.vision_resolution[1], 3)).astype(np.float32)
        rgb_image /= 255.
        y_image = np.asarray([.2126 * px[0] + .7152 * px[1] + .0722 * px[2] for px in rgb_image]).astype(np.float32).reshape((self.world.vision_resolution[0], self.world.vision_resolution[1]))[::-1,:]   # todo: npyify and make faster
        self.datasource_values[self.image_offset:len(self.datasource_values)-1] = y_image.flatten()

        self.image.set_data(y_image)

        return self.image

    def fetch_sensor_and_feedback_values_from_simulation(self, include_feedback=False):

        # get data and feedback
        # read distance value
        if self.world.ball_handle > 0:
            res, ball_pos = vrep.simxGetObjectPosition(self.world.clientID, self.world.ball_handle, -1, vrep.simx_opmode_buffer)
            res, joint_pos = vrep.simxGetObjectPosition(self.world.clientID, self.world.joints[len(self.world.joints)-1], -1, vrep.simx_opmode_streaming)
            dist = np.linalg.norm(np.array(ball_pos) - np.array(joint_pos))
            self.datasource_values[self.distance_offset] = dist

        res, joint_ids, something, data, se = vrep.simxGetObjectGroupData(self.world.clientID, vrep.sim_object_joint_type, 15, vrep.simx_opmode_blocking)

        if len(data) == 0:
            self.world.logger.warning("No data from vrep received")
            return

        for i, joint_handle in enumerate(self.world.joints):
            target_angle = self.datatarget_values[self.joint_offset + i]
            angle = 0
            force = 0
            if self.world.control_type == "force/torque":
                angle = data[i*2] / math.pi
                force = data[i*2 + 1]
                if abs(angle) - abs(target_angle) < .001 and include_feedback:
                    self.datatarget_feedback_values[self.joint_offset + i] = 1
            elif self.world.control_type == "angles":
                angle = data[i * 2] / math.pi
            elif self.world.control_type == "movements":
                angle = data[i * 2] / math.pi
            self.datasource_values[self.joint_angle_offset + i] = angle
            self.datasource_values[self.joint_force_offset + i] = force
