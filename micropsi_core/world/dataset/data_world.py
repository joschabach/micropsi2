import numpy as np

from micropsi_core.world.world import World
from micropsi_core.world.worldadapter import ArrayWorldAdapter

"""
World and worldadapter to allow processing a fixed data array.

Basic structure: The world holds a reference to a data archive (currently numpy npz, later perhaps also hdf5)
Different worldadapters implement different ways of splitting and iterating over this data.

----

Some considerations for larger-than-RAM-datasets:

These worldadapters do only basic slicing (indexing operations that can be described by 'start:stop:step').
If the data is a numpy archive, this means that only array views are created, no copies.
If it is a HDF5 archive, as far as I know, these operations do not even cause the data to be read from disk.

This ends only at the point where a minibatch is created, which involves integer based fancy indexing (requiring copying).

So this setup will need `size of full dataset + 1 minibatch` of RAM if the data comes in a numpy archive,
and unless I'm mistaken `size of 1 minibatch` if comes in a Hdf5 archive.

Caveat: I have not tested this.
"""


class Dataset(World):
    supported_worldadapters = ['SupervisedLearning', 'UnsupervisedLearning']

    def __init__(self, filename, world_type="Dataset", name="", owner="", engine=None, uid=None, version=1, config={}):
        World.__init__(self, filename, world_type=world_type, name=name, owner=owner, uid=uid, version=version)

        self.archive = np.load(config['path'])
        # todo: allow hdf5 archives, too

    @classmethod
    def get_config_options(cls):
        return [
            {'name': 'path',
             'description': 'path of a numpy archive',
             'default': ''}
            ]


class SupervisedLearning(ArrayWorldAdapter):

    @classmethod
    def get_config_options(cls):
        return [
             {'name': 'input_key',
             'description': 'key under which the Nxk matrix of input (predictor) variables is found',
             'default': 'x'},
             {'name': 'target_key',
             'description': 'key under which the Nxl matrix of target variables is found',
             'default': 'y'},
             {'name':'holdout_fraction',
             'description': 'ratio of training to holdout data',
             'default': 0.75},
             {'name': 'batch_size',
             'description': '(optional) provide only a certain number of samples from the training set in each world step',
             'default': 500}

            ]

    def __init__(self, world, uid=None, **data):
        super().__init__(world, uid, **data)

        self.rng = np.random.RandomState(seed=1)

        X = world.archive[self.input_key]
        Y = world.archive[self.target_key]
        assert X.shape[0] == Y.shape[0]
        self.N = X.shape[0]
        self.k = X.shape[1]
        self.l = Y.shape[1]

        self.len_train = int(self.N*self.holdout_fraction)
        self.train_X = X[:self.len_train, :]
        self.train_Y = Y[:self.len_train, :]

        test_X = X[self.len_train:, :]
        test_Y = Y[self.len_train:, :]

        self.epoch_count = 0 # nr of times the whole training set has been seen
        self.batch_start = 0 # row idx where the current batch begins
        self.max_batch_start = self.len_train - self.batch_size -1 # last row idx where we can start a batch
        self.shuffle()

        if not self.batch_size:
            self.batch_size = self.len_train

        self.add_flow_datasource("train_x", shape=(self.batch_size, self.k))
        self.add_flow_datasource("train_y", shape=(self.batch_size, self.l))

        self.add_flow_datasource("test_x", shape=(self.N - self.len_train, self.k))
        self.add_flow_datasource("test_y", shape=(self.N - self.len_train, self.l))

        self.add_flow_datasource("epoch_count", shape=1)

        # the contents of the test set never change, so we can write to this datasource
        # at init time and never touch it again.
        self.set_flow_datasource("test_x", test_X)
        self.set_flow_datasource("test_y", test_Y)

    def shuffle(self):
        self.shuffle_order = self.rng.permutation(self.len_train)

    def batch_step(self):
        bs = self.batch_start

        if bs < self.max_batch_start:
            self.batch_start += self.batch_size
        else:
            self.shuffle()
            self.batch_start = 0
            bs = 0
            self.epoch_count += 1

        batch_idxs = self.shuffle_order[bs:bs+self.batch_size]

        # assert batch_end < self.len_train # numpy silently returns fewer elements (!) if a slice index is out of bounds

        assert len(batch_idxs) == self.batch_size

        return batch_idxs


    def update_data_sources_and_targets(self):
        batch_idxs = self.batch_step()

        batch_X = self.train_X[batch_idxs, :]
        batch_Y = self.train_Y[batch_idxs, :]

        self.set_flow_datasource("train_x", batch_X)
        self.set_flow_datasource("train_y", batch_Y)
        self.set_flow_datasource("epoch_count", self.epoch_count)

class UnsupervisedLearning(ArrayWorldAdapter):
    # like Supervised, but without Y datasource
    pass

class TimeseriesPrediction(ArrayWorldAdapter):
    # adds the option for temporal embeddings (with special attention to time discontinuities)
    pass