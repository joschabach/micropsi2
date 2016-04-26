"""
Worlds and bodies for agents whose habitats are ordered sequences of vectors.
"""
import os
from configuration import config as cfg
from micropsi_core.world.world import World
from micropsi_core.world.worldadapter import WorldAdapter, ArrayWorldAdapter
import numpy as np
from datetime import datetime


class TimeSeries(World):
    """ A world that cycles through a fixed time series loaded from a file.
    The file should be a numpy archive with the following fields:
    'data': numpy array of shape (nr of ids) x (nr of timestamps)
    'timestamps', a list of timestamps - the legend for the data's second axis
    'ids': a list of IDs - the legend for data's first axis.
    """
    supported_worldadapters = ['TimeSeriesRunner']

    assets = {
        'js': "timeseries/timeseries.js",
        'template': 'timeseries/timeseries.tpl'
    }

    def __init__(self, filename, world_type="TimeSeries", name="", owner="", engine=None, uid=None, version=1, config={}):
        World.__init__(self, filename, world_type=world_type, name=name, owner=owner, uid=uid, version=version, config=config)

        self.data['assets'] = self.assets

        filename = config.get('time_series_data_file', "timeseries.npz")
        if os.path.isabs(filename):
            path = filename
        else:
            path = os.path.join(cfg['micropsi2']['data_directory'], filename)
        self.logger.info("loading timeseries from %s for world %s" % (path, uid))

        self.realtime_per_entry = int(config['realtime_per_entry'])
        self.last_realtime_step = datetime.utcnow().timestamp() * 1000

        try:
            with np.load(path) as f:
                self.timeseries = f['data']
                self.ids = f['ids']
                self.timestamps = f['timestamps']
        except IOError as error:
            self.logger.error("Could not load data file %s, error was: %s" % (path, str(error)))
            self.ids = [0]
            self.timeseries[[0, 0, 0]]
            self.timestamps = [0]
            self.len_ts = 1
            return

        # todo use the new configurable world options.
        dummydata = config['dummy_data'] == "True"
        z_transform = config['z_transform'] == "True"
        clip_and_scale = config['clip_and_scale'] == "True"
        sigmoid = config['sigmoid'] == "True"
        self.shuffle = config['shuffle'] == "True"

        if clip_and_scale and sigmoid:
            self.logger.warn("clip_and_scale and sigmoid cannot both be configured, choosing sigmoid")
            clip_and_scale = False

        def sigm(X):
            """ sigmoid that avoids float overflows for very small inputs.
                expects a numpy float array.
            """
            cutoff = np.log(np.finfo(X.dtype).max) - 1
            X[np.nan_to_num(X) <= -cutoff] = -cutoff
            return 1. / (1. + np.exp(-X))

        if (z_transform or clip_and_scale or sigmoid) and not dummydata:
            data_z = np.empty_like(self.timeseries)
            data_z[:] = np.nan
            pstds = []
            for i, row in enumerate(self.timeseries):
                if not np.all(np.isnan(row)):
                    std = np.sqrt(np.nanvar(row))
                    if std > 0:
                        if not clip_and_scale:
                            row_z = (row - np.nanmean(row)) / std
                        if clip_and_scale:
                            row_z = row - np.nanmean(row)
                            pstd = std * 4
                            row_z[np.nan_to_num(row_z) > pstd] = pstd
                            row_z[np.nan_to_num(row_z) < -pstd] = -pstd
                            row_z = ((row_z / pstd) + 1) * 0.5
                        data_z[i,:] = row_z
            self.timeseries = data_z if not sigmoid else sigm(data_z)

        if dummydata:
            self.logger.warn("! Using dummy data")
            n_ids = self.timeseries.shape[1]
            self.timeseries = np.tile(np.random.rand(n_ids,1),(1,10))

        self.len_ts = self.timeseries.shape[0]

    # todo: option to use only a subset of the data (e.g. for training/test)

    def step(self):
        now = datetime.utcnow().timestamp() * 1000
        if self.realtime_per_entry == 0 or now - self.realtime_per_entry > self.last_realtime_step:
            self.current_step += 1
            for uid in self.agents:
                with self.agents[uid].datasource_lock:
                    self.agents[uid].update()
            self.last_realtime_step = now

    @property
    def state(self):
        t = (self.current_step - 1) % self.len_ts
        if self.shuffle:
            if t == 0:
                idxs = np.arange(self.len_ts)
                self.permutation = np.random.permutation(idxs)
            t = self.permutation[t]
        return self.timeseries[t, :]

    @staticmethod
    def get_config_options():
        """ Returns a list of configuration-options for this world.
        Expected format:
        [{
            'name': 'param1',
            'description': 'this is just an example',
            'options': ['value1', 'value2'],
            'default': 'value1'
        }]
        description, options and default are optional settings
        """
        return [
            {'name': 'time_series_data_file',
             'description': 'The data file with the time series',
             'default': 'timeseries.npz'},
            {'name': 'shuffle',
             'description': 'Randomize order of presentation',
             'default': 'True',
             'options': ["True", "False"]},
            {'name': 'z_transform',
             'description': 'For each ID, center on mean & normalize by standard deviation',
             'default': 'False',
             'options': ["True", "False"]},
            {'name': 'clip_and_scale',
             'description': 'For each ID, center on mean & clip to 4 standard deviations and rescale to [0,1].',
             'default': 'False',
             'options': ["True", "False"]},
            {'name': 'sigmoid',
             'description': 'For each ID, z-transform and apply a sigmoid activation function',
             'default': 'False',
             'options': ["True", "False"]},
            {'name': 'realtime_per_entry',
             'description': 'Present each pattern from the data for this number of milliseconds',
             'default': '0'},
            {'name': 'dummy_data',
             'description': 'Present the same random pattern in each step (instead of the actual time series data)',
             'default': 'False',
             'options': ["True", "False"]}
        ]

    def set_user_data(self, data):
        """ Allow the user to set the step of this world"""
        if 'step' in data:
            self.last_realtime_step = datetime.utcnow().timestamp() * 1000
            self.current_step = data['step']
            for uid in self.agents:
                with self.agents[uid].datasource_lock:
                    self.agents[uid].update()

    def get_world_view(self, step):
        return {
            'first_timestamp': self.timestamps[0].isoformat(),
            'last_timestamp': self.timestamps[-1].isoformat(),
            'total_timestamps': len(self.timestamps),
            'current_timestamp': self.timestamps[self.current_step].isoformat(),
            'current_step': self.current_step,
        }


class TimeSeriesRunner(ArrayWorldAdapter):

    def __init__(self, world, uid=None, **data):
        super().__init__(world, uid, **data)

        self.available_datatargets = []
        self.available_datasources = []

        for idx, ID in enumerate(self.world.ids):
            self.available_datasources.append(str(ID))

    def get_available_datasources(self):
        return self.available_datasources

    def get_available_datatargets(self):
        return self.available_datatargets

    def update_data_sources_and_targets(self):
        self.datasource_values = self.world.state