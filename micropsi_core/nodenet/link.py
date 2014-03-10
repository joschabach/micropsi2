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
    def uid(self):
        return self.data.get("uid")

    @property
    def weight(self):
        return self.data.get("weight")

    @weight.setter
    def weight(self, value):
        self.data["weight"] = value

    @property
    def certainty(self):
        return self.data.get("certainty")

    @certainty.setter
    def certainty(self, value):
        self.data["certainty"] = value

    @property
    def source_node(self):
        return self.nodenet.nodes.get(self.data.get('source_node_uid', self.data.get('source_node')))  # fixme

    @source_node.setter
    def source_node(self, node):
        self.data["source_node_uid"] = node.uid

    @property
    def source_gate(self):
        return self.source_node.gates.get(self.data.get("source_gate_name"))

    @source_gate.setter
    def source_gate(self, gate):
        self.data["source_gate_name"] = gate.type

    @property
    def target_node(self):
        return self.nodenet.nodes.get(self.data.get('target_node_uid', self.data.get('target_node')))  # fixme

    @target_node.setter
    def target_node(self, node):
        self.data["target_node_uid"] = node.uid

    @property
    def target_slot(self):
        return self.target_node.slots.get(self.data.get("target_slot_name"))

    @target_slot.setter
    def target_slot(self, slot):
        self.data["target_slot_name"] = slot.type

    def __init__(self, source_node, source_gate_name, target_node, target_slot_name, weight=1, certainty=1, uid=None):
        """create a link between the source_node and the target_node, from the source_gate to the target_slot.
        Note: you should make sure that no link between source and gate exists.

        Attributes:
            weight (optional): the weight of the link (default is 1)
        """

        uid = uid or micropsi_core.tools.generate_uid()
        self.nodenet = source_node.nodenet
        if not uid in self.nodenet.state["links"]:
            self.nodenet.state["links"][uid] = {}
        self.data = source_node.nodenet.state["links"][uid]
        self.data["uid"] = uid
        self.data["source_node"] = self.data["source_node_uid"] = source_node.uid  # fixme
        self.data["target_node"] = self.data["target_node_uid"] = target_node.uid  # fixme
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

    def remove(self):
        """unplug the link from the node net
           can't be handled in the destructor, since it removes references to the instance
        """
        del self.source_gate.outgoing[self.uid]
        del self.target_slot.incoming[self.uid]

