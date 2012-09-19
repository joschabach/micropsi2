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


from worldobject import WorldObject


class WorldAdapter(WorldObject):
    """Transmits data between agent and environment.

    The agent writes activation values into data targets, and receives it from data sources. The world adapter
    takes care of translating between the world and these values at each world cycle.
    """

    datasources = {}
    datatargets = {}

    def initialize_worldobject(self, data):
        for key in self.datasources:
            self.datasources[key] = data.get('datasources', {}).get(key)
        for key in self.datatargets:
            self.datasources[key] = data.get('datatargets', {}).get(key)

    # agent facing methods:
    def get_available_datasources(self):
        """returns a list of identifiers of the datasources available for this world adapter"""
        return self.datasources.keys()

    def get_available_datatargets(self):
        """returns a list of identifiers of the datatargets available for this world adapter"""
        return self.datatargets.keys()

    def get_datasource(self, key):
        """allows the agent to read a value from a datasource"""
        if key in self.datasources:
            return self.datasources[key]
        return None

    def set_datatarget(self, key, value):
        """allows the agent to write a value to a datatarget"""
        if key in self.datatargets:
            self.datatargets[key] = value

    # world facing methods:
    def update(self):
        """called by the world to update datasources"""
        pass


class Default(WorldAdapter):
    datasources = {'default': 1}
    datatargets = {'default': 0}


class Braitenberg(WorldAdapter):
    datasources = {'brightness': 1.7}
    datatargets = {}
