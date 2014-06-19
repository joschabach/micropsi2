# -*- coding: utf-8 -*-

"""
Nodenet definition
"""
from copy import deepcopy

import micropsi_core.tools
import json
import os
import warnings
from .node import Node, Nodetype, SheafElement, STANDARD_NODETYPES
import logging
from .nodespace import Nodespace
from .link import Link
from .monitor import Monitor

__author__ = 'joscha'
__date__ = '09.05.12'

NODENET_VERSION = 1

class NodenetLockException(Exception):
    pass

class Nodenet(object):
    """Main data structure for MicroPsi agents,

    Contains the net entities and runs the activation spreading. The nodenet stores persistent data.

    Attributes:
        state: a dict of persistent nodenet data; everything stored within the state can be stored and exported
        uid: a unique identifier for the node net
        name: an optional name for the node net
        filename: the path and file name to the file storing the persisted net data
        nodespaces: a dictionary of node space UIDs and respective node spaces
        nodes: a dictionary of node UIDs and respective nodes
        links: a dictionary of link UIDs and respective links
        gate_types: a dictionary of gate type names and the individual types of gates
        slot_types: a dictionary of slot type names and the individual types of slots
        node_types: a dictionary of node type names and node type definitions
        world: an environment for the node net
        worldadapter: an actual world adapter object residing in a world implementation, provides interface
        owner: an id of the user who created the node net
        step: the current simulation step of the node net
    """

    @property
    def uid(self):
        return self.state.get("uid")

    @property
    def name(self):
        return self.state.get("name", self.state.get("uid"))

    @name.setter
    def name(self, identifier):
        self.state["name"] = identifier

    @property
    def owner(self):
        return self.state.get("owner")

    @owner.setter
    def owner(self, identifier):
        self.state["owner"] = identifier

    @property
    def world(self):
        if "world" in self.state:
            from micropsi_core.runtime import worlds
            return worlds.get(self.state["world"])
        return None

    @world.setter
    def world(self, world):
        if world:
            self.state["world"] = world.uid
        else:
            self.state["world"] = None

    @property
    def worldadapter(self):
        return self.state.get("worldadapter")

    @worldadapter.setter
    def worldadapter(self, worldadapter_uid):
        self.state["worldadapter"] = worldadapter_uid

    @property
    def current_step(self):
        return self.state.get("step")

    @property
    def is_active(self):
        return self.state.get("is_active", False)

    @is_active.setter
    def is_active(self, is_active):
        self.state['is_active'] = is_active

    def __init__(self, filename, name="", worldadapter="Default", world=None, owner="", uid=None, nodetypes={}, native_modules={}):
        """Create a new MicroPsi agent.

        Arguments:
            filename: the path and filename of the agent
            agent_type (optional): the interface of this agent to its environment
            name (optional): the name of the agent
            owner (optional): the user that created this agent
            uid (optional): unique handle of the agent; if none is given, it will be generated
        """

        uid = uid or micropsi_core.tools.generate_uid()

        self.state = {
            "version": NODENET_VERSION,  # used to check compatibility of the node net data
            "uid": uid,
            "nodes": {},
            "links": {},
            "monitors": {},
            "nodespaces": {'Root': {}},
            "activatortypes": list(nodetypes.keys()),
            "step": 0
        }

        self.world = world
        self.owner = owner
        self.name = name or os.path.basename(filename)
        self.filename = filename
        if world and worldadapter:
            self.worldadapter = worldadapter

        self.nodes = {}
        self.links = {}
        self.nodetypes = nodetypes
        self.native_modules = native_modules
        self.nodespaces = {}
        self.monitors = {}
        self.locks = {}
        self.nodes_by_coords = {}
        self.max_coords = {'x': 0, 'y': 0}
        self.netapi = NetAPI(self)

        self.logger = logging.getLogger("nodenet")
        self.logger.info("Setting up nodenet %s", self.name)

        self.load()

    def load(self, string=None):
        """Load the node net from a file"""
        # try to access file
        if string:
            self.logger.info("Loading nodenet %s from string", self.name)
            try:
                self.state = json.loads(string)
            except ValueError:
                warnings.warn("Could not read nodenet data from string")
                return False
        else:
            try:
                self.logger.info("Loading nodenet %s from file %s", self.name, self.filename)
                with open(self.filename) as file:
                    self.state = json.load(file)
            except ValueError:
                warnings.warn("Could not read nodenet data")
                return False
            except IOError:
                warnings.warn("Could not open nodenet file")

        if "version" in self.state and self.state["version"] == NODENET_VERSION:
            self.initialize_nodenet()
            return True
        else:
            warnings.warn("Wrong version of the nodenet data; starting new nodenet")
            return False

    def initialize_nodespace(self, id, data):
        if id not in self.nodespaces:
            # move up the nodespace tree until we find an existing parent or hit root
            while id != 'Root' and data[id].get('parent_nodespace') not in self.nodespaces:
                self.initialize_nodespace(data[id]['parent_nodespace'], data)
            self.nodespaces[id] = Nodespace(self,
                data[id]['parent_nodespace'],
                data[id]['position'],
                name=data[id]['name'],
                uid=id,
                index=data[id].get('index'),
                gatefunctions=data[id].get('gatefunctions', {}))

    def initialize_nodenet(self):
        """Called after reading new nodenet state.

        Parses the nodenet state and set up the non-persistent data structures necessary for efficient
        computation of the node net
        """

        nodetypes = {}
        for type, data in self.nodetypes.items():
            nodetypes[type] = Nodetype(nodenet=self, **data)
        self.nodetypes = nodetypes

        native_modules = {}
        for type, data in self.native_modules.items():
            native_modules[type] = Nodetype(nodenet=self, **data)
        self.native_modules = native_modules

        # set up nodespaces; make sure that parent nodespaces exist before children are initialized
        self.nodespaces = {}

        nodespaces_to_initialize = set(self.state.get('nodespaces', {}).keys())
        for next_nodespace in nodespaces_to_initialize:
            self.initialize_nodespace(next_nodespace, self.state['nodespaces'])

        nodespaces_to_initialize = []
        if not self.nodespaces:
            self.nodespaces["Root"] = Nodespace(self, None, (0, 0), name="Root", uid="Root")

        # set up nodes
        for uid in self.state.get('nodes', {}):
            data = self.state['nodes'][uid]
            if data['type'] in nodetypes or data['type'] in native_modules:
                self.nodes[uid] = Node(self, **data)
                pos = self.nodes[uid].position
                xpos = int(pos[0] - (pos[0] % 100))
                ypos = int(pos[1] - (pos[1] % 100))
                if xpos not in self.nodes_by_coords:
                    self.nodes_by_coords[xpos] = {}
                    if xpos > self.max_coords['x']:
                        self.max_coords['x'] = xpos
                if ypos not in self.nodes_by_coords[xpos]:
                    self.nodes_by_coords[xpos][ypos] = []
                    if ypos > self.max_coords['y']:
                        self.max_coords['y'] = ypos
                self.nodes_by_coords[xpos][ypos].append(uid)
            else:
                warnings.warn("Invalid nodetype %s for node %s" % (data['type'], uid))
            # set up links
        for uid in self.state.get('links', {}):
            data = self.state['links'][uid]
            if data['source_node_uid'] in self.nodes and \
                    data['source_gate_name'] in self.nodes[data['source_node_uid']].gates and\
                    data['target_node_uid'] in self.nodes and\
                    data['target_slot_name'] in self.nodes[data['target_node_uid']].slots:
                self.links[uid] = Link(
                    self.nodes[data['source_node_uid']], data['source_gate_name'],
                    self.nodes[data['target_node_uid']], data['target_slot_name'],
                    weight=data['weight'], certainty=data['certainty'],
                    uid=uid)
            else:
                warnings.warn("Slot or gatetype for link %s invalid" % uid)
        for uid in self.state.get('monitors', {}):
            self.monitors[uid] = Monitor(self, **self.state['monitors'][uid])

            # TODO: check if data sources and data targets match

    def get_nodetype(self, type):
        """ Returns the nodetpype instance for the given nodetype or native_module or None if not found"""
        if type in self.nodetypes:
            return self.nodetypes[type]
        else:
            return self.native_modules.get(type)

    def get_nodespace_area(self, nodespace, x1, x2, y1, y2):
        x_range = (x1 - (x1 % 100), 100 + x2 - (x2 % 100), 100)
        y_range = (y1 - (y1 % 100), 100 + y2 - (y2 % 100), 100)
        data = {
            'links': {},
            'nodes': {},
            'name': self.name,
            'max_coords': self.max_coords,
            'is_active': self.is_active,
            'step': self.current_step,
            'nodespaces': {i: self.state['nodespaces'][i] for i in self.state['nodespaces']
                           if self.state['nodespaces'][i]["parent_nodespace"] == nodespace},
            'world': self.state["world"],
            'worldadapter': self.worldadapter
        }
        links = []
        followupnodes = []
        for x in range(*x_range):
            if x in self.nodes_by_coords:
                for y in range(*y_range):
                    if y in self.nodes_by_coords[x]:
                        for uid in self.nodes_by_coords[x][y]:
                            if self.nodes[uid].parent_nodespace == nodespace:  # maybe sort directly by nodespace??
                                data['nodes'][uid] = self.state['nodes'][uid]
                                links.extend(self.nodes[uid].get_associated_link_ids())
                                followupnodes.extend(self.nodes[uid].get_associated_node_ids())
        for uid in links:
            data['links'][uid] = self.state['links'][uid]
        for uid in followupnodes:
            if uid not in data['nodes']:
                data['nodes'][uid] = self.state['nodes'][uid]
        return data

    def update_node_positions(self):
        """ recalculates the position hash """
        self.nodes_by_coords = {}
        self.max_coords = {'x': 0, 'y': 0}
        for uid in self.nodes:
            pos = self.nodes[uid].position
            xpos = int(pos[0] - (pos[0] % 100))
            ypos = int(pos[1] - (pos[1] % 100))
            if xpos not in self.nodes_by_coords:
                self.nodes_by_coords[xpos] = {}
                if xpos > self.max_coords['x']:
                    self.max_coords['x'] = xpos
            if ypos not in self.nodes_by_coords[xpos]:
                self.nodes_by_coords[xpos][ypos] = []
                if ypos > self.max_coords['y']:
                    self.max_coords['y'] = ypos
            self.nodes_by_coords[xpos][ypos].append(uid)

    def delete_node(self, node_uid):
        link_uids = []
        for key, gate in self.nodes[node_uid].gates.items():
            link_uids.extend(gate.outgoing.keys())
        for key, slot in self.nodes[node_uid].slots.items():
            link_uids.extend(slot.incoming.keys())
        for uid in link_uids:
            if uid in self.links:
                self.links[uid].remove()
                del self.links[uid]
            if uid in self.state['links']:
                del self.state['links'][uid]
        parent_nodespace = self.nodespaces.get(self.nodes[node_uid].parent_nodespace)
        parent_nodespace.netentities["nodes"].remove(node_uid)
        if self.nodes[node_uid].type == "Activator":
            parent_nodespace.activators.pop(self.nodes[node_uid].parameters["type"], None)
        del self.nodes[node_uid]
        del self.state['nodes'][node_uid]
        self.update_node_positions()

    def get_nodespace(self, nodespace_uid, max_nodes):
        """returns the nodes and links in a given nodespace"""
        data = {'nodes': {}, 'links': {}, 'nodespaces': {}}
        for key in self.state:
            if key in ['uid', 'links', 'nodespaces', 'monitors']:
                data[key] = self.state[key]
            elif key == "nodes":
                i = 0
                data[key] = {}
                for id in self.state[key]:
                    i += 1
                    data[key][id] = self.state[key][id]
                    if max_nodes and i > max_nodes:
                        break
        return data

    def clear(self):
        self.nodes = {}
        self.links = {}
        self.monitors = {}

        self.nodes_by_coords = {}
        self.max_coords = {'x': 0, 'y': 0}

        self.nodespaces = {}
        Nodespace(self, None, (0, 0), "Root", "Root")

    # add functions for exporting and importing node nets
    def export_data(self):
        """serializes and returns the nodenet state for export to a end user"""
        pass

    def import_data(self, nodenet_data):
        """imports nodenet state as the current node net"""
        pass

    def merge_data(self, nodenet_data):
        """merges the nodenet state with the current node net, might have to give new UIDs to some entities"""
        # these values shouldn't be overwritten:
        for key in ['uid', 'filename', 'world']:
            nodenet_data.pop(key, None)
        self.state.update(nodenet_data)

    def copy_nodes(self, nodes, nodespaces, target_nodespace=None, copy_associated_links=True):
        """takes a dictionary of nodes and merges them into the current nodenet.
        Links between these nodes will be copied, too.
        If the source nodes are within the current nodenet, it is also possible to retain the associated links.
        If the source nodes originate within a different nodespace (either because they come from a different
        nodenet, or because they are copied into a different nodespace), the associated links (i.e. those that
        link the copied nodes to elements that are themselves not being copied), can be retained, too.
        Nodes and links may need to receive new UIDs to avoid conflicts.

        Arguments:
            nodes: a dictionary of node_uids with nodes
            target_nodespace: if none is given, we copy into the same nodespace of the originating nodes
            copy_associated_links: if True, also copy connections to not copied nodes
        """
        rename_nodes = {}
        rename_nodespaces = {}
        if not target_nodespace:
            target_nodespace = "Root"
            # first, check for nodespace naming conflicts
        for nodespace_uid in nodespaces:
            if nodespace_uid in self.nodespaces:
                rename_nodespaces[nodespace_uid] = micropsi_core.tools.generate_uid()
            # create the nodespaces
        for nodespace_uid in nodespaces:
            original = nodespaces[nodespace_uid]
            uid = rename_nodespaces.get(nodespace_uid, nodespace_uid)

            Nodespace(self, target_nodespace,
                position=original.position,
                name=original.name,
                gatefunctions=deepcopy(original.gatefunctions),
                uid=uid)

        # set the parents (needs to happen in seperate loop to ensure nodespaces are already created
        for nodespace_uid in nodespaces:
            if nodespaces[nodespace_uid].parent_nodespace in nodespaces:
                uid = rename_nodespaces.get(nodespace_uid, nodespace_uid)
                target_nodespace = rename_nodespaces.get(nodespaces[nodespace_uid].parent_nodespace)
                self.nodespaces[uid].parent_nodespace = target_nodespace

        # copy the nodes
        for node_uid in nodes:
            if node_uid in self.nodes:
                rename_nodes[node_uid] = micropsi_core.tools.generate_uid()
                uid = rename_nodes[node_uid]
            else:
                uid = node_uid

            original = nodes[node_uid]
            target = original.parent_nodespace if original.parent_nodespace in nodespaces else target_nodespace
            target = rename_nodespaces.get(target, target)

            Node(self, target,
                position=original.position,
                name=original.name,
                type=original.type,
                uid=uid,
                parameters=deepcopy(original.parameters),
                gate_parameters=original.get_gate_parameters()
            )

        # copy the links
        if len(nodes):
            links = {}
            origin_links = nodes[list(nodes.keys())[0]].nodenet.links
            for node_uid in nodes:
                node = nodes[node_uid]
                for slot in node.slots:
                    for l in node.slots[slot].incoming:
                        link = origin_links[l]
                        if link.source_node.uid in nodes or (copy_associated_links
                                                             and link.source_node.uid in self.nodes):
                            if not l in links:
                                links[l] = link
                for gate in node.gates:
                    for l in node.gates[gate].outgoing:
                        link = origin_links[l]
                        if link.target_node.uid in nodes or (copy_associated_links
                                                             and link.target_node.uid in self.nodes):
                            if not l in links:
                                links[l] = link
            for l in links:
                uid = l if not l in self.links else micropsi_core.tools.generate_uid()
                link = links[l]
                source_node = self.nodes[rename_nodes.get(link.source_node.uid, link.source_node.uid)]
                target_node = self.nodes[rename_nodes.get(link.target_node.uid, link.target_node.uid)]

                Link(source_node, link.source_gate.type, target_node, link.target_slot.type,
                    link.weight, link.certainty, uid)

    def move_nodes(self, nodes, nodespaces, target_nodespace=None):
        """moves the nodes into a new nodespace or nodenet, and deletes them at their original position.
        Links will be retained within the same nodenet.
        When moving into a different nodenet, nodes and links may receive new UIDs to avoid conflicts."""
        pass

    def step(self):
        """perform a simulation step"""

        if self.world is not None and self.world.agents is not None and self.uid in self.world.agents:
            self.world.agents[self.uid].snapshot()      # world adapter snapshot
                                                        # TODO: Not really sure why we don't just know our world adapter,
                                                        # but instead the world object itself

        self.propagate_link_activation(self.nodes.copy())

        self.timeout_locks()

        activators = self.get_activators()
        nativemodules = self.get_nativemodules()
        everythingelse = self.nodes.copy()
        for key in nativemodules.keys():
            del everythingelse[key]

        self.calculate_node_functions(activators)       # activators go first
        self.calculate_node_functions(nativemodules)    # then native modules, so API sees a deterministic state
        self.calculate_node_functions(everythingelse)   # then all the peasant nodes get calculated

        self.netapi._step()

        self.state["step"] += 1
        for uid in self.monitors:
            self.monitors[uid].step(self.state["step"])
        for uid, node in activators.items():
            node.activation = self.nodespaces[node.parent_nodespace].activators[node.parameters['type']]

    def propagate_link_activation(self, nodes, limit_gatetypes=None):
        """ the linkfunction
            propagate activation from gates to slots via their links. returns the nodes that received activation.
            Arguments:
                nodes: the dict of nodes to consider
                limit_gatetypes (optional): a list of gatetypes to restrict the activation to links originating
                    from the given slottypes.
        """
        for uid, node in nodes.items():
            node.reset_slots()

        # propagate sheaf existence
        for uid, node in nodes.items():
            if limit_gatetypes is not None:
                gates = [(name, gate) for name, gate in node.gates.items() if name in limit_gatetypes]
            else:
                gates = node.gates.items()
            for type, gate in gates:
                if gate.parameters['spreadsheaves'] is True:
                    for sheaf in gate.sheaves.keys():
                        for uid, link in gate.outgoing.items():
                            for slotname in link.target_node.slots.keys():
                                if sheaf not in link.target_node.get_slot(slotname).sheaves:
                                    link.target_node.get_slot(slotname).sheaves[sheaf] = SheafElement(uid=gate.sheaves[sheaf].uid, name=gate.sheaves[sheaf].name)

        # propagate activation
        for uid, node in nodes.items():
            if limit_gatetypes is not None:
                gates = [(name, gate) for name, gate in node.gates.items() if name in limit_gatetypes]
            else:
                gates = node.gates.items()

            for type, gate in gates:
                for uid, link in gate.outgoing.items():
                    for sheaf in gate.sheaves.keys():
                        if sheaf in link.target_slot.sheaves:
                            link.target_slot.sheaves[sheaf].activation += float(gate.sheaves[sheaf].activation) * float(link.weight)  # TODO: where's the string coming from?
                        elif sheaf.endswith(link.target_node.uid):
                            upsheaf = sheaf[:-(len(link.target_node.uid)+1)]
                            link.target_slot.sheaves[upsheaf].activation += float(gate.sheaves[sheaf].activation) * float(link.weight)  # TODO: where's the string coming from?

    def timeout_locks(self):
        """
        Removes all locks that time out in the current step
        """
        locks_to_delete = []
        for lock, data in self.locks.items():
            self.locks[lock] = (data[0] + 1, data[1], data[2])
            if data[0] + 1 >= data[1]:
                locks_to_delete.append(lock)
        for lock in locks_to_delete:
            del self.locks[lock]

    def calculate_node_functions(self, nodes):
        """for all given nodes, call their node function, which in turn should update the gate functions
           Arguments:
               nodes: the dict of nodes to consider
        """
        for uid, node in nodes.copy().items():
            node.node_function()

    def get_nativemodules(self, nodespace=None):
        """Returns a dict of native modules. Optionally filtered by the given nodespace"""
        nodes = self.nodes if nodespace is None else self.nodespaces[nodespace].netentities['nodes']
        nativemodules = {}
        for uid in nodes:
            if self.nodes[uid].type not in STANDARD_NODETYPES.keys():
                nativemodules.update({uid: self.nodes[uid]})
        return nativemodules

    def get_activators(self, nodespace=None, type=None):
        """Returns a dict of activator nodes. OPtionally filtered by the given nodespace and the given type"""
        nodes = self.nodes if nodespace is None else self.nodespaces[nodespace].netentities['nodes']
        activators = {}
        for uid in nodes:
            if self.nodes[uid].type == 'Activator':
                if type is None or type == self.nodes[uid].parameters['type']:
                    activators.update({uid: self.nodes[uid]})
        return activators

    def get_sensors(self, nodespace=None):
        """Returns a dict of all sensor nodes. Optionally filtered by the given nodespace"""
        nodes = self.nodes if nodespace is None else self.nodespaces[nodespace].netentities['nodes']
        sensors = {}
        for uid in nodes:
            if self.nodes[uid].type == 'Sensor':
                sensors[uid] = self.nodes[uid]
        return sensors

    def get_actors(self, nodespace=None):
        """Returns a dict of all sensor nodes. Optionally filtered by the given nodespace"""
        nodes = self.nodes if nodespace is None else self.nodespaces[nodespace].netentities['nodes']
        actors = {}
        for uid in nodes:
            if self.nodes[uid].type == 'Actor':
                actors[uid] = self.nodes[uid]
        return actors

    def get_link_uid(self, source_uid, source_gate_name, target_uid, target_slot_name):
        """links are uniquely identified by their origin and targets; this function checks if a link already exists.

        Arguments:
            source_node: actual node from which the link originates
            source_gate_name: type of the gate of origin
            target_node: node that the link ends at
            target_slot_name: type of the terminating slot

        Returns the link uid, or None if it does not exist"""
        outgoing_candidates = set(self.nodes[source_uid].get_gate(source_gate_name).outgoing.keys())
        incoming_candidates = set(self.nodes[target_uid].get_slot(target_slot_name).incoming.keys())
        try:
            return (outgoing_candidates & incoming_candidates).pop()
        except KeyError:
            return None

    def set_link_weight(self, link_uid, weight, certainty=1):
        """Set weight of the given link."""
        self.state['links'][link_uid]['weight'] = weight
        self.state['links'][link_uid]['certainty'] = certainty
        self.links[link_uid].weight = weight
        self.links[link_uid].certainty = certainty
        return True

    def create_link(self, source_node_uid, gate_type, target_node_uid, slot_type, weight=1, certainty=1, uid=None):
        """Creates a new link.

        Arguments.
            source_node_uid: uid of the origin node
            gate_type: type of the origin gate (usually defines the link type)
            target_node_uid: uid of the target node
            slot_type: type of the target slot
            weight: the weight of the link (a float)
            certainty (optional): a probabilistic parameter for the link
            uid (option): if none is supplied, a uid will be generated

        Returns:
            link_uid if successful,
            None if failure
        """

        # check if link already exists
        existing_uid = self.get_link_uid(
            source_node_uid, gate_type,
            target_node_uid, slot_type)
        if existing_uid:
            self.set_link_weight(existing_uid, weight, certainty)
            link = self.links[existing_uid]
        else:
            link = Link(
                self.nodes[source_node_uid],
                gate_type,
                self.nodes[target_node_uid],
                slot_type,
                weight=weight,
                certainty=certainty,
                uid=uid)
            self.links[link.uid] = link
        return True, link.uid

    def delete_link(self, link_uid):
        """Delete the given link."""
        self.links[link_uid].remove()
        del self.links[link_uid]
        del self.state['links'][link_uid]
        return True

    def is_locked(self, lock):
        """Returns true if a lock of the given name exists"""
        return lock in self.locks

    def is_locked_by(self, lock, key):
        """Returns true if a lock of the given name exists and the key used is the given one"""
        return lock in self.locks and self.locks[lock][2] == key

    def lock(self, lock, key, timeout=100):
        """Creates a lock with the given name that will time out after the given number of steps
        """
        if self.is_locked(lock):
            raise NodenetLockException("Lock %s is already locked." % lock)
        self.locks[lock] = (0, timeout, key)

    def unlock(self, lock):
        """Removes the given lock
        """
        del self.locks[lock]

class NetAPI(object):
    """
    Node Net API facade class for use from within the node net (in node functions)
    """

    __locks_to_delete = []

    @property
    def uid(self):
        return self.__nodenet.uid

    @property
    def world(self):
        return self.__nodenet.world

    @property
    def nodespaces(self):
        return self.__nodenet.nodespaces

    def __init__(self, nodenet):
        self.__nodenet = nodenet

    @property
    def logger(self):
        return self.__nodenet.logger

    def get_node(self, uid):
        """
        Returns the node with the given uid
        """
        return self.__nodenet.nodes[uid]

    def get_nodes(self, nodespace=None, node_name_prefix=None):
        """
        Returns a list of nodes in the given nodespace (all Nodespaces if None) whose names start with
        the given prefix (all if None)
        """
        nodes = []
        for node_uid, node in self.__nodenet.nodes.items():
            if ((node_name_prefix is None or node.name.startswith(node_name_prefix)) and
                    (nodespace is None or node.parent_nodespace == nodespace)):
                nodes.append(node)
        return nodes

    def get_nodes_field(self, node, gate, no_links_to=None, nodespace=None):
        """
        Returns all nodes linked to a given node on the gate, excluding the ones that have
        links of any of the given types
        """
        nodes = []
        for link_uid, link in self.__nodenet.nodes[node.uid].get_gate(gate).outgoing.items():
            candidate = link.target_node
            linked_gates = []
            for candidate_gate_name, candidate_gate in candidate.gates.items():
                if len(candidate_gate.outgoing) > 0:
                    linked_gates.append(candidate_gate_name)
            if ((nodespace is None or nodespace == link.target_node.parent_nodespace) and
                (no_links_to is None or not len(set(no_links_to).intersection(set(linked_gates))))):
                nodes.append(candidate)
        return nodes

    def get_nodes_feed(self, node, slot, no_links_to=None, nodespace=None):
        """
        Returns all nodes linking to a given node on the given slot, excluding the ones that
        have links of any of the given types
        """
        nodes = []
        for link_uid, link in self.__nodenet.nodes[node.uid].get_slot(slot).incoming.items():
            candidate = link.source_node
            linked_gates = []
            for candidate_gate_name, candidate_gate in candidate.gates.items():
                if len(candidate_gate.outgoing) > 0:
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
                    if gate in node.gates:
                        if node.get_gate(gate).sheaves[sheaf].activation >= min_activation:
                            nodes.append(node)
                else:
                    if node.sheaves[sheaf].activation >= min_activation:
                        nodes.append(node)
        return nodes

    def delete_node(self, node):
        """
        Deletes a node and all links connected to it.
        """
        self.__nodenet.delete_node(node.uid)

    def create_node(self, nodetype, nodespace, name=None):
        """
        Creates a new node or node space of the given type, with the given name and in the given nodespace.
        Returns the newly created entity.
        """
        if name is None:
            name = ""   #TODO: empty names crash the client right now, but really shouldn't
        pos = (self.__nodenet.max_coords['x'] + 50, 100)  # default so native modules will not be bothered with positions
        if nodetype == "Nodespace":
            entity = Nodespace(self.__nodenet, nodespace, pos, name=name)
        else:
            entity = Node(self.__nodenet, nodespace, pos, name=name, type=nodetype)
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
        if linktype == "subsur":
            subslot = "sub" if "sub" in target_node.slots else "gen"
            surslot = "sur" if "sur" in source_node.slots else "gen"
            self.__nodenet.create_link(source_node.uid, "sub", target_node.uid, subslot, weight, certainty)
            self.__nodenet.create_link(target_node.uid, "sur", source_node.uid, surslot, weight, certainty)
        elif linktype == "porret":
            porslot = "por" if "por" in target_node.slots else "gen"
            retslot = "ret" if "ret" in source_node.slots else "gen"
            self.__nodenet.create_link(source_node.uid, "por", target_node.uid, porslot, weight, certainty)
            self.__nodenet.create_link(target_node.uid, "ret", source_node.uid, retslot, weight, certainty)
        elif linktype == "catexp":
            catslot = "cat" if "cat" in target_node.slots else "gen"
            expslot = "exp" if "exp" in source_node.slots else "gen"
            self.__nodenet.create_link(source_node.uid, "cat", target_node.uid, catslot, weight, certainty)
            self.__nodenet.create_link(target_node.uid, "exp", source_node.uid, expslot, weight, certainty)
        elif linktype == "symref":
            symslot = "sym" if "sym" in target_node.slots else "gen"
            refslot = "ref" if "ref" in source_node.slots else "gen"
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
        links_to_delete = []
        for gatetype, gateobject in source_node.gates.items():
            if source_gate is None or source_gate is gatetype:
                for linkid, link in gateobject.outgoing.items():
                    if target_node is None or target_node.uid == link.target_node.uid:
                        if target_slot is None or target_slot == link.target_slot.type:
                            links_to_delete.append(linkid)

        for uid in links_to_delete:
            self.__nodenet.delete_link(uid)

    def link_actor(self, node, datatarget, weight=1, certainty=1, gate='sub', slot='sur'):
        """
        Links a node to an actor. If no actor exists in the node's nodespace for the given datatarget,
        a new actor will be created, otherwise the first actor found will be used
        """
        if datatarget not in self.world.get_available_datatargets(self.__nodenet.uid):
            raise KeyError("Data target %s not found" % datatarget)
        actor = None
        for uid, candidate in self.__nodenet.get_actors(node.parent_nodespace).items():
            if candidate.parameters['datatarget'] == datatarget:
                actor = candidate
        if actor is None:
            actor = self.create_node("Actor", node.parent_nodespace, datatarget)
            actor.parameters.update({'datatarget': datatarget})

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
            if candidate.parameters['datasource'] == datasource:
                sensor = candidate
        if sensor is None:
            sensor = self.create_node("Sensor", node.parent_nodespace, datasource)
            sensor.parameters.update({'datasource': datasource})

        self.link(sensor, 'gen', node, slot)

    def import_actors(self, nodespace, datatarget_prefix=None):
        """
        Makes sure an actor for all datatargets whose names start with the given prefix, or all datatargets,
        exists in the given nodespace.
        """
        all_actors = []
        for datatarget in self.world.get_available_datatargets(self.__nodenet.uid):
            if datatarget_prefix is None or datatarget.startwith(datatarget_prefix):
                actor = None
                for uid, candidate in self.__nodenet.get_actors(nodespace).items():
                    if candidate.parameters['datatarget'] == datatarget:
                        actor = candidate
                if actor is None:
                    actor = self.create_node("Actor", nodespace, datatarget)
                    actor.parameters.update({'datatarget': datatarget})
                all_actors.append(actor)
        return all_actors

    def import_sensors(self, nodespace, datasource_prefix=None):
        """
        Makes sure a sensor for all datasources whose names start with the given prefix, or all datasources,
        exists in the given nodespace.
        """
        all_sensors = []
        for datasource in self.world.get_available_datasources(self.__nodenet.uid):
            if datasource_prefix is None or datasource.startswith(datasource_prefix):
                sensor = None
                for uid, candidate in self.__nodenet.get_sensors(nodespace).items():
                    if candidate.parameters['datasource'] == datasource:
                        sensor = candidate
                if sensor is None:
                    sensor = self.create_node("Sensor", nodespace, datasource)
                    sensor.parameters.update({'datasource': datasource})
                all_sensors.append(sensor)
        return all_sensors

    def set_gatefunction(self, nodespace, nodetype, gatetype, gatefunction):
        """Sets the gatefunction for gates of type gatetype of nodes of type nodetype, in the given
            nodespace.
            The gatefunction needs to be given as a string.
        """
        self.__nodenet.nodespaces[nodespace].set_gate_function(nodetype, gatetype, gatefunction)

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

    def _step(self):
        for lock in self.__locks_to_delete:
            self.__nodenet.unlock(lock)
        self.__locks_to_delete = []
