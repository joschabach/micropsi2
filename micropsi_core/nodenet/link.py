# -*- coding: utf-8 -*-

"""
Link definition
"""

from abc import ABCMeta, abstractmethod

__author__ = 'joscha'
__date__ = '09.05.12'


class Link(metaclass=ABCMeta):
    """
    A link between two nodes, starting from a gate and ending in a slot.
    """

    @property
    def signature(self):
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

    def get_data(self, complete=False, **_):
        data = {
            "weight": self.weight,
            "target_slot_name": self.target_slot.type,
            "target_node_uid": self.target_node.uid,
        }
        if complete:
            data.update({
                "source_gate_name": self.source_gate.type,
                "source_node_uid": self.source_node.uid,
            })
        return data
