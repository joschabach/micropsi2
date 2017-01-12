import math
import time
import logging
import numpy as np
import matplotlib

import threading
import socket
import struct
import numpy as np

from micropsi_core.world.world import World
from micropsi_core.world.worldadapter import ArrayWorldAdapter, WorldAdapterMixin

from micropsi_core.world.ur.optoforce_mixin import OptoForce6DMixin
from micropsi_core.world.ur.speedj_control_mixin import SpeedJControlMixin

class URConnection(threading.Thread):
    """
    Connection thread to continuously read the UR 125Hz real time interface
    """

    def __init__(self, host):
        threading.Thread.__init__(self)
        self.host = host
        self.port = 30003
        self.socket = None
        self.daemon = True
        self.stop = threading.Event()
        self.is_connected = False
        self.logger = logging.getLogger("world")

        self.tool_pos_6D = np.zeros(6)
        self.tool_frc_6D = np.zeros(6)

        self.is_active = True
        self.start()

    def run(self):
        self.reconnect()
        while self.is_active:
            self.update_values_from_robot()

    def reconnect(self):
        self.is_connected = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        self.logger.info("Connected to UR realtime interface at %s:%d" % (self.host, self.port))
        self.is_connected = True

    def terminate(self):
        self.stop.set()

    def write_command_to_robot(self, command):
        #print(command)
        self.socket.sendall(command.encode("ascii"))

    def update_values_from_robot(self):
        if not self.is_connected:
            return

        read = 0
        pkt_messagelength = self.socket.recv(4)  # message length
        read += 4
        messagelength = struct.unpack('!i', pkt_messagelength)[0]

        pkt_timestamp = self.socket.recv(8)  # timestamp
        read += 8

        pkt_tgt_joint_pos = self.socket.recv(48)  # target joint positions
        read += 48

        pkt_tgt_joint_vel = self.socket.recv(48)  # target joint velocities
        read += 48

        pkt_tgt_joint_acc = self.socket.recv(48)  # target joint accelerations
        read += 48

        pkt_tgt_joint_cur = self.socket.recv(48)  # target joint currents
        read += 48

        pkt_tgt_joint_tqe = self.socket.recv(48)  # target joint moments (torques)
        read += 48

        pkt_act_joint_pos = self.socket.recv(48)  # actual joint positions
        read += 48

        pkt_act_joint_vel = self.socket.recv(48)  # actual joint velocities
        read += 48

        pkt_act_joint_cur = self.socket.recv(48)  # actual joint currents
        read += 48

        pkt_joint_control_cur = self.socket.recv(48)  # actual joint control currents
        read += 48

        pkt_act_tool_x = self.socket.recv(8)
        read += 8
        self.tool_pos_6D[0] = struct.unpack('!d', pkt_act_tool_x)[0] * 1000      # actual tool x

        pkt_act_tool_y = self.socket.recv(8)
        read += 8
        self.tool_pos_6D[1] = struct.unpack('!d', pkt_act_tool_y)[0] * 1000      # actual tool y

        pkt_act_tool_z = self.socket.recv(8)
        read += 8
        self.tool_pos_6D[2] = struct.unpack('!d', pkt_act_tool_z)[0] * 1000      # actual tool z

        pkt_act_tool_rx = self.socket.recv(8)
        read += 8
        self.tool_pos_6D[3] = struct.unpack('!d', pkt_act_tool_rx)[0]            # actual tool x rotation

        pkt_act_tool_ry = self.socket.recv(8)
        read += 8
        self.tool_pos_6D[4] = struct.unpack('!d', pkt_act_tool_ry)[0]            # actual tool y rotation

        pkt_act_tool_rz = self.socket.recv(8)
        read += 8
        self.tool_pos_6D[5] = struct.unpack('!d', pkt_act_tool_rz)[0]            # actual tool z rotation

        pkt_act_tool_speed = self.socket.recv(48)  # actual tool speed cartesian
        read += 48

        pkt_act_tool_frc_x = self.socket.recv(8)
        read += 8
        self.tool_frc_6D[0] = struct.unpack('!d', pkt_act_tool_frc_x)[0]         # tool force x

        pkt_act_tool_frc_y = self.socket.recv(8)
        read += 8
        self.tool_frc_6D[1] = struct.unpack('!d', pkt_act_tool_frc_y)[0]         # tool force y

        pkt_act_tool_frc_z = self.socket.recv(8)
        read += 8
        self.tool_frc_6D[2] = struct.unpack('!d', pkt_act_tool_frc_z)[0]         # tool force z

        pkt_act_tool_frc_rx = self.socket.recv(8)
        read += 8
        self.tool_frc_6D[3] = struct.unpack('!d', pkt_act_tool_frc_rx)[0]        # tool force rx

        pkt_act_tool_frc_ry = self.socket.recv(8)
        read += 8
        self.tool_frc_6D[4] = struct.unpack('!d', pkt_act_tool_frc_ry)[0]        # tool force ry

        pkt_act_tool_frc_rz = self.socket.recv(8)
        read += 8
        self.tool_frc_6D[5] = struct.unpack('!d', pkt_act_tool_frc_rz)[0]        # tool force rz

        # read the rest of the message
        self.socket.recv(messagelength - read)


class URWorld(World):
    """
    A Universal Robots environment, using the port 30003 realtime ("matlab") interface of the
    robot controller.
    """
    supported_worldadapters = ['UR', 'URSpeedJControlled', 'UROptoForce6D']

    #assets = {
    #    'template': 'ur/ur.tpl',
    #    'js': "ur/ur.js",
    #}

    def __init__(self, filename, world_type="URWorld", name="", owner="", engine=None, uid=None, version=1, config={}):
        World.__init__(self, filename, world_type=world_type, name=name, owner=owner, uid=uid, version=version, config=config)

        self.connection_daemon = URConnection(config['ur_ip'])

        time.sleep(5)  # wait for the daemon to get started before continuing.

    def get_world_view(self, step):
        return None

    def shutdown(self):
        for uid in self.agents:
            self.agents[uid].shutdown()

    def signal_handler(self, *args):
        self.shutdown()

    def __del__(self):
        self.shutdown()

    @classmethod
    def get_config_options(cls):
        return [
            {'name': 'ur_ip',
             'default': '127.0.0.1'}
        ]


class UR(WorldAdapterMixin, ArrayWorldAdapter):
    """
    The basic worldadapter to control a Universal Robots robot.
    """

    @classmethod
    def get_config_options(cls):
        options = super().get_config_options()
        #options.extend([])
        return options

    def __init__(self, world, uid=None, **data):
        super().__init__(world, uid, **data)
        self.initialized = False
        self.initialize()

    def initialize(self):

        self.datasource_names = []
        self.datatarget_names = []
        self.datasource_values = np.zeros(0)
        self.datatarget_values = np.zeros(0)
        self.datatarget_feedback_values = np.zeros(0)

        super().initialize()

        self.add_datasource("tip-x")
        self.add_datasource("tip-y")
        self.add_datasource("tip-z")
        self.add_datasource("tip-rx")
        self.add_datasource("tip-ry")
        self.add_datasource("tip-rz")

        if self.nodenet:
            self.nodenet.worldadapter_instance = self
        self.initialized = True

        self.reset_simulation_state()

    def update_data_sources_and_targets(self):
        self.write_to_world()
        self.read_from_world()

    def read_from_world(self):
        super().read_from_world()
        self.set_datasource_range("tip-x", np.copy(self.world.connection_daemon.tool_pos_6D))

    def reset_datatargets(self):
        self.datatarget_values = np.zeros_like(self.datatarget_values)

    def shutdown(self):
        pass


class URSpeedJControlled(UR, SpeedJControlMixin):
    """
    A world adapter for a UR system that can be controlled using speedj commands.
    """


class UROptoForce6D(UR, OptoForce6DMixin):
    """
    A world adapter for a UR system with an OptoForce 6D F/T sensor.
    """
