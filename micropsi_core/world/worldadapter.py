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
world simulation (for robotic bodies, the equivalent might consist in powering up/setup/boot operations.
Thus, agent types should be instantiated by the world, inherit from a moving object class of some kind
and treated as parts of the world.
"""

__author__ = 'joscha'
__date__ = '10.05.12'

from threading import Lock
from micropsi_core.world.worldobject import WorldObject


class WorldAdapter(WorldObject):
    """Transmits data between agent and environment.

    The agent writes activation values into data targets, and receives it from data sources. The world adapter
    takes care of translating between the world and these values at each world cycle.
    """
    supported_datasources = []
    supported_datatargets = []

    def __init__(self, world, uid=None, **data):
        self.datasources = {}
        for key in self.supported_datasources:
            self.datasources[key] = 0
        self.datatargets = {}
        for key in self.supported_datatargets:
            self.datatargets[key] = 0
        self.datatarget_feedback = {}
        self.datasource_lock = Lock()
        self.datasource_snapshots = {}
        WorldObject.__init__(self, world, category='agents', uid=uid, **data)
        self.snapshot()

    def initialize_worldobject(self, data):
        for key in self.datasources:
            if key in data.get('datasources', {}):
                self.datasources[key] = data['datasources'][key]
        for key in self.datatargets:
            if key in data.get('datatargets', {}):
                self.datatargets[key] = data['datatargets'][key]
                self.datatarget_feedback[key] = 0

    # agent facing methods:
    def snapshot(self):
        """called by the agent every netstep to create a consistent set of sensory input"""
        with self.datasource_lock:
            self.datasource_snapshots = self.datasources.copy()

    def get_available_datasources(self):
        """returns a list of identifiers of the datasources available for this world adapter"""
        return list(self.datasources.keys())

    def get_available_datatargets(self):
        """returns a list of identifiers of the datatargets available for this world adapter"""
        return list(self.datatargets.keys())

    def get_datasource(self, key):
        """allows the agent to read a value from a datasource"""
        return self.datasource_snapshots.get(key)

    def add_to_datatarget(self, key, value):
        """allows the agent to write a value to a datatarget"""
        if key in self.datatargets:
            self.datatargets[key] += value

    def get_datatarget_feedback(self, key):
        """get feedback whether the actor-induced action succeeded"""
        return self.datatarget_feedback.get(key, 0)

    def set_datatarget_feedback(self, key, value):
        """set feedback for the given datatarget"""
        self.datatarget_feedback[key] = value

    def update(self):
        """ Called by the world at each world iteration """
        self.update_data_sources_and_targets()
        self.reset_datatargets()

    def reset_datatargets(self):
        """ resets (zeros) the datatargets """
        for datatarget in self.supported_datatargets:
            self.datatargets[datatarget] = 0

    def update_data_sources_and_targets(self):
        """must be implemented by concrete world adapters to read datatargets and fill datasources"""
        pass

    def is_alive(self):
        """called by the world to check whether the agent has died and should be removed"""
        return True


class Default(WorldAdapter):

    supported_datasources = ['static_on', 'random', 'static_off']
    supported_datatargets = ['echo']

    def update_data_sources_and_targets(self):
        import random
        if self.datatargets['echo'] != 0:
            self.datatarget_feedback['echo'] = self.datatargets['echo']
        self.datasources['static_on'] = 1
        self.datasources['random'] = random.uniform(0, 1)
