# -*- coding: utf-8 -*-

"""
Nodenet definition
"""
from copy import deepcopy

import micropsi_core.tools
import json
import os
import warnings
from .node import Node, Nodetype, STANDARD_NODETYPES
from .nodespace import Nodespace
from .link import Link
from .monitor import Monitor

__author__ = 'joscha'
__date__ = '09.05.12'

NODENET_VERSION = 1

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

    def __init__(self, filename, name="", worldadapter="Default", world=None, owner="", uid=None):
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
            "nodetypes": STANDARD_NODETYPES,
            "activatortypes": list(STANDARD_NODETYPES.keys()),
            "step": 0,
            "filename": filename
        }

        self.world = world
        self.owner = owner
        self.name = name or os.path.basename(filename)
        self.filename = filename
        if world and worldadapter:
            self.worldadapter = worldadapter

        self.nodes = {}
        self.links = {}
        self.nodetypes = {}
        self.nodespaces = {}
        self.monitors = {}
        self.nodes_by_coords = {}
        self.max_coords = {'x': 0, 'y': 0}

        self.active_nodes = {}
        self.privileged_active_nodes = {}

        self.load()

    def load(self, string=None):
        """Load the node net from a file"""
        # try to access file
        if string:
            try:
                self.state = json.loads(string)
            except ValueError:
                warnings.warn("Could not read nodenet data from string")
                return False
        else:
            try:
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

        nodetypes = self.state.get('nodetypes', {}).copy()
        nodetypes.update(STANDARD_NODETYPES)
        for type, data in nodetypes.items():
            self.nodetypes[type] = Nodetype(nodenet=self, **data)

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
            # set up links
        for uid in self.state.get('links', {}):
            data = self.state['links'][uid]
            self.links[uid] = Link(
                self.nodes[data.get('source_node_uid', data.get('source_node'))], data['source_gate_name'],  # fixme
                self.nodes[data.get('target_node_uid', data.get('target_node'))], data['target_slot_name'],  # fixme
                weight=data['weight'], certainty=data['certainty'],
                uid=uid)
        for uid in self.state.get('monitors', {}):
            self.monitors[uid] = Monitor(self, **self.state['monitors'][uid])

            # TODO: check if data sources and data targets match

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
        self.active_nodes = {}
        self.privileged_active_nodes = {}
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
        self.active_nodes.update(self.get_sensors())
        if self.active_nodes:
            activators = self.get_activators()
            self.calculate_node_functions(activators)
            self.calculate_node_functions(self.active_nodes)
            new_active_nodes = self.propagate_link_activation(self.active_nodes.copy())
            self.state["step"] += 1
            for uid, node in activators.items():
                node.activation = self.nodespaces[node.parent_nodespace].activators[node.parameters['type']]
            self.active_nodes.update(new_active_nodes)
            tmp_active_nodes = {}
            for uid, node in self.active_nodes.items():
                if node.activation != 0:
                    tmp_active_nodes[uid] = node
            self.active_nodes = tmp_active_nodes
        for uid in self.monitors:
            self.monitors[uid].step(self.state["step"])

    def step_privileged(self):
        """ performs a simulation step within the privileged nodes"""
        if self.privileged_active_nodes:
            self.calculate_node_functions(self.privileged_active_nodes)
            self.privileged_active_nodes = self.propagate_link_activation(self.privileged_active_nodes,
                limit_gatetypes=["cat"])

    def step_nodespace(self, nodespace):
        """ perform a simulation step limited to the given nodespace"""
        self.active_nodes.update(self.get_sensors(nodespace))
        activators = self.get_activators(nodespace=nodespace)
        active_nodes = dict((uid, node) for uid, node in self.active_nodes.items() if node.parent_nodespace == nodespace)
        self.calculate_node_functions(activators)
        self.calculate_node_functions(active_nodes)
        new_active_nodes = self.propagate_link_activation(active_nodes)
        self.state["step"] += 1
        self.active_nodes.update(new_active_nodes)
        for uid, node in self.active_nodes.items():
            if node.activation == 0:
                del self.active_nodes[uid]
        for uid in self.monitors:
            self.monitors[uid].step(self.state["step"])
        for uid, node in activators.items():
            node.activation = self.nodespaces[nodespace].activators[node.parameters['type']]

    def get_active_nodes(self, nodespace=None):
        """ returns a list of active nodes, ordered by activation.
        If you give a nodespace, the list will be filtered to return only active nodes from the
        given nodespace
        """
        if nodespace is None:
            nodes = self.active_nodes.values()
        else:
            nodes = [node for node in self.active_nodes.values() if node.parent_nodespace == nodespace]
        return sorted(nodes, key=lambda n: n.activation, reverse=True)

    def propagate_link_activation(self, nodes, limit_gatetypes=None):
        """ the linkfunction
            propagate activation from gates to slots via their links. returns the nodes that received activation.
            Arguments:
                nodes: the dict of nodes to consider
                limit_gatetypes (optional): a list of gatetypes to restrict the activation to links originating
                    from the given slottypes.
            Returns:
                new_active_nodes: the dict of nodes, that received activation through the propagation
        """
        new_active_nodes = {}
        for uid, node in nodes.items():
            if node.type != 'Activator':
                node.reset_slots();

        for uid, node in nodes.items():
            if limit_gatetypes is not None:
                gates = [(name, gate) for name, gate in node.gates.items() if name in limit_gatetypes]
            else:
                gates = node.gates.items()
            for type, gate in gates:
                for uid, link in gate.outgoing.items():
                    link.target_slot.activation += gate.activation * float(link.weight)  # TODO: where's the string coming from?
                    new_active_nodes[link.target_node.uid] = link.target_node
        for uid, node in new_active_nodes.items():
            # hack. needed, since node.data['activation'] was not altered.
            # Goes away when we switch to numpy and explicit delivery of these values.
            node.data['activation'] = node.activation
        return new_active_nodes

    def calculate_node_functions(self, nodes):
        """for all given nodes, call their node function, which in turn should update the gate functions
           Arguments:
               nodes: the dict of nodes to consider
        """
        for uid, node in nodes.items():
            node.node_function()

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


