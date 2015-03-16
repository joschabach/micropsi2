# -*- coding: utf-8 -*-

"""
Nodenet definition
"""
from copy import deepcopy

import json
import os

import theano
from theano import tensor as T
import numpy as np

import micropsi_core.tools

from micropsi_core.nodenet.nodenet import Nodenet
from micropsi_core.nodenet.node import Node
from threading import Lock
import logging

from micropsi_core.nodenet.theano_engine.theano_node import *
from micropsi_core.nodenet.theano_engine.theano_stepoperators import *

NODENET_VERSION = 1

NUMBER_OF_NODES = 5
NUMBER_OF_ELEMENTS = NUMBER_OF_NODES * NUMBER_OF_ELEMENTS_PER_NODE


class TheanoNodenet(Nodenet):
    """
        theano runtime engine implementation
    """

    allocated_nodes = None
    last_allocated_node = -1

    # numpy data structures holding the actual data
    w_matrix = None
    a_array = None
    theta_array = None

    # theano tensors for performing operations
    w = None            # matrix of weights
    a = None            # vector of activations
    theta = None        # vector of thetas (i.e. biases)

    @property
    def engine(self):
        return "theano_engine"

    @property
    def current_step(self):
        return self.__step

    @property
    def data(self):
        pass

    def __init__(self, filename, name="", worldadapter="Default", world=None, owner="", uid=None, nodetypes={}, native_modules={}):

        super(TheanoNodenet, self).__init__(name or os.path.basename(filename), worldadapter, world, owner, uid)

        self.stepoperators = [TheanoPropagate()]
        self.stepoperators.sort(key=lambda op: op.priority)

        self.__version = NODENET_VERSION  # used to check compatibility of the node net data
        self.__step = 0
        self.__modulators = {}

        self.allocated_nodes = np.zeros(NUMBER_OF_NODES, dtype=np.int32)

        self.w_matrix = np.zeros((NUMBER_OF_ELEMENTS, NUMBER_OF_ELEMENTS), dtype=np.float32)
        self.w = theano.shared(value=self.w_matrix.astype(T.config.floatX), name="w", borrow=True)

        self.a_array = np.zeros(NUMBER_OF_ELEMENTS, dtype=np.float32)
        self.a = theano.shared(value=self.a_array.astype(T.config.floatX), name="a", borrow=True)

        self.theta_array = np.zeros(NUMBER_OF_ELEMENTS, dtype=np.float32)
        self.theta = theano.shared(value=self.theta_array.astype(T.config.floatX), name="theta", borrow=True)

    def step(self):
        #self.user_prompt = None                        # todo: re-introduce user prompts when looking into native modules
        if self.world is not None and self.world.agents is not None and self.uid in self.world.agents:
            self.world.agents[self.uid].snapshot()      # world adapter snapshot
                                                        # TODO: Not really sure why we don't just know our world adapter,
                                                        # but instead the world object itself

        with self.netlock:

            #self.timeout_locks()

            for operator in self.stepoperators:
                operator.execute(self, None, self.netapi)

            self.netapi._step()

            self.__step += 1

    def get_node(self, uid):
        if int(uid) in self.get_node_uids():
            return TheanoNode(self, int(uid))
        else:
            return None

    def get_node_uids(self):
        return np.nonzero(self.allocated_nodes)[0]

    def is_node(self, uid):
        return int(uid) in self.get_node_uids()

    def create_node(self, nodetype, nodespace_uid, position, name="", uid=None, parameters=None, gate_parameters=None):

        uid = -1
        while uid < 0:
            for i in range((self.last_allocated_node+1), NUMBER_OF_NODES):
                if self.allocated_nodes[i] == 0:
                    uid = i
                    break

        if uid < 0:
            for i in range(self.last_allocated_node-1):
                if self.allocated_nodes[i] == 0:
                    uid = i
                    break

        if uid < 0:
            self.logger.warning("Cannot find free id, all "+NUMBER_OF_NODES+" node entries already in use.")
            return None

        self.last_allocated_node = uid
        self.allocated_nodes[uid] = get_numerical_node_type(nodetype)
        return str(int(uid))

    def delete_node(self, uid):
        self.allocated_nodes[int(uid)] = 0
        self.last_allocated_node = int(uid)-1

    def get_nodespace(self, uid):
        pass

    def get_nodespace_uids(self):
        pass

    def is_nodespace(self, uid):
        pass

    def create_nodespace(self, parent_uid, position, name="", uid=None, gatefunction_strings=None):
        pass

    def delete_nodespace(self, uid):
        pass

    def create_link(self, source_node_uid, gate_type, target_node_uid, slot_type, weight=1, certainty=1):
        self.set_link_weight(source_node_uid, gate_type, target_node_uid, slot_type, weight)

    def set_link_weight(self, source_node_uid, gate_type, target_node_uid, slot_type, weight=1, certainty=1):
        ngt = get_numerical_gate_type(gate_type)
        nst = get_numerical_gate_type(slot_type)
        self.w_matrix[int(source_node_uid)*NUMBER_OF_ELEMENTS_PER_NODE + ngt][int(target_node_uid)*NUMBER_OF_ELEMENTS_PER_NODE + nst] = weight
        self.w.set_value(self.w_matrix, borrow=True)

    def delete_link(self, source_node_uid, gate_type, target_node_uid, slot_type):
        self.set_link_weight(source_node_uid, gate_type, target_node_uid, slot_type, 0)

    def reload_native_modules(self, native_modules):
        pass

    def get_nodespace_area_data(self, nodespace_uid, x1, x2, y1, y2):
        pass

    def get_nodespace_data(self, nodespace_uid, max_nodes):
        pass

    def merge_data(self, nodenet_data):
        pass

    def is_locked(self, lock):
        pass

    def is_locked_by(self, lock, key):
        pass

    def lock(self, lock, key, timeout=100):
        pass

    def unlock(self, lock):
        pass

    def get_modulator(self, modulator):
        pass

    def change_modulator(self, modulator, diff):
        pass

    def set_modulator(self, modulator, value):
        pass