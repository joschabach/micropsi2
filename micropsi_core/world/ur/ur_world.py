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

        self.joint_pos = np.zeros(6)
        self.joint_speeds = np.zeros(6)
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

        pkt_act_joint_pos_base = self.socket.recv(8)
        read += 8
        self.joint_pos[0] = struct.unpack('!d', pkt_act_joint_pos_base)[0]              # actual base position

        pkt_act_joint_pos_shoulder = self.socket.recv(8)
        read += 8
        self.joint_pos[1] = struct.unpack('!d', pkt_act_joint_pos_shoulder)[0]          # actual shoulder position

        pkt_act_joint_pos_elbow = self.socket.recv(8)
        read += 8
        self.joint_pos[2] = struct.unpack('!d', pkt_act_joint_pos_elbow)[0]             # actual elbow position

        pkt_act_joint_pos_wrist1 = self.socket.recv(8)
        read += 8
        self.joint_pos[3] = struct.unpack('!d', pkt_act_joint_pos_wrist1)[0]            # actual wrist1 position

        pkt_act_joint_pos_wrist2 = self.socket.recv(8)
        read += 8
        self.joint_pos[4] = struct.unpack('!d', pkt_act_joint_pos_wrist2)[0]            # actual wrist2 position

        pkt_act_joint_pos_wrist3 = self.socket.recv(8)
        read += 8
        self.joint_pos[5] = struct.unpack('!d', pkt_act_joint_pos_wrist3)[0]            # actual wrist3 position

        pkt_act_joint_speed_base = self.socket.recv(8)
        read += 8
        self.joint_speeds[0] = struct.unpack('!d', pkt_act_joint_speed_base)[0]         # actual base speed

        pkt_act_joint_speed_shoulder = self.socket.recv(8)
        read += 8
        self.joint_speeds[1] = struct.unpack('!d', pkt_act_joint_speed_shoulder)[0]     # actual shoulder speed

        pkt_act_joint_speed_elbow = self.socket.recv(8)
        read += 8
        self.joint_speeds[2] = struct.unpack('!d', pkt_act_joint_speed_elbow)[0]        # actual elbow speed

        pkt_act_joint_speed_wrist1 = self.socket.recv(8)
        read += 8
        self.joint_speeds[3] = struct.unpack('!d', pkt_act_joint_speed_wrist1)[0]       # actual wrist1 speed

        pkt_act_joint_speed_wrist2 = self.socket.recv(8)
        read += 8
        self.joint_speeds[4] = struct.unpack('!d', pkt_act_joint_speed_wrist2)[0]       # actual wrist2 speed

        pkt_act_joint_speed_wrist3 = self.socket.recv(8)
        read += 8
        self.joint_speeds[5] = struct.unpack('!d', pkt_act_joint_speed_wrist3)[0]       # actual wrist3 speed

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

        self.add_flow_datasource("tip-pos", 6, self.world.connection_daemon.tool_pos_6D)
        self.add_datasource("tip-pos-x")
        self.add_datasource("tip-pos-y")
        self.add_datasource("tip-pos-z")
        self.add_datasource("tip-pos-rx")
        self.add_datasource("tip-pos-ry")
        self.add_datasource("tip-pos-rz")

        self.add_flow_datasource("tip-force", 6, self.world.connection_daemon.tool_frc_6D)
        self.add_datasource("tip-force-x")
        self.add_datasource("tip-force-y")
        self.add_datasource("tip-force-z")
        self.add_datasource("tip-force-rx")
        self.add_datasource("tip-force-ry")
        self.add_datasource("tip-force-rz")

        self.add_flow_datasource("joint-pos", 6, self.world.connection_daemon.tool_frc_6D)
        self.add_datasource("joint-pos-base")
        self.add_datasource("joint-pos-shoulder")
        self.add_datasource("joint-pos-elbow")
        self.add_datasource("joint-pos-wrist1")
        self.add_datasource("joint-pos-wrist2")
        self.add_datasource("joint-pos-wrist3")

        self.add_flow_datasource("joint-speed", 6, self.world.connection_daemon.tool_frc_6D)
        self.add_datasource("joint-speed-base")
        self.add_datasource("joint-speed-shoulder")
        self.add_datasource("joint-speed-elbow")
        self.add_datasource("joint-speed-wrist1")
        self.add_datasource("joint-speed-wrist2")
        self.add_datasource("joint-speed-wrist3")

        if self.nodenet:
            self.nodenet.worldadapter_instance = self
        self.initialized = True

        self.reset_simulation_state()

    def update_data_sources_and_targets(self):
        self.write_to_world()
        self.read_from_world()

    def read_from_world(self):
        super().read_from_world()

        self.set_flow_datasource("tip-pos", np.copy(self.world.connection_daemon.tool_pos_6D))
        self.set_datasource_value("tip-pos-x", self.world.connection_daemon.tool_pos_6D[0])
        self.set_datasource_value("tip-pos-y", self.world.connection_daemon.tool_pos_6D[1])
        self.set_datasource_value("tip-pos-z", self.world.connection_daemon.tool_pos_6D[2])
        self.set_datasource_value("tip-pos-rx", self.world.connection_daemon.tool_pos_6D[3])
        self.set_datasource_value("tip-pos-ry", self.world.connection_daemon.tool_pos_6D[4])
        self.set_datasource_value("tip-pos-rz", self.world.connection_daemon.tool_pos_6D[5])

        self.set_flow_datasource("tip-force", np.copy(self.world.connection_daemon.tool_frc_6D))
        self.set_datasource_value("tip-force-x", self.world.connection_daemon.tool_frc_6D[0])
        self.set_datasource_value("tip-force-y", self.world.connection_daemon.tool_frc_6D[1])
        self.set_datasource_value("tip-force-z", self.world.connection_daemon.tool_frc_6D[2])
        self.set_datasource_value("tip-force-rx", self.world.connection_daemon.tool_frc_6D[3])
        self.set_datasource_value("tip-force-ry", self.world.connection_daemon.tool_frc_6D[4])
        self.set_datasource_value("tip-force-rz", self.world.connection_daemon.tool_frc_6D[5])

        self.set_flow_datasource("joint-pos", np.copy(self.world.connection_daemon.joint_pos))
        self.set_datasource_value("joint-pos-base", self.world.connection_daemon.joint_pos[0])
        self.set_datasource_value("joint-pos-shoulder", self.world.connection_daemon.joint_pos[1])
        self.set_datasource_value("joint-pos-elbow", self.world.connection_daemon.joint_pos[2])
        self.set_datasource_value("joint-pos-wrist1", self.world.connection_daemon.joint_pos[3])
        self.set_datasource_value("joint-pos-wrist2", self.world.connection_daemon.joint_pos[4])
        self.set_datasource_value("joint-pos-wrist3", self.world.connection_daemon.joint_pos[5])

        self.set_flow_datasource("joint-speed", np.copy(self.world.connection_daemon.joint_speeds))
        self.set_datasource_value("joint-speed-base", self.world.connection_daemon.joint_speeds[0])
        self.set_datasource_value("joint-speed-shoulder", self.world.connection_daemon.joint_speeds[1])
        self.set_datasource_value("joint-speed-elbow", self.world.connection_daemon.joint_speeds[2])
        self.set_datasource_value("joint-speed-wrist1", self.world.connection_daemon.joint_speeds[3])
        self.set_datasource_value("joint-speed-wrist2", self.world.connection_daemon.joint_speeds[4])
        self.set_datasource_value("joint-speed-wrist3", self.world.connection_daemon.joint_speeds[5])

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
