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
    - the scope for directional activators

    directional activator scope are not heritable.
    """

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
    def name(self):
        """
        This nodespace's human readable name for display purposes. Returns the UID if no human readable name has been set.
        """
        pass  # pragma: no cover

    @name.setter
    @abstractmethod
    def name(self, name):
        """
        Sets this nodespace's human readable name for display purposes.
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def parent_nodespace(self):
        """
        The UID of this node's parent nodespace
        """
        pass  # pragma: no cover

    def get_data(self):
        """
        Returns the json representation of this nodespace
        """
        return {
            "uid": self.uid,
            "index": self.index,
            "name": self.name,
            "parent_nodespace": self.parent_nodespace,
        }

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
    def get_known_ids(self, entitytype=None):
        """
        Returns a list of all UIDs in this nodespace.
        If an entity type is given, the list will be filtered. Valid entity type parameters are:
        "nodes" - return nodes only
        "nodespaces" - return node spaces only
        """
        pass  # pragma: no cover

    def __repr__(self):
        return "<Nodespace \"%s\" (%s)>" % (self.name, self.uid)
