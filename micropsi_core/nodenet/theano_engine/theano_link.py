# -*- coding: utf-8 -*-


from micropsi_core.nodenet.link import Link


class TheanoLink(Link):
    """
        theano link proxy class
    """

    @property
    def data(self):
        data = {
            "uid": self.uid,
            "weight": self.weight,
            "certainty": 1,
            "source_gate_name": self.__source_gate_type,
            "source_node_uid": self.__source_node_uid,
            "target_slot_name": self.__target_slot_type,
            "target_node_uid": self.__target_node_uid
        }
        return data

    __nodenet = None
    __weight = None
    __source_node_uid = None
    __target_node_uid = None
    __source_gate_type = None
    __target_slot_type = None

    @property
    def uid(self):
        return self.__source_node_uid + ":" + self.__source_gate_type + ":" + self.__target_slot_type + ":" + self.__target_node_uid

    @property
    def weight(self):
        return float(self.__weight)

    @property
    def certainty(self):
        return 1

    @property
    def source_node(self):
        return self.__nodenet.get_node(self.__source_node_uid)

    @property
    def source_gate(self):
        return self.source_node.get_gate(self.__source_gate_type)

    @property
    def target_node(self):
        return self.__nodenet.get_node(self.__target_node_uid)

    @property
    def target_slot(self):
        return self.target_node.get_slot(self.__target_slot_type)

    def __init__(self, nodenet, source_node_uid, source_gate_type, target_node_uid, target_slot_type, weight=1):
        self.__nodenet = nodenet
        self.__source_node_uid = source_node_uid
        self.__source_gate_type = source_gate_type
        self.__target_node_uid = target_node_uid
        self.__target_slot_type = target_slot_type
        self.__weight = weight
