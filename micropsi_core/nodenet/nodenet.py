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
    def current_step(self):
        """
        Returns the current net step, an integer
        """
        pass

    @property
    @abstractmethod
    def data(self):
        """
        Returns a dict representing the whole node net.
        Concrete implementations are to call this (super) method and then add the following fields:

        links
        nodes
        nodespaces
        monitors
        version
        """

        #todo: data dicts will be replaced with a save/load/export API at some point.

        data = {
            'uid': self.uid,
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
        self.logger.info("Setting up nodenet %s", self.name)

        self.user_prompt = None

        self.netapi = NetAPI(self)

    @abstractmethod
    def step(self):
        """
        Performs one calculatio step, propagating activation accross links
        """
        pass

    @abstractmethod
    def get_node(self, uid):
        """
        Returns the Node object with the given UID or None if no such Node object exists
        """
        pass

    @abstractmethod
    def get_node_uids(self):
        """
        Returns a list of the UIDs of all Node objects that exist in the node net
        """
        pass

    @abstractmethod
    def is_node(self, uid):
        """
        Returns true if the given UID is the UID of an existing Node object
        """
        pass

    @abstractmethod
    def create_node(self, nodetype, nodespace_uid, position, name="", uid=None, parameters=None, gate_parameters=None):
        """
        Creates a new node of the given node type (string), in the nodespace with the given UID, at the given
        position.
        """
        pass

    @abstractmethod
    def delete_node(self, uid):
        """
        Deletes the node with the given UID.
        """
        pass

    @abstractmethod
    def get_nodespace(self, uid):
        """
        Returns the Nodespace object with the given UID or None if no such Nodespace object exists
        """
        pass

    @abstractmethod
    def get_nodespace_uids(self):
        """
        Returns a list of the UIDs of all Nodespace objects that exist in the node net
        """
        pass

    @abstractmethod
    def is_nodespace(self, uid):
        """
        Returns true if the given UID is the UID of an existing Nodespace object
        """
        pass

    @abstractmethod
    def create_nodespace(self, parent_uid, position, name="", uid=None, gatefunction_strings=None):
        """
        Creates a new nodespace  in the nodespace with the given UID, at the given position.
        """
        pass

    @abstractmethod
    def delete_nodespace(self, uid):
        """
        Deletes the nodespace with the given UID, and everything it contains
        """
        pass

    @abstractmethod
    def create_link(self, source_node_uid, gate_type, target_node_uid, slot_type, weight=1, certainty=1):
        """
        Creates a new link between the given node/gate and node/slot
        """
        pass

    @abstractmethod
    def set_link_weight(self, source_node_uid, gate_type, target_node_uid, slot_type, weight=1, certainty=1):
        """
        Set weight of the link between the given node/gate and node/slot
        """
        pass

    @abstractmethod
    def delete_link(self, source_node_uid, gate_type, target_node_uid, slot_type):
        """
        Deletes the link between the given node/gate and node/slot
        """
        pass

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
        pass

    @abstractmethod
    def get_nodespace_area_data(self, nodespace_uid, x1, x2, y1, y2):
        """
        Returns a data dict of the sztructure defined in the .data property, filtered for nodes in the given
        nodespace, and within the given rectangle.
        """
        #todo: data dicts will be replaced with a save/load/export API at some point.
        #todo: Positional data will either be made entirely transient at some point, or moved somewhere else
        pass

    @abstractmethod
    def get_nodespace_data(self, nodespace_uid, max_nodes):
        """
        Returns a data dict of the sztructure defined in the .data property, filtered for nodes in the given
        nodespace and limited to the given number of nodes.
        """
        #todo: data dicts will be replaced with a save/load/export API at some point.
        pass

    @abstractmethod
    def merge_data(self, nodenet_data):
        """
        Merges in the data in nodenet_data, which is a dict of the structure defined by the .data property.
        This is a legacy method from when the only available implementation was dict-based and will either be
        removed or implemented in the abstact base class as a generic JSON/dict import mechanism.
        """
        #todo: data dicts will be replaced with a save/load/export API at some point.
        pass

    @abstractmethod
    def get_nodetype(self, type):
        """ Returns the nodetpype instance for the given nodetype or native_module or None if not found"""
        pass

    @abstractmethod
    def is_locked(self, lock):
        """Returns true if a lock of the given name exists"""
        pass

    @abstractmethod
    def is_locked_by(self, lock, key):
        """Returns true if a lock of the given name exists and the key used is the given one"""
        pass

    @abstractmethod
    def lock(self, lock, key, timeout=100):
        """Creates a lock with the given name that will time out after the given number of steps
        """
        pass

    @abstractmethod
    def unlock(self, lock):
        """Removes the given lock
        """
        pass

    def clear(self):
        self.__monitors = {}

    def get_monitor(self, uid):
        return self.__monitors[uid]

    def update_monitors(self):
        for uid in self.__monitors:
            self.__monitors[uid].step(self.step)

    def construct_monitors_dict(self):
        data = {}
        for monitor_uid in self.__monitors:
            data[monitor_uid] = self.__monitors[monitor_uid].data
        return data

    def _register_monitor(self, monitor):
        self.__monitors[monitor.uid] = monitor

    def _unregister_monitor(self, monitor_uid):
        del self.__monitors[monitor_uid]


class NetAPI(object):
    """
    Node Net API facade class for use from within the node net (in node functions)
    """

    __locks_to_delete = []

    @property
    def uid(self):
        return self.__nodenet.uid

    @property
    def step(self):
        return self.__nodenet.current_step

    @property
    def world(self):
        return self.__nodenet.world

    def __init__(self, nodenet):
        self.__nodenet = nodenet

    @property
    def logger(self):
        return self.__nodenet.logger

    def get_nodespace(self, uid):
        """
        Returns the nodespace with the given uid
        """
        return self.__nodenet.get_nodespace(uid)

    def get_nodespaces(self, parent="Root"):
        """
        Returns a list of all nodespaces in the given nodespace
        """
        return [self.__nodenet.get_nodespace(uid) for
                uid in self.__nodenet.get_nodespace(parent).get_known_ids('nodespaces')]

    def get_node(self, uid):
        """
        Returns the node with the given uid
        """
        return self.__nodenet.get_node(uid)

    def get_nodes(self, nodespace=None, node_name_prefix=None):
        """
        Returns a list of nodes in the given nodespace (all Nodespaces if None) whose names start with
        the given prefix (all if None)
        """
        nodes = []
        for node_uid in self.__nodenet.get_node_uids():
            node = self.__nodenet.get_node(node_uid)
            if ((node_name_prefix is None or node.name.startswith(node_name_prefix)) and
                    (nodespace is None or node.parent_nodespace == nodespace)):
                nodes.append(node)
        return nodes

    def get_nodes_in_gate_field(self, node, gate=None, no_links_to=None, nodespace=None):
        """
        Returns all nodes linked to a given node on the gate, excluding the ones that have
        links of any of the given types
        """
        nodes = []
        if gate is not None:
            gates = [gate]
        else:
            gates = self.__nodenet.get_node(node.uid).get_gate_types()
        for gate in gates:
            for link in self.__nodenet.get_node(node.uid).get_gate(gate).get_links():
                candidate = link.target_node
                linked_gates = []
                for candidate_gate_name in candidate.get_gate_types():
                    if len(candidate.get_gate(candidate_gate_name).get_links()) > 0:
                        linked_gates.append(candidate_gate_name)
                if ((nodespace is None or nodespace == link.target_node.parent_nodespace) and
                    (no_links_to is None or not len(set(no_links_to).intersection(set(linked_gates))))):
                    nodes.append(candidate)
        return nodes

    def get_nodes_in_slot_field(self, node, slot=None, no_links_to=None, nodespace=None):
        """
        Returns all nodes linking to a given node on the given slot, excluding the ones that
        have links of any of the given types
        """
        nodes = []
        if slot is not None:
            slots = [slot]
        else:
            slots = self.__nodenet.get_node(node.uid).get_slot_types()
        for slot in slots:
            for link in self.__nodenet.get_node(node.uid).get_slot(slot).get_links():
                candidate = link.source_node
                linked_gates = []
                for candidate_gate_name in candidate.get_gate_types():
                    if len(candidate.get_gate(candidate_gate_name).get_links()) > 0:
                        linked_gates.append(candidate_gate_name)
                if ((nodespace is None or nodespace == link.source_node.parent_nodespace) and
                    (no_links_to is None or not len(set(no_links_to).intersection(set(linked_gates))))):
                    nodes.append(candidate)
        return nodes

    def get_nodes_active(self, nodespace, type=None, min_activation=1, gate=None, sheaf='default'):
        """
        Returns all nodes with a min activation, of the given type, active at the given gate, or with node.activation
        """
        nodes = []
        for node in self.get_nodes(nodespace):
            if type is None or node.type == type:
                if gate is not None:
                    if gate in node.get_gate_types():
                        if node.get_gate(gate).sheaves[sheaf]['activation'] >= min_activation:
                            nodes.append(node)
                else:
                    if node.sheaves[sheaf]['activation'] >= min_activation:
                        nodes.append(node)
        return nodes

    def delete_node(self, node):
        """
        Deletes a node and all links connected to it.
        """
        self.__nodenet.delete_node(node.uid)

    def delete_nodespace(self, nodespace):
        """
        Deletes a node and all nodes and nodespaces contained within, and all links connected to it.
        """
        self.__nodenet.delete_nodespace(nodespace.uid)

    def create_node(self, nodetype, nodespace, name=None):
        """
        Creates a new node or node space of the given type, with the given name and in the given nodespace.
        Returns the newly created entity.
        """
        if name is None:
            name = ""   # TODO: empty names crash the client right now, but really shouldn't
        pos = (self.__nodenet.max_coords['x'] + 50, 100)  # default so native modules will not be bothered with positions

        # todo: There should be a separate method for this Nodespaces are net entities, but they're not nodes.
        if nodetype == "Nodespace":
            uid = self.__nodenet.create_nodespace(nodespace, pos, name=name)
            entity = self.__nodenet.get_nodespace(uid)
        else:
            uid = self.__nodenet.create_node(nodetype, nodespace, pos, name)
            entity = self.__nodenet.get_node(uid)
        self.__nodenet.update_node_positions()
        return entity

    def link(self, source_node, source_gate, target_node, target_slot, weight=1, certainty=1):
        """
        Creates a link between two nodes. If the link already exists, it will be updated
        with the given weight and certainty values (or the default 1 if not given)
        """
        self.__nodenet.create_link(source_node.uid, source_gate, target_node.uid, target_slot, weight, certainty)

    def link_with_reciprocal(self, source_node, target_node, linktype, weight=1, certainty=1):
        """
        Creates two (reciprocal) links between two nodes, valid linktypes are subsur, porret, catexp and symref
        """
        target_slot_types = target_node.get_slot_types()
        source_slot_types = source_node.get_slot_types()
        if linktype == "subsur":
            subslot = "sub" if "sub" in target_slot_types else "gen"
            surslot = "sur" if "sur" in source_slot_types else "gen"
            self.__nodenet.create_link(source_node.uid, "sub", target_node.uid, subslot, weight, certainty)
            self.__nodenet.create_link(target_node.uid, "sur", source_node.uid, surslot, weight, certainty)
        elif linktype == "porret":
            porslot = "por" if "por" in target_slot_types else "gen"
            retslot = "ret" if "ret" in source_slot_types else "gen"
            self.__nodenet.create_link(source_node.uid, "por", target_node.uid, porslot, weight, certainty)
            self.__nodenet.create_link(target_node.uid, "ret", source_node.uid, retslot, weight, certainty)
        elif linktype == "catexp":
            catslot = "cat" if "cat" in target_slot_types else "gen"
            expslot = "exp" if "exp" in source_slot_types else "gen"
            self.__nodenet.create_link(source_node.uid, "cat", target_node.uid, catslot, weight, certainty)
            self.__nodenet.create_link(target_node.uid, "exp", source_node.uid, expslot, weight, certainty)
        elif linktype == "symref":
            symslot = "sym" if "sym" in target_slot_types else "gen"
            refslot = "ref" if "ref" in source_slot_types else "gen"
            self.__nodenet.create_link(source_node.uid, "sym", target_node.uid, symslot, weight, certainty)
            self.__nodenet.create_link(target_node.uid, "ref", source_node.uid, refslot, weight, certainty)

    def link_full(self, nodes, linktype="porret", weight=1, certainty=1):
        """
        Creates two (reciprocal) links between all nodes in the node list (every node to every node),
        valid linktypes are subsur, porret, and catexp.
        """
        for source in nodes:
            for target in nodes:
                self.link_with_reciprocal(source, target, linktype, weight, certainty)

    def unlink(self, source_node, source_gate=None, target_node=None, target_slot=None):
        """
        Deletes a link, or links, originating from the given node
        """
        target_node_uid = target_node.uid if target_node is not None else None
        source_node.unlink(source_gate, target_node_uid, target_slot)

    def unlink_direction(self, node, gateslot=None):
        """
        Deletes all links from a node ending at the given gate or originating at the given slot
        Read this as 'delete all por linkage from this node'
        """
        node.unlink(gateslot)

        links_to_delete = set()
        for slottype in node.get_slot_types():
            if gateslot is None or gateslot == slottype:
                for link in node.get_slot(slottype).get_links():
                    links_to_delete.add(link)

        for link in links_to_delete:
            link.source_node.unlink(gateslot, node.uid)

    def link_actor(self, node, datatarget, weight=1, certainty=1, gate='sub', slot='sur'):
        """
        Links a node to an actor. If no actor exists in the node's nodespace for the given datatarget,
        a new actor will be created, otherwise the first actor found will be used
        """
        if datatarget not in self.world.get_available_datatargets(self.__nodenet.uid):
            raise KeyError("Data target %s not found" % datatarget)
        actor = None
        for uid, candidate in self.__nodenet.get_actors(node.parent_nodespace).items():
            if candidate.get_parameter('datatarget') == datatarget:
                actor = candidate
        if actor is None:
            actor = self.create_node("Actor", node.parent_nodespace, datatarget)
            actor.set_parameter('datatarget', datatarget)

        self.link(node, gate, actor, 'gen', weight, certainty)
        #self.link(actor, 'gen', node, slot)

    def link_sensor(self, node, datasource, slot='sur'):
        """
        Links a node to a sensor. If no sensor exists in the node's nodespace for the given datasource,
        a new sensor will be created, otherwise the first sensor found will be used
        """
        if datasource not in self.world.get_available_datasources(self.__nodenet.uid):
            raise KeyError("Data source %s not found" % datasource)
        sensor = None
        for uid, candidate in self.__nodenet.get_sensors(node.parent_nodespace).items():
            if candidate.get_parameter('datasource') == datasource:
                sensor = candidate
        if sensor is None:
            sensor = self.create_node("Sensor", node.parent_nodespace, datasource)
            sensor.set_parameter('datasource', datasource)

        self.link(sensor, 'gen', node, slot)

    def import_actors(self, nodespace, datatarget_prefix=None):
        """
        Makes sure an actor for all datatargets whose names start with the given prefix, or all datatargets,
        exists in the given nodespace.
        """
        all_actors = []
        if self.world is None:
            return all_actors

        for datatarget in self.world.get_available_datatargets(self.__nodenet.uid):
            if datatarget_prefix is None or datatarget.startswith(datatarget_prefix):
                actor = None
                for uid, candidate in self.__nodenet.get_actors(nodespace).items():
                    if candidate.get_parameter('datatarget') == datatarget:
                        actor = candidate
                if actor is None:
                    actor = self.create_node("Actor", nodespace, datatarget)
                    actor.set_parameter('datatarget', datatarget)
                all_actors.append(actor)
        return all_actors

    def import_sensors(self, nodespace, datasource_prefix=None):
        """
        Makes sure a sensor for all datasources whose names start with the given prefix, or all datasources,
        exists in the given nodespace.
        """
        all_sensors = []
        if self.world is None:
            return all_sensors

        for datasource in self.world.get_available_datasources(self.__nodenet.uid):
            if datasource_prefix is None or datasource.startswith(datasource_prefix):
                sensor = None
                for uid, candidate in self.__nodenet.get_sensors(nodespace).items():
                    if candidate.get_parameter('datasource') == datasource:
                        sensor = candidate
                if sensor is None:
                    sensor = self.create_node("Sensor", nodespace, datasource)
                    sensor.set_parameter('datasource', datasource)
                all_sensors.append(sensor)
        return all_sensors

    def set_gatefunction(self, nodespace, nodetype, gatetype, gatefunction):
        """Sets the gatefunction for gates of type gatetype of nodes of type nodetype, in the given
            nodespace.
            The gatefunction needs to be given as a string.
        """
        self.__nodenet.get_nodespace(nodespace).set_gate_function(nodetype, gatetype, gatefunction)

    def is_locked(self, lock):
        """Returns true if the given lock is locked in the current net step
        """
        return self.__nodenet.is_locked(lock)

    def is_locked_by(self, lock, key):
        """Returns true if the given lock is locked in the current net step, with the given key
        """
        return self.__nodenet.is_locked_by(lock, key)

    def lock(self, lock, key, timeout=100):
        """
        Creates a lock with immediate effect.
        If two nodes try to create the same lock in the same net step, the second call will fail.
        As nodes need to check is_locked before acquiring locks anyway, this effectively means that if two
        nodes attempt to acquire the same lock at the same time (in the same net step), the node to get the
        lock will be chosen randomly.
        """
        self.__nodenet.lock(lock, key, timeout)

    def unlock(self, lock):
        """
        Removes a lock by the end of the net step, after all node functions have been called.
        Thus, locks can only be acquired in the next net step (no indeterminism based on node function execution
        order as with creating locks).
        """
        self.__locks_to_delete.append(lock)

    def notify_user(self, node, msg):
        """
        Stops the nodenetrunner for this nodenet, and displays an information to the user,
        who can then choose to continue or suspend running nodenet
        Parameters:
            node: the node object that emits this message
            msg: a string to display to the user
        """
        self.__nodenet.user_prompt = {
            'node': node.data,
            'msg': msg,
            'options': None
        }
        self.__nodenet.is_active = False

    def ask_user_for_parameter(self, node, msg, options):
        """
        Stops the nodenetrunner for this nodenet, and asks the user for values to the given parameters.
        These parameters will be passed into the nodefunction in the next step of the nodenet.
        The user can choose to either continue or suspend running the nodenet
        Parameters:
            node: the node object that emits this message
            msg: a string to display to the user
            options: an array of objects representing the variables to set by the user. Needs key, label. Optional: array or object of values

        example usage:
            options = [{
                'key': 'where',
                'label': 'Where should I go next?',
                'values': {'north': 'North', 'east': 'East', 'south': 'South', 'west': 'west'}
            }, {
                'key': 'wait':
                'label': 'How long should I wait until I go there?',
            }]
            netapi.ask_user_for_parameter(node, "Please decide what to do next", options)
        """
        self.__nodenet.user_prompt = {
            'node': node.data,
            'msg': msg,
            'options': options
        }
        self.__nodenet.is_active = False

    def autoalign_nodespace(self, nodespace):
        """ Calls the autoalignment on the given nodespace """
        from micropsi_core.nodenet.node_alignment import align
        if nodespace in self.__nodenet.get_nodespace_uids():
            align(self.__nodenet, nodespace)

    def _step(self):
        for lock in self.__locks_to_delete:
            self.__nodenet.unlock(lock)
        self.__locks_to_delete = []
