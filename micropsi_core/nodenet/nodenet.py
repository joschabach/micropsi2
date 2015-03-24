# -*- coding: utf-8 -*-

"""
Nodenet definition
"""
from copy import deepcopy

import micropsi_core.tools
from abc import ABCMeta, abstractmethod

from .node import Node
from threading import Lock
import logging
from .nodespace import Nodespace
from .netapi import NetAPI

__author__ = 'joscha'
__date__ = '09.05.12'

NODENET_VERSION = 1


class NodenetLockException(Exception):
    pass


class Nodenet(metaclass=ABCMeta):
    """
    Nodenet is the abstract base class for all node net implementations and defines the interface towards
    runtime.py, which is where JSON API and tests access node nets.

    This abstract Nodenet class defines handling of node net uid, name, world and worldadapter connections,
    but makes no assumptions on persistency (filesystem, database, memory-only) or implementation.
    """

    __uid = ""
    __name = ""
    __world_uid = None
    __worldadapter_uid = None
    is_active = False

    @property
    @abstractmethod
    def engine(self):
        """
        Returns the type of node net engine this nodenet is implemented with
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def current_step(self):
        """
        Returns the current net step, an integer
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def data(self):
        """
        Returns a dict representing the whole node net.
        Concrete implementations may call this (super) method and then add the following fields if they want to
        use JSON persistency:

        links
        nodes
        nodespaces
        version
        """

        # todo: data dicts will be replaced with a save/load/export API at some point.

        data = {
            'uid': self.uid,
            'engine': self.engine,
            'owner': self.owner,
            'links': {},
            'nodes': {},
            'name': self.name,
            'max_coords': self.max_coords,
            'is_active': self.is_active,
            'current_step': self.current_step,
            'nodespaces': {},
            'world': self.__world_uid,
            'worldadapter': self.__worldadapter_uid,
            'settings': self.settings,
            'monitors': self.construct_monitors_dict(),
            'modulators': {},
            'version': "abstract"
        }
        return data

    @property
    def uid(self):
        """
        Returns the uid of the node net
        """
        return self.__uid

    @property
    def name(self):
        """
        Returns the name of the node net for display purposes
        """
        if self.__name is not None:
            return self.__name
        else:
            return self.uid

    @name.setter
    def name(self, name):
        """
        Sets the name of the node net to the given string
        """
        self.__name = name

    @property
    def world(self):
        """
        Returns the currently connected world (as an object) or none if no world is set
        """
        if self.__world_uid is not None:
            from micropsi_core.runtime import worlds
            return worlds.get(self.__world_uid)
        return None

    @world.setter
    def world(self, world):
        """
        Connects the node net to the given world object, or disconnects if None is given
        """
        if world:
            self.__world_uid = world.uid
        else:
            self.__world_uid = None

    @property
    def worldadapter(self):
        """
        Returns the uid of the currently connected world adapter
        """
        return self.__worldadapter_uid

    @worldadapter.setter
    def worldadapter(self, worldadapter_uid):
        """
        Connects the node net to the given world adapter uid, or disconnects if None is given
        """
        self.__worldadapter_uid = worldadapter_uid

    def __init__(self, name="", worldadapter="Default", world=None, owner="", uid=None):
        """
        Constructor for the abstract base class, must be called by implementations
        """
        uid = uid or micropsi_core.tools.generate_uid()

        self.__version = NODENET_VERSION  # used to check compatibility of the node net data
        self.__uid = uid

        self.world = world
        self.owner = owner
        self.name = name
        if world and worldadapter:
            self.worldadapter = worldadapter

        self.__monitors = {}

        self.max_coords = {'x': 0, 'y': 0}

        self.netlock = Lock()

        self.logger = logging.getLogger("nodenet")
        self.logger.info("Setting up nodenet %s with engine %s", self.name, self.engine)

        self.user_prompt = None

        self.netapi = NetAPI(self)

    @abstractmethod
    def step(self):
        """
        Performs one calculation step, propagating activation accross links
        """
        pass  # pragma: no cover

    @abstractmethod
    def get_node(self, uid):
        """
        Returns the Node object with the given UID or None if no such Node object exists
        """
        pass  # pragma: no cover

    @abstractmethod
    def get_node_uids(self):
        """
        Returns a list of the UIDs of all Node objects that exist in the node net
        """
        pass  # pragma: no cover

    @abstractmethod
    def is_node(self, uid):
        """
        Returns true if the given UID is the UID of an existing Node object
        """
        pass  # pragma: no cover

    @abstractmethod
    def create_node(self, nodetype, nodespace_uid, position, name="", uid=None, parameters=None, gate_parameters=None):
        """
        Creates a new node of the given node type (string), in the nodespace with the given UID, at the given
        position and returns the uid of the new node
        """
        pass  # pragma: no cover

    @abstractmethod
    def delete_node(self, uid):
        """
        Deletes the node with the given UID.
        """
        pass  # pragma: no cover

    @abstractmethod
    def get_nodespace(self, uid):
        """
        Returns the Nodespace object with the given UID or None if no such Nodespace object exists
        """
        pass  # pragma: no cover

    @abstractmethod
    def get_nodespace_uids(self):
        """
        Returns a list of the UIDs of all Nodespace objects that exist in the node net
        """
        pass  # pragma: no cover

    @abstractmethod
    def is_nodespace(self, uid):
        """
        Returns true if the given UID is the UID of an existing Nodespace object
        """
        pass  # pragma: no cover

    @abstractmethod
    def create_nodespace(self, parent_uid, position, name="", uid=None, gatefunction_strings=None):
        """
        Creates a new nodespace  in the nodespace with the given UID, at the given position.
        """
        pass  # pragma: no cover

    @abstractmethod
    def delete_nodespace(self, uid):
        """
        Deletes the nodespace with the given UID, and everything it contains
        """
        pass  # pragma: no cover

    @abstractmethod
    def create_link(self, source_node_uid, gate_type, target_node_uid, slot_type, weight=1, certainty=1):
        """
        Creates a new link between the given node/gate and node/slot
        """
        pass  # pragma: no cover

    @abstractmethod
    def set_link_weight(self, source_node_uid, gate_type, target_node_uid, slot_type, weight=1, certainty=1):
        """
        Set weight of the link between the given node/gate and node/slot
        """
        pass  # pragma: no cover

    @abstractmethod
    def delete_link(self, source_node_uid, gate_type, target_node_uid, slot_type):
        """
        Deletes the link between the given node/gate and node/slot
        """
        pass  # pragma: no cover

    @abstractmethod
    def reload_native_modules(self, native_modules):
        """
        Replaces the native module definitions in the nodenet with the native module definitions given in the
        native_modules dict.

        Format example for the definition dict:

        "native_module_id": {
            "name": "Name of the Native Module",
            "slottypes": ["trigger"],
            "nodefunction_name": "native_module_function",
            "gatetypes": ["done"],
            "gate_defaults": {
                "done": {
                    "minimum": -100,
                    "maximum": 100,
                    "threshold": -100
                }
            }
        }

        """
        pass  # pragma: no cover

    @abstractmethod
    def get_nodespace_area_data(self, nodespace_uid, x1, x2, y1, y2):
        """
        Returns a data dict of the structure defined in the .data property, filtered for nodes in the given
        nodespace, and within the given rectangle.

        Implementations are expected to fill the following keys:
        'nodes' - map of nodes it the given rectangle
        'links' - map of links ending or originating in the given rectangle
        'nodespaces' - map of nodespaces positioned in the given rectangle
        'monitors' - result of self.construct_monitors_dict()
        'user_prompt' - self.user_prompt if set, should be cleared then
        """
        # todo: data dicts will be replaced with a save/load/export API at some point.
        # todo: Positional data will either be made entirely transient at some point, or moved somewhere else
        pass  # pragma: no cover

    @abstractmethod
    def get_nodespace_data(self, nodespace_uid, max_nodes):
        """
        Returns a data dict of the structure defined in the .data property, filtered for nodes in the given
        nodespace and limited to the given number of nodes.

        Implementations are expected to fill the following keys:
        'nodes' - map of nodes it the given rectangle
        'links' - map of links ending or originating in the given rectangle
        'nodespaces' - map of nodespaces positioned in the given rectangle
        'monitors' - result of self.construct_monitors_dict()
        'user_prompt' - self.user_prompt if set, should be cleared then
        """
        # todo: data dicts will be replaced with a save/load/export API at some point.
        pass  # pragma: no cover

    @abstractmethod
    def merge_data(self, nodenet_data):
        """
        Merges in the data in nodenet_data, which is a dict of the structure defined by the .data property.
        This is a legacy method from when the only available implementation was dict-based and will either be
        removed or implemented in the abstact base class as a generic JSON/dict import mechanism.
        """
        # todo: data dicts will be replaced with a save/load/export API at some point.
        pass  # pragma: no cover

    @abstractmethod
    def is_locked(self, lock):
        """
        Returns true if a lock of the given name exists
        """
        pass  # pragma: no cover

    @abstractmethod
    def is_locked_by(self, lock, key):
        """
        Returns true if a lock of the given name exists and the key used is the given one
        """
        pass  # pragma: no cover

    @abstractmethod
    def lock(self, lock, key, timeout=100):
        """
        Creates a lock with the given name that will time out after the given number of steps
        """
        pass  # pragma: no cover

    @abstractmethod
    def unlock(self, lock):
        """
        Removes the given lock
        """
        pass  # pragma: no cover

    @abstractmethod
    def get_modulator(self, modulator):
        """
        Returns the numeric value of the given global modulator
        """
        pass  # pragma: no cover

    @abstractmethod
    def change_modulator(self, modulator, diff):
        """
        Changes the value of the given global modulator by the value of diff
        """
        pass  # pragma: no cover

    @abstractmethod
    def set_modulator(self, modulator, value):
        """
        Changes the value of the given global modulator to the given value
        """
        pass  # pragma: no cover

    @abstractmethod
    def get_standard_nodetype_definitions(self):
        """
        Returns the standard node types supported by this nodenet
        """
        pass  # pragma: no cover

    def clear(self):
        self.__monitors = {}

    def get_monitor(self, uid):
        return self.__monitors[uid]

    def update_monitors(self):
        for uid in self.__monitors:
            self.__monitors[uid].step(self.current_step)

    def construct_monitors_dict(self):
        data = {}
        for monitor_uid in self.__monitors:
            data[monitor_uid] = self.__monitors[monitor_uid].data
        return data

    def _register_monitor(self, monitor):
        self.__monitors[monitor.uid] = monitor

    def _unregister_monitor(self, monitor_uid):
        del self.__monitors[monitor_uid]
