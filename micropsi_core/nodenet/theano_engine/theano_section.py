

import json
import os
import copy
import warnings

import theano
from theano import tensor as T
import numpy as np
import scipy.sparse as sp
import scipy

from configuration import config as settings

class TheanoSection():

    def __init__(self, nodenet, sparse):

        self.nodenet = nodenet
        self.sparse = sparse
        self.logger = nodenet.logger

        # array, index is node id, value is numeric node type
        self.allocated_nodes = None

        # array, index is node id, value is offset in a and w
        self.allocated_node_offsets = None

        # array, index is element index, value is node id
        self.allocated_elements_to_nodes = None

        # array, index is node id, value is nodespace id
        self.allocated_node_parents = None

        # array, index is nodespace id, value is parent nodespace id
        self.allocated_nodespaces = None

        # directional activator assignment, key is nodespace ID, value is activator ID
        self.allocated_nodespaces_por_activators = None
        self.allocated_nodespaces_ret_activators = None
        self.allocated_nodespaces_sub_activators = None
        self.allocated_nodespaces_sur_activators = None
        self.allocated_nodespaces_cat_activators = None
        self.allocated_nodespaces_exp_activators = None

        # directional activators map, index is element id, value is the directional activator's element id
        self.allocated_elements_to_activators = None

        # theano tensors for performing operations
        self.w = None            # matrix of weights

        self.allocated_nodes = np.zeros(self.nodenet.NoN, dtype=np.int32)
        self.allocated_node_offsets = np.zeros(self.nodenet.NoN, dtype=np.int32)
        self.allocated_elements_to_nodes = np.zeros(self.nodenet.NoE, dtype=np.int32)

        self.allocated_node_parents = np.zeros(self.nodenet.NoN, dtype=np.int32)
        self.allocated_nodespaces = np.zeros(self.nodenet.NoNS, dtype=np.int32)

        self.allocated_nodespaces_por_activators = np.zeros(self.nodenet.NoNS, dtype=np.int32)
        self.allocated_nodespaces_ret_activators = np.zeros(self.nodenet.NoNS, dtype=np.int32)
        self.allocated_nodespaces_sub_activators = np.zeros(self.nodenet.NoNS, dtype=np.int32)
        self.allocated_nodespaces_sur_activators = np.zeros(self.nodenet.NoNS, dtype=np.int32)
        self.allocated_nodespaces_cat_activators = np.zeros(self.nodenet.NoNS, dtype=np.int32)
        self.allocated_nodespaces_exp_activators = np.zeros(self.nodenet.NoNS, dtype=np.int32)

        self.allocated_elements_to_activators = np.zeros(self.nodenet.NoE, dtype=np.int32)

        # instantiate theano data structures
        if self.sparse:
            self.w = theano.shared(sp.csr_matrix((self.nodenet.NoE, self.nodenet.NoE), dtype=nodenet.scipyfloatX), name="w")
        else:
            w_matrix = np.zeros((self.nodenet.NoE, self.nodenet.NoE), dtype=nodenet.scipyfloatX)
            self.w = theano.shared(value=w_matrix.astype(T.config.floatX), name="w", borrow=True)
