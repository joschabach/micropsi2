
from micropsi_core.world.world import World
from micropsi_core.world.worldadapter import ArrayWorldAdapter, WorldAdapterMixin
from micropsi_core.world.ur.optoforce import optoforce
import numpy as np

class OptoForce6DMixin(WorldAdapterMixin):
    """
    World Adapter Mixin for reading sensor values from an OptopForce 6D F/T sensor connected through USB.
    This will only work on Linux right now, as it uses the sensor interface libaries provided by OptoForce.
    """

    def initialize(self):
        super().initialize()

        self.add_flow_datasource("wrist-ft", 6, optoforce.get_ft_np())
        self.add_datasource("wrist-ft-fx")
        self.add_datasource("wrist-ft-fy")
        self.add_datasource("wrist-ft-fz")
        self.add_datasource("wrist-ft-tx")
        self.add_datasource("wrist-ft-ty")
        self.add_datasource("wrist-ft-tz")

        optoforce.init()

    def read_from_world(self):
        super().read_from_world()

        optodata = np.copy(optoforce.get_ft_np())
        self.set_flow_datasource("wrist-force", optodata)
        self.set_datasource_value("wrist-ft-fx", optodata[0])
        self.set_datasource_value("wrist-ft-fy", optodata[1])
        self.set_datasource_value("wrist-ft-fz", optodata[2])
        self.set_datasource_value("wrist-ft-tx", optodata[3])
        self.set_datasource_value("wrist-ft-ty", optodata[4])
        self.set_datasource_value("wrist-ft-tz", optodata[5])

    def shutdown(self):
        optoforce.shutdown()
