"""
Nodenet definition
"""

import micropsi_core.tools
import json, os, warnings

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
        return self.runtime.worlds.get(self.state["world"])

    @world.setter
    def world(self, world):
        self.state["world"] = world.uid

    # @property
    # def worldadapter(self):
    #     return self.state.get("worldadapter")

    # @worldadapter.setter
    # def worldadapter(self, worldadapter_uid):
    #     self.state["worldadapter"] = worldadapter_uid

    @property
    def current_step(self):
        return self.state.get("step")

    def __init__(self, runtime, filename, name = "", worldadapter = "Default", world = None, owner = "", uid = None):
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
            "nodespaces": {'Root': {}},
            "nodetypes": STANDARD_NODETYPES,
            "activatortypes": STANDARD_NODETYPES.keys(),
            "step": 0,
            "filename": filename
        }

        self.world = world
        self.runtime = runtime
        self.owner = owner
        self.name = name or os.path.basename(filename)
        self.filename = filename
        self.worldadapter = self.world.worldadapters[worldadapter]

        self.nodespaces = {"Root": Nodespace(self, None, (0,0), name="Root", entitytype="nodespaces", uid = "Root")}

        self.nodes = {}
        self.links = {}
        self.nodetypes = {}

        self.load()

        # todo: persist these?
        self.active_nodes = {}


    def load(self, string = None):
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
        for type, data in self.state.get('nodetypes', STANDARD_NODETYPES).items():
            self.nodetypes[type] = Nodetype(nodenet=self, **data)
        # set up nodes
        for uid in self.state['nodes']:
            data = self.state['nodes'][uid]
            self.nodes[uid] = Node(self, "Root", (data['x'], data['y']), name=data['name'], type=data.get('type', 'Concept'), uid=uid, parameters = data.get('parameters'))
        # set up links
        for uid in self.state['links']:
            data = self.state['links'][uid]
            self.links[uid] = Link(self.nodes[data['sourceNode']], data['sourceGate'], self.nodes[data['targetNode']], data['targetSlot'], weight=data['weight'], uid=uid)

        # TODO: check if data sources and data targets match

    def get_nodespace_data(self, nodespace_uid):
        """returns the nodes and links in a given nodespace"""
        pass

    # add functions for exporting and importing node nets
    def export_data(self):
        """serializes and returns the nodenet state for export to a end user"""
        pass

    def import_data(self, nodenet_data):
        """imports nodenet state as the current node net"""
        pass

    def merge_data(self, nodenet_data):
        """merges the nodenet state with the current node net, might have to give new UIDs to some entities"""
        pass

    def step(self):
        """perform a simulation step"""
        # first step will activate the sensors:
        if self.state['step'] == 0:
            self.active_nodes = {uid: node for uid,node in self.nodes.items() if node.type == "Sensor"}

        if self.active_nodes:
            self.calculate_node_functions()
            self.propagate_link_activation()
            self.state["step"] +=1

    def propagate_link_activation(self):
        """propagate activation through all links, taking it from the gates and summing it up in the slots"""
        new_active_nodes = {}
        for uid, node in self.active_nodes.items():
            for type, gate in node.gates.items():
                for uid, link in gate.outgoing.items():
                    link.target_slot.activation += gate.activation * link.weight
                    new_active_nodes[link.target_node.uid] = link.target_node
        self.active_nodes = new_active_nodes
        print self.active_nodes

    def calculate_node_functions(self):
        """for all active nodes, call their node function, which in turn should update the gate functions"""
        for uid, node in self.active_nodes.items():
            node.node_function()


class NetEntity(object):
    """The basic building blocks of node nets.

    Attributes:
        uid: the unique identifier of the net entity
        name: a human readable name (optional)
        position: a pair of coordinates on the screen
        nodenet: the node net in which the entity resides
        parent_nodespace: the node space this entity is contained in
    """

    @property
    def uid(self):
        return self.data.get("uid")

    @property
    def name(self):
        return self.data.get("name") or self.data.get("uid")

    @name.setter
    def name(self, string):
        self.data["name"] = string

    @property
    def position(self):
        return self.data.get("position", (0,0))

    @position.setter
    def position(self, pos):
        self.data['x'] = pos[0]
        self.data['y'] = pos[1]
        self.data["position"] = pos

    @property
    def parent_nodespace(self):
        return self.data.get("parent_nodespace", 0)

    @parent_nodespace.setter
    def parent_nodespace(self, uid):
        nodespace = self.nodenet.nodespaces[uid]
        if self.entitytype not in nodespace.netentities:
            nodespace.netentities[self.entitytype] = []
        nodespace.netentities[self.entitytype].append(self.uid)
        #if uid in self.nodenet.state["nodespaces"][uid][self.entitytype]:
        #    self.nodenet.state["nodespaces"][uid][self.entitytype] = self.uid
        # tell my old parent that I move out
        if "parent_nodespace" in self.data:
            old_parent = self.nodenet.nodespaces.get(self.data["parent_nodespace"])
            if old_parent and self.uid in old_parent.netentities.get(self.entitytype, []):
                old_parent.netentities[self.entitytype].remove(self.uid)

    def __init__(self, nodenet, parent_nodespace, position, name = "", entitytype = "abstract_entities", uid = None):
        """create a net entity at a certain position and in a given node space"""
        uid = uid or micropsi_core.tools.generate_uid()
        self.nodenet = nodenet
        if not entitytype in nodenet.state:
            nodenet.state[entitytype] = {}
        if not uid in nodenet.state[entitytype]:
            nodenet.state[entitytype][uid] = {}
        self.data = nodenet.state[entitytype][uid]
        self.data["uid"] = uid
        self.entitytype = entitytype

        self.name = name
        self.position = position
        if parent_nodespace:
            self.parent_nodespace = parent_nodespace


class Nodespace(NetEntity):  # todo: adapt to new form, as net entitities
    """A container for net entities.

    One nodespace is marked as root, all others are contained in
    exactly one other nodespace.

    Attributes:
        activators: a dictionary of activators that control the spread of activation, via activator nodes
        netentities: a dictionary containing all the contained nodes and nodespaces, to speed up drawing
    """


    def __init__(self, nodenet, parent_nodespace, position, name = "Comment", entitytype = "comments", uid = None):
        """create a node space at a given position and within a given node space"""
        self.activators = {}
        self.netentities = {}
        NetEntity.__init__(self, nodenet, parent_nodespace, position, name, entitytype, uid)

    def get_contents(self):
        """returns a dictionary with all contained net entities, related links and dependent nodes"""
        pass

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

class Link(object): # todo: adapt to new form, like net entitities
    """A link between two nodes, starting from a gate and ending in a slot.

    Links propagate activation between nodes and thereby facilitate the function of the agent.
    Links have weights, but apart from that, all their properties are held in the gates where they emanate.
    Gates contain parameters, and the gate type effectively determines a link type.

    You may retrieve links either from the global dictionary (by uid), or from the gates of nodes themselves.
    """

    def __init__(self, source_node, source_gate_name, target_node, target_slot_name, weight=1, certainty=1, uid=None):
        """create a link between the source_node and the target_node, from the source_gate to the target_slot

        Attributes:
            weight (optional): the weight of the link (default is 1)
        """
        self.uid = uid or  micropsi_core.tools.generate_uid()
        self.source_node = None
        self.target_node = None
        self.link(source_node, source_gate_name, target_node, target_slot_name)
        self.weight = weight
        self.certainty = 1

    def link(self, source_node, source_gate_name, target_node, target_slot_name, weight=1):
        """link between source and target nodes, from a gate to a slot.

            You may call this function to change the connections of an existing link. If the link is already
            linked, it will be unlinked first.
        """
        if self.source_node: self.source_gate.outgoing.remove(self.uid)
        if self.target_node: self.target_slot.incoming.remove(self.uid)
        self.source_node = source_node
        self.target_node = target_node
        self.source_gate = source_node.get_gate(source_gate_name)
        self.target_slot = target_node.get_slot(target_slot_name)
        self.weight = weight
        self.source_gate.outgoing[self.uid] = self
        self.target_slot.incoming[self.uid] = self

    def remove(self):
        """unplug the link from the node net
           can't be handled in the destructor, since it removes references to the instance
        """
        del self.source_gate.outgoing[self.uid]
        del self.target_slot.incoming[self.uid]

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

    @property
    def type(self):
        return self.data.get("type")

    @property
    def parameters(self):
        return self.data.get("parameters", {})

    @parameters.setter
    def parameters(self, dictionary):
        self.data["parameters"] = dictionary

    def __init__(self, nodenet, parent_nodespace, position, name = "", type = "Concept", uid = None, parameters = None):
        NetEntity.__init__(self, nodenet, parent_nodespace, position, name = name, entitytype = "nodes", uid = uid)

        self.gates = {}
        self.slots = {}
        self.data["type"] = type
        self.parameters = {}
        if type in self.nodenet.nodetypes:
            self.nodetype = self.nodenet.nodetypes[type]
            self.parameters = {key:None for key in self.nodetype.parameters} if parameters is None else parameters
            for gate in self.nodetype.gatetypes:
                self.gates[gate] = Gate(gate, self)
            for slot in self.nodetype.slottypes:
                self.slots[slot] = Slot(slot, self)

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
            if self.parameters['datasource']:
                self.activation = self.nodenet.worldadapter.datasources[self.parameters['datasource']]
            else:
                self.activation = 0
        else:
            self.activation = sum([self.slots[slot].activation for slot in self.slots])

        # call nodefunction of my node type
        if self.nodetype and self.nodetype.nodefunction is not None:
            try:
                self.nodetype.nodefunction(nodenet = self.nodenet, node = self, **self.parameters)
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

class Gate(object): # todo: take care of gate functions at the level of nodespaces, handle gate params
    """The activation outlet of a node. Nodes may have many gates, from which links originate.

    Attributes:
        type: a string that determines the type of the gate
        node: the parent node of the gate
        activation: a numerical value which is calculated at every step by the gate function
        parameters: a dictionary of values used by the gate function
        gate_function: called by the node function, updates the activation
        outgoing: the set of links originating at the gate
    """
    def __init__(self, type, node, gate_function = None, parameters = None):
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
        self.parameters = parameters or {
                "minimum": -1,
                "maximum": 1,
                "certainty": 1,
                "amplification": 1,
                "threshold": 0,
                "decay": 0
            }

    def gate_function(self, input_activation):
        """This function sets the activation of the gate.

        The gate function should be called by the node function, and can be replaced by different functions
        if necessary. This default gives a linear function (input * amplification), cut off below a threshold.
        You might want to replace it with a radial basis function, for instance.
        """

        gate_factor = 1

        # check if the current node space has an activator that would prevent the activity of this gate
        if self.type in self.node.nodenet.nodespaces[self.node.data['nodespace']].activators:
            gate_factor = self.node.parent_nodespace.activators[self.type]
            if gate_factor == 0.0:
                self.activation = 0
                return  # if the gate is closed, we don't need to execute the gate function

        # simple linear threshold function; you might want to use a sigmoid for neural learning
        activation = max(input_activation, self.parameters["threshold"]) * self.parameters["amplification"] *gate_factor

        if self.parameters["decay"]:  # let activation decay gradually
            if activation < 0:
                activation = min(activation, self.activation*(1-self.parameters["decay"]))
            else:
                activation = max(activation, self.activation*(1-self.parameters["decay"]))

        self.activation = min(self.parameters["maximum"],max(self.parameters["minimum"],activation))

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
        "parameters":["datasource"],
        "nodefunction_definition": """node.gates["gen"].gate_function(nodenet.worldadapter.get_datasource(datasource))""",
        "gatetypes": ["gen"]
    },
    "Actor": {
        "name": "Actor",
        "parameters":["datasource", "datatarget"],
        "nodefunction_definition": """node.nodenet.worldadapter.set_datatarget(datatarget, node.activation)""",
        "slottypes": ["gen"],
        "gatetypes": ["gen"]
    },
    "Concept": {
        "name": "Concept",
        "slottypes": ["gen"],
        "nodefunction_definition": """for type, gate in node.gates.items(): gate.gate_function(node.activation)""",
        "gatetypes": ["gen", "por", "ret", "sub", "sur", "cat", "exp"]
    },
    "Activator": {
        "name": "Activator",
        "slottypes": ["gen"],
        "parameters": ["type"],
        "nodefunction_definition": """nodenet.nodespaces[node.parent_nodespace].activators[node.type] = node.slots["gen"].activation"""
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

    @property
    def nodefunction_definition(self):
        return self.data.get("nodefunction_definition")

    @nodefunction_definition.setter
    def nodefunction_definition(self, string):
        self.data["nodefunction_definition"] = string
        args = ','.join(self.parameters).strip(',')
        try:
            self.nodefunction = micropsi_core.tools.create_function(string,
                parameters = "nodenet, node, " + args)
        except SyntaxError, err:
            warnings.warn("Syntax error while compiling node function.")
            self.nodefunction = micropsi_core.tools.create_function("""node.activation = 'Syntax error'""",
                parameters = "nodenet, node, " + args)

    def __init__(self, name, nodenet, slottypes = None, gatetypes = None, parameters = None, nodefunction_definition = None):
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
        if not "nodetypes" in nodenet.state: self.nodenet.state["nodetypes"] = {}
        if not name in self.nodenet.state["nodetypes"]: self.nodenet.state["nodetypes"][name] = {}
        self.data = self.nodenet.state["nodetypes"][name]
        self.data["name"] = name

        self.slottypes = self.data.get("slottypes", ["gen"]) if slottypes is None else slottypes
        self.gatetypes = self.data.get("gatetypes", ["gen"]) if gatetypes is None else gatetypes

        self.parameters = self.data.get("parameters", []) if parameters is None else parameters

        if nodefunction_definition:
            self.nodefunction_definition = nodefunction_definition
        else:
            self.nodefunction = None



