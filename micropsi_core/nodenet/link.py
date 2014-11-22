# -*- coding: utf-8 -*-

"""
Link definition
"""

import micropsi_core.tools

__author__ = 'joscha'
__date__ = '09.05.12'


class Link(object):
    """A link between two nodes, starting from a gate and ending in a slot.

    Links propagate activation between nodes and thereby facilitate the function of the agent.
    Links have weights, but apart from that, all their properties are held in the gates where they emanate.
    Gates contain parameters, and the gate type effectively determines a link type.

    You may retrieve links either from the global dictionary (by uid), or from the gates of nodes themselves.
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

    def __init__(self, source_node, source_gate_name, target_node, target_slot_name, weight=1, certainty=1):
        """create a link between the source_node and the target_node, from the source_gate to the target_slot.
        Note: you should make sure that no link between source and gate exists.

        Attributes:
            weight (optional): the weight of the link (default is 1)
        """

        self.weight = weight
        self.certainty = certainty
        self.nodenet = source_node.nodenet
        self.source_node = source_node
        self.target_node = target_node
        self.source_gate = source_node.get_gate(source_gate_name)
        self.target_slot = target_node.get_slot(target_slot_name)
        self.link(source_node, source_gate_name, target_node, target_slot_name, weight, certainty)

    def link(self, source_node, source_gate_name, target_node, target_slot_name, weight=1, certainty=1):
        """link between source and target nodes, from a gate to a slot.

            You may call this function to change the connections of an existing link. If the link is already
            linked, it will be unlinked first.
        """
        if self.source_node:
            if self.source_node != source_node and self.source_gate.type != source_gate_name:
                del self.source_gate.outgoing[self.uid]
        if self.target_node:
            if self.target_node != target_node and self.target_slot.type != target_slot_name:
                del self.target_slot.incoming[self.uid]
        self.source_node = source_node
        self.target_node = target_node
        self.source_gate = source_node.get_gate(source_gate_name)
        self.target_slot = target_node.get_slot(target_slot_name)
        self.weight = weight
        self.certainty = certainty
        self.source_gate.outgoing[self.uid] = self
        self.target_slot.incoming[self.uid] = self

        self.nodenet.links[self.uid] = self

    def remove(self):
        """unplug the link from the node net
           can't be handled in the destructor, since it removes references to the instance
        """
        del self.source_gate.outgoing[self.uid]
        del self.target_slot.incoming[self.uid]
        del self.nodenet.links[self.uid]
