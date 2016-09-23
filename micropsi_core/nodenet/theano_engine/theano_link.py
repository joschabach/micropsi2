# -*- coding: utf-8 -*-


from micropsi_core.nodenet.link import Link
from micropsi_core.nodenet.theano_engine.theano_definitions import *
import numpy as np


class TheanoLink(Link):
    """
        theano link proxy class
    """

    @property
    def signature(self):
        return "%s:%s:%s:%s" % (self.__source_node_uid, self.__source_gate_type, self.__target_slot_type, self.__target_node_uid)

    @property
    def weight(self):

        source_partition = self.__nodenet.get_partition(self.__source_node_uid)
        target_partition = self.__nodenet.get_partition(self.__target_node_uid)

        source_nodetype = self.__nodenet.get_node(self.__source_node_uid).nodetype
        target_nodetype = self.__nodenet.get_node(self.__target_node_uid).nodetype
        ngt = get_numerical_gate_type(self.__source_gate_type, source_nodetype)
        nst = get_numerical_slot_type(self.__target_slot_type, target_nodetype)

        if source_partition == target_partition:
            w_matrix = source_partition.w.get_value(borrow=True)
            x = source_partition.allocated_node_offsets[node_from_id(self.__target_node_uid)] + nst
            y = source_partition.allocated_node_offsets[node_from_id(self.__source_node_uid)] + ngt
            if source_partition.sparse:
                weight = w_matrix[x, y]
            else:
                weight = w_matrix[x][y]
            return float(weight)
        else:
            inlinks = target_partition.inlinks[source_partition.spid]
            from_elements = inlinks[0].get_value(borrow=True)
            to_elements = inlinks[1].get_value(borrow=True)

            target_element = target_partition.allocated_node_offsets[node_from_id(self.__target_node_uid)] + nst
            source_element = source_partition.allocated_node_offsets[node_from_id(self.__source_node_uid)] + ngt

            y = np.where(from_elements == source_element)[0][0]
            x = np.where(to_elements == target_element)[0][0]

            inlink_type = inlinks[4]
            if inlink_type == "dense":
                weights = inlinks[2].get_value(borrow=True)
                return float(weights[x][y])
            elif inlink_type == "identity":
                return 1. if x == y else 0.

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

    def __init__(self, nodenet, source_node_uid, source_gate_type, target_node_uid, target_slot_type):
        self.__nodenet = nodenet
        self.__source_node_uid = source_node_uid
        self.__source_gate_type = source_gate_type
        self.__target_node_uid = target_node_uid
        self.__target_slot_type = target_slot_type