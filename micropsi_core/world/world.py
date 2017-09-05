"""
The World superclass.
A simple world simulator for MicroPsi nodenet agents

Individual world classes must not only inherit from this one, but also be imported here.
"""

__author__ = 'joscha'
__date__ = '10.05.12'

import json
import os
import sys
import micropsi_core
from micropsi_core.world import worldadapter
from micropsi_core.world import worldobject
from micropsi_core import tools
from micropsi_core.tools import generate_uid
import logging


WORLD_VERSION = 1


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
        return self.data.get('current_step', 0)

    @current_step.setter
    def current_step(self, current_step):
        self.data['current_step'] = current_step

    @property
    def config(self):
        return self.data['config']

    @classmethod
    def get_config_options(cls):
        """ Returns a list of configuration-options for this world.
        Expected format:
        [{
            'name': 'param1',
            'description': 'this is just an example',
            'options': ['value1', 'value2'],
            'default': 'value1'
        }]
        description, options and default are optional settings
        """
        return []

    @classmethod
    def get_supported_worldadapters(cls):
        folder = cls.__module__.split('.')
        folder.pop()
        folder = '.'.join(folder)
        return {wacls.__name__: wacls for wacls in tools.itersubclasses(worldadapter.WorldAdapter, folder=folder) if wacls.__name__ in cls.supported_worldadapters}

    supported_worldadapters = []
    supported_worldobjects = []
    is_realtime = False

    def __init__(self, filename, world_type="", name="", owner="", uid=None, engine=None, version=WORLD_VERSION, config={}):
        """Create a new MicroPsi world environment.

        Arguments:
            filename: the path and filename of the world data
            name (optional): the name of the environment
            owner (optional): the user that created this environment
            uid (optional): unique handle of the world; if none is given, it will be generated
        """

        self.logger = logging.getLogger('world')

        # persistent data
        self.data = {
            "version": version,  # used to check compatibility of the world data
            "objects": {},
            "agents": {},
            "current_step": 0,
            "config": config
        }
        self.is_active = False
        folder = self.__module__.split('.')
        folder.pop()
        folder = '.'.join(folder)

        self.supported_worldadapters = {name: cls for name, cls in micropsi_core.runtime.worldadapter_classes.items() if name in self.supported_worldadapters}
        self.supported_worldobjects = {name: cls for name, cls in micropsi_core.runtime.worldobject_classes.items() if name in self.supported_worldobjects}

        self.uid = uid or generate_uid()
        self.owner = owner
        self.name = name or os.path.basename(filename)
        self.filename = filename
        self.agents = {}
        self.objects = {}

        # self.the_image = None

        self.load()

    def load(self):
        """ Load the world state from persistance """
        # try to access file
        try:
            with open(self.filename, encoding="utf-8") as file:
                self.data.update(json.load(file))
        except ValueError:
            self.logger.warning("Could not read world data")
            return False
        except IOError:
            self.logger.warning("Could not open world file: " + self.filename)
        self.data['world_type'] = self.__class__.__name__
        if "version" in self.data and self.data["version"] == WORLD_VERSION:
            self.initialize_world()
            return True
        else:
            self.logger.warning("Wrong version of the world data")
            return False

    def simulation_started(self):
        self.is_active = True

    def simulation_stopped(self):
        self.is_active = False

    def get_available_worldadapters(self):
        """ return the list of instantiated worldadapters """
        return self.supported_worldadapters

    def initialize_world(self, data=None):
        """Called after reading new world data.

        Parses the nodenet data and set up the non-persistent data structures necessary for efficient
        computation of the world
        """
        if data is None:
            data = self.data
        for uid, object_data in data['objects'].copy().items():
            if object_data['type'] in self.supported_worldobjects:
                self.objects[uid] = self.supported_worldobjects[object_data['type']](self, **object_data)
            else:
                self.logger.warning('Worldobject of type %s not supported anymore. Deleting object of this type.' % object_data['type'])
                del data['objects'][uid]
        for uid in list(self.data['agents']):
            if uid not in micropsi_core.runtime.nodenet_data:
                del self.data['agents'][uid]

    def step(self):
        """ advance the simluation """
        self.current_step += 1
        for uid in self.objects:
            self.objects[uid].update()
        for uid in self.agents:
            with self.agents[uid].datasource_lock:
                self.agents[uid].update()
        for uid in self.agents.copy():
            if not self.agents[uid].is_alive():
                # remove from living agents for the moment
                # TODO: unregister?
                # TODO: respawn?
                del self.agents[uid]

    def get_world_view(self, step):
        """ returns a list of world objects, and the current step of the calculation """
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

    def register_nodenet(self, worldadapter, nodenet_uid, nodenet_name=None, config={}):
        """Attempts to register a nodenet at this world.

        Returns True, spawned_agent_instance if successful,
        Returns False, error_message if not successful

        The methods checks if an existing worldadapterish object without a bound nodenet exists, and if not,
        attempts to spawn one. Then the nodenet is bound to it. It is a good idea to make the worldadapter_uid the
        same as the nodenet_uid

        We don't do it the other way around, because the soulless agent body may have been loaded as part of the
        world definition itself.
        """
        if nodenet_uid in self.agents:
            if self.agents[nodenet_uid].__class__.__name__ != worldadapter:
                return False, "Nodenet agent already exists in this world, but has the wrong type"
            elif config == self.agents[nodenet_uid].config:
                    return True, self.agents[nodenet_uid]
        return self.spawn_agent(worldadapter, nodenet_uid, nodenet_name=nodenet_name, config=config)

    def unregister_nodenet(self, nodenet_uid):
        """Removes the connection between a nodenet and its incarnation in this world; may remove the corresponding
        agent object
        """
        if nodenet_uid in self.agents:
            # stop corresponding nodenet
            micropsi_core.runtime.stop_nodenetrunner(nodenet_uid)
            del self.agents[nodenet_uid]
        if nodenet_uid in self.data['agents']:
            del self.data['agents'][nodenet_uid]

    def spawn_agent(self, worldadapter_name, nodenet_uid, nodenet_name=None, config={}):
        """Creates an agent object,

        Returns True, spawned_agent_instance if successful,
        Returns False, error_message if not successful
        """
        if worldadapter_name in self.supported_worldadapters:
            self.agents[nodenet_uid] = self.supported_worldadapters[worldadapter_name](
                self,
                uid=nodenet_uid,
                type=worldadapter_name,
                name=nodenet_name or worldadapter_name,
                config=config)
            return True, self.agents[nodenet_uid]
        else:
            self.logger.error("World %s does not support Worldadapter %s" % (self.name, worldadapter_name))
            return False, "World %s does not support Worldadapter %s" % (self.name, worldadapter_name)

    def set_object_properties(self, uid, position=None, orientation=None, name=None, parameters=None):
        """set attributes of the world object 'uid'; only supplied attributes will be changed.

       Arguments:
           uid: the uid of the worldobject. Mandatory.
           position: a new position for the object. Optional
           orientation: a new orientation for the object. Optional
           name: a new name for the object. Optional
           parameters: a new dict of parameters for the object. optional.

        Returns True if object exists, otherwise False"""
        if uid in self.objects:
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

    def set_user_data(self, data):
        """ Sets some data from the user. Implement this in your worldclass to allow
        the user to set certain properties of this world"""
        pass  # pragma: no cover

    def signal_handler(self, *args):
        """ stuff to do on sigint, sigabrt, etc"""
        pass  # pragma: no cover

    def __del__(self):
        """ Empty destructor """
        pass


class DefaultWorld(World):
    supported_worldadapters = ['Default', 'DefaultArray']
    supported_worldobjects = ['TestObject']
