
from micropsi_core.world.worldadapter import WorldAdapterMixin
import numpy as np
import os


class MoveJControlMixin(WorldAdapterMixin):
    """
    World Adatpter Mixin for controlling a UR robot with movej move commands
    """

    @classmethod
    def get_config_options(cls):
        options = super().get_config_options()
        options.extend([{'name': 'acceleration',
                        'description': 'joint acceleration parameter to be used in movej commands',
                        'default': '0.4'},
                        {'name': 'velocity',
                        'description': 'joint speed parameter to be used in movej commands',
                        'default': '0.3'}])
        return options

    def initialize(self):
        super().initialize()

        self.last_target = np.zeros(6)

        self.add_flow_datatarget("tip-pos", 6, np.zeros(6))
        self.add_datatarget("tip-pos-x")
        self.add_datatarget("tip-pos-y")
        self.add_datatarget("tip-pos-z")
        self.add_datatarget("tip-pos-rx")
        self.add_datatarget("tip-pos-ry")
        self.add_datatarget("tip-pos-rz")

        self.add_datasource("in-target")

    def write_to_world(self):
        super().write_to_world()

        flow_target = self.get_flow_datatarget("tip-pos")

        self.last_target = [
            self.get_datatarget_value('tip-pos-x') + flow_target[0],
            self.get_datatarget_value('tip-pos-y') + flow_target[1],
            self.get_datatarget_value('tip-pos-z') + flow_target[2],
            self.get_datatarget_value('tip-pos-rx') + flow_target[3],
            self.get_datatarget_value('tip-pos-ry') + flow_target[4],
            self.get_datatarget_value('tip-pos-rz') + flow_target[5]
        ]

        command = "movej(p[%.4f, %.4f, %.4f, %.4f, %.4f, %.4f], %.4f, %.4f)" % (
            self.last_target[0],
            self.last_target[1],
            self.last_target[2],
            self.last_target[3],
            self.last_target[4],
            self.last_target[5],
            float(self.acceleration),
            float(self.velocity)
        )
        command += os.linesep
        self.world.connection_daemon.write_command_to_robot(command)

    def read_from_world(self):
        super().read_from_world()

        in_target = sum(np.abs(self.world.connection_daemon.tool_pos_6D - self.last_target)) < 0.01
        self.set_datasource_value("in-target", 1 if in_target else 0)

    def shutdown(self):
        pass
