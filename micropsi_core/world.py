"""
A simple world simulator for MicroPsi nodenet agents
"""

__author__ = 'joscha'
__date__ = '10.05.12'

import worldadapter
import json
import os
import warnings
from micropsi_core.tools import generate_uid

WORLD_VERSION = 1.0

def World(object):
    """The environment of MicroPsi agents. The world connects to their nodenets via world adapters."""

    @property
    def uid(self):
        return self.data.get("uid")

    @uid.setter
    def uid(self, identifier):
        self.data["uid"] = identifier

    @property
    def name(self):
        return self.data.get("name", self.data.get("uid"))

    @name.setter
    def name(self, identifier):
        self.data["name"] = identifier

    @property
    def owner(self):
        return self.data.get("owner")

    @owner.setter
    def owner(self, identifier):
        self.data["owner"] = identifier

    @property
    def step(self):
        return self.data.get("step")

    @property
    def worldadapters(self):
        return [self.worldadapters[type].world_adapter for type in self.worldadapters]

    def __init__(self, runtime, filename, name = "", world_type = "Default", owner = "", uid = None):
        """Create a new MicroPsi simulation environment.

        Arguments:
            filename: the path and filename of the world data
            world_type (optional): the type of the environment
            name (optional): the name of the environment
            owner (optional): the user that created this environment
            uid (optional): unique handle of the world; if none is given, it will be generated
        """

        self.runtime = runtime
        self.uid = uid or generate_uid()
        self.owner = owner
        self.name = name or os.path.basename(filename)
        self.filename = filename
        self.agents = {}
        self.world_type = world_type

        self.worldadapters = {"Default": worldadapter.WorldAdapter(self, "Default")}

        # persistent data
        self.data = {
            "version": WORLD_VERSION,  # used to check compatibility of the world data
            "worldadapters": self.worldadapters,
            "objects": {},
            "step": 0
        }
        self.load()

    def load(self, string = None):
        """Load the world data from a file

        Arguments:
            string (optional): if given, the world data is taken from the string instead.
        """
        # try to access file
        if string:
            try:
                self.data = json.loads(string)
            except ValueError:
                warnings.warn("Could not read world data from string")
                return False
        else:
            try:
                with open(self.filename) as file:
                    self.data = json.load(file)
            except ValueError:
                warnings.warn("Could not read world data")
                return False
            except IOError:
                warnings.warn("Could not open world file")

        if "version" in self.data and self.data["version"] == WORLD_VERSION:
            self.initialize_world()
            return True
        else:
            warnings.warn("Wrong version of the world data; starting new world")
            return False

    def initialize_worlddata(self):
        """Called after reading new world data.

        Parses the nodenet data and set up the non-persistent data structures necessary for efficient
        computation of the world
        """
        pass

    def register_nodenet(self, worldadapter, nodenet_uid):
        """Attempts to register a nodenet at this world.

        Returns True, nodenet_uid if successful,
        Returns False, error_message if not successful

        The methods checks if an existing worldadapterish object without a bound nodenet exists, and if not,
        attempts to spawn one. Then the nodenet is bound to it. It is a good idea to make the worldadapter_uid the
        same as the nodenet_uid

        We don't do it the other way around, because the soulless agent body may have been loaded as part of the
        world definition itself.
        """
        if nodenet_uid in self.agents:
            if self.agent[nodenet_uid].world_adapter == worldadapter:
                return True, nodenet_uid
            else:
                return False, "Nodenet agent already exists in this world, but has the wrong type"

        return self.spawn_agent(worldadapter, nodenet_uid)


    def unregister_nodenet(self, nodenet_uid):
        """Removes the connection between a nodenet and its incarnation in this world; may remove the corresponding
        agent object
        """
        pass

    def spawn_agent(self, worldadapter, nodenet_uid, options = None):
        """Creates an agent object (nodenet incarnation),

        Returns True, nodenet_uid if successful,
        Returns False, error_message if not successful
        """
        pass

    def get_available_datasources(self, nodenet_uid):
        """Returns the datasource types for a registered nodenet, or None if the nodenet is not registered."""
        if nodenet_uid in self.agents:
            return self.agent[nodenet_uid].datasources
        else: return None

    def get_available_datatargets(self, nodenet_uid):
        """Returns the datatarget types for a registered nodenet, or None if the nodenet is not registered."""
        if nodenet_uid in self.worldadapters:
            return self.agent[agent_uid].datatargets
        else: return None

    def get_datasource(self, nodenet_uid, key):
        """allows the nodenet to read a value from a datasource"""
        if nodenet_uid in self.agents:
            return self.agents[nodenet_uid].datasources.get(key)
        else: return None

    def set_datatarget(self, nodenet_uid, key, value):
        """allows the nodenet to write a value to a datatarget"""
        if nodenet_uid in self.agents:
            self.agents[nodenet_uid].datatargets.set(key, value)
