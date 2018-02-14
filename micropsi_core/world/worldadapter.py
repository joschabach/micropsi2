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
from micropsi_core.device.device import InputDevice, OutputDevice
from micropsi_core.device import devicemanager


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

    def update_data_sources_and_targets(self):
        super().update_data_sources_and_targets()

    def write_to_world(self):
        super().write_to_world()

    def read_from_world(self):
        super().read_from_world()

    def on_start(self):
        pass  # pragma: no cover

    def on_stop(self):
        pass  # pragma: no cover

    def shutdown(self):
        super().shutdown()
        pass  # pragma: no cover


class WorldAdapter(WorldObject, metaclass=ABCMeta):
    """Transmits data between agent and environment.

    The agent writes activation values into data targets, and receives it from data sources. The world adapter
    takes care of translating between the world and these values at each world cycle.
    """

    @classmethod
    def get_config_options(cls):
        return []

    @classmethod
    def supports_devices(cls):
        return False

    @property
    def generate_flow_modules(self):
        return False

    def __init__(self, world, uid=None, config={}, **data):
        self.datasources = {}
        self.datatargets = {}
        self.device_map = {}
        self.step_interval_ms = -1
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

    def update(self, step_inteval_ms):
        """ Called by the world at each world iteration """
        self.step_interval_ms = step_inteval_ms
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

    def shutdown(self):
        """ Called before the instance is deleted or recreated """
        pass


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

    class ArrayWorldAdapter(WorldAdapter):
        """
        The ArrayWorldAdapter base class allows to avoid python dictionaries and loops for transmitting values
        to nodenet engines.
        Engines that bulk-query values, such as the theano_engine, will be faster.
        Numpy arrays can be passed directly into the engine.
        """

        @classmethod
        def supports_devices(cls):
            return True

        @property
        def generate_flow_modules(self):
            return len(self.flow_datasources) or len(self.flow_datatargets)

        def __init__(self, world, uid=None, **data):
            WorldAdapter.__init__(self, world, uid=uid, **data)
            self.datasource_names = []
            self.datatarget_names = []
            self.flow_datasources = OrderedDict()
            self.flow_datatargets = OrderedDict()
            self.flow_datatarget_feedbacks = OrderedDict()
            self.datasource_values = np.zeros(0)
            self.datatarget_values = np.zeros(0)
            self.datatarget_feedback_values = np.zeros(0)
            if data.get('device_map'):
                for k in data['device_map']:
                    if k not in devicemanager.get_known_devices():
                        self.logger.error("Device %s (uid: %s) not found, not adding datasource or datatarget" % (data['device_map'][k], k))
                    else:
                        self.device_map[k] = data['device_map'][k]
                        if k in devicemanager.online_devices:
                            device_data = devicemanager.online_devices[k].get_config()
                        else:
                            device_data = devicemanager.known_devices[k]
                            if device_data['type'] not in devicemanager.device_types:
                                self.logger.error("Device %s (uid: %s) has unknown type %s. not adding datasource or datatarget" % (data['device_map'][k], k, device_data['type']))
                                continue
                        if device_data.get('nature') == InputDevice.__name__:
                            self.add_flow_datasource(self.device_map[k], device_data['data_size'])
                        elif device_data.get('nature') == OutputDevice.__name__:
                            self.add_flow_datatarget(self.device_map[k], device_data['data_size'])
                        else:
                            self.logger.error("Device %s (uid: %s) not found, not adding datasource or datatarget" % (data['device_map'][k], k))

        def add_datasource(self, name, initial_value=0.):
            """ Adds a datasource, and returns the index
            where they were added"""
            self.datasource_names.append(name)
            self.datasource_values = np.concatenate((self.datasource_values, np.asarray([initial_value])))
            return len(self.datasource_names) - 1

        def add_datatarget(self, name, initial_value=0.):
            """ Adds a datatarget, and returns the index
            where they were added"""
            self.datatarget_names.append(name)
            self.datatarget_values = np.concatenate((self.datatarget_values, np.asarray([initial_value])))
            self.datatarget_feedback_values = np.concatenate((self.datatarget_feedback_values, np.asarray([initial_value])))
            return len(self.datatarget_names) - 1

        def add_flow_datasource(self, name, shape, initial_values=None):
            """ Add a high-dimensional datasource for flowmodules."""
            if initial_values is None:
                initial_values = np.zeros(shape)

            self.flow_datasources[name] = initial_values
            return self.flow_datasources[name]

        def add_flow_datatarget(self, name, shape, initial_values=None):
            """ Add a high-dimensional datatarget for flowmodules"""
            if initial_values is None:
                initial_values = np.zeros(shape)

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
            shape = self.flow_datasources[name].shape
            assert shape == values.shape, "Datasource %s expects shape %s, got %s" % (name, shape, values.shape)
            self.flow_datasources[name] = values

        def add_to_flow_datatarget(self, name, values):
            """Add the given values to the given flow_datatarget """
            assert isinstance(values, np.ndarray), "must provide numpy array"
            shape = self.flow_datatargets[name].shape
            assert shape == values.shape, "Datatarget %s expects shape %s, got %s" % (name, shape, values.shape)
            self.flow_datatargets[name] += values

        def set_flow_datatarget_feedback(self, name, values):
            """Set the values of the given flow_datatarget_feedback """
            assert isinstance(values, np.ndarray), "must provide numpy array"
            shape = self.flow_datatarget_feedbacks[name].shape
            assert shape == values.shape, "DatatargetFeedback %s expects shape %s, got %s" % (name, shape, values.shape)
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

        def read_from_world(self):
            for k in self.device_map:
                if k in devicemanager.online_devices:
                    if issubclass(devicemanager.online_devices[k].__class__, InputDevice):
                        data = devicemanager.online_devices[k].get_data()
                        assert isinstance(data, np.ndarray), "device %s must provide numpy array, not %s" % (self.device_map[k], type(data))
                        self.set_flow_datasource(self.device_map[k], data)
                elif devicemanager.known_devices[k].get('nature') == "InputDevice":
                    self.logger.error("Device %s is not connected. Using zeros." % self.device_map[k])

        def write_to_world(self):
            for k in self.device_map:
                if k in devicemanager.online_devices:
                    if issubclass(devicemanager.online_devices[k].__class__, OutputDevice):
                        data = self.get_flow_datatarget(self.device_map[k])
                        devicemanager.online_devices[k].set_data(data)
                elif devicemanager.known_devices[k].get('nature') == "OutputDevice":
                    self.logger.error("Device %s is not connected." % self.device_map[k])

        def update_data_sources_and_targets(self):
            self.write_to_world()
            self.read_from_world()

except ImportError:  # pragma: no cover
    pass
