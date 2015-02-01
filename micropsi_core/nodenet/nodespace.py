# -*- coding: utf-8 -*-
"""
Nodespace definition
"""

from abc import ABCMeta, abstractmethod

__author__ = 'joscha'
__date__ = '09.05.12'


class Nodespace(metaclass=ABCMeta):
    """
    A container for Nodes and Nodespaces.
    All Nodes and Nodespaces have exactly one parent nodespace, except for the 'Root' nodespace, whose
    parent nodespace is None.

    Nodespaces define for their direct children nodes:
    - the gate function per gate type (if no gate function is set for a gate type, the default linear gate function
        will be used
    - the scope for directional activators

    gate functions and directional activator scope are not heritable.
    """

    __gatefunction_strings = {}

    @property
    def data(self):
        data = {
            "uid": self.uid,
            "index": self.index,
            "name": self.name,
            "position": self.position,
            "parent_nodespace": self.parent_nodespace,
            "gatefunctions": self.__gatefunction_strings
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
        This nodespace's human reaable name for display purposes. Returns the UID if no human readable name has been set.
        """
        pass  # pragma: no cover

    @name.setter
    @abstractmethod
    def name(self, name):
        """
        Sets this nodespace's human reaable name for display purposes.
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
        Sets this nodespace's parent nodespace by UID, effectively moving from its old parent space to the new one
        """
        pass  # pragma: no cover

    @abstractmethod
    def get_activator_value(self, type):
        """
        Returns the current value for the directional activator with the given type
        This only needs to be implemented if the reference implementation for the node functions from
        nodefunctions.py is being used.

        Alternative implementations are free to handle directional activators in node functions directly and
        can pass on the implementation of this method.

        """
        pass  # pragma: no cover

    @abstractmethod
    def set_activator_value(self, type, value):
        """
        Sets the value for the directional activator with the given type, causing gates of nodes in this node space
        to calculate their gate functions accordingly.
        This only needs to be implemented if the reference implementation for the node functions from
        nodefunctions.py is being used.

        Alternative implementations are free to handle directional activators in node functions directly and
        can pass on the implementation of this method.
        """
        pass  # pragma: no cover

    @abstractmethod
    def unset_activator_value(self, type):
        """
        Unsets the value for the directional activator with the given type, causing gates of nodes in this node space
        to calculate their gate functions accordingly (with default behavior, i.e. as if a value of 1 had been set)
        This only needs to be implemented if the reference implementation for the node functions from
        nodefunctions.py is being used.

        Alternative implementations are free to handle directional activators in node functions directly and
        can pass on the implementation of this method.
        """
        pass  # pragma: no cover

    @abstractmethod
    def set_gate_function_string(self, nodetype, gatetype, gatefunction, parameters=None):
        """
        Sets (and typically compiles) the gate function for a given node type / gate type combination in this
        nodespace.
        Implemetations with a fixed set of gate functions can use the gatefunction parameter as a key identifying
        which of the fixed gate functions to select
        """
        pass  # pragma: no cover

    @abstractmethod
    def get_gatefunction_string(self, nodetype, gatetype):
        """
        Returns the gate function for a given node type / gate type combination in this nodespace.
        Implementations with a fixed set of gate functions can return the key of the currently configured
        gate function
        """
        pass  # pragma: no cover

    @abstractmethod
    def get_gatefunction_strings(self):
        """
        Returns a dict of gate functions for all node type / gate type combinations in this nodespace.
        Implementations with a fixed set of gate functions can return the keys of the currently configured
        gate functions
        """
        pass  # pragma: no cover

    @abstractmethod
    def get_known_ids(self, entitytype=None):
        """
        Returns a list of all UIDs in this nodespace.
        If an entity type is given, the list will be filtered. Valid entity type parameters are:
        "nodes" - return nodes only
        "nodespaces" - return node spaces only
        """
        pass  # pragma: no cover

