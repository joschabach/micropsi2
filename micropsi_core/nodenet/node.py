# -*- coding: utf-8 -*-

"""
Node definition

Gate definition
Slot definition
Nodetype definition

default Nodetypes

"""

import warnings
import micropsi_core.tools
from .link import Link
from .netentity import NetEntity
import logging

__author__ = 'joscha'
__date__ = '09.05.12'


emptySheafElement = dict(uid="default", name="default", activation=0)


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

    __type = None

    @property
    def data(self):
        data = NetEntity.data.fget(self)
        data.update({
            "uid": self.uid,
            "type": self.type,
            "parameters": self.parameters,
            "state": self.state,
            "gate_parameters": self.gate_parameters,  # still a redundant field, get rid of it
            "sheaves": self.sheaves,
            "activation": self.activation,
            "gate_activations": self.construct_gates_dict()
        })
        return data

    @property
    def activation(self):
        return self.sheaves['default']['activation']

    @activation.setter
    def activation(self, activation):
        self.set_sheaf_activation(activation)

    def set_sheaf_activation(self, activation, sheaf="default"):
        sheaves_to_calculate = self.get_sheaves_to_calculate()
        if sheaf not in sheaves_to_calculate:
            raise "Sheaf " + sheaf + " can not be set as it hasn't been propagated to any slot"

        if activation is None:
            activation = 0

        self.sheaves[sheaf]['activation'] = float(activation)
        if len(self.nodetype.gatetypes):
            self.set_gate_activation(self.nodetype.gatetypes[0], activation, sheaf)

    @property
    def type(self):
        return self.__type

    @property
    def nodetype(self):
        return self.nodenet.get_nodetype(self.type)

    def __init__(self, nodenet, parent_nodespace, position, state=None, activation=0,
                 name="", type="Concept", uid=None, index=None, parameters=None, gate_parameters=None, gate_activations=None, **_):
        if not gate_parameters:
            gate_parameters = {}

        if uid in nodenet.nodes:
            raise KeyError("Node already exists")

        NetEntity.__init__(self, nodenet, parent_nodespace, position,
            name=name, entitytype="nodes", uid=uid, index=index)

        self.gate_parameters = {}

        self.state = {}

        self.__gates = {}
        self.__slots = {}
        self.__type = type

        self.parameters = dict((key, None) for key in self.nodetype.parameters)
        if parameters is not None:
            self.parameters.update(parameters)

        for gate_name in gate_parameters:
            for key in gate_parameters[gate_name]:
                if gate_parameters[gate_name][key] != self.nodetype.gate_defaults.get(key, None):
                    if gate_name not in self.gate_parameters:
                        self.gate_parameters[gate_name] = {}
                    self.gate_parameters[gate_name][key] = gate_parameters[gate_name][key]

        gate_parameters = self.nodetype.gate_defaults.copy()
        gate_parameters.update(self.gate_parameters)
        for gate in self.nodetype.gatetypes:
            if gate_activations is None or gate not in gate_activations:
                sheaves_to_use = None
            else:
                sheaves_to_use = gate_activations[gate]
            self.__gates[gate] = Gate(gate, self, sheaves=sheaves_to_use, gate_function=None, parameters=gate_parameters.get(gate), gate_defaults=self.nodetype.gate_defaults[gate])
        for slot in self.nodetype.slottypes:
            self.__slots[slot] = Slot(slot, self)
        if state:
            self.state = state
        nodenet.nodes[self.uid] = self
        self.sheaves = {"default": emptySheafElement.copy()}

        self.activation = 0

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

            sheaves_to_calculate = self.get_sheaves_to_calculate()

            # find node activation to carry over
            node_activation_to_carry_over = {}
            for id in self.sheaves:
                if id in sheaves_to_calculate:
                    node_activation_to_carry_over[id] = self.sheaves[id]

            # clear activation states
            for gatename in self.get_gate_types():
                gate = self.get_gate(gatename)
                gate.sheaves = {}
            self.sheaves = {}

            # calculate activation states for all open sheaves
            for sheaf_id in sheaves_to_calculate:

                # prepare sheaves
                for gatename in self.get_gate_types():
                    gate = self.get_gate(gatename)
                    gate.sheaves[sheaf_id] = sheaves_to_calculate[sheaf_id].copy()
                if sheaf_id in node_activation_to_carry_over:
                    self.sheaves[sheaf_id] = node_activation_to_carry_over[sheaf_id].copy()
                    self.set_sheaf_activation(node_activation_to_carry_over[sheaf_id]['activation'], sheaf_id)
                else:
                    self.sheaves[sheaf_id] = sheaves_to_calculate[sheaf_id].copy()
                    self.set_sheaf_activation(0, sheaf_id)

                # and actually calculate new values for them
                try:
                    self.nodetype.nodefunction(netapi=self.nodenet.netapi, node=self, sheaf=sheaf_id, **self.parameters)
                except Exception:
                    self.nodenet.is_active = False
                    self.activation = -1
                    raise
        else:
            # default node function (only using the "default" sheaf)
            if len(self.get_slot_types()):
                self.activation = sum([self.get_slot(slot).activation for slot in self.get_slot_types()])
                if len(self.get_gate_types()):
                    for gatetype in self.get_gate_types():
                        self.get_gate(gatetype).gate_function(self.activation)

    def get_gate(self, gatename):
        try:
            return self.__gates[gatename]
        except KeyError:
            return None

    def get_slot(self, slotname):
        try:
            return self.__slots[slotname]
        except KeyError:
            return None

    def get_gate_parameters(self):
        """Looks into the gates and returns gate parameters if these are defined"""
        gate_parameters = {}
        for gatetype in self.get_gate_types():
            if self.get_gate(gatetype).parameters:
                gate_parameters[gatetype] = self.get_gate(gatetype).parameters
        if len(gate_parameters):
            return gate_parameters
        else:
            return None

    def set_gate_activation(self, gatetype, activation, sheaf="default"):
        """ sets the activation of the given gate"""
        activation = float(activation)
        gate = self.get_gate(gatetype)
        if gate is not None:
            gate.sheaves[sheaf]['activation'] = activation

    def get_associated_links(self):
        links = []
        for key in self.get_gate_types():
            links.extend(self.get_gate(key).outgoing.values())
        for key in self.get_slot_types():
            links.extend(self.get_slot(key).incoming.values())
        return links

    def get_associated_node_uids(self):
        nodes = []
        for link in self.get_associated_links():
            if link.source_node.uid != self.uid:
                nodes.append(link.source_node.uid)
            if link.target_node.uid != self.uid:
                nodes.append(link.target_node.uid)
        return nodes

    def get_sheaves_to_calculate(self):
        sheaves_to_calculate = {}
        for slotname in self.get_slot_types():
            for uid in self.get_slot(slotname).sheaves:
                sheaves_to_calculate[uid] = self.get_slot(slotname).sheaves[uid].copy()
        if 'default' not in sheaves_to_calculate:
            sheaves_to_calculate['default'] = emptySheafElement.copy()
        return sheaves_to_calculate

    def set_gate_parameters(self, gate_type, parameters):
        if self.gate_parameters is None:
            self.gate_parameters = {}
        for parameter, value in parameters.items():
            if parameter in Nodetype.GATE_DEFAULTS:
                try:
                    value = float(value)
                except:
                    raise Exception("Standard gate parameters must be numeric")
                if value != Nodetype.GATE_DEFAULTS[parameter]:
                    if gate_type not in self.parameters:
                        self.gate_parameters[gate_type] = {}
                    self.gate_parameters[gate_type][parameter] = value
            self.get_gate(gate_type).parameters[parameter] = value

    def reset_slots(self):
        for slottype in self.get_slot_types():
            self.get_slot(slottype).sheaves = {"default": emptySheafElement.copy()}

    def get_parameter(self, parameter):
        if parameter in self.parameters:
            return self.parameters[parameter]
        else:
            return None

    def clear_parameter(self, parameter):
        if parameter in self.parameters:
            if parameter not in self.nodetype.parameters:
                del self.parameters[parameter]
            else:
                self.parameters[parameter] = None

    def set_parameter(self, parameter, value):
        self.parameters[parameter] = value

    def set_parameters(self, parameters):
        for key in parameters:
            self.set_parameter(key, parameters[key])

    def get_state(self, state_element):
        if state_element in self.state:
            return self.state[state_element]
        else:
            return None

    def set_state(self, state_element, value):
        self.state[state_element] = value

    def link(self, gate_name, target_node_uid, slot_name, weight=1, certainty=1):
        """Ensures a link exists with the given parameters and returns it
           Only one link between a node/gate and a node/slot can exist, its parameters will be updated with the
           given parameters if a link existed prior to the call of this method
           Will return None if no such link can be created.
        """

        if target_node_uid not in self.nodenet.nodes:
            return None

        target = self.nodenet.nodes[target_node_uid]

        if slot_name not in target.get_slot_types():
            return None

        gate = self.get_gate(gate_name)
        if gate is None:
            return None
        link = None
        for candidate_uid, candidate in gate.outgoing.items():
            if candidate.target_node.uid == target.uid and candidate.target_slot == slot_name:
                link = candidate
                break
        if link is None:
            link = Link(self, gate_name, target, slot_name)

        link.weight = weight
        link.certainty = certainty
        return link

    def unlink_completely(self):
        """Deletes all links originating from this node or ending at this node"""
        links_to_delete = set()
        for gate_name_candidate in self.get_gate_types():
            for link_uid_candidate, link_candidate in self.get_gate(gate_name_candidate).outgoing.items():
                links_to_delete.add(link_candidate)
        for slot_name_candidate in self.get_slot_types():
            for link_uid_candidate, link_candidate in self.get_slot(slot_name_candidate).incoming.items():
                links_to_delete.add(link_candidate)
        for link in links_to_delete:
            link.remove()

    def unlink(self, gate_name=None, target_node_uid=None, slot_name=None):
        """Deletes all links originating from this node or ending at this node"""
        links_to_delete = set()
        for gate_name_candidate in self.get_gate_types():
            if gate_name is None or gate_name == gate_name_candidate:
                for link_uid_candidate, link_candidate in self.get_gate(gate_name_candidate).outgoing.items():
                    if target_node_uid is None or target_node_uid == link_candidate.target_node.uid:
                        if slot_name is None or slot_name == link_candidate.target_slot.type:
                            links_to_delete.add(link_candidate)
        for link in links_to_delete:
            link.remove()

    def get_gate_types(self):
        return self.__gates.keys()

    def get_slot_types(self):
        return self.__slots.keys()

    def construct_gates_dict(self):
        data = {}
        for gate_name in self.get_gate_types():
            data[gate_name] = self.get_gate(gate_name).sheaves
        return data


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

    @property
    def activation(self):
        return self.sheaves['default']['activation']

    @activation.setter
    def activation(self, activation):
        self.sheaves['default']['activation'] = activation

    def __init__(self, type, node, sheaves=None, gate_function=None, parameters=None, gate_defaults=None):
        """create a gate.

        Parameters:
            type: a string that refers to a node type
            node: the parent node
            parameters: an optional dictionary of parameters for the gate function
        """
        self.type = type
        self.node = node
        if sheaves is None:
            self.sheaves = {"default": emptySheafElement.copy()}
        else:
            self.sheaves = {}
            for key in sheaves:
                self.sheaves[key] = dict(uid=sheaves[key]['uid'], name=sheaves[key]['name'], activation=sheaves[key]['activation'])
        self.outgoing = {}
        self.gate_function = gate_function or self.gate_function
        self.parameters = {}
        if gate_defaults is not None:
            self.parameters = gate_defaults.copy()
        if parameters is not None:
            for key in parameters:
                if key in Nodetype.GATE_DEFAULTS:
                    try:
                        self.parameters[key] = float(parameters[key])
                    except:
                        logging.getLogger('nodenet').warn('Invalid gate parameter value for gate %s, param %s, node %s' % (type, key, node.uid))
                        self.parameters[key] = Nodetype.GATE_DEFAULTS.get(key, 0)
                else:
                    self.parameters[key] = float(parameters[key])
        self.monitor = None

    def gate_function(self, input_activation, sheaf="default"):
        """This function sets the activation of the gate.

        The gate function should be called by the node function, and can be replaced by different functions
        if necessary. This default gives a linear function (input * amplification), cut off below a threshold.
        You might want to replace it with a radial basis function, for instance.
        """
        if input_activation is None:
            input_activation = 0

        # check if the current node space has an activator that would prevent the activity of this gate
        nodespace = self.node.nodenet.nodespaces[self.node.parent_nodespace]
        if self.type in nodespace.activators:
            gate_factor = nodespace.activators[self.type]
        else:
            gate_factor = 1.0
        if gate_factor == 0.0:
            self.sheaves[sheaf]['activation'] = 0
            return  # if the gate is closed, we don't need to execute the gate function
            # simple linear threshold function; you might want to use a sigmoid for neural learning
        gatefunction = self.node.nodenet.nodespaces[self.node.parent_nodespace].get_gatefunction(self.node.type,
            self.type)
        if gatefunction:
            activation = gatefunction(input_activation, self.parameters.get('rho', 0), self.parameters.get('theta', 0))
        else:
            activation = input_activation

        if activation * gate_factor < self.parameters['threshold']:
            activation = 0
        else:
            activation = activation * self.parameters["amplification"] * gate_factor

        # if self.parameters["decay"]:  # let activation decay gradually
        #     if activation < 0:
        #         activation = min(activation, self.activation * (1 - self.parameters["decay"]))
        #     else:
        #         activation = max(activation, self.activation * (1 - self.parameters["decay"]))

        self.sheaves[sheaf]['activation'] = min(self.parameters["maximum"], max(self.parameters["minimum"], activation))

    def open_sheaf(self, input_activation, sheaf="default"):
        """This function opens a new sheaf and calls the gate function for the newly opened sheaf
        """
        if sheaf is "default":
            sheaf_uid_prefix = "default" + "-"
            sheaf_name_prefix = ""
        else:
            sheaf_uid_prefix = sheaf + "-"
            sheaf_name_prefix = self.sheaves[sheaf].name + "-"

        new_sheaf = dict(uid=sheaf_uid_prefix + self.node.uid, name=sheaf_name_prefix + self.node.name, activation=0)
        self.sheaves[new_sheaf['uid']] = new_sheaf

        self.gate_function(input_activation, new_sheaf['uid'])


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
        self.sheaves = {"default": emptySheafElement.copy()}

    @property
    def activation(self):
        return self.get_activation("default")

    def get_activation(self, sheaf="default"):
        if len(self.incoming) == 0:
            return 0
        if sheaf not in self.sheaves:
            return 0
        return self.sheaves[sheaf]['activation']


STANDARD_NODETYPES = {
    "Nodespace": {
        "name": "Nodespace"
    },

    "Comment": {
        "name": "Comment",
        "symbol": "#",
        'parameters': ['comment'],
        "shape": "Rectangle"
    },

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
    "Script": {
        "name": "Script",
        "slottypes": ["gen", "por", "ret", "sub", "sur"],
        "nodefunction_name": "script",
        "gatetypes": ["gen", "por", "ret", "sub", "sur", "cat", "exp", "sym", "ref"],
        "gate_defaults": {
            "por": {
                "threshold": -1
            },
            "ret": {
                "threshold": -1
            },
            "sub": {
                "threshold": -1
            },
            "sur": {
                "threshold": -1
            }
        }
    },
    "Pipe": {
        "name": "Pipe",
        "slottypes": ["gen", "por", "ret", "sub", "sur", "cat", "exp"],
        "nodefunction_name": "pipe",
        "gatetypes": ["gen", "por", "ret", "sub", "sur", "cat", "exp"],
        "gate_defaults": {
            "gen": {
                "minimum": -100,
                "maximum": 100,
                "threshold": -100,
                "spreadsheaves": False
            },
            "por": {
                "minimum": -100,
                "maximum": 100,
                "threshold": -100,
                "spreadsheaves": False
            },
            "ret": {
                "minimum": -100,
                "maximum": 100,
                "threshold": -100,
                "spreadsheaves": False
            },
            "sub": {
                "minimum": -100,
                "maximum": 100,
                "threshold": -100,
                "spreadsheaves": True
            },
            "sur": {
                "minimum": -100,
                "maximum": 100,
                "threshold": -100,
                "spreadsheaves": False
            },
            "cat": {
                "minimum": -100,
                "maximum": 100,
                "threshold": -100,
                "spreadsheaves": True
            },
            "exp": {
                "minimum": -100,
                "maximum": 100,
                "threshold": -100,
                "spreadsheaves": False
            }
        },
        'symbol': 'πp',
        'shape': 'Rectangle'
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

    GATE_DEFAULTS = {
        "minimum": -1,
        "maximum": 1,
        "certainty": 1,
        "amplification": 1,
        "threshold": 0,
        "decay": 0,
        "theta": 0,
        "rho": 0,
        "spreadsheaves": False
    }

    _parameters = []
    _nodefunction_definition = None
    _nodefunction_name = None

    @property
    def data(self):
        data = {
            "name": self.name,
            "slottypes": self.slottypes,
            "gatetypes": self.gatetypes,
            "parameters": self.parameters
        }
        return data

    @property
    def parameters(self):
        return self._parameters

    @parameters.setter
    def parameters(self, parameters):
        self._parameters = parameters
        self.nodefunction = self._nodefunction_definition  # update nodefunction

    @property
    def nodefunction_definition(self):
        return self._nodefunction_definition

    @nodefunction_definition.setter
    def nodefunction_definition(self, nodefunction_definition):
        self._nodefunction_definition = nodefunction_definition
        args = ','.join(self.parameters).strip(',')
        try:
            self.nodefunction = micropsi_core.tools.create_function(nodefunction_definition,
                parameters="nodenet, node, " + args)
        except SyntaxError as err:
            warnings.warn("Syntax error while compiling node function: %s", str(err))
            raise err

    @property
    def nodefunction_name(self):
        return self._nodefunction_name

    @nodefunction_name.setter
    def nodefunction_name(self, nodefunction_name):
        self._nodefunction_name = nodefunction_name
        try:
            from micropsi_core.nodenet import nodefunctions
            if hasattr(nodefunctions, nodefunction_name):
                self.nodefunction = getattr(nodefunctions, nodefunction_name)
            else:
                import nodefunctions as custom_nodefunctions
                self.nodefunction = getattr(custom_nodefunctions, nodefunction_name)

        except (ImportError, AttributeError) as err:
            warnings.warn("Import error while importing node function: nodefunctions.%s %s" % (nodefunction_name, err))
            raise err

    def reload_nodefunction(self):
        from micropsi_core.nodenet import nodefunctions
        if self.nodefunction_name and not self.nodefunction_definition and not hasattr(nodefunctions, self.nodefunction_name):
            import nodefunctions as custom_nodefunctions
            from imp import reload
            reload(custom_nodefunctions)
            self.nodefunction = getattr(custom_nodefunctions, self.nodefunction_name)

    def __init__(self, name, nodenet, slottypes=None, gatetypes=None, parameters=None,
                 nodefunction_definition=None, nodefunction_name=None, parameter_values=None, gate_defaults=None,
                 symbol=None, shape=None):
        """Initializes or creates a nodetype.

        Arguments:
            name: a unique identifier for this nodetype
            nodenet: the nodenet that this nodetype is part of

        If a nodetype with the same name is already defined in the nodenet, it is overwritten. Parameters that
        are not given here will be taken from the original definition. Thus, you may use this initializer to
        set up the nodetypes after loading new nodenet state (by using it without parameters).
        """
        self.name = name
        self.slottypes = slottypes or {}
        self.gatetypes = gatetypes or {}

        self.gate_defaults = {}
        for g in self.gatetypes:
            self.gate_defaults[g] = Nodetype.GATE_DEFAULTS.copy()

        if gate_defaults is not None:
            for g in gate_defaults:
                for key in gate_defaults[g]:
                    if g not in self.gate_defaults:
                        raise Exception("Invalid gate default value for nodetype %s: Gate %s not found" % (name, g))
                    self.gate_defaults[g][key] = gate_defaults[g][key]

        self.parameters = parameters or {}
        self.parameter_values = parameter_values or {}

        if nodefunction_definition:
            self.nodefunction_definition = nodefunction_definition
        elif nodefunction_name:
            self.nodefunction_name = nodefunction_name
        else:
            self.nodefunction = None
