import numpy as np

from micropsi_core.world.world import World
from micropsi_core.world.worldadapter import ArrayWorldAdapter


# basic structure: the world holds a dataset in memory
# worldadapters implement different ways of splitting and iterating over that dataset.


class Dataset(World):
    supported_worldadapters = ['SupervisedLearning', 'UnsupervisedLearning']

    def __init__(self, filename, world_type="Dataset", name="", owner="", engine=None, uid=None, version=1, config={}):
        World.__init__(self, filename, world_type=world_type, name=name, owner=owner, uid=uid, version=version)

        archive = np.load(config['path'])


    @classmethod
    def get_config_options(cls):
        return [
            {'name': 'path',
             'description': 'file containing the data set',
             'default': ''}
        ]


# ideally, WAs operate as much as possible with _views_ (i.e. only slice-based indexing)

class SupervisedLearning(ArrayWorldAdapter):
    # configurable train, test, validation split
    # selection of input and target variables, exposed in separate flow datasources
    # iterates over the shuffled training set in mini batches: two ever changing data sources
    # keeps validation and test set fixed in separate data sources: four unchanging datasources (should produce 0 overhead)


class UnsupervisedLearning(ArrayWorldAdapter):
    # configurable train, test, validation split
    # selection of interesting variables
    # iterates over the shuffled training set in mini batches: one ever changing data source
    # keeps validation and test set fixed in separate data sources: two unchanging datasources (should produce 0 overhead)


class TimeseriesPrediction(ArrayWorldAdapter):
    # like unsupervised, but doesnt shuffle and adds option for temporal embedding (with special attention to temporal discontinuities) [the embedded data matrix can optionally be shuffled again]