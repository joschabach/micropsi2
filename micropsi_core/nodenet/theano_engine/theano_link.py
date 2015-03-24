# -*- coding: utf-8 -*-


from micropsi_core.nodenet.link import Link


class TheanoLink(Link):
    """
        theano link proxy class
    """

    __weight = None
    __certainty = None
    __source_node = None
    __target_node = None
    __source_gate = None
    __target_slot = None

    @property
    def uid(self):
        return self.source_node.uid + ":" + self.source_gate.type + ":" + self.target_slot.type + ":" + self.target_node.uid

    @property
    def weight(self):
        return float(self.__weight)

    @property
    def certainty(self):
        return float(self.__certainty)

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
        self.__source_node = source_node
        self.__source_gate = source_gate_name
        self.__target_node = target_node
        self.__target_slot = target_slot_name
        self.__weight = weight
        self.__certainty = 1
