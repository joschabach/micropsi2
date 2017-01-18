
from micropsi_core.world.world import World
from micropsi_core.world.worldadapter import ArrayWorldAdapter, WorldAdapterMixin
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
                        'default': '0.3',}])
        return options

    def initialize(self):
        super().initialize()

        self.add_flow_datatarget("tip-pos", 6, np.zeros(6))
        self.add_datatarget("tip-pos-x")
        self.add_datatarget("tip-pos-y")
        self.add_datatarget("tip-pos-z")
        self.add_datatarget("tip-pos-rx")
        self.add_datatarget("tip-pos-ry")
        self.add_datatarget("tip-pos-rz")

    def write_to_world(self):
        super().write_to_world()


        command = "movej(p[%.4f, %.4f, %.4f, %.4f, %.4f, %.4f], %.4f, %.4f)" % (
            self.get_datatarget_value('tip-pos-x'),
            self.get_datatarget_value('tip-pos-y'),
            self.get_datatarget_value('tip-pos-z'),
            self.get_datatarget_value('tip-pos-rx'),
            self.get_datatarget_value('tip-pos-ry'),
            self.get_datatarget_value('tip-pos-rz'),
            float(self.acceleration),
            float(self.velocity)

        )
        command += os.linesep
        self.world.connection_daemon.write_command_to_robot(command)

    def shutdown(self):
        pass