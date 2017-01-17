
from micropsi_core.world.world import World
from micropsi_core.world.worldadapter import ArrayWorldAdapter, WorldAdapterMixin
import numpy as np

class SpeedJControlMixin(WorldAdapterMixin):
    """
    World Adapter Mixin for controlling a UR robot with speedj move commands.
    """

    @classmethod
    def get_config_options(cls):
        options = super().get_config_options()
        options.extend([{'name': 'acceleration',
                         'description': 'joint acceleration parameter to be used in speedj commands',
                         'default': '0.4'}])
        return options

    def initialize(self):
        super().initialize()

        self.add_flow_datatarget("joint-speed", 6, np.zeros(6))
        self.add_datatarget("joint-speed-base")
        self.add_datatarget("joint-speed-shoulder")
        self.add_datatarget("joint-speed-elbow")
        self.add_datatarget("joint-speed-wrist1")
        self.add_datatarget("joint-speed-wrist2")
        self.add_datatarget("joint-speed-wrist3")

    def write_to_world(self):
        super().write_to_world()

        speeds = self.get_flow_datatarget("joint-speed")

        command = "speedj([%.4f, %.4f, %.4f, %.4f, %.4f, %.4f], %.4f)\n" % (
            min(max(self.get_datatarget_value('joint-speed-base')+speeds[0], -1), 1),
            min(max(self.get_datatarget_value('joint-speed-shoulder')+speeds[1], -1), 1),
            min(max(self.get_datatarget_value('joint-speed-elbow')+speeds[2], -1), 1),
            min(max(self.get_datatarget_value('joint-speed-wrist1')+speeds[3], -1), 1),
            min(max(self.get_datatarget_value('joint-speed-wrist2')+speeds[4], -1), 1),
            min(max(self.get_datatarget_value('joint-speed-wrist3')+speeds[5], -1), 1),
            float(self.acceleration)
        )

        self.world.connection_daemon.write_command_to_robot(command)

    def shutdown(self):
        pass
