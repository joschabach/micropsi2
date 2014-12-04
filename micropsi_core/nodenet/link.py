# -*- coding: utf-8 -*-

"""
Link definition
"""

import micropsi_core.tools
from abc import ABCMeta, abstractmethod

__author__ = 'joscha'
__date__ = '09.05.12'


class Link(metaclass=ABCMeta):
    """
    A link between two nodes, starting from a gate and ending in a slot.
    """

    @property
    def data(self):
        data = {
            "uid": self.uid,
            "weight": self.weight,
            "certainty": self.certainty,
            "source_gate_name": self.source_gate.type,
            "source_node_uid": self.source_node.uid,
            "target_slot_name": self.target_slot.type,
            "target_node_uid": self.target_node.uid,
        }
        return data

    @property
    def uid(self):
        return self.source_node.uid + ":" + self.source_gate.type + ":" + self.target_slot.type + ":" + self.target_node.uid

    @property
    @abstractmethod
    def weight(self):
        """
        Returns the weight (the strength) of this link
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def certainty(self):
        """
        Returns the certainty value of this link.
        Note that this is not being used right now and defined/reserved for future use.
        Implementations can always return 1 for the time being
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def source_node(self):
        """
        Returns the Node (object) from which this link originates
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def source_gate(self):
        """
        Returns the Gate (object) from which this link originates
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def target_node(self):
        """
        Returns the Node (object) at which this link ends
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def target_slot(self):
        """
        Returns the Slot (object) at which this link ends
        """
        pass  # pragma: no cover
