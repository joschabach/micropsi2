# -*- coding: utf-8 -*-

"""
Node definition

Gate definition
Slot definition
Nodetype definition

default Nodetypes

"""

from abc import ABCMeta, abstractmethod

import warnings
import micropsi_core.tools
from .link import Link
import logging

__author__ = 'joscha'
__date__ = '09.05.12'


emptySheafElement = dict(uid="default", name="default", activation=0)


class Node(metaclass=ABCMeta):
    """
    Abstract base class for node implementations.
    """

    __nodetype_name = None
    __nodetype = None

    @property
    def data(self):
        data = {
            "uid": self.uid,
            "index": self.index,
            "name": self.name,
            "position": self.position,
            "parent_nodespace": self.parent_nodespace,
            "type": self.type,
            "parameters": self.clone_parameters(),
            "state": self.clone_state(),
            "gate_parameters": self.clone_non_default_gate_parameters(),
            "sheaves": self.clone_sheaves(),
            "activation": self.activation,
            "gate_activations": self.construct_gates_dict()
        }
        return data

    @property
    @abstractmethod
    def uid(self):
        """
        The uid of this node
        """
        pass

    @property
    @abstractmethod
    def index(self):
        """
        The index property of this node. Index properties are used for persistent sorting information.
        """
        pass

    @index.setter
    @abstractmethod
    def index(self, index):
        """
        Sets the index property of this node. Index properties are used for persistent sorting information.
        """
        pass

    @property
    @abstractmethod
    def position(self):
        """
        This node's 2D coordinates within its nodespace
        """
        # todo: persistent 2D coordinates are likely to be made non-persistent or stored elsewhere
        pass

    @position.setter
    @abstractmethod
    def position(self, position):
        """
        This node's 2D coordinates within its nodespace
        """
        # todo: persistent 2D coordinates are likely to be made non-persistent or stored elsewhere
        pass

    @property
    @abstractmethod
    def name(self):
        """
        This node's human reaable name for display purposes. Returns the UID if no human readable name has been set.
        """
        pass

    @name.setter
    @abstractmethod
    def name(self, name):
        """
        Sets this node's human reaable name for display purposes.
        """
        pass

    @property
    @abstractmethod
    def parent_nodespace(self):
        """
        The UID of this node's parent nodespace
        """
        pass

    @parent_nodespace.setter
    @abstractmethod
    def parent_nodespace(self, uid):
        """
        Sets this node's parent nodespace by UID, effectively moving from its old parent space to the new one
        """
        pass

    @property
    @abstractmethod
    def activation(self):
        """
        This node's activation property as calculated once per step by its node function
        """
        pass

    @activation.setter
    @abstractmethod
    def activation(self, activation):
        """
        Sets this node's activation property, overriding what has been calculated by the node fucntion
        """
        pass

    @property
    def type(self):
        """
        The node's type (as a string)
        """
        return self.__nodetype_name

    @property
    def nodetype(self):
        """
        The Nodetype instance for this node
        """
        return self.__nodetype

    def __init__(self, nodetype_name, nodetype):
        """
        Constructor needs the string name of this node's type, and a Nodetype instance
        """
        self.__nodetype_name = nodetype_name
        self.__nodetype = nodetype

    @abstractmethod
    def get_gate(self, type):
        """
        Returns this node's gate of the given type, or None if no such gate exists
        """
        pass

    @abstractmethod
    def set_gate_parameters(self, gate_type, parameters):
        pass

    @abstractmethod
    def clone_non_default_gate_parameters(self):
        pass


    @abstractmethod
    def get_slot(self, type):
        pass

    @abstractmethod
    def get_parameter(self, parameter):
        pass

    @abstractmethod
    def clear_parameter(self, parameter):
        pass

    @abstractmethod
    def set_parameter(self, parameter, value):
        pass

    @abstractmethod
    def set_parameters(self, parameters):
        pass

    @abstractmethod
    def clone_parameters(self):
        pass

    @abstractmethod
    def get_state(self, state_element):
        pass

    @abstractmethod
    def set_state(self, state_element, value):
        pass

    @abstractmethod
    def clone_state(self):
        pass

    @abstractmethod
    def clone_sheaves(self):
        pass

    @abstractmethod
    def node_function(self):
        """
        """
        pass


    def get_gate_types(self):
        """
        Returns the types of gates existing in this node
        """
        return list(self.nodetype.gatetypes)

    def get_slot_types(self):
        """
        Returns the types of slots existing in this node
        """
        return list(self.nodetype.slottypes)

    def get_associated_links(self):
        links = []
        for key in self.get_gate_types():
            links.extend(self.get_gate(key).get_links())
        for key in self.get_slot_types():
            links.extend(self.get_slot(key).get_links())
        return links

    def get_associated_node_uids(self):
        nodes = []
        for link in self.get_associated_links():
            if link.source_node.uid != self.uid:
                nodes.append(link.source_node.uid)
            if link.target_node.uid != self.uid:
                nodes.append(link.target_node.uid)
        return nodes

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

    def __init__(self, type, node, sheaves=None, gate_function=None, parameters=None):
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
        self.__outgoing = {}
        self.gate_function = gate_function or self.gate_function
        self.parameters = parameters
        self.monitor = None

    def get_links(self):
        return list(self.__outgoing.values())

    def _register_outgoing(self, link):
        self.__outgoing[link.uid] = link

    def _unregister_outgoing(self, link):
        del self.__outgoing[link.uid]


    def gate_function(self, input_activation, sheaf="default"):
        """This function sets the activation of the gate.

        The gate function should be called by the node function, and can be replaced by different functions
        if necessary. This default gives a linear function (input * amplification), cut off below a threshold.
        You might want to replace it with a radial basis function, for instance.
        """
        if input_activation is None:
            input_activation = 0

        # check if the current node space has an activator that would prevent the activity of this gate
        nodespace = self.node.nodenet.get_nodespace(self.node.parent_nodespace)
        if nodespace.has_activator(self.type):
            gate_factor = nodespace.get_activator_value(self.type)
        else:
            gate_factor = 1.0
        if gate_factor == 0.0:
            self.sheaves[sheaf]['activation'] = 0
            return  # if the gate is closed, we don't need to execute the gate function
            # simple linear threshold function; you might want to use a sigmoid for neural learning
        gatefunction = self.node.nodenet.get_nodespace(self.node.parent_nodespace).get_gatefunction(self.node.type,
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
        self.__incoming = {}
        self.current_step = -1
        self.sheaves = {"default": emptySheafElement.copy()}

    @property
    def activation(self):
        return self.get_activation("default")

    def get_activation(self, sheaf="default"):
        if len(self.__incoming) == 0:
            return 0
        if sheaf not in self.sheaves:
            return 0
        return self.sheaves[sheaf]['activation']

    def get_links(self):
        return list(self.__incoming.values())

    def _register_incoming(self, link):
        self.__incoming[link.uid] = link

    def _unregister_incoming(self, link):
        del self.__incoming[link.uid]


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
