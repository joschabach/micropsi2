"""
Agent types provide an interface between agents (which are implemented in node nets) and environments,
such as the MicroPsi world simulator.

At each agent cycle, the activity of this actuator nodes are written to data targets within the agent type,
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
import functools
import operator
from collections import OrderedDict
from threading import Lock
from micropsi_core.world.worldobject import WorldObject
from abc import ABCMeta, abstractmethod


class WorldAdapterMixin(object):

    """ Superclass for modular world-adapter extensions that provide
    functionality reusable in several worldadapters. See examples in vrep_world.py"""

    @classmethod
    def get_config_options(cls):
        """ returns an array of parameters that are needed
        to configure this mixin """
        return []

    def __init__(self, world, uid=None, config={}, **kwargs):
        super().__init__(world, uid=uid, config=config, **kwargs)

    def initialize(self):
        """ Called after a reset of the simulation """
        pass  # pragma: no cover

    def reset_simulation_state(self):
        """ Called on reset """
        pass  # pragma: no cover

    def update_datasources_and_targets(self):
        pass  # pragma: no cover

    def write_to_world(self):
        pass  # pragma: no cover

    def read_from_world(self):
        pass  # pragma: no cover

    def on_simulation_started(self):
        pass  # pragma: no cover

    def on_simulation_paused(self):
        pass  # pragma: no cover

    def shutdown(self):
        pass  # pragma: no cover


class WorldAdapter(WorldObject, metaclass=ABCMeta):
    """Transmits data between agent and environment.

    The agent writes activation values into data targets, and receives it from data sources. The world adapter
    takes care of translating between the world and these values at each world cycle.
    """

    @classmethod
    def get_config_options(cls):
        return []

    @property
    def generate_flow_modules(self):
        return False

    def __init__(self, world, uid=None, config={}, **data):
        self.datasources = {}
        self.datatargets = {}
        self.flow_datasources = OrderedDict()
        self.flow_datatargets = OrderedDict()
        self.flow_datatarget_feedbacks = OrderedDict()
        self.datatarget_feedback = {}
        self.datasource_lock = Lock()
        self.config = config
        self.nodenet = None  # will be assigned by the nodenet once it's loaded
        WorldObject.__init__(self, world, category='agents', uid=uid, **data)
        self.logger = logging.getLogger('agent.%s' % self.uid)
        if data.get('name'):
            self.data['name'] = data['name']
        for item in self.__class__.get_config_options():
            if item['name'] not in config:
                config[item['name']] = item.get('default')
        for key in config:
            setattr(self, key, config[key])

    def initialize_worldobject(self, data):
        pass

    def add_datasource(self, name, initial_value=0.0):
        """ add a datasource """
        self.datasources[name] = initial_value

    def add_datatarget(self, name, initial_value=0.0):
        """ add a datatarget """
        self.datatargets[name] = initial_value
        self.datatarget_feedback[name] = 0.0

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

    def add_datatarget_values(self, values):
        """allows the agent to add a list of values to the datatargets"""
        for i, key in enumerate(self.get_available_datatargets()):
            self.datatargets[key] += values[i]

    def get_datatarget_feedback_value(self, key):
        """get feedback whether the actuator-induced action succeeded"""
        return self.datatarget_feedback.get(key, 0)

    def get_datatarget_feedback_values(self):
        """allows the agent to read all datasource values"""
        return [float(self.datatarget_feedback[x]) for x in self.get_available_datatargets()]

    def set_datatarget_feedback_value(self, key, value):
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
        pass  # pragma: no cover

    def is_alive(self):
        """called by the world to check whether the agent has died and should be removed"""
        return True


class Default(WorldAdapter):
    """
    A default Worldadapter, that provides example-datasources and -targets
    """
    @classmethod
    def get_config_options(cls):
        return [
            {'name': 'foo',
             'description': 'does nothing',
             'default': 'bar'}
        ]

    def __init__(self, world, uid=None, config={}, **data):
        super().__init__(world, uid=uid, config=config, **data)
        for s in ['static_on', 'random', 'static_off']:
            self.add_datasource(s, 0)
        self.add_datatarget('echo', 0)
        self.update_data_sources_and_targets()

    def update_data_sources_and_targets(self):
        import random
        self.datatarget_feedback['echo'] = self.datatargets['echo']
        self.datasources['static_on'] = 1
        self.datasources['random'] = random.uniform(0, 1)


try:
    # Only available if numpy is installed
    import numpy as np

    # configure dtype for value arrays.
    # TODO: Move this and the config in theano_nodenet to one central point
    from configuration import config as settings

    class ArrayWorldAdapter(WorldAdapter, metaclass=ABCMeta):
        """
        The ArrayWorldAdapter base class allows to avoid python dictionaries and loops for transmitting values
        to nodenet engines.
        Engines that bulk-query values, such as the theano_engine, will be faster.
        Numpy arrays can be passed directly into the engine.
        """

        @property
        def generate_flow_modules(self):
            return len(self.flow_datasources) or len(self.flow_datatargets)

        def __init__(self, world, uid=None, **data):
            WorldAdapter.__init__(self, world, uid=uid, **data)

            precision = settings['theano']['precision']
            self.floatX = np.float32
            if precision == "64":
                self.floatX = np.float64

            self.datasource_names = []
            self.datatarget_names = []
            self.flow_datasources = OrderedDict()
            self.flow_datatargets = OrderedDict()
            self.flow_datatarget_feedbacks = OrderedDict()
            self.datasource_values = np.zeros(0, dtype=self.floatX)
            self.datatarget_values = np.zeros(0, dtype=self.floatX)
            self.datatarget_feedback_values = np.zeros(0, dtype=self.floatX)

        def add_datasource(self, name, initial_value=0.):
            """ Adds a datasource, and returns the index
            where they were added"""
            self.datasource_names.append(name)
            self.datasource_values = np.concatenate((self.datasource_values, np.asarray([initial_value], dtype=self.floatX)))
            return len(self.datasource_names) - 1

        def add_datatarget(self, name, initial_value=0.):
            """ Adds a datatarget, and returns the index
            where they were added"""
            self.datatarget_names.append(name)
            self.datatarget_values = np.concatenate((self.datatarget_values, np.asarray([initial_value], dtype=self.floatX)))
            self.datatarget_feedback_values = np.concatenate((self.datatarget_feedback_values, np.asarray([initial_value], dtype=self.floatX)))
            return len(self.datatarget_names) - 1

        def add_flow_datasource(self, name, shape, initial_values=None):
            """ Add a high-dimensional datasource for flowmodules."""
            if initial_values is None:
                initial_values = np.zeros(shape, dtype=self.floatX)

            self.flow_datasources[name] = initial_values
            return self.flow_datasources[name]

        def add_flow_datatarget(self, name, shape, initial_values=None):
            """ Add a high-dimensional datatarget for flowmodules"""
            if initial_values is None:
                initial_values = np.zeros(shape, dtype=self.floatX)

            self.flow_datatargets[name] = initial_values
            self.flow_datatarget_feedbacks[name] = np.zeros_like(initial_values)
            return self.flow_datatargets[name]

        def get_available_datasources(self):
            """Returns a list of all datasource names"""
            return self.datasource_names

        def get_available_datatargets(self):
            """Returns a list of all datatarget names"""
            return self.datatarget_names

        def get_available_flow_datasources(self):
            return list(self.flow_datasources.keys())

        def get_available_flow_datatargets(self):
            return list(self.flow_datatargets.keys())

        def get_datasource_index(self, name):
            """Returns the index of the given datasource in the value array"""
            return self.datasource_names.index(name)

        def get_datatarget_index(self, name):
            """Returns the index of the given datatarget in the value array"""
            return self.datatarget_names.index(name)

        def get_datasource_value(self, key):
            """allows the agent to read a value from a datasource"""
            index = self.get_datasource_index(key)
            return self.datasource_values[index]

        def get_datatarget_value(self, key):
            """allows the agent to read a value from a datatarget"""
            index = self.get_datatarget_index(key)
            return self.datatarget_values[index]

        def get_datatarget_feedback_value(self, key):
            """allows the agent to read a value from a datatarget"""
            index = self.get_datatarget_index(key)
            return self.datatarget_feedback_values[index]

        def get_datasource_values(self):
            """allows the agent to read all datasource values"""
            return self.datasource_values

        def get_datatarget_values(self):
            """allows the agent to read all datatarget values"""
            return self.datatarget_values

        def get_datatarget_feedback_values(self):
            """allows the agent to read all datatarget_feedback values"""
            return self.datatarget_feedback_values

        def get_flow_datasource(self, name):
            """ return the array/matrix for the given flow datasource"""
            return self.flow_datasources[name]

        def get_flow_datatarget(self, name):
            """ return the array/matrix for the given flow datatarget"""
            return self.flow_datatargets[name]

        def get_flow_datatarget_feedback(self, name):
            """ return the array/matrix for the given flow datatarget_feedback"""
            return self.flow_datatarget_feedbacks[name]

        def set_datasource_value(self, key, value):
            """Sets the given datasource value"""
            idx = self.get_datasource_index(key)
            self.datasource_values[idx] = value

        def set_datatarget_value(self, key, value):
            """Sets the given datasource value"""
            idx = self.get_datatarget_index(key)
            self.datatarget_values[idx] = value

        def add_to_datatarget(self, key, value):
            """Adds the given value to the given datatarget"""
            idx = self.get_datatarget_index(key)
            self.datatarget_values[idx] += value

        def set_datatarget_feedback_value(self, key, value):
            """Sets the given datatarget_feedback value"""
            idx = self.get_datatarget_index(key)
            self.datatarget_feedback_values[idx] = value

        def set_flow_datasource(self, name, values):
            """Set the values of the given flow_datasource """
            assert isinstance(values, np.ndarray), "must provide numpy array"
            assert values.dtype == self.floatX
            assert self.flow_datasources[name].shape == values.shape
            self.flow_datasources[name] = values

        def add_to_flow_datatarget(self, name, values):
            """Add the given values to the given flow_datatarget """
            assert isinstance(values, np.ndarray), "must provide numpy array"
            assert values.dtype == self.floatX
            assert self.flow_datatargets[name].shape == values.shape
            self.flow_datatargets[name] += values

        def set_flow_datatarget_feedback(self, name, values):
            """Set the values of the given flow_datatarget_feedback """
            assert isinstance(values, np.ndarray), "must provide numpy array"
            assert values.dtype == self.floatX
            assert self.flow_datatarget_feedbacks[name].shape == values.shape
            self.flow_datatarget_feedbacks[name] = values

        def set_datasource_values(self, values):
            """sets the complete datasources to new values"""
            assert len(values) == len(self.datasource_values)
            self.datasource_values = values

        def set_datatarget_values(self, values):
            """sets the complete datatargets to new values"""
            assert len(values) == len(self.datatarget_values)
            self.datatarget_values = values

        def add_datatarget_values(self, values):
            """sets the complete datatargets to new values"""
            assert len(values) == len(self.datatarget_values)
            self.datatarget_values += values

        def set_datatarget_feedback_values(self, values):
            """sets the complete datatargets_feedback to new values"""
            assert len(values) == len(self.datatarget_feedback_values)
            self.datatarget_feedback_values = values

        def reset_datatargets(self):
            """ resets (zeros) the datatargets """
            self.datatarget_values = np.zeros_like(self.datatarget_values)
            for name in self.flow_datatargets:
                self.flow_datatargets[name] = np.zeros_like(self.flow_datatargets[name])

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
            pass  # pragma: no cover

    class DefaultArray(ArrayWorldAdapter):
        """
        A default ArrayWorldadapter, that provides example-datasources and -targets
        """
        def __init__(self, world, uid=None, config={}, **data):
            super().__init__(world, uid=uid, config=config, **data)
            self.add_datasource("test", initial_value=0)
            self.add_flow_datasource("vision", (3, 7))
            self.add_datatarget("test", initial_value=0)
            self.add_flow_datatarget("action", (2, 3))
            self.update_data_sources_and_targets()

        def update_data_sources_and_targets(self):
            import random
            self.datatarget_feedback_values[:] = self.datatarget_values
            self.datasource_values[:] = np.random.randn(len(self.datasource_values))
            self.flow_datasources['vision'][:] = np.random.randn(*self.flow_datasources['vision'].shape)
            self.flow_datatargets['action'][:] = np.zeros_like(self.flow_datatargets['action'])


except ImportError:  # pragma: no cover
    pass
