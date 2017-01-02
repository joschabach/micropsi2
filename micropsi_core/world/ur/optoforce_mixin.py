
from micropsi_core.world.world import World
from micropsi_core.world.worldadapter import ArrayWorldAdapter, WorldAdapterMixin
from micropsi_core.world.ur.optoforce import optoforce


class OptoForce6DMixin(WorldAdapterMixin):
    """
    World Adapter Mixin for reading sensor values from an OptopForce 6D F/T sensor connected through USB.
    This will only work on Linux right now, as it uses the sensor interface libaries provided by OptoForce.
    """

    def initialize(self):
        super().initialize()

        self.add_datasource("wrist-fx")
        self.add_datasource("wrist-fy")
        self.add_datasource("wrist-fz")
        self.add_datasource("wrist-tx")
        self.add_datasource("wrist-ty")
        self.add_datasource("wrist-tz")

        optoforce.init()

    def read_from_world(self):
        super().read_from_world()
        self.set_datasource_range("wrist-fx", optoforce.get_ft_np())
