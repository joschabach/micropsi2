

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
        self.a = None            # vector of activations
        self.a_shifted = None    # matrix with each row defined as [a[n], a[n+1], a[n+2], a[n+3], a[n+4], a[n+5], a[n+6]]
                            # this is a view on the activation values instrumental in calculating concept node functions

        self.g_factor = None     # vector of gate factors, controlled by directional activators
        self.g_threshold = None  # vector of thresholds (gate parameters)
        self.g_amplification = None  # vector of amplification factors
        self.g_min = None        # vector of lower bounds
        self.g_max = None        # vector of upper bounds

        self.g_function_selector = None # vector of gate function selectors

        self.g_theta = None      # vector of thetas (i.e. biases, use depending on gate function)

        self.g_expect = None     # vector of expectations
        self.g_countdown = None  # vector of number of steps until expectation needs to be met
        self.g_wait = None       # vector of initial values for g_countdown

        # instantiate numpy data structures
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

        a_array = np.zeros(self.nodenet.NoE, dtype=nodenet.numpyfloatX)
        self.a = theano.shared(value=a_array.astype(T.config.floatX), name="a", borrow=True)

        a_shifted_matrix = np.lib.stride_tricks.as_strided(a_array, shape=(self.nodenet.NoE, 7), strides=(nodenet.byte_per_float, nodenet.byte_per_float))
        self.a_shifted = theano.shared(value=a_shifted_matrix.astype(T.config.floatX), name="a_shifted", borrow=True)

        g_theta_array = np.zeros(self.nodenet.NoE, dtype=nodenet.numpyfloatX)
        self.g_theta = theano.shared(value=g_theta_array.astype(T.config.floatX), name="theta", borrow=True)

        g_factor_array = np.ones(self.nodenet.NoE, dtype=nodenet.numpyfloatX)
        self.g_factor = theano.shared(value=g_factor_array.astype(T.config.floatX), name="g_factor", borrow=True)

        g_threshold_array = np.zeros(self.nodenet.NoE, dtype=nodenet.numpyfloatX)
        self.g_threshold = theano.shared(value=g_threshold_array.astype(T.config.floatX), name="g_threshold", borrow=True)

        g_amplification_array = np.ones(self.nodenet.NoE, dtype=nodenet.numpyfloatX)
        self.g_amplification = theano.shared(value=g_amplification_array.astype(T.config.floatX), name="g_amplification", borrow=True)

        g_min_array = np.zeros(self.nodenet.NoE, dtype=nodenet.numpyfloatX)
        self.g_min = theano.shared(value=g_min_array.astype(T.config.floatX), name="g_min", borrow=True)

        g_max_array = np.ones(self.nodenet.NoE, dtype=nodenet.numpyfloatX)
        self.g_max = theano.shared(value=g_max_array.astype(T.config.floatX), name="g_max", borrow=True)

        g_function_selector_array = np.zeros(self.nodenet.NoE, dtype=np.int8)
        self.g_function_selector = theano.shared(value=g_function_selector_array, name="gatefunction", borrow=True)

        g_expect_array = np.ones(self.nodenet.NoE, dtype=nodenet.numpyfloatX)
        self.g_expect = theano.shared(value=g_expect_array, name="expectation", borrow=True)

        g_countdown_array = np.zeros(self.nodenet.NoE, dtype=np.int8)
        self.g_countdown = theano.shared(value=g_countdown_array, name="countdown", borrow=True)

        g_wait_array = np.ones(self.nodenet.NoE, dtype=np.int8)
        self.g_wait = theano.shared(value=g_wait_array, name="wait", borrow=True)
