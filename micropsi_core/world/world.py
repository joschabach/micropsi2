"""
The World superclass.
A simple world simulator for MicroPsi nodenet agents

Individual world classes must not only inherit from this one, but also be imported here.
"""

__author__ = 'joscha'
__date__ = '10.05.12'

import json
import os
import warnings
import sys
from micropsi_core.world import worldadapter
from micropsi_core.world import worldobject
from micropsi_core import tools
from micropsi_core.tools import generate_uid
import logging


WORLD_VERSION = 1.0


class World(object):
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
    def current_step(self):
        return self.data.get("step", 0)

    @current_step.setter
    def current_step(self, current_step):
        self.data['step'] = current_step

    @property
    def is_active(self):
        return self.data.get("is_active", False)

    @is_active.setter
    def is_active(self, is_active):
        self.data['is_active'] = is_active

    supported_worldadapters = []

    def __init__(self, filename, world_type="", name="", owner="", uid=None, version=WORLD_VERSION):
        """Create a new MicroPsi simulation environment.

        Arguments:
            filename: the path and filename of the world data
            name (optional): the name of the environment
            owner (optional): the user that created this environment
            uid (optional): unique handle of the world; if none is given, it will be generated
        """

        self.logger = logging.getLogger('world_logger');

        # persistent data
        self.data = {
            "version": WORLD_VERSION,  # used to check compatibility of the world data
            "objects": {},
            "agents": {},
            "step": 0
        }

        folder = self.__module__.split('.')
        folder.pop()
        folder = '.'.join(folder)
        self.supported_worldadapters = { cls.__name__:cls for cls in tools.itersubclasses(worldadapter.WorldAdapter, folder=folder) if cls.__name__ in self.supported_worldadapters }

        self.supported_worldobjects = { cls.__name__:cls for cls in tools.itersubclasses(worldobject.WorldObject, folder=folder)
                                        if cls.__name__ not in self.supported_worldadapters}
        # freaky hack.
        self.supported_worldobjects.pop('WorldAdapter', None)
        self.supported_worldobjects['Default'] = worldobject.WorldObject

        self.uid = uid or generate_uid()
        self.owner = owner
        self.name = name or os.path.basename(filename)
        self.filename = filename
        self.agents = {}
        self.objects = {}

        #self.the_image = None

        self.load()

    def load(self, string=None):
        """Load the world state from a file

        Arguments:
            string (optional): if given, the world state is taken from the string instead.
        """
        # try to access file
        if string:
            try:
                self.data.update(json.loads(string))
            except ValueError:
                warnings.warn("Could not read world data from string")
                return False
        else:
            try:
                with open(self.filename) as file:
                    self.data.update(json.load(file))
            except ValueError:
                warnings.warn("Could not read world data")
                return False
            except IOError:
                warnings.warn("Could not open world file: " + self.filename)
        self.data['world_type'] = self.__class__.__name__
        if "version" in self.data and self.data["version"] == WORLD_VERSION:
            self.initialize_world()
            return True
        else:
            warnings.warn("Wrong version of the world data")
            return False

    def get_available_worldadapters(self):
        """ return the list of instantiated worldadapters """
        return self.supported_worldadapters

    def initialize_world(self):
        """Called after reading new world data.

        Parses the nodenet data and set up the non-persistent data structures necessary for efficient
        computation of the world
        """
        for uid, worldobject in self.data['objects'].copy().items():
            if worldobject['type'] in self.supported_worldobjects:
                self.objects[uid] = self.supported_worldobjects[worldobject['type']](self, **worldobject)
            else:
                self.logger.warn('Worldobject of type %s not supported anymore. Deleting object of this type.' % worldobject['type'])
                del self.data['objects'][uid]
        for uid, agent in self.data.get('agents', {}).items():
            try:
                self.agents[uid] = self.supported_worldadapters[agent['type']](self, **agent)
            except KeyError:
                warnings.warn('Worldadapter %s not found, can not spawn agent %s' % (agent['type'], agent['name']))

    def step(self):
        """ advance the simluation """
        for uid in self.objects:
            self.objects[uid].update()
        for uid in self.agents:
            with self.agents[uid].datasource_lock:
                self.agents[uid].update()
        for uid in self.agents.copy():
            if not self.agents[uid].is_alive():
                self.unregister_nodenet(uid)
                #TODO: stop nodenet and disconnect, prevent respawn
        self.current_step += 1

    def get_world_view(self, step):
        """ returns a list of world objects, and the current step of the simulation """
        return {
            'objects': self.get_world_objects(),
            'agents': self.data.get('agents', {}),
            'current_step': self.current_step,
        }

    def add_object(self, type, position, uid=None, orientation=0.0, name="", parameters=None, **data):
        """
        Add a new object to the current world.

        Arguments:
            type: the type of the object (currently, only "light_source" is supported
            position: a (x, y) tuple with the coordinates
            orientation (optional): an angle, usually between 0 and 2*pi
            name (optional): a readable name for that object
            uid (optional): if omitted, a uid will be generated

        Returns:
            True, uid if successful
            False, errormessage if not
        """
        if not uid:
            uid = tools.generate_uid()
        if type in self.supported_worldobjects:
            self.objects[uid] = self.supported_worldobjects[type](self, type=type, uid=uid, position=position, orientation=orientation, name=name, parameters=parameters, **data)
            return True, uid
        return False, "type not supported"

    def delete_object(self, object_uid):
        if object_uid in self.objects:
            del self.objects[object_uid]
            del self.data['objects'][object_uid]
            return True
        return False

    def get_world_objects(self, type=None):
        """ returns a dictionary of world objects. """
        objects = {}
        if type is None:
            return self.data['objects']
        else:
            for uid, obj in self.data['objects'].items():
                if obj['type'] == type:
                    objects[uid] = obj
        return objects

    def register_nodenet(self, worldadapter, nodenet):
        """Attempts to register a nodenet at this world.

        Returns True, nodenet_uid if successful,
        Returns False, error_message if not successful

        The methods checks if an existing worldadapterish object without a bound nodenet exists, and if not,
        attempts to spawn one. Then the nodenet is bound to it. It is a good idea to make the worldadapter_uid the
        same as the nodenet_uid

        We don't do it the other way around, because the soulless agent body may have been loaded as part of the
        world definition itself.
        """
        if nodenet.uid in self.agents:
            if self.agents[nodenet.uid].__class__.__name__ == worldadapter:
                return True, nodenet.uid
            else:
                return False, "Nodenet agent already exists in this world, but has the wrong type"
        return self.spawn_agent(worldadapter, nodenet.uid, name=nodenet.name)

    def unregister_nodenet(self, nodenet_uid):
        """Removes the connection between a nodenet and its incarnation in this world; may remove the corresponding
        agent object
        """
        if nodenet_uid in self.agents:
            del self.agents[nodenet_uid]
        if nodenet_uid in self.data['agents']:
            del self.data['agents'][nodenet_uid]

    def spawn_agent(self, worldadapter_name, nodenet_uid, **options):
        """Creates an agent object,

        Returns True, nodenet_uid if successful,
        Returns False, error_message if not successful
        """
        try:
            self.agents[nodenet_uid] = self.supported_worldadapters[worldadapter_name](self, uid=nodenet_uid, **options)
            return True, nodenet_uid
        except AttributeError:
            return False, "Worldadapter \"%s\" not found" % worldadapter_name
        except KeyError:
            return False, "Incompatible Worldadapter for this World."

    def set_object_properties(self, uid, type=None, position=None, orientation=None, name=None, parameters=None):
        """set attributes of the world object 'uid'; only supplied attributes will be changed.

       Arguments:
           uid: the uid of the worldobject. Mandatory.
           type: a new type for the object. Optional
           position: a new position for the object. Optional
           orientation: a new orientation for the object. Optional
           name: a new name for the object. Optional
           parameters: a new dict of parameters for the object. optional.

        Returns True if object exists, otherwise False"""
        if uid in self.objects:
            if type:
                self.objects[uid].type = type
            if position:
                self.objects[uid].position = position
            if orientation:
                self.objects[uid].orientation = orientation
            if name:
                self.objects[uid].name = name
            if parameters:
                self.objects[uid].parameters = parameters
            return True
        return False

    def set_agent_properties(self, uid, position=None, orientation=None, name=None, parameters=None):
        """set attributes of the agent 'uid'; only supplied attributes will be changed.
        Returns True if agent exists, otherwise False"""

        if uid in self.agents:
            if position:
                self.agents[uid].position = position
            if orientation:
                self.agents[uid].orientation = orientation
            if name:
                self.agents[uid].name = name
            if parameters:
                self.agents[uid].parameters = parameters
            return True
        return False

    def get_available_datasources(self, nodenet_uid):
        """Returns the datasource types for a registered nodenet, or None if the nodenet is not registered."""
        if nodenet_uid in self.agents:
            return self.agents[nodenet_uid].get_available_datasources()
        return None

    def get_available_datatargets(self, nodenet_uid):
        """Returns the datatarget types for a registered nodenet, or None if the nodenet is not registered."""
        if nodenet_uid in self.agents:
            return self.agents[nodenet_uid].get_available_datatargets()
        return None

    def get_datasource(self, nodenet_uid, key):
        """allows the nodenet to read a value from a datasource"""
        if nodenet_uid in self.agents:
            return self.agents[nodenet_uid].get_datasource(key)
        return None

    def set_datatarget(self, nodenet_uid, key, value):
        """allows the nodenet to write a value to a datatarget"""
        if nodenet_uid in self.agents:
            return self.agents[nodenet_uid].set_datatarget(key, value)

    def get_datatarget_feedback(self, nodenet_uid, key):
        """allows the nodenet to write a value to a datatarget"""
        if nodenet_uid in self.agents:
            return self.agents[nodenet_uid].get_datatarget_feedback(key)


# imports of individual world types:
try:
    from micropsi_core.world.island import island
except ImportError as e:
    sys.stdout.write("Could not import island world.\nError: %s \n\n" % e.msg)

try:
    from micropsi_core.world.island.structured_objects import structured_objects
except ImportError as e:
    sys.stdout.write("Could not import island world / structured objects.\nError: %s \n\n" % e.msg)

try:
    from micropsi_core.world.berlin import berlin
except ImportError as e:
    sys.stdout.write("Could not import berlin world.\nError: %s \n\n" % e.msg)

try:
    from micropsi_core.world.minecraft import minecraft
    from micropsi_core.world.minecraft.minecraft import Minecraft
except ImportError as e:
    sys.stdout.write("Could not import minecraft world.\nError: %s \n\n" % e.msg)
