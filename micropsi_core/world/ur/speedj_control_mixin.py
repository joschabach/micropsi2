
from micropsi_core.world.world import World
from micropsi_core.world.worldadapter import ArrayWorldAdapter, WorldAdapterMixin

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

        self.add_datatarget("js-base")
        self.add_datatarget("js-shoulder")
        self.add_datatarget("js-elbow")
        self.add_datatarget("js-wrist1")
        self.add_datatarget("js-wrist2")
        self.add_datatarget("js-wrist3")

    def write_to_world(self):
        super().write_to_world()

        command = "speedj([%.4f, %.4f, %.4f, %.4f, %.4f, %.4f], %.4f)\n" % (
            min(max(self.get_datatarget_value('js-base'), -1), 1),
            min(max(self.get_datatarget_value('js-shoulder'), -1), 1),
            min(max(self.get_datatarget_value('js-elbow'), -1), 1),
            min(max(self.get_datatarget_value('js-wrist1'), -1), 1),
            min(max(self.get_datatarget_value('js-wrist2'), -1), 1),
            min(max(self.get_datatarget_value('js-wrist3'), -1), 1),
            float(self.acceleration)
        )

        self.world.connection_daemon.write_command_to_robot(command)

    def shutdown(self):
        pass
