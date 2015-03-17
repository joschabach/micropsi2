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
from micropsi_core.nodenet.node import Node, Nodetype
from threading import Lock
import logging

from micropsi_core.nodenet.theano_engine.theano_node import *
from micropsi_core.nodenet.theano_engine.theano_stepoperators import *
from micropsi_core.nodenet.theano_engine.theano_nodespace import *

NODENET_VERSION = 1

NUMBER_OF_NODES = 5
NUMBER_OF_ELEMENTS = NUMBER_OF_NODES * NUMBER_OF_ELEMENTS_PER_NODE


class TheanoNodenet(Nodenet):
    """
        theano runtime engine implementation
    """

    allocated_nodes = None
    last_allocated_node = -1

    # todo: get rid of positions
    positions = []

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
        data = super(TheanoNodenet, self).data
        data['links'] = self.construct_links_dict()
        data['nodes'] = self.construct_nodes_dict()
        #for uid in data['nodes']:
        #    data['nodes'][uid]['gate_parameters'] = self.get_node(uid).clone_non_default_gate_parameters()
        data['nodespaces'] = self.construct_nodespaces_dict("Root")
        data['version'] = self.__version
        data['modulators'] = self.construct_modulators_dict()
        return data


    def __init__(self, filename, name="", worldadapter="Default", world=None, owner="", uid=None, nodetypes={}, native_modules={}):

        super(TheanoNodenet, self).__init__(name or os.path.basename(filename), worldadapter, world, owner, uid)

        self.stepoperators = [TheanoPropagate()]
        self.stepoperators.sort(key=lambda op: op.priority)

        self.__version = NODENET_VERSION  # used to check compatibility of the node net data
        self.__step = 0
        self.__modulators = {}
        self.__nodetypes = nodetypes

        # this conversion of dicts to living objects in the same variable name really isn't pretty.
        # dict_nodenet is also doing it, and it's evil and should be fixed.
        self.__nodetypes = {}
        for type, data in nodetypes.items():
            self.__nodetypes[type] = Nodetype(nodenet=self, **data)

        self.allocated_nodes = np.zeros(NUMBER_OF_NODES, dtype=np.int32)

        self.positions = [(10,10) for i in range(0,NUMBER_OF_NODES)]

        w_matrix = np.zeros((NUMBER_OF_ELEMENTS, NUMBER_OF_ELEMENTS), dtype=np.float32)
        self.w = theano.shared(value=w_matrix.astype(T.config.floatX), name="w", borrow=True)

        a_array = np.zeros(NUMBER_OF_ELEMENTS, dtype=np.float32)
        self.a = theano.shared(value=a_array.astype(T.config.floatX), name="a", borrow=True)

        theta_array = np.zeros(NUMBER_OF_ELEMENTS, dtype=np.float32)
        self.theta = theano.shared(value=theta_array.astype(T.config.floatX), name="theta", borrow=True)

        self.rootnodespace = TheanoNodespace(self)

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
        if uid in self.get_node_uids():
            return TheanoNode(self, uid, self.allocated_nodes[from_id(uid)])
        else:
            return None

    def get_node_uids(self):
        return [to_id(id) for id in np.nonzero(self.allocated_nodes)[0]]

    def is_node(self, uid):
        return uid in self.get_node_uids()

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
        self.positions[uid] = position

        return to_id(uid)

    def delete_node(self, uid):
        self.allocated_nodes[from_id(uid)] = 0
        self.last_allocated_node = from_id(uid)-1

    def get_nodespace(self, uid):
        if uid == "Root":
            return self.rootnodespace
        else:
            return None

    def get_nodespace_uids(self):
        return ["Root"]

    def is_nodespace(self, uid):
        return uid == "Root"

    def create_nodespace(self, parent_uid, position, name="", uid=None, gatefunction_strings=None):
        pass

    def delete_nodespace(self, uid):
        pass

    def create_link(self, source_node_uid, gate_type, target_node_uid, slot_type, weight=1, certainty=1):
        self.set_link_weight(source_node_uid, gate_type, target_node_uid, slot_type, weight)

        # todo: the interface for create_link makes no sense: it always returns true and a link object that is only
        # being used to query the UID which is useless
        links = self.get_node(source_node_uid).get_gate(gate_type).get_links()
        link = None
        for candidate in links:
            if candidate.target_slot.type == slot_type and candidate.target_node.uid == target_node_uid:
                link = candidate
                break

        return True, link

    def set_link_weight(self, source_node_uid, gate_type, target_node_uid, slot_type, weight=1, certainty=1):
        ngt = get_numerical_gate_type(gate_type)
        nst = get_numerical_gate_type(slot_type)
        w_matrix = self.w.get_value(borrow=True, return_internal_type=True)
        w_matrix[from_id(target_node_uid)*NUMBER_OF_ELEMENTS_PER_NODE + nst][from_id(source_node_uid)*NUMBER_OF_ELEMENTS_PER_NODE + ngt] = weight
        self.w.set_value(w_matrix, borrow=True)

    def delete_link(self, source_node_uid, gate_type, target_node_uid, slot_type):
        self.set_link_weight(source_node_uid, gate_type, target_node_uid, slot_type, 0)

    def reload_native_modules(self, native_modules):
        pass

    def get_nodespace_area_data(self, nodespace_uid, x1, x2, y1, y2):
        return self.data                    # todo: implement

    def get_nodespace_data(self, nodespace_uid, max_nodes):
        return self.data                    # todo: implement

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

    def get_nodetype(self, type):
        if type in self.__nodetypes:
            return self.__nodetypes[type]
        else:
            return None
            #return self.__native_modules.get(type)         # todo: implement native modules

    def construct_links_dict(self):
        data = {}
        for node_uid in self.get_node_uids():
            links = self.get_node(node_uid).get_associated_links()
            for link in links:
                data[link.uid] = link.data
        return data

    def construct_nodes_dict(self, max_nodes=-1):
        data = {}
        i = 0
        for node_uid in self.get_node_uids():
            i += 1
            data[node_uid] = self.get_node(node_uid).data
            if max_nodes > 0 and i > max_nodes:
                break
        return data

    def construct_nodespaces_dict(self, nodespace_uid):
        data = {}
        for nodespace_candidate_uid in self.get_nodespace_uids():
            if self.get_nodespace(nodespace_candidate_uid).parent_nodespace == nodespace_uid or nodespace_candidate_uid == nodespace_uid:
                data[nodespace_candidate_uid] = self.get_nodespace(nodespace_candidate_uid).data
        return data

    def construct_modulators_dict(self):
        return {}

    def update_node_positions(self):
        pass