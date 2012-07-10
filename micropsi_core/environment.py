"""
A simple world simulator for MicroPsi agents
"""

__author__ = 'joscha'
__date__ = '10.05.12'

from worldadapter import WorldAdapter

class WorldManager(object):

    def __init__(self, filename, world_type = "Default", name = "", owner = "", uid = None):
        self.world = {
            "supported_agent_types": []
        }
        self.worldadapters = {}

    def get_name(self):
        """returns the name of this world"""
        return ""

    # Interaction with agents

    def get_agent_types(self):
        """return the agent types (kinds of world adapters) supported by this world"""
        return []

    def register_agent(self, agent_type, agent_uid):
        """Attempts to register an agent at this world.

        Returns True, agent_id if successful,
        Returns False, error_message if not successful

        The methods checks if an existing worldadapterish object without a bound agent exists, and if not,
        attempts to spawn one. Then the agent is bound to it. It is a good idea to make the worldadapter_uid the
        same as the agent_uid

        We don't do it the other way around, because the soulless agent body may have been loaded with the
        world definition itself.
        """
        if agent_uid in self.worldadapters:
            if self.worldadapters[agent_uid].agent_type == agent_type:
                return True, agent_uid
            else:
                return False, "Agent already exists in this world, but has the wrong type"

        return self.spawn_agent(agent_type, agent_uid)


    def unregister_agent(self, agent_uid):
        """Removes the connection between an agent and its incarnation in this world; may remove the corresponding
        world object
        """
        pass

    def spawn_agent(self, agent_type, agent_uid, options = None):
        """Creates a worldadapterish object (agent incarnation),

        Returns True, agent_uid if successful,
        Returns False, error_message if not successful
        """
        pass

    def get_available_datasources(self, agent_uid):
        """Returns the datasource types for a registered agent, or None if the agent is not registered."""
        if agent_uid in self.worldadapters:
            return self.worldadapters[agent_uid].get_available_datasources()
        else: return None

    def get_available_datatargets(self, agent_uid):
        """Returns the datatarget types for a registered agent, or None if the agent is not registered."""
        if agent_uid in self.worldadapters:
            return self.worldadapters[agent_uid].get_available_datatargets()
        else: return None

    def get_datasource(self, agent_uid, key):
        """allows the agent to read a value from a datasource"""
        if agent_uid in self.worldadapters:
            return self.worldadapters[agent_uid].get_datasource(key)
        else: return None

    def set_datatarget(self, agent_uid, key, value):
        """allows the agent to write a value to a datatarget"""
        if agent_uid in self.worldadapters:
            self.worldadapters[agent_uid].set_datatarget(key, value)

    # Interaction with UI

    def load_world(self, filename):
        """load the world from a file"""
        pass

    def save_world(self, filename):
        """save the world to a file"""
        pass

    def step(self):
        """Perform a simulation step on the world"""
        pass
