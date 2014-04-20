# -*- coding: utf-8 -*-

"""
Node definition

Gate definition
Slot definition
Nodetype definition

default Nodetypes

"""

import json
import warnings
import micropsi_core.tools
from .netentity import NetEntity

__author__ = 'joscha'
__date__ = '09.05.12'

class SheafElement:
    def __init__(self, uid="default", name="default", oomph=0):
        self.uid = uid
        self.name = name
        self.oomph = oomph

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
        return self.data['activation']

    @activation.setter
    def activation(self, activation):
        activation = float(activation)
        self.data['activation'] = activation
        if len(self.gates) > 0:
            self.gates['gen'].sheaves['default'].oomph = activation
            self.report_gate_activation('gen', self.gates['gen'].sheaves['default'])

    @property
    def type(self):
        return self.data.get("type")

    @property
    def parameters(self):
        return self.data.get("parameters", {})

    @parameters.setter
    def parameters(self, dictionary):
        if self.data["type"] == "Native":
            self.nodetype.parameters = list(dictionary.keys())
        self.data["parameters"] = dictionary

    @property
    def state(self):
        return self.data.get("state", None)

    @state.setter
    def state(self, state):
        self.data['state'] = state

    def __init__(self, nodenet, parent_nodespace, position, state=None, activation=0,
                 name="", type="Concept", uid=None, index=None, parameters=None, gate_parameters=None, **_):
        if not gate_parameters:
            gate_parameters = {}

        if uid in nodenet.nodes:
            raise KeyError("Node already exists")

        NetEntity.__init__(self, nodenet, parent_nodespace, position,
            name=name, entitytype="nodes", uid=uid, index=index)

        self.gates = {}
        self.slots = {}
        self.data["type"] = type
        self.nodetype = None

        self.nodetype = self.nodenet.nodetypes[type]
        self.parameters = dict((key, None) for key in self.nodetype.parameters) if parameters is None else parameters
        for gate in self.nodetype.gatetypes:
            self.gates[gate] = Gate(gate, self, gate_function=None, parameters=gate_parameters.get(gate), gate_defaults=self.nodetype.gate_defaults[gate])
        for slot in self.nodetype.slottypes:
            self.slots[slot] = Slot(slot, self)
        if state:
            self.state = state
            # TODO: @doik: before, you explicitly added the state to nodenet.nodes[uid], too (in Runtime). Any reason?
        nodenet.nodes[self.uid] = self
        self.activation = activation

    def get_gate_parameters(self):
        """Looks into the gates and returns gate parameters if these are defined"""
        gate_parameters = {}
        for gate in self.gates:
            if self.gates[gate].parameters:
                gate_parameters[gate] = self.gates[gate].parameters
        if len(gate_parameters):
            return gate_parameters
        else:
            return None

    def node_function(self):
        """Called whenever the node is activated or active.

        In different node types, different node functions may be used, i.e. override this one.
        Generally, a node function must process the slot activations and call each gate function with
        the result of the slot activations.

        Metaphorically speaking, the node function is the soma of a MicroPsi neuron. It reacts to
        incoming activations in an arbitrarily specific way, and may then excite the outgoing dendrites (gates),
        which transmit activation to other neurons with adaptive synaptic strengths (link weights).
        """

        # call nodefunction of my node type
        if self.nodetype and self.nodetype.nodefunction is not None:
            try:
                self.nodetype.nodefunction(nodenet=self.nodenet, node=self, **self.parameters)
            except SyntaxError as err:
                warnings.warn("Syntax error during node execution: %s" % err.message)
                self.data["activation"] = "Syntax error"
            except TypeError as err:
                warnings.warn("Type error during node execution: %s" % err.message)
                self.data["activation"] = "Parameter mismatch"
            return

        # default node function
        if len(self.slots):
            self.activation = sum([self.slots[slot].activation for slot in self.slots])
            if len(self.gates):
                for type, gate in self.gates.items():
                    gate.gate_function(self.activation)


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

    def report_gate_activation(self, gate_type, sheafelement):
        if 'gate_activations' not in self.data:
            self.data['gate_activations'] = {}
        if gate_type not in self.data['gate_activations']:
            self.data['gate_activations'][gate_type] = {}
        if sheafelement.uid not in self.data['gate_activations'][gate_type]:
            self.data['gate_activations'][gate_type][sheafelement.uid] = {}
        self.data['gate_activations'][gate_type][sheafelement.uid] = {"uid":sheafelement.uid, "name":sheafelement.name, "oomph":sheafelement.oomph}

    def reset_slots(self):
        for slot in self.slots.keys():
            self.slots[slot].sheaves = {"default": SheafElement()}

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

    def __init__(self, type, node, gate_function=None, parameters=None, gate_defaults=None):
        """create a gate.

        Parameters:
            type: a string that refers to a node type
            node: the parent node
            parameters: an optional dictionary of parameters for the gate function
        """
        self.type = type
        self.node = node
        self.sheaves = {"default" : SheafElement()}
        self.node.report_gate_activation(self.type, self.sheaves['default'])
        self.outgoing = {}
        self.gate_function = gate_function or self.gate_function
        self.parameters = {}
        if gate_defaults is not None:
            self.parameters = gate_defaults.copy()
        if parameters is not None:
            for key in parameters:
                if key in self.parameters:
                    self.parameters[key] = float(parameters[key])
                else:
                    self.parameters[key] = parameters[key]
        self.monitor = None

    def gate_function(self, input_activation, sheaf="default"):
        """This function sets the activation of the gate.

        The gate function should be called by the node function, and can be replaced by different functions
        if necessary. This default gives a linear function (input * amplification), cut off below a threshold.
        You might want to replace it with a radial basis function, for instance.
        """

        # check if the current node space has an activator that would prevent the activity of this gate
        nodespace = self.node.nodenet.nodespaces[self.node.parent_nodespace]
        if self.type in nodespace.activators:
            gate_factor = nodespace.activators[self.type]
        else:
            gate_factor = 1.0
        if gate_factor == 0.0:
            self.sheaves[sheaf].oomph = 0
            self.node.report_gate_activation(self.type, self.sheaves[sheaf])
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

        self.sheaves[sheaf].oomph = min(self.parameters["maximum"], max(self.parameters["minimum"], activation))
        self.node.report_gate_activation(self.type, self.sheaves[sheaf])


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
        self.sheaves = {"default": SheafElement()}

    @property
    def activation(self, sheaf="default"):
        if len(self.incoming) == 0:
            return 0;
        return self.sheaves[sheaf].oomph

    @property
    def voted_activation(self, sheaf="default"):
        if len(self.incoming) == 0:
            return 0;
        return self.sheaves[sheaf].oomph / len(self.incoming)


STANDARD_NODETYPES = {
    "Register": {
        "name": "Register",
        "slottypes": ["gen"],
        "nodefunction_name": "register",
        "gatetypes": ["gen"]
    },
    "Sensor": {
        "name": "Sensor",
        "parameters": ["datasource"],
        "nodefunction_name": "sensor",
        "gatetypes": ["gen"]
    },
    "Actor": {
        "name": "Actor",
        "parameters": ["datatarget"],
        "nodefunction_name": "actor",
        "slottypes": ["gen"],
        "gatetypes": ["gen"]
    },
    "Concept": {
        "name": "Concept",
        "slottypes": ["gen"],
        "nodefunction_name": "concept",
        "gatetypes": ["gen", "por", "ret", "sub", "sur", "cat", "exp", "sym", "ref"]
    },
    "Pipe": {
        "name": "Pipe",
        "slottypes": ["gen", "por", "ret", "sub", "sur"],
        "nodefunction_name": "pipe",
        "gatetypes": ["gen", "por", "ret", "sub", "sur"],
        "gate_defaults": {
            "gen": {
                "minimum": -100,
                "maximum": 100,
                "threshold": -100
            },
            "por": {
                "minimum": -100,
                "maximum": 100,
                "threshold": -100
            },
            "ret": {
                "minimum": -100,
                "maximum": 100,
                "threshold": -100
            },
            "sub": {
                "minimum": -100,
                "maximum": 100,
                "threshold": -100
            },
            "sur": {
                "minimum": -100,
                "maximum": 100,
                "threshold": -100
            }
        }
    },
    "Label": {
        "name": "Label",
        "slottypes": ["gen"],
        "nodefunction_name": "label",
        "gatetypes": ["sym", "ref"]
    },
    "Event": {
        "name": "Event",
        "parameters": ["time"],
        "slottypes": ["gen"],
        "gatetypes": ["gen", "por", "ret", "sub", "sur", "cat", "exp", "sym"],
        "nodefunction_name": "event",
        # TODO: this needs to juggle the states
        "states": ['suggested', 'rejected', 'commited', 'scheduled', 'active', 'overdue', 'active overdue', 'dropped',
                   'failed', 'completed']
    },
    "Activator": {
        "name": "Activator",
        "slottypes": ["gen"],
        "parameters": ["type"],
        "parameter_values": {"type": ["gen", "por", "ret", "sub", "sur", "cat", "exp", "sym", "ref"]},
        "nodefunction_name": "activator"
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
        except SyntaxError as err:
            warnings.warn("Syntax error while compiling node function: %s", err.message)
            self.nodefunction = micropsi_core.tools.create_function("""node.activation = 'Syntax error'""",
                parameters="nodenet, node, " + args)

    @property
    def nodefunction_name(self):
        return self.data.get("nodefunction_name")

    @nodefunction_name.setter
    def nodefunction_name(self, name):
        self.data["nodefunction_name"] = name
        try:
            from . import nodefunctions
            self.nodefunction = getattr(nodefunctions, name)
        except (ImportError, AttributeError) as err:
            warnings.warn("Import error while importing node function: nodefunctions.%s" % (name))
            self.nodefunction = micropsi_core.tools.create_function("""node.activation = 'Syntax error'""",
                parameters="nodenet, node")

    def __init__(self, name, nodenet, slottypes=None, gatetypes=None, states=None, parameters=None,
                 nodefunction_definition=None, nodefunction_name=None, parameter_values=None, gate_defaults=None):
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

        self.gate_defaults = {}
        for g in self.gatetypes:
            self.gate_defaults[g] = {
                "minimum": -1,
                "maximum": 1,
                "certainty": 1,
                "amplification": 1,
                "threshold": 0,
                "decay": 0
            }

        gate_defaults = self.data.get("gate_defaults") if gate_defaults is None else gate_defaults
        if gate_defaults is not None:
            for g in gate_defaults:
                for key in gate_defaults[g]:
                    self.gate_defaults[g][key] = gate_defaults[g][key]

        self.parameters = self.data.get("parameters", []) if parameters is None else parameters
        self.parameter_values = self.data.get("parameter_values", []) if parameter_values is None else parameter_values

        if nodefunction_definition:
            self.nodefunction_definition = nodefunction_definition
        elif nodefunction_name:
            self.nodefunction_name = nodefunction_name
        else:
            self.nodefunction = None
