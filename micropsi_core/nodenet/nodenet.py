"""
Nodenet definition
"""
from copy import deepcopy

import micropsi_core.tools
import json
import os
import warnings

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
            "activatortypes": STANDARD_NODETYPES.keys(),
            "step": 0,
            "filename": filename
        }

        self.world = world
        self.owner = owner
        self.name = name or os.path.basename(filename)
        self.filename = filename
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
        while len(nodespaces_to_initialize):
            next_nodespace = iter(nodespaces_to_initialize).next()
            # move up the nodespace tree until we find an existing parent or hit root
            while self.state["nodespaces"][next_nodespace].get(
                'parent_nodespace') not in self.nodespaces and next_nodespace != "Root":
                next_nodespace = self.state["nodespaces"][next_nodespace]['parent_nodespace']
            data = self.state["nodespaces"][next_nodespace]
            self.nodespaces[next_nodespace] = Nodespace(self,
                data['parent_nodespace'],
                data['position'],
                name=data['name'],
                uid=next_nodespace,
                index=data.get('index'),
                gatefunctions=data.get('gatefunctions', {}))
            nodespaces_to_initialize.remove(next_nodespace)

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
            'max_coords': self.max_coords,
            'is_active': self.is_active,
            'step': self.current_step,
            'nodespaces': {i: self.state['nodespaces'][i] for i in self.state['nodespaces']
                           if self.state['nodespaces'][i]["parent_nodespace"] == nodespace}
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
            self.links[uid].remove()
            del self.links[uid]
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
            origin_links = nodes[nodes.keys()[0]].nodenet.links
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
        if self.state['step'] == 0 and not self.active_nodes:
            self.active_nodes = dict((uid, node) for uid, node in self.nodes.items() if node.type == "Sensor")
        if self.active_nodes:
            self.calculate_node_functions(self.active_nodes)
            self.active_nodes = self.propagate_link_activation(self.active_nodes)
            self.state["step"] += 1
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
        active_nodes = self.get_active_nodes(nodespace)
        for key in active_nodes:
            del self.active_nodes[key]
        self.calculate_node_functions(active_nodes)
        self.active_nodes = self.active_nodes.update(active_nodes)

    def get_active_nodes(self, nodespace=None):
        """ returns a list of active nodes, ordered by activation.
        If you give a nodespace, the list will be filtered to return only active nodes from the
        given nodespace
        """
        if nodespace is not None:
            nodes = self.active_nodes.values()
        else:
            nodes = [node for node in self.active_nodes.values() if node.parent_nodespace == nodespace]
        return sorted(nodes, key=lambda n: n.activation, reverse=True)

    def propagate_link_activation(self, nodes, limit_gatetypes=None):
        """ propagate activation from gates to slots via their links. returns the nodes that received activation.
            Arguments:
                nodes: the dict of nodes to consider
                limit_gatetypes (optional): a list of gatetypes to restrict the activation to links originating
                    from the given slottypes.
            Returns:
                new_active_nodes: the dict of nodes, that received activation through the propagation
        """
        new_active_nodes = {}
        for uid, node in nodes.items():
            if limit_gatetypes is not None:
                gates = [(name, gate) for name, gate in node.gates.items() if name in limit_gatetypes]
            else:
                gates = node.gates.items()
            for type, gate in gates:
                for uid, link in gate.outgoing.items():
                    link.target_slot.activation += gate.activation * link.weight
                    new_active_nodes[link.target_node.uid] = link.target_node
        return new_active_nodes

    def calculate_node_functions(self, nodes):
        """for all given nodes, call their node function, which in turn should update the gate functions
           Arguments:
               nodes: the dict of nodes to consider
        """
        for uid, node in nodes.items():
            node.node_function()


class NetEntity(object):
    """The basic building blocks of node nets.

    Attributes:
        uid: the unique identifier of the net entity
        index: an attempt at creating an ordering criterion for net entities
        name: a human readable name (optional)
        position: a pair of coordinates on the screen
        nodenet: the node net in which the entity resides
        parent_nodespace: the node space this entity is contained in
    """

    @property
    def uid(self):
        return self.data.get("uid")

    @property
    def index(self):
        return self.data.get("index")

    @property
    def name(self):
        return self.data.get("name") or self.data.get("uid")

    @name.setter
    def name(self, string):
        self.data["name"] = string

    @property
    def position(self):
        return self.data.get("position", (0, 0))

    @position.setter
    def position(self, pos):
        self.data["position"] = pos

    @property
    def parent_nodespace(self):
        return self.data.get("parent_nodespace", 0)

    @parent_nodespace.setter
    def parent_nodespace(self, uid):
        nodespace = self.nodenet.nodespaces[uid]
        if self.entitytype not in nodespace.netentities:
            nodespace.netentities[self.entitytype] = []
        if self.uid not in nodespace.netentities[self.entitytype]:
            nodespace.netentities[self.entitytype].append(self.uid)
            #if uid in self.nodenet.state["nodespaces"][uid][self.entitytype]:
            #    self.nodenet.state["nodespaces"][uid][self.entitytype] = self.uid
            # tell my old parent that I move out
            if "parent_nodespace" in self.data:
                old_parent = self.nodenet.nodespaces.get(self.data["parent_nodespace"])
                if old_parent and old_parent.uid != uid and self.uid in old_parent.netentities.get(self.entitytype, []):
                    old_parent.netentities[self.entitytype].remove(self.uid)
        self.data['parent_nodespace'] = uid

    def __init__(self, nodenet, parent_nodespace, position, name="", entitytype="abstract_entities",
                 uid=None, index=None):
        """create a net entity at a certain position and in a given node space"""
        if uid in nodenet.state.get("entitytype", []):
            raise KeyError, "Netentity already exists"

        uid = uid or micropsi_core.tools.generate_uid()
        self.nodenet = nodenet
        if not entitytype in nodenet.state:
            nodenet.state[entitytype] = {}
        if not uid in nodenet.state[entitytype]:
            nodenet.state[entitytype][uid] = {}
        self.data = nodenet.state[entitytype][uid]
        self.data["uid"] = uid
        self.data["index"] = index or len(nodenet.state.get("nodes", [])) + len(nodenet.state.get("nodespaces", []))
        self.entitytype = entitytype
        self.name = name
        self.position = position
        if parent_nodespace:
            self.parent_nodespace = parent_nodespace
        else:
            self.data['parent_nodespace'] = None


class Nodespace(NetEntity):  # todo: adapt to new form, as net entitities
    """A container for net entities.

    One nodespace is marked as root, all others are contained in
    exactly one other nodespace.

    Attributes:
        activators: a dictionary of activators that control the spread of activation, via activator nodes
        netentities: a dictionary containing all the contained nodes and nodespaces, to speed up drawing
    """

    def __init__(self, nodenet, parent_nodespace, position, name="", uid=None,
                 index=None, gatefunctions=None):
        """create a node space at a given position and within a given node space"""
        self.activators = {}
        self.netentities = {}
        NetEntity.__init__(self, nodenet, parent_nodespace, position, name, "nodespaces", uid, index)
        nodenet.nodespaces[uid] = self
        if not gatefunctions: gatefunctions = dict()
        self.gatefunctions = gatefunctions
        for nodetype in gatefunctions:
            for gatetype in gatefunctions[nodetype]:
                self.set_gate_function(nodetype, gatetype, gatefunctions[nodetype][gatetype])

    def get_contents(self):
        """returns a dictionary with all contained net entities, related links and dependent nodes"""
        return self.netentities

    def get_activator_value(self, type):
        """returns the value of the activator of the given type, or 1, if none exists"""
        pass

    def get_data_targets(self):
        """Returns a dictionary of available data targets to associate actors with.

        Data targets are either handed down by the node net manager (to operate on the environment), or
        by the node space itself, to perform directional activation."""
        pass

    def get_data_sources(self):
        """Returns a dictionary of available data sources to associate sensors with.

        Data sources are either handed down by the node net manager (to read from the environment), or
        by the node space itself, to obtain information about its contents."""
        pass

    def set_gate_function(self, nodetype, gatetype, gatefunction, parameters=None):
        """Sets the gatefunction for a given node- and gatetype within this nodespace"""
        if gatefunction:
            if nodetype not in self.data['gatefunctions']:
                self.data['gatefunctions'][nodetype] = {}
            self.data['gatefunctions'][nodetype][gatetype] = gatefunction
            if nodetype not in self.gatefunctions:
                self.gatefunctions[nodetype] = {}
            try:
                self.gatefunctions[nodetype] = micropsi_core.tools.create_function(gatefunction,
                    parameters="gate, params")
            except SyntaxError, err:
                warnings.warn("Syntax error while compiling gate function: %s, %s" % (gatefunction, err.message))
                self.nodefunction = micropsi_core.tools.create_function("""gate.activation = 'Syntax error'""",
                    parameters="gate, params")
        else:
            if nodetype in self.gatefunctions and gatetype in self.gatefunctions[nodetype]:
                del self.gatefunctions[nodetype][gatetype]
            if nodetype in self.data['gatefunctions'] and gatetype in self.data['gatefunctions'][nodetype]:
                del self.data['gatefunctions'][nodetype][gatetype]

    def get_gatefunction(self, nodetype, gatetype):
        """Retrieve a bytecode-compiled gatefunction for a given node- and gatetype"""
        if nodetype in self.gatefunctions and gatetype in self.gatefunctions[nodetype]:
            return self.gatefunctions[nodetype][gatetype]


class Link(object):
    """A link between two nodes, starting from a gate and ending in a slot.

    Links propagate activation between nodes and thereby facilitate the function of the agent.
    Links have weights, but apart from that, all their properties are held in the gates where they emanate.
    Gates contain parameters, and the gate type effectively determines a link type.

    You may retrieve links either from the global dictionary (by uid), or from the gates of nodes themselves.
    """

    @property
    def uid(self):
        return self.data.get("uid")

    @property
    def weight(self):
        return self.data.get("weight")

    @weight.setter
    def weight(self, value):
        self.data["weight"] = value

    @property
    def certainty(self):
        return self.data.get("certainty")

    @certainty.setter
    def certainty(self, value):
        self.data["certainty"] = value

    @property
    def source_node(self):
        return self.nodenet.nodes.get(self.data.get('source_node_uid', self.data.get('source_node')))  # fixme

    @source_node.setter
    def source_node(self, node):
        self.data["source_node_uid"] = node.uid

    @property
    def source_gate(self):
        return self.source_node.gates.get(self.data.get("source_gate_name"))

    @source_gate.setter
    def source_gate(self, gate):
        self.data["source_gate_name"] = gate.type

    @property
    def target_node(self):
        return self.nodenet.nodes.get(self.data.get('target_node_uid', self.data.get('target_node')))  # fixme

    @target_node.setter
    def target_node(self, node):
        self.data["target_node_uid"] = node.uid

    @property
    def target_slot(self):
        return self.target_node.slots.get(self.data.get("target_slot_name"))

    @target_slot.setter
    def target_slot(self, slot):
        self.data["target_slot_name"] = slot.type

    def __init__(self, source_node, source_gate_name, target_node, target_slot_name, weight=1, certainty=1, uid=None):
        """create a link between the source_node and the target_node, from the source_gate to the target_slot.
        Note: you should make sure that no link between source and gate exists.

        Attributes:
            weight (optional): the weight of the link (default is 1)
        """

        uid = uid or micropsi_core.tools.generate_uid()
        self.nodenet = source_node.nodenet
        if not uid in self.nodenet.state["links"]:
            self.nodenet.state["links"][uid] = {}
        self.data = source_node.nodenet.state["links"][uid]
        self.data["uid"] = uid
        self.data["source_node"] = self.data["source_node_uid"] = source_node.uid  # fixme
        self.data["target_node"] = self.data["target_node_uid"] = target_node.uid  # fixme
        self.link(source_node, source_gate_name, target_node, target_slot_name, weight, certainty)

    def link(self, source_node, source_gate_name, target_node, target_slot_name, weight=1, certainty=1):
        """link between source and target nodes, from a gate to a slot.

            You may call this function to change the connections of an existing link. If the link is already
            linked, it will be unlinked first.
        """
        if self.source_node:
            if self.source_node != source_node and self.source_gate.type != source_gate_name:
                del self.source_gate.outgoing[self.uid]
        if self.target_node:
            if self.target_node != target_node and self.target_slot.type != target_slot_name:
                del self.target_slot.incoming[self.uid]
        self.source_node = source_node
        self.target_node = target_node
        self.source_gate = source_node.get_gate(source_gate_name)
        self.target_slot = target_node.get_slot(target_slot_name)
        self.weight = weight
        self.certainty = certainty
        self.source_gate.outgoing[self.uid] = self
        self.target_slot.incoming[self.uid] = self

    def remove(self):
        """unplug the link from the node net
           can't be handled in the destructor, since it removes references to the instance
        """
        del self.source_gate.outgoing[self.uid]
        del self.target_slot.incoming[self.uid]


def get_link_uid(source_node, source_gate_name, target_node, target_slot_name):
    """links are uniquely identified by their origin and targets; this function checks if a link already exists.

    Arguments:
        source_node: actual node from which the link originates
        source_gate_name: type of the gate of origin
        target_node: node that the link ends at
        target_slot_name: type of the terminating slot

    Returns the link uid, or None if it does not exist"""
    outgoing_candidates = set(source_node.get_gate(source_gate_name).outgoing.keys())
    incoming_candidates = set(target_node.get_slot(target_slot_name).incoming.keys())
    try:
        return (outgoing_candidates & incoming_candidates).pop()
    except KeyError:
        return None


class Node(NetEntity):
    """A net entity with slots and gates and a node function.

    Node functions are called alternating with the link functions. They process the information in the slots
    and usually call all the gate functions to transmit the activation towards the links.

    Attributes:
        activation: a numeric value (usually between -1 and 1) to indicate its activation. Activation is determined
            by the node function, usually depending on the value of the slots.
        slots: a list of slots (activation inlets)
        gates: a list of gates (activation outlets)
        node_function: a function to be executed whenever the node receives activation
    """

    @property
    def activation(self):
        return self.data.get("activation", 0)

    @activation.setter
    def activation(self, activation):
        self.data['activation'] = activation
        if activation == 0 and self.uid in self.nodenet.active_nodes:
            del self.nodenet.active_nodes[self.uid]
        elif activation != 0:
            self.nodenet.active_nodes[self.uid] = self

    @property
    def type(self):
        return self.data.get("type")

    @property
    def parameters(self):
        return self.data.get("parameters", {})

    @parameters.setter
    def parameters(self, dictionary):
        if self.data["type"] == "Native":
            self.nodetype.parameters = dictionary.keys()
        self.data["parameters"] = dictionary

    @property
    def state(self):
        return self.data.get("state", None)

    @state.setter
    def state(self, state):
        self.data['state'] = state

    def __init__(self, nodenet, parent_nodespace, position, state=None,
                 name="", type="Concept", uid=None, index=None, parameters=None, gate_parameters=None, **_):
        if not gate_parameters: gate_parameters = {}

        if uid in nodenet.nodes:
            raise KeyError, "Node already exists"

        NetEntity.__init__(self, nodenet, parent_nodespace, position,
            name=name, entitytype="nodes", uid=uid, index=index)

        self.gates = {}
        self.slots = {}
        self.data["type"] = type
        self.nodetype = None

        self.nodetype = self.nodenet.nodetypes[type]
        self.parameters = dict((key, None) for key in self.nodetype.parameters) if parameters is None else parameters
        for gate in self.nodetype.gatetypes:
            self.gates[gate] = Gate(gate, self, gate_function=None, parameters=gate_parameters.get(gate))
        for slot in self.nodetype.slottypes:
            self.slots[slot] = Slot(slot, self)
        if state:
            self.state = state
            # TODO: @doik: before, you explicitly added the state to nodenet.nodes[uid], too (in Runtime). Any reason?
        nodenet.nodes[self.uid] = self
        nodenet.nodes[self.uid].activation = 0  # TODO: should this be persisted?

    def get_gate_parameters(self):
        """Looks into the gates and returns gate parameters if these are defined"""
        gate_parameters = {}
        for gate in self.gates:
            if self.gates[gate].parameters:
                gate_parameters[gate] = self.gates[gate].parameters
        if len(gate_parameters): return gate_parameters
        else: return None

    def node_function(self):
        """Called whenever the node is activated or active.

        In different node types, different node functions may be used, i.e. override this one.
        Generally, a node function must process the slot activations and call each gate function with
        the result of the slot activations.

        Metaphorically speaking, the node function is the soma of a MicroPsi neuron. It reacts to
        incoming activations in an arbitrarily specific way, and may then excite the outgoing dendrites (gates),
        which transmit activation to other neurons with adaptive synaptic strengths (link weights).
        """
        # process the slots
        if self.type == 'Sensor':
            if self.parameters['datasource'] and self.nodenet.world:
                self.activation = self.nodenet.world.get_datasource(self.nodenet.uid, self.parameters['datasource'])
            else:
                self.activation = 0
        elif self.type == "Actor" and not self.nodenet.world:
            return
        else:
            self.activation = sum([self.slots[slot].activation for slot in self.slots])

        # call nodefunction of my node type
        if self.nodetype and self.nodetype.nodefunction is not None:
            try:
                self.nodetype.nodefunction(nodenet=self.nodenet, node=self, **self.parameters)
            except SyntaxError, err:
                warnings.warn("Syntax error during node execution: %s" % err.message)
                self.data["activation"] = "Syntax error"
            except TypeError, err:
                warnings.warn("Type error during node execution: %s" % err.message)
                self.data["activation"] = "Parameter mismatch"

    def get_gate(self, gatename):
        return self.gates.get(gatename)

    def get_slot(self, slotname):
        return self.slots.get(slotname)

    def get_associated_link_ids(self):
        links = []
        for key in self.gates:
            links.extend(self.gates[key].outgoing)
        for key in self.slots:
            links.extend(self.slots[key].incoming)
        return links

    def get_associated_node_ids(self):
        nodes = []
        for link in self.get_associated_link_ids():
            if self.nodenet.links[link].source_node.uid != self.uid:
                nodes.append(self.nodenet.links[link].source_node.uid)
            if self.nodenet.links[link].target_node.uid != self.uid:
                nodes.append(self.nodenet.links[link].target_node.uid)
        return nodes

    def set_gate_parameters(self, gate_type, parameters):
        if 'gate_parameters' not in self.data:
            self.data['gate_parameters'] = {}
        self.data['gate_parameters'][gate_type] = parameters
        self.gates[gate_type].parameters = parameters


class Gate(object):  # todo: take care of gate functions at the level of nodespaces, handle gate params
    """The activation outlet of a node. Nodes may have many gates, from which links originate.

    Attributes:
        type: a string that determines the type of the gate
        node: the parent node of the gate
        activation: a numerical value which is calculated at every step by the gate function
        parameters: a dictionary of values used by the gate function
        gate_function: called by the node function, updates the activation
        outgoing: the set of links originating at the gate
    """

    def __init__(self, type, node, gate_function=None, parameters=None):
        """create a gate.

        Parameters:
            type: a string that refers to a node type
            node: the parent node
            parameters: an optional dictionary of parameters for the gate function
        """
        self.type = type
        self.node = node
        self.parameters = parameters
        self.activation = 0
        self.outgoing = {}
        self.gate_function = gate_function or self.gate_function
        self.parameters = {
            "minimum": -1,
            "maximum": 1,
            "certainty": 1,
            "amplification": 1,
            "threshold": 0,
            "decay": 0
        }
        if parameters is not None:
            for key in parameters:
                if key in self.parameters:
                    self.parameters[key] = float(parameters[key])
                else:
                    self.parameters[key] = parameters[key]
        self.monitor = None

    def gate_function(self, input_activation):
        """This function sets the activation of the gate.

        The gate function should be called by the node function, and can be replaced by different functions
        if necessary. This default gives a linear function (input * amplification), cut off below a threshold.
        You might want to replace it with a radial basis function, for instance.
        """

        gate_factor = 1

        # check if the current node space has an activator that would prevent the activity of this gate
        if self.type in self.node.nodenet.nodespaces[self.node.parent_nodespace].activators:
            gate_factor = self.node.parent_nodespace.activators[self.type]
            if gate_factor == 0.0:
                self.activation = 0
                return  # if the gate is closed, we don't need to execute the gate function
            # simple linear threshold function; you might want to use a sigmoid for neural learning
        gatefunction = self.node.nodenet.nodespaces[self.node.parent_nodespace].get_gatefunction(self.node.type,
            self.type)
        if gatefunction:
            activation = gatefunction(self, self.parameters)
        else:
            activation = max(input_activation,
                self.parameters["threshold"]) * self.parameters["amplification"] * gate_factor

        if self.parameters["decay"]:  # let activation decay gradually
            if activation < 0:
                activation = min(activation, self.activation * (1 - self.parameters["decay"]))
            else:
                activation = max(activation, self.activation * (1 - self.parameters["decay"]))

        self.activation = min(self.parameters["maximum"], max(self.parameters["minimum"], activation))


class Slot(object):
    """The entrance of activation into a node. Nodes may have many slots, in which links terminate.

    Attributes:
        type: a string that determines the type of the slot
        node: the parent node of the slot
        activation: a numerical value which is the sum of all incoming activations
        current_step: the simulation step when the slot last received activation
        incoming: a dictionary of incoming links together with the respective activation received by them
    """

    def __init__(self, type, node):
        """create a slot.

        Parameters:
            type: a string that refers to the slot type
            node: the parent node
        """
        self.type = type
        self.node = node
        self.incoming = {}
        self.current_step = -1
        self.activation = 0


STANDARD_NODETYPES = {
    "Register": {
        "name": "Register",
        "slottypes": ["gen"],
        "gatetypes": ["gen"]
    },
    "Sensor": {
        "name": "Sensor",
        "parameters": ["datasource"],
        "nodefunction_definition": """node.gates["gen"].gate_function(nodenet.world.get_datasource(nodenet.uid, datasource))""",
        "gatetypes": ["gen"]
    },
    "Actor": {
        "name": "Actor",
        "parameters": ["datasource", "datatarget"],
        "nodefunction_definition": """node.nodenet.world.set_datatarget(datatarget, nodenet.uid, node.activation)""",
        "slottypes": ["gen"],
        "gatetypes": ["gen"]
    },
    "Concept": {
        "name": "Concept",
        "slottypes": ["gen"],
        "nodefunction_definition": """for type, gate in node.gates.items(): gate.gate_function(node.activation)""",
        "gatetypes": ["gen", "por", "ret", "sub", "sur", "cat", "exp", "sym", "ref"]
    },
    "Label": {
        "name": "Label",
        "slottypes": ["gen"],
        "nodefunction_definition": """for type, gate in node.gates.items(): gate.gate_function(node.activation)""",
        "gatetypes": ["sym", "ref"]
    },
    "Event": {
        "name": "Event",
        "parameters": ["time"],
        "slottypes": ["gen"],
        "gatetypes": ["gen", "por", "ret", "sub", "sur", "cat", "exp", "sym"],
        "nodefunction_definition": """for type, gate in node.gates.items(): gate.gate_function(node.activation)""",
        # TODO: this needs to juggle the states
        "states": ['suggested', 'rejected', 'commited', 'scheduled', 'active', 'overdue', 'active overdue', 'dropped',
                   'failed', 'completed']
    },
    "Activator": {
        "name": "Activator",
        "slottypes": ["gen"],
        "parameters": ["type"],
        "parameter_values": {"type": ["gen", "por", "ret", "sub", "sur", "cat", "exp", "sym", "ref"]},
        "nodefunction_definition": """nodenet.nodespaces[node.parent_nodespace].activators[node.parameters[type]] = node.slots["gen"].activation"""
    }
}


class Nodetype(object):
    """Every node has a type, which is defined by its slot types, gate types, its node function and a list of
    node parameteres."""

    @property
    def name(self):
        return self.data["name"]

    @name.setter
    def name(self, identifier):
        self.nodenet.state["nodetypes"][identifier] = self.nodenet.state["nodetypes"][self.data["name"]]
        del self.nodenet.state["nodetypes"][self.data["name"]]
        self.data["name"] = identifier

    @property
    def slottypes(self):
        return self.data.get("slottypes")

    @slottypes.setter
    def slottypes(self, list):
        self.data["slottypes"] = list

    @property
    def gatetypes(self):
        return self.data.get("gatetypes")

    @gatetypes.setter
    def gatetypes(self, list):
        self.data["gatetypes"] = list

    @property
    def parameters(self):
        return self.data.get("parameters", [])

    @parameters.setter
    def parameters(self, list):
        self.data["parameters"] = list
        self.nodefunction = self.data.get("nodefunction")  # update nodefunction

    @property
    def states(self):
        return self.data.get("states", [])

    @states.setter
    def states(self, list):
        self.data["states"] = list

    @property
    def nodefunction_definition(self):
        return self.data.get("nodefunction_definition")

    @nodefunction_definition.setter
    def nodefunction_definition(self, string):
        self.data["nodefunction_definition"] = string
        args = ','.join(self.parameters).strip(',')
        try:
            self.nodefunction = micropsi_core.tools.create_function(string,
                parameters="nodenet, node, " + args)
        except SyntaxError, err:
            warnings.warn("Syntax error while compiling node function: %s", err.message)
            self.nodefunction = micropsi_core.tools.create_function("""node.activation = 'Syntax error'""",
                parameters="nodenet, node, " + args)

    def __init__(self, name, nodenet, slottypes=None, gatetypes=None, states=None, parameters=None,
                 nodefunction_definition=None, parameter_values=None):
        """Initializes or creates a nodetype.

        Arguments:
            name: a unique identifier for this nodetype
            nodenet: the nodenet that this nodetype is part of

        If a nodetype with the same name is already defined in the nodenet, it is overwritten. Parameters that
        are not given here will be taken from the original definition. Thus, you may use this initializer to
        set up the nodetypes after loading new nodenet state (by using it without parameters).

        Within the nodenet, the nodenet state dict stores the whole nodenet definition. The part that defines
        nodetypes is structured as follows:

            { "slots": list of slot types or None,
              "gates": list of gate types or None,
              "parameters": string of parameters to store values in or read values from
              "nodefunction": <a string that stores a sequence of python statements, and gets the node and the
                    nodenet as arguments>
            }
        """
        self.nodenet = nodenet
        if name not in STANDARD_NODETYPES:
            if not "nodetypes" in nodenet.state:
                self.nodenet.state["nodetypes"] = {}
            if not name in self.nodenet.state["nodetypes"]:
                self.nodenet.state["nodetypes"][name] = {}
            self.data = self.nodenet.state["nodetypes"][name]
        else:
            self.data = {}
        self.data["name"] = name

        self.states = self.data.get('states', {}) if states is None else states
        self.slottypes = self.data.get("slottypes", ["gen"]) if slottypes is None else slottypes
        self.gatetypes = self.data.get("gatetypes", ["gen"]) if gatetypes is None else gatetypes

        self.parameters = self.data.get("parameters", []) if parameters is None else parameters
        self.parameter_values = self.data.get("parameter_values", []) if parameter_values is None else parameter_values

        if nodefunction_definition:
            self.nodefunction_definition = nodefunction_definition
        else:
            self.nodefunction = None


class Monitor(object):
    """A gate or slot monitor watching the activation of the given slot or gate over time

    Attributes:
        nodenet: the parent Nodenet
        node: the parent Node
        type: either "slot" or "gate"
        target: the name of the observerd Slot or Gate
    """

    def __init__(self, nodenet, node_uid, type, target, uid=None, **_):
        if 'monitors' not in nodenet.state:
            nodenet.state['monitors'] = {}
        self.uid = uid or micropsi_core.tools.generate_uid()
        self.data = {'uid': self.uid}
        self.nodenet = nodenet
        nodenet.state['monitors'][self.uid] = self.data
        self.data['values'] = self.values = {}
        self.data['node_uid'] = self.node_uid = node_uid
        self.data['type'] = self.type = type
        self.data['target'] = self.target = target

    def step(self, step):
        self.values[step] = getattr(self.nodenet.nodes[self.node_uid], self.type + 's')[self.target].activation

    def clear(self):
        self.data['values'] = {}
