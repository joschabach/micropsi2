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
        data: persistent nodenet data
        nodespaces: A dictionary of node space UIDs and respective node spaces
        nodes: A dictionary of node UIDs and respective nodes
        calculate_now_nodes: A set of nodes that has received activation in the current step
        links: A dictionary of link UIDs and respective links
        gate_types: A dictionary of gate type names and the individual types of gates
        slot_types: A dictionary of slot type names and the individual types of slots
        native_module_types: A dictionary of native module names and individual native modules types
        agent_type: The type of the agent, which is matched to a world adapter
        worldadapter: An actual world adapter object (agent body) residing in a world implementation
    """

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
    def world(self):
        return self.runtime.worlds.get(self.data["world"])

    @world.setter
    def world(self, world):
        self.data["world"] = world.uid

    @property
    def world_adapter(self):
        return self.data.get("worldadapter")

    @world_adapter.setter
    def world_adapter(self, worldadapter_uid):
        self.data["worldadapter"] = worldadapter_uid

    @property
    def step(self):
        return self.data.get("step")

    def __init__(self, runtime, filename, name = "", world_adapter = "Default", world = None, owner = "", uid = None):
        """Create a new MicroPsi agent.

        Arguments:
            filename: the path and filename of the agent
            agent_type (optional): the interface of this agent to its environment
            name (optional): the name of the agent
            owner (optional): the user that created this agent
            uid (optional): unique handle of the agent; if none is given, it will be generated
        """

        self.data = {
            "version": NODENET_VERSION,  # used to check compatibility of the node net data
            "nodes": {},
            "links": {},
            "nodespaces": {},
            "nodetypes": ["Concept", "Register", "Sensor", "Actor"],
            "nodefunctions": {},
            "gatetypes": ["por", "ret", "sub", "sur", "cat", "exp"],
            "step": 0
        }

        self.world = world
        self.runtime = runtime
        self.uid = uid or micropsi_core.tools.generate_uid()
        self.owner = owner
        self.name = name or os.path.basename(filename)
        self.filename = filename
        self.world_adapter = world_adapter

        self.nodespaces = {}
        self.nodes = {}
        self.links = {}
        self.nodetypes = {}

        self.active_nodes = {} # these are the nodes that received activation and must be calculated

        self.load()

    def load(self, string = None):
        """Load the node net from a file"""
        # try to access file
        if string:
            try:
                self.data = json.loads(string)
            except ValueError:
                warnings.warn("Could not read nodenet data from string")
                return False
        else:
            try:
                with open(self.filename) as file:
                    self.data = json.load(file)
            except ValueError:
                warnings.warn("Could not read nodenet data")
                return False
            except IOError:
                warnings.warn("Could not open nodenet file")

        if "version" in self.data and self.data["version"] == NODENET_VERSION:
            self.initialize_nodenet()
            return True
        else:
            warnings.warn("Wrong version of the nodenet data; starting new nodenet")
            return False

    def initialize_nodenet(self):
        """Called after reading new nodenet data.

        Parses the nodenet data and set up the non-persistent data structures necessary for efficient
        computation of the node net
        """
        # check if data sources and data targets match
        pass

    def get_nodespace_data(self, nodespace_uid):
        """returns the nodes and links in a given nodespace"""
        pass

    # add functions for exporting and importing node nets
    def export_data(self):
        """serializes and returns the nodenet data for export to a end user"""
        pass

    def import_data(self, nodenet_data):
        """imports nodenet data as the current node net"""
        pass

    def merge_data(self, nodenet_data):
        """merges the nodenet data with the current node net, might have to give new UIDs to some entities"""
        pass

    def step(self):
        """perform a simulation step"""
        self.calculate_node_functions()
        self.propagate_link_activation()
        self.data["step"] +=1
    def propagate_link_activation(self):
        """propagate activation through all links, taking it from the gates and summing it up in the slots"""
        pass

    def calculate_node_functions(self):
        """for all active nodes, call their node function, which in turn should update the gate functions"""
        pass

    def set_node_function(self, node_type, node_function_string):
        """For all nodes of the given type, use the given node function.

        The node function is handed the current node, the current nodespace and the current agent, so that it may
        """


class NetEntity(object):
    """The basic building blocks of node nets.

    Attributes:
        uid: the unique identifier of the net entity
        name: a human readable name (optional)
        position: a pair of coordinates on the screen
        nodenet: the node net in which the entity resides
        parent_nodespace: the node space this entity is contained in
    """

    def __init__(self, position, nodenet, parent_nodespace, name = ""):
        """create a net entity at a certain position and in a given node space"""

        self.uid = micropsi_core.tools.generate_uid()
        self.name = name
        self.position = position
        self.nodenet = nodenet
        self.parent_nodespace = parent_nodespace

class Comment(NetEntity):
    """Comments are simple text boxes that can be arbitrarily positioned to aid in understanding the node net.

    Attributes:
        the same as for NetEntities, and
        comment: a string of text
    """

    def __init__(self, position, nodenet, parent_nodespace = 0, comment = ""):
        self.comment = comment
        NetEntity.__init__(position, nodenet, parent_nodespace, name = "Comment")

class Nodespace(NetEntity):
    """A container for net entities.

    One nodespace is marked as root, all others are contained in
    exactly one other nodespace.

    Attributes:
        activators: a dictionary of activators that control the spread of activation, via activator nodes
        netentities: a dictionary containing all the contained nodes and nodespaces, to speed up drawing
    """
    def __init__(self, position, nodenet, parent_nodespace = None, name = ""):
        """create a node space at a given position and within a given node space"""
        self.activators = {}
        self.netentities = {}
        NetEntity.__init__(self, position, nodenet, parent_nodespace, name)

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

class Link(object):
    """A link between two nodes, starting from a gate and ending in a slot.

    Links propagate activation between nodes and thereby facilitate the function of the agent.
    Links have weights, but apart from that, all their properties are held in the gates where they emanate.
    Gates contain parameters, and the gate type effectively determines a link type.

    You may retrieve links either from the global dictionary (by uid), or from the gates of nodes themselves.
    """
    def __init__(self, source_node, source_gate_name, target_node, target_slot_name, weight = 1):
        """create a link between the source_node and the target_node, from the source_gate to the target_slot

        Attributes:
            weight (optional): the weight of the link (default is 1)
        """
        self.uid = micropsi_core.tools.generate_uid()
        self.link(source_node, source_gate_name, target_node, target_slot_name)
        self.weight = weight

    def link(self, source_node, source_gate_name, target_node, target_slot_name, weight = 1):
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
        self.source_gate.outgoing.add(self.uid)
        self.target_slot.incoming[self.uid] = 0

    def __del__(self):
        """unplug the link from the node net"""
        self.source_gate.outgoing.remove(self.uid)
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

    def __init__(self, position, nodenet, parent_nodespace = 0, name = "",
                 type = "Register",
                 node_function = None,
                 activation = 0, slots = None, gates = None):
        NetEntity.__init__(position, nodenet, parent_nodespace, name)
        self.type = type
        #if type == ""


    def node_function(self, ):
        """Called whenever the node is activated or active.

        In different node types, different node functions may be used, i.e. override this one.
        Generally, a node function must process the slot activations and call each gate function with
        the result of the slot activations.

        Metaphorically speaking, the node function is the soma of a MicroPsi neuron. It reacts to
        incoming activations in an arbitrarily specific way, and may then excite the outgoing dendrites (gates),
        which transmit activation to other neurons with adaptive synaptic strengths (link weights).
        """
        # process the slots
        if self.slots:
            activation = 0
            for i in self.slots:
                if self.slots[i].incoming:
                    pass
                    # if self.slots[i].current_step < current_step:  # we have not processed this yet
        self.activation = sum([self.slots[slot].incoming[link] for slot in self.slots for link in self.slots[slot].incoming])

class Gate(object):
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
        if self.type in self.node.parent_nodespace.activators:
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
        self.incoming = {}
        self.current_step = -1
        self.activation = 0

class NativeModule(Node):
    """A node with a complex node function that may perform arbitrary operations on the node net

        Native Modules encapsulate arbitrary functionality within the node net. They are written in a
        programming language (here: Python) and refer to an external resource file for the code, so it
        can be edited at runtime.
    """
    pass


# new idea: do not use classes for nodes, slots and gates, instead, make them dicts
# handlers are defined on the level of the nodenet itself
# what does the structure look like? we need constructors, destructors, executors, but no changers

STANDARD_NODETYPES = {
    "register": {
        "slots": ["gen"],
        "gates": ["gen"]
    },
    "sensor": {
        "parameters":["datasource"],
        "nodefunction": """node.gates["gen"].gatefunction(nodenet.datasources[datasource])""",
        "gates": ["gen"]
    },
    "actor": {
        "parameters":["datasource", "datatarget"],
        "nodefunction": """nodenet.datatargets[datatarget] = node.slots["gen"].activation""",
        "slots": ["gen"]
    },
    "concept": {
        "slots": ["gen"],
        "nodefunction": """for type in node.gates: node.gates[type].gatefunction(node.slots["gen"])""",
        "gates": ["gen", "por", "ret", "sub", "sur", "cat", "exp"]
    },
    "activator": {
        "slots": ["gen"],
        "parameters": ["type"],
        "nodefunction": """node.nodespace.activators[type] = node.slots["gen"].activation"""
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
        self.nodenet.data["nodetypes"][identifier] = self.nodenet.data["nodetypes"][self.data["name"]]
        del self.nodenet.data["nodetypes"][self.data["name"]]
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
        return self.data.get("parameters")

    @parameters.setter
    def parameters(self, string):
        self.data["parameters"] = string.strip()

    @property
    def nodefunction_definition(self):
        return self.data.get("nodefunction_definition")

    @nodefunction_definition.setter
    def nodefunction_definition(self, string):
        self.data["nodefunction_definition"] = string
        try:
            self.nodefunction = micropsi_core.tools.create_function(string,
                parameters = "nodenet, node, " + self.data.get('parameters', ''))
        except SyntaxError, err:
            warnings.warn("Syntax error while compiling node function.")
            self.nodefunction = micropsi_core.tools.create_function("""node.activation = 'Syntax error'""",
                parameters = "nodenet, node, " + self.data.get('parameters', ''))

    def __init__(self, name, nodenet, slots = None, gates = None, parameters = None, nodefunction = None):
        """Initializes or creates a nodetype.

        Arguments:
            name: a unique identifier for this nodetype
            nodenet: the nodenet that this nodetype is part of

        If a nodetype with the same name is already defined in the nodenet, it is overwritten. Parameters that
        are not given here will be taken from the original definition. Thus, you may use this initializer to
        set up the nodetypes after loading new nodenet data (by using it without parameters).

        Within the nodenet, the nodenet data dict stores the whole nodenet definition. The part that defines
        nodetypes is structured as follows:

            { "slots": list of slot types or None,
              "gates": list of gate types or None,
              "parameters": string of parameters to store values in or read values from
              "nodefunction": <a string that stores a sequence of python statements, and gets the node and the
                    nodenet as arguments>
            }
        """
        self.nodenet = nodenet
        if not "nodetypes" in nodenet.data: self.nodenet.data["nodetypes"] = {}
        if not name in self.nodenet.data["nodetypes"]: self.nodenet.data["nodetypes"][name] = {}
        self.data = self.nodenet.data["nodetypes"][name]
        self.data["name"] = name

        self.slots = self.data.get("slots", ["gen"]) if slots is None else slots
        self.gates = self.data.get("gates", ["gen"]) if gates is None else gates

        self.parameters = self.data.get("parameters", '') if parameters is None else parameters

        nodefunction = self.data.get("nodefunction",
            """for type in node.gates: node.gates[type].gatefunction(node.slots["gen"])"""
        ) if nodefunction is None else nodefunction

        self.nodefunction_definition = self.data.get("nodefunction",
            """for type in node.gates: node.gates[type].gatefunction(node.slots["gen"])"""
        ) if nodefunction is None else nodefunction








"""
# nodefunctions will often just change slot and gate values, but may also interact with the environment and the node net itself. Thus, we pass everything into them as parameters.

# the nodefunction gets the node passed. the node has references to the nodespace (and via the nodespace to data sources and data targets), the slots and gates, and the nodenet

    # new idea for refactoring: the node net is a hash, too. all the handling will be done in the agent class. the agent stores all efficiency stuff.


standard_nodefunctions = {
    "actor":
}

    Nodenet = Nodes, Links, Nodespaces, DataSources, DataTargets, Netfunction (+ owner, agent)
    Nodespace = Nodes, Nodespaces, Activators
    Node = id, type, Slots, Gates, Nodefunction (+ parentnodespace, )
    Slot = slottype, act, slotfunction = avg(incoming acts) --> idea: let us store all incoming activations and process them in the nodefunction
    even better: slotfunction/gatefunction is given by nodetype
    Gate = gatetype, gatefunction (params), outputfunction (act(type), amp, min, max)


even better: all persistent data is stored within the nodenet, and everything else is in classes as before! yay!
"""