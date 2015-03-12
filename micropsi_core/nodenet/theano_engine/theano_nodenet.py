# -*- coding: utf-8 -*-

"""
Nodenet definition
"""
from copy import deepcopy

import json
import os

from theano import tensor as T
import numpy as np

import micropsi_core.tools

from micropsi_core.nodenet.nodenet import Nodenet
from micropsi_core.nodenet.node import Node
from threading import Lock
import logging

NODENET_VERSION = 1

NUMBER_OF_NODES = 1000
NUMBER_OF_ELEMENTS_PER_NODE = 7
NUMBER_OF_ELEMENTS = NUMBER_OF_NODES * NUMBER_OF_ELEMENTS_PER_NODE

class TheanoNodenet(Nodenet):
    """
        theano runtime engine implementation
    """

    w = None            # matrix of weights
    a = None            # vector of activations
    

    @property
    def engine(self):
        return "theano_engine"

    @property
    def current_step(self):
        pass

    @property
    def data(self):
        pass

    def __init__(self, filename, name="", worldadapter="Default", world=None, owner="", uid=None, nodetypes={}, native_modules={}):

        super(TheanoNodenet, self).__init__(name or os.path.basename(filename), worldadapter, world, owner, uid)

        a_array = np.zeros(NUMBER_OF_ELEMENTS,dtype=np.float32)
        a = T.shared(value=a_array.theano.config.floatX, name="a", borrow=True)

    def step(self):
        pass

    def get_node(self, uid):
        pass

    def get_node_uids(self):
        pass

    def is_node(self, uid):
        pass

    def create_node(self, nodetype, nodespace_uid, position, name="", uid=None, parameters=None, gate_parameters=None):
        pass

    def delete_node(self, uid):
        pass

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
        pass

    def set_link_weight(self, source_node_uid, gate_type, target_node_uid, slot_type, weight=1, certainty=1):
        pass

    def delete_link(self, source_node_uid, gate_type, target_node_uid, slot_type):
        pass

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