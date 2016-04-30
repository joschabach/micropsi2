import math
import time
import logging
import numpy as np
from micropsi_core.world.iiwasim import vrep
from micropsi_core.world.iiwasim import vrepConst
from micropsi_core.world.world import World
from micropsi_core.world.worldadapter import ArrayWorldAdapter


class iiwasim(World):
    """ A simulated KUKA iiwa, using the vrep robot simulator

        In V-REP, the following setup has to be performed:
        - An LBR_iiwa_7_R800 has to have been added to the scene
        - simExtRemoteApiStart(19999) has to have been run
        - the simulation must have been started

    """

    supported_worldadapters = ['iiwa']

    def __init__(self, filename, world_type="iiwasim", name="", owner="", engine=None, uid=None, version=1, config={}):
        World.__init__(self, filename, world_type=world_type, name=name, owner=owner, uid=uid, version=version)

        vrep.simxFinish(-1) # just in case, close all opened connections
        self.clientID = vrep.simxStart('127.0.0.1', 19999, True, True, 5000, 5) # Connect to V-REP
        if self.clientID == -1:
            raise Exception("Could not connect to v-rep.")

        self.logger.info("Connected to local V-REP at port 19999")

        res, pingtime = vrep.simxGetPingTime(self.clientID)
        self.handle_res(res)

        self.logger.info('Ping time to v-rep: %dms' % pingtime)

        res, self.iiwa_handle = vrep.simxGetObjectHandle(self.clientID, "LBR_iiwa_7_R800", vrep.simx_opmode_blocking)
        self.handle_res(res)
        if self.iiwa_handle == 0:
            raise Exception("There seems to be no robot with the name LBR_iiwa_7_R800 in the v-rep simulation.")

        res, self.joints = vrep.simxGetObjects(self.clientID, vrep.sim_object_joint_type, vrep.simx_opmode_blocking)
        self.handle_res(res)
        if len(self.joints) != 7:
            raise Exception("Could not get handles for all 7 joints of the LBR_iiwa_7_R800.")

        res, self.observer_handle = vrep.simxGetObjectHandle(self.clientID, "Observer", vrep.simx_opmode_blocking)
        self.handle_res(res)
        if self.observer_handle == 0:
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

    def handle_res(self, res):
        if res != vrep.simx_return_ok:
            error = vrep.simxGetLastErrors(self.clientID, vrep.simx_opmode_blocking)
            self.logger.warn("v-rep call returned error code %d, error: %s" % (res, error))


class iiwa(ArrayWorldAdapter):

    def __init__(self, world, uid=None, **data):
        super().__init__(world, uid, **data)

        self.available_datatargets = []
        self.available_datasources = []

        for i in range(len(self.world.joints)):
            self.available_datatargets.append("joint_%s" % str(i+1))

        for y in range(self.world.vision_resolution[1]):
            for x in range(self.world.vision_resolution[0]):
                self.available_datasources.append("px_%d_%d" % (x, y))

    def get_available_datasources(self):
        return self.available_datasources

    def get_available_datatargets(self):
        return self.available_datatargets

    def update_data_sources_and_targets(self):
        vrep.simxPauseCommunication(self.world.clientID, True)
        for i, joint_handle in enumerate(self.world.joints):
            tval = self.datatarget_values[i] * math.pi
            vrep.simxSetJointTargetPosition(self.world.clientID, joint_handle, tval, vrep.simx_opmode_oneshot)
        vrep.simxPauseCommunication(self.world.clientID, False)

        res, joint_ids, something, data, se = vrep.simxGetObjectGroupData(self.world.clientID, vrep.sim_object_joint_type, 15, vrep.simx_opmode_blocking)
        self.datatarget_feedback_values = [0] * len(self.available_datatargets)
        for i, joint_handle in enumerate(self.world.joints):
            tval = self.datatarget_values[i]
            rval = data[i*2] / math.pi
            if abs(rval) - abs(tval) < .0001:
                self.datatarget_feedback_values[i] = 1

        # if no observer present, don't query vision data
        if self.world.observer_handle == 0:
            return

        res, resolution, image = vrep.simxGetVisionSensorImage(self.world.clientID, self.world.observer_handle, 0, vrep.simx_opmode_buffer)
        rgb_image = np.reshape(np.asarray(image, dtype=np.uint8), (self.world.vision_resolution[0]*self.world.vision_resolution[1], 3)).astype(np.float32)
        rgb_image /= 255.
        y_image = np.asarray([.2126 * px[0] + .7152 * px[1] + .0722 * px[2] for px in rgb_image])[::-1]   # todo: npyify and make faster

        self.datasource_values = y_image

        # images for debug purposes, should later be used in the world's GUI
        # maybe use matplotlib instead of PIL?

        #from PIL import Image
        #img = Image.new('L', self.world.vision_resolution)
        #y_image *= 255
        #img.putdata(y_image.astype(np.uint8))
        #img.save('/tmp/test.png', 'PNG') #, transparency=0)