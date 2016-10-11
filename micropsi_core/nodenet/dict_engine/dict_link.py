# -*- coding: utf-8 -*-

"""
Link definition
"""

from micropsi_core.nodenet.link import Link

__author__ = 'joscha'
__date__ = '09.05.12'


class DictLink(Link):
    """A link between two nodes, starting from a gate and ending in a slot.

    Links propagate activation between nodes and thereby facilitate the function of the agent.
    Links have weights, but apart from that, all their properties are held in the gates where they emanate.
    Gates contain parameters, and the gate type effectively determines a link type.

    You may retrieve links either from the global dictionary (by uid), or from the gates of nodes themselves.
    """

    @property
    def weight(self):
        return self.__weight

    @property
    def source_node(self):
        return self.__source_node

    @property
    def source_gate(self):
        return self.__source_gate

    @property
    def target_node(self):
        return self.__target_node

    @property
    def target_slot(self):
        return self.__target_slot

    def __init__(self, source_node, source_gate_name, target_node, target_slot_name, weight=1):
        """create a link between the source_node and the target_node, from the source_gate to the target_slot.
        Note: you should make sure that no link between source and gate exists.

        Attributes:
            weight (optional): the weight of the link (default is 1)
        """
        self.link(source_node, source_gate_name, target_node, target_slot_name, weight)

    def link(self, source_node, source_gate_name, target_node, target_slot_name, weight=1):
        """link between source and target nodes, from a gate to a slot.

            You may call this function to change the connections of an existing link. If the link is already
            linked, it will be unlinked first.
        """
        self.__source_node = source_node
        self.__target_node = target_node
        self.__source_gate = source_node.get_gate(source_gate_name)
        self.__target_slot = target_node.get_slot(target_slot_name)
        self.__weight = weight
        self.__source_gate._register_outgoing(self)
        self.__target_slot._register_incoming(self)

    def remove(self):
        """unplug the link from the node net
           can't be handled in the destructor, since it removes references to the instance
        """
        self.__source_gate._unregister_outgoing(self)
        self.__target_slot._unregister_incoming(self)

    def _set_weight(self, weight):
        self.__weight = weight
