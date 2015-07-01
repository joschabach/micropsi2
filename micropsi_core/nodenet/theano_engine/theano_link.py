# -*- coding: utf-8 -*-


from micropsi_core.nodenet.link import Link
from micropsi_core.nodenet.theano_engine.theano_definitions import *

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

    @property
    def uid(self):
        return "%s:%s:%s:%s" % (self.__source_node_uid, self.__source_gate_type, self.__target_slot_type, self.__target_node_uid)

    @property
    def weight(self):
        source_nodetype = self.__nodenet.get_node(self.__source_node_uid).nodetype
        target_nodetype = self.__nodenet.get_node(self.__target_node_uid).nodetype
        w_matrix = self.__partition.w.get_value(borrow=True)
        ngt = get_numerical_gate_type(self.__source_gate_type, source_nodetype)
        nst = get_numerical_slot_type(self.__target_slot_type, target_nodetype)
        x = self.__partition.allocated_node_offsets[node_from_id(self.__target_node_uid)] + nst
        y = self.__partition.allocated_node_offsets[node_from_id(self.__source_node_uid)] + ngt
        if self.__partition.sparse:
            weight = w_matrix[x, y]
        else:
            weight = w_matrix[x][y]

        return float(weight)

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

    def __init__(self, nodenet, partition, source_node_uid, source_gate_type, target_node_uid, target_slot_type):
        self.__nodenet = nodenet
        self.__partition = partition
        self.__source_node_uid = source_node_uid
        self.__source_gate_type = source_gate_type
        self.__target_node_uid = target_node_uid
        self.__target_slot_type = target_slot_type