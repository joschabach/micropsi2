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
            "gate_parameters": self.get_gate_parameters(),
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
        pass  # pragma: no cover

    @property
    @abstractmethod
    def index(self):
        """
        The index property of this node. Index properties are used for persistent sorting information.
        """
        pass  # pragma: no cover

    @index.setter
    @abstractmethod
    def index(self, index):
        """
        Sets the index property of this node. Index properties are used for persistent sorting information.
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def position(self):
        """
        This node's 2D coordinates within its nodespace
        """
        # todo: persistent 2D coordinates are likely to be made non-persistent or stored elsewhere
        pass  # pragma: no cover

    @position.setter
    @abstractmethod
    def position(self, position):
        """
        This node's 2D coordinates within its nodespace
        """
        # todo: persistent 2D coordinates are likely to be made non-persistent or stored elsewhere
        pass  # pragma: no cover

    @property
    @abstractmethod
    def name(self):
        """
        This node's human readable name for display purposes. Returns the UID if no human readable name has been set.
        """
        pass  # pragma: no cover

    @name.setter
    @abstractmethod
    def name(self, name):
        """
        Sets this node's human readable name for display purposes.
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def parent_nodespace(self):
        """
        The UID of this node's parent nodespace
        """
        pass  # pragma: no cover

    @parent_nodespace.setter
    @abstractmethod
    def parent_nodespace(self, uid):
        """
        Sets this node's parent nodespace by UID, effectively moving from its old parent space to the new one
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def activation(self):
        """
        This node's activation property ('default' sheaf) as calculated once per step by its node function
        """
        pass  # pragma: no cover

    #@property
    #@abstractmethod
    #def activations(self):
    #    """
    #    This node's activation properties (dict of all sheaves) as calculated once per step by its node function
    #    """

    @property
    @abstractmethod
    def activations(self):
        """
        Returns a copy of the nodes's activations (all sheaves)
        Changes to the returned dict will not affect the node
        """
        pass  # pragma: no cover

    @activation.setter
    @abstractmethod
    def activation(self, activation):
        """
        Sets this node's activation property ('default' sheaf), overriding what has been calculated by the node function
        """
        pass  # pragma: no cover

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
        pass  # pragma: no cover

    @abstractmethod
    def set_gate_parameter(self, gate_type, parameter, value):
        """
        Sets the given gate parameter to the given value
        """
        pass  # pragma: no cover

    @abstractmethod
    def clone_non_default_gate_parameters(self, gate_type):
        """
        Returns a copy of all gate parameters set to a non-default value.
        Write access to this dict will not affect the node.
        """
        pass  # pragma: no cover

    @abstractmethod
    def get_slot(self, type):
        """
        Returns the slot of the given type or none if no such slot exists
        """
        pass  # pragma: no cover

    @abstractmethod
    def get_parameter(self, parameter):
        """
        Returns the value of a node parameter of None if the parameter is not set.
        Parameters are used to change what a node does and do typically not change between net steps.
        An example is the "type" parameter of directional activators that configures the activator to control
        the gates of type "type"
        """
        pass  # pragma: no cover

    @abstractmethod
    def set_parameter(self, parameter, value):
        """
        Changes the value of the given parameter.
        Parameters are used to change what a node does and do typically not change between net steps.
        An example is the "type" parameter of directional activators that configures the activator to control
        the gates of type "type"
        """
        pass  # pragma: no cover

    @abstractmethod
    def clone_parameters(self):
        """
        Returns a copy of this node's parameter set.
        Write access to this dict will not affect the node.
        Parameters are used to change what a node does and do typically not change between net steps.
        An example is the "type" parameter of directional activators that configures the activator to control
        the gates of type "type"
        """
        pass  # pragma: no cover

    @abstractmethod
    def get_state(self, state):
        """
        Returns the value of the given state.
        Node state is runtime-information that can change between net steps.
        A typical use is native modules "attaching" a bit of information to a node for later retrieval.
        Node states are not formally required by the node net specification. They exist for convenience reasons only.
        """
        pass  # pragma: no cover

    @abstractmethod
    def set_state(self, state, value):
        """
        Sets the value of a given state.
        Node state is runtime-information that can change between net steps.
        A typical use is native modules "attaching" a bit of information to a node for later retrieval.
        Node states are not formally required by the node net specification. They exist for convenience reasons only.
        """
        pass  # pragma: no cover

    @abstractmethod
    def clone_state(self):
        """
        Returns a copy of the node's state.
        Write access to this dict will not affect the node.
        Node state is runtime-information that can change between net steps.
        A typical use is native modules "attaching" a bit of information to a node for later retrieval.
        Node states are not formally required by the node net specification. They exist for convenience reasons only.
        """
        pass  # pragma: no cover

    @abstractmethod
    def clone_sheaves(self):
        """
        Returns a copy of the activation values present in the node.
        Note that this is about node activation, not gate activation (gates have their own sheaves).
        Write access to this dict will not affect the node.
        """
        pass  # pragma: no cover

    @abstractmethod
    def node_function(self):
        """
        The node function of the node, called after activation has been propagated to the node's slots.
        This method is expected to set the node's activation(s) and all of the gates' activations by calling the
        gate_function of all gates.
        Implementations can either directly implement this method based on the type of the node, or implement some
        sort of indirection mechanism that selects the code to be executed.
        For native modules (nodes with non-standard node_functions) that can be reloaded at runtime, this is a must.
        """
        pass  # pragma: no cover

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
            data[gate_name] = self.get_gate(gate_name).clone_sheaves()
        return data


class Gate(metaclass=ABCMeta):
    """
    Activation outlet of nodes, where links (connected to slots on the other side) originate.
    Gate activations are set by the node's node_function through calling gate_function for all of their gates.
    """

    @property
    @abstractmethod
    def type(self):
        """
        Returns the type of the gate (as a string)
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def node(self):
        """
        Returns the Node object that this gate belongs to
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def empty(self):
        """
        Returns true if the gate has no links
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def activation(self):
        """
        Returns the gate's activation ('default' sheaf)
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def activations(self):
        """
        Returns a copy of the gate's activations (all sheaves)
        Changes to the returned dict will not affect the gate
        """
        pass  # pragma: no cover

    @abstractmethod
    def get_links(self):
        """
        Returns a list of Link objects originating from this gate
        """
        pass  # pragma: no cover

    @abstractmethod
    def get_parameter(self, parameter):
        """
        Returns the value of the given parameter or none if the parameter is not set.
        Note that the returned value may be a default inherited from gate parameter defaults as defined in Nodetype
        """
        pass  # pragma: no cover

    @abstractmethod
    def clone_sheaves(self):
        """
        Returns a copy of the activation values present in the gate.
        Write access to this dict will not affect the gate.
        """
        pass  # pragma: no cover

    @abstractmethod
    def gate_function(self, input_activation, sheaf="default"):
        """
        This function sets the activation of the gate.
        This only needs to be implemented if the reference implementation for the node functions from
        nodefunctions.py is being used.

        Alternative implementations are free to calculate gate activation values in node functions directly and
        can pass on the implementation of this method.

        The default gate function should be linear (input * amplification) if over the threshold parameter, plus
        band-passed by the min and max parameters.

        Implementations should allow to define alternative gate functions on a per-nodespace basis, i.e. all
        gates of nodes in a given nodespace should use the same gate function.
        """
        pass  # pragma: no cover

    @abstractmethod
    def open_sheaf(self, input_activation, sheaf="default"):
        """
        This function opens a new sheaf and calls gate_function function for the newly opened sheaf.
        This only needs to be implemented if the reference implementation for the node functions from
        nodefunctions.py is being used.

        Alternative implementations are free to handle sheaves in the node functions directly and
        can pass on the implementation of this method.
        """
        pass  # pragma: no cover


class Slot(metaclass=ABCMeta):
    """
    Activation intake for nodes. Nodes may have many slots, in which links terminate.
    Slot activations are set by the node net's activation propagation logic. They are immediately read (in the same
    net step by node functions.)
    """

    @property
    @abstractmethod
    def type(self):
        """
        Returns the type of the slot (as a string)
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def node(self):
        """
        Returns the Node object that this slot belongs to
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def empty(self):
        """
        Returns true if the slot has no links
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def activation(self):
        """
        Returns the activation in this slot ('default' sheaf)
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def activations(self):
        """
        Returns a copy of the slots's activations (all sheaves)
        Changes to the returned dict will not affect the gate
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def get_activation(self, sheaf="default"):
        """
        Returns the activation in this slot for the given sheaf.
        Will return the activation in the 'default' sheaf if the sheaf does not exist
        """
        pass  # pragma: no cover

    @abstractmethod
    def get_links(self):
        """
        Returns a list of Link objects terminating at this slot
        """
        pass  # pragma: no cover


class Nodetype(object):
    """Every node has a type, which is defined by its slot types, gate types, its node function and a list of
    node parameteres."""

    GATE_DEFAULTS = {
        "minimum": -1,
        "maximum": 1,
        "certainty": 1,
        "amplification": 1,
        "threshold": -1,
        "decay": 0,
        "theta": 0,
        "rho": 0,
        "spreadsheaves": 0
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
