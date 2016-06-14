"""
Agent types provide an interface between agents (which are implemented in node nets) and environments,
such as the MicroPsi world simulator.

At each agent cycle, the activity of this actor nodes are written to data targets within the agent type,
and the activity of sensor nodes is determined by the values exposed in its data sources.
At each world cycle, the value of the data targets is translated into operations performed upon the world,
and the value of the data sources is updated according to sensory data derived from the world.

Note that agent and world do not need to be synchronized, so agents will have to be robust against time lags
between actions and sensory confirmation (among other things).

During the initialization of the agent type, it might want to register an agent body object within the
world environment (for robotic bodies, the equivalent might consist in powering up/setup/boot operations.
Thus, agent types should be instantiated by the world, inherit from a moving object class of some kind
and treated as parts of the world.
"""

__author__ = 'joscha'
__date__ = '10.05.12'

import logging
from threading import Lock
from micropsi_core.world.worldobject import WorldObject
from abc import ABCMeta, abstractmethod


class WorldAdapter(WorldObject, metaclass=ABCMeta):
    """Transmits data between agent and environment.

    The agent writes activation values into data targets, and receives it from data sources. The world adapter
    takes care of translating between the world and these values at each world cycle.
    """

    def __init__(self, world, uid=None, **data):
        self.datasources = {}
        self.datatargets = {}
        self.datatarget_feedback = {}
        self.datasource_lock = Lock()
        self.nodenet = None  # will be assigned by the nodenet once it's loaded
        WorldObject.__init__(self, world, category='agents', uid=uid, **data)
        self.logger = logging.getLogger('agent.%s' % self.uid)
        if data.get('name'):
            self.data['name'] = data['name']

    def initialize_worldobject(self, data):
        for key in self.datasources:
            if key in data.get('datasources', {}):
                self.datasources[key] = data['datasources'][key]
        for key in self.datatargets:
            if key in data.get('datatargets', {}):
                self.datatargets[key] = data['datatargets'][key]
                self.datatarget_feedback[key] = 0

    def get_available_datasources(self):
        """returns a list of identifiers of the datasources available for this world adapter"""
        return sorted(list(self.datasources.keys()))

    def get_available_datatargets(self):
        """returns a list of identifiers of the datatargets available for this world adapter"""
        return sorted(list(self.datatargets.keys()))

    def get_datasource_value(self, key):
        """allows the agent to read a value from a datasource"""
        return self.datasources.get(key)

    def get_datasource_values(self):
        """allows the agent to read all datasource values"""
        return [float(self.datasources[x]) for x in self.get_available_datasources()]

    def add_to_datatarget(self, key, value):
        """allows the agent to write a value to a datatarget"""
        if key in self.datatargets:
            self.datatargets[key] += value

    def set_datatarget_values(self, values):
        """allows the agent to write a list of value to the datatargets"""
        for i, key in enumerate(self.get_available_datatargets()):
            self.datatargets[key] = values[i]

    def get_datatarget_feedback_value(self, key):
        """get feedback whether the actor-induced action succeeded"""
        return self.datatarget_feedback.get(key, 0)

    def get_datatarget_feedback_values(self):
        """allows the agent to read all datasource values"""
        return [float(self.datatarget_feedback[x]) for x in self.get_available_datatargets()]

    def set_datatarget_feedback(self, key, value):
        """set feedback for the given datatarget"""
        self.datatarget_feedback[key] = value

    def update(self):
        """ Called by the world at each world iteration """
        self.update_data_sources_and_targets()
        self.reset_datatargets()

    def reset_datatargets(self):
        """ resets (zeros) the datatargets """
        for datatarget in self.datatargets:
            self.datatargets[datatarget] = 0

    @abstractmethod
    def update_data_sources_and_targets(self):
        """must be implemented by concrete world adapters to read datatargets and fill datasources"""
        pass

    def is_alive(self):
        """called by the world to check whether the agent has died and should be removed"""
        return True


class Default(WorldAdapter):
    """
    A default Worldadapter, that provides example-datasources and -targets
    """
    def __init__(self, world, uid=None, **data):
        super().__init__(world, uid=uid, **data)
        self.datasources = dict((s, 0) for s in ['static_on', 'random', 'static_off'])
        self.datatargets = {'echo': 0}
        self.datatarget_feedback = {'echo': 0}
        self.update_data_sources_and_targets()

    def update_data_sources_and_targets(self):
        import random
        if self.datatargets['echo'] != 0:
            self.datatarget_feedback['echo'] = self.datatargets['echo']
        self.datasources['static_on'] = 1
        self.datasources['random'] = random.uniform(0, 1)


class ArrayWorldAdapter(WorldAdapter, metaclass=ABCMeta):
    """
    The ArrayWorldAdapter base class allows to avoid python dictionaries and loops for transmitting values
    to nodenet engines.
    Engines that bulk-query values, such as the theano_engine, will be faster.
    Numpy arrays can be passed directly into the engine.
    """
    def __init__(self, world, uid=None, **data):
        WorldAdapter.__init__(self, world, uid=uid, **data)

        self.datasource_names = []
        self.datatarget_names = []
        self.datasource_values = []
        self.datatarget_values = []
        self.datatarget_feedback_values = []

    def add_datasource(self, name, initial_value=0):
        """ Adds a datasource, and returns the index
        where they were added"""
        self.datasource_names.append(name)
        self.datasource_values.append(0)
        return len(self.datasource_names) - 1

    def add_datatarget(self, name, initial_value=0):
        """ Adds a datatarget, and returns the index
        where they were added"""
        self.datatarget_names.append(name)
        self.datatarget_values.append(0)
        return len(self.datatarget_names) - 1

    def add_datasources(self, names, initial_values=False):
        """ Adds a list of datasources, and returns the indexes
        where they were added"""
        offset = len(self.datasource_names)
        self.datasource_names.extend(names)
        self.datasource_values.extend([0] * len(names))
        return range(offset, offset + len(names))

    def add_datatargets(self, names, initial_values=False):
        """ Adds a list of datatargets, and returns the indexes
        where they were added"""
        offset = len(self.datatarget_names)
        self.datatarget_names.extend(names)
        self.datatarget_values.extend([0] * len(names))
        self.datatarget_feedback_values.extend([0] * len(names))
        return range(offset, offset + len(names))

    def get_available_datasources(self):
        return self.datasource_names

    def get_available_datatargets(self):
        return self.datatarget_names

    def get_datasource_index(self, name):
        return self.datasource_names.index(name)

    def get_datatarget_index(self, name):
        return self.datatarget_names.index(name)

    def get_datasource_value(self, key):
        """allows the agent to read a value from a datasource"""
        index = self.get_available_datasources().index(key)
        return self.datasource_values[index]

    def get_datasource_values(self):
        """allows the agent to read all datasource values"""
        return self.datasource_values

    def add_to_datatarget(self, key, value):
        """allows the agent to write a value to a datatarget"""
        index = self.get_available_datasources().index(key)
        self.datatarget_values[index] += value

    def set_datatarget_values(self, values):
        """allows the agent to write a list of value to the datatargets"""
        self.datatarget_values = values

    def get_datatarget_feedback_value(self, key):
        """get feedback whether the actor-induced action succeeded"""
        index = self.get_available_datatargets().index(key)
        return self.datatarget_feedback_values[index]

    def set_datatarget_feedback(self, key, value):
        """set feedback for the given datatarget"""
        index = self.get_available_datatargets().index(key)
        self.datatarget_feedback_values[index] = value

    def get_datatarget_feedback_values(self):
        """allows the agent to read all datasource values"""
        return self.datatarget_feedback_values

    def reset_datatargets(self):
        """ resets (zeros) the datatargets """
        pass

    def _set_datasource_value(self, key, value):
        self.datasource_values[self.get_datasource_index(key)] = value

    def _set_datatarget_value(self, key, value):
        self.datatarget_values[self.get_datatarget_index(key)] = value

    def _get_datatarget_value(self, key):
        return self.datatarget_values[self.get_datatarget_index(key)]

    def _set_datatarget_feedback_value(self, key, value):
        self.datatarget_feedback_values[self.get_datatarget_index(key)] = value

    def _set_datasource_values(self, start_key, values):
        idx = self.get_datasource_index(start_key)
        self.datasource_values[idx:idx + len(values)] = values

    def _get_datatarget_values(self, start_key, length):
        idx = self.get_datatarget_index(start_key)
        return self.datatarget_values[idx:idx + length]

    def _set_datatarget_values(self, start_key, values):
        idx = self.get_datatarget_index(start_key)
        self.datatarget_feedback_values[idx:idx + len(values)] = values

    @abstractmethod
    def update_data_sources_and_targets(self):
        """
        must be implemented by concrete world adapters to read and set the following arrays:
        datasource_values
        datatarget_values
        datatarget_feedback_values

        Arrays sizes need to be equal to the corresponding responses of get_available_datasources() and
        get_available_datatargets().
        Values of the superclass' dict objects will be bypassed and ignored.
        """
        pass
