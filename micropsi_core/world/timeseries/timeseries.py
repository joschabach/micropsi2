"""
Worlds and bodies for agents whose habitats are ordered sequences of vectors.
"""
import os.path
from configuration import config as cfg
from micropsi_core.world.world import World
from micropsi_core.world.worldadapter import WorldAdapter
import numpy as np


class TimeSeries(World):
    """ A world that cycles through a fixed time series loaded from a file.
    This world looks for a file named timeseries.npz in the data_directory
    that has been set in configuration. This is a stopgap, we want to add the
    option to choose a file whenever such worlds are instantiated in the GUI.

    The file should be a numpy archive with the following fields:

    'startdate', 'enddate': datetime objects
    'data': numpy array of shape (nr of ids) x (nr minutes between startdate and enddate)
    'ids': a list of IDs - the legend for data's first axis.
    """
    supported_worldadapters = ['TimeSeriesRunner']

    def __init__(self, filename, world_type="Island", name="", owner="", engine=None, uid=None, version=1):
        World.__init__(self, filename, world_type=world_type, name=name, owner=owner, uid=uid, version=version)
        path = os.path.join(cfg['micropsi2']['data_directory'], 'timeseries.npz')
        print("loading timeseries from", path, "for world", uid)
        with np.load(path) as f:
            self.timeseries = f['data']
            self.ids = f['ids']
            self.startdate = f['startdate']
            self.enddate = f['enddate']
        self.len_ts = self.timeseries.shape[1]

    # todo: option to use only a subset of the data (e.g. for training/test)

    @property
    def t(self):
        """current index into the original time series"""
        return self.current_step % self.len_ts

    @property
    def state(self):
        return self.timeseries[:, self.t]


class TimeSeriesRunner(WorldAdapter):
    supported_datasources = []
    supported_datatargets = []

    def __init__(self, world, uid=None, **data):
        super().__init__(world, uid, **data)
        for idx, ID in enumerate(self.world.ids):
            self.supported_datasources.append(str(ID))

    def update_data_sources_and_targets(self):
        state = self.world.state
        for idx, ID in enumerate(self.world.ids):
            self.datasources[str(ID)] = state[idx]
