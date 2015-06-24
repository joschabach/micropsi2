

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

    @property
    def has_new_usages(self):
        return self.__has_new_usages

    @has_new_usages.setter
    def has_new_usages(self, value):
        self.__has_new_usages = value

    @property
    def has_pipes(self):
        return self.__has_pipes

    @has_pipes.setter
    def has_pipes(self, value):
        if value != self.__has_pipes:
            self.__has_new_usages = True
            self.__has_pipes = value

    @property
    def has_directional_activators(self):
        return self.__has_directional_activators

    @has_directional_activators.setter
    def has_directional_activators(self, value):
        if value != self.__has_directional_activators:
            self.__has_new_usages = True
            self.__has_directional_activators = value

    @property
    def has_gatefunction_absolute(self):
        return self.__has_gatefunction_absolute

    @has_gatefunction_absolute.setter
    def has_gatefunction_absolute(self, value):
        if value != self.__has_gatefunction_absolute:
            self.__has_new_usages = True
            self.__has_gatefunction_absolute = value

    @property
    def has_gatefunction_sigmoid(self):
        return self.__has_gatefunction_sigmoid

    @has_gatefunction_sigmoid.setter
    def has_gatefunction_sigmoid(self, value):
        if value != self.__has_gatefunction_sigmoid:
            self.__has_new_usages = True
            self.__has_gatefunction_sigmoid = value

    @property
    def has_gatefunction_tanh(self):
        return self.__has_gatefunction_tanh

    @has_gatefunction_tanh.setter
    def has_gatefunction_tanh(self, value):
        if value != self.__has_gatefunction_tanh:
            self.__has_new_usages = True
            self.__has_gatefunction_tanh = value

    @property
    def has_gatefunction_rect(self):
        return self.__has_gatefunction_rect

    @has_gatefunction_rect.setter
    def has_gatefunction_rect(self, value):
        if value != self.__has_gatefunction_rect:
            self.__has_new_usages = True
            self.__has_gatefunction_rect = value

    @property
    def has_gatefunction_one_over_x(self):
        return self.__has_gatefunction_one_over_x

    @has_gatefunction_one_over_x.setter
    def has_gatefunction_one_over_x(self, value):
        if value != self.__has_gatefunction_one_over_x:
            self.__has_new_usages = True
            self.__has_gatefunction_one_over_x = value


    def __init__(self, nodenet, sparse, initial_NoN, initial_NoE, initial_NoNS):

        self.native_module_instances = {}
        self.comment_instances = {}

        self.NoN = initial_NoN
        self.NoE = initial_NoE
        self.NoNS = initial_NoNS

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

        self.n_function_selector = None      # vector of per-gate node function selectors
        self.n_node_porlinked = None         # vector with 0/1 flags to indicated whether the element belongs to a por-linked
                                             # node. This could in theory be inferred with T.max() on upshifted versions of w,
                                             # but for now, we manually track this property
        self.n_node_retlinked = None         # same for ret

        # instantiate numpy data structures
        self.allocated_nodes = np.zeros(self.NoN, dtype=np.int32)
        self.allocated_node_offsets = np.zeros(self.NoN, dtype=np.int32)
        self.allocated_elements_to_nodes = np.zeros(self.NoE, dtype=np.int32)

        self.allocated_node_parents = np.zeros(self.NoN, dtype=np.int32)
        self.allocated_nodespaces = np.zeros(self.NoNS, dtype=np.int32)

        self.allocated_nodespaces_por_activators = np.zeros(self.NoNS, dtype=np.int32)
        self.allocated_nodespaces_ret_activators = np.zeros(self.NoNS, dtype=np.int32)
        self.allocated_nodespaces_sub_activators = np.zeros(self.NoNS, dtype=np.int32)
        self.allocated_nodespaces_sur_activators = np.zeros(self.NoNS, dtype=np.int32)
        self.allocated_nodespaces_cat_activators = np.zeros(self.NoNS, dtype=np.int32)
        self.allocated_nodespaces_exp_activators = np.zeros(self.NoNS, dtype=np.int32)

        self.allocated_elements_to_activators = np.zeros(self.NoE, dtype=np.int32)

        # instantiate theano data structures
        if self.sparse:
            self.w = theano.shared(sp.csr_matrix((self.NoE, self.NoE), dtype=nodenet.scipyfloatX), name="w")
        else:
            w_matrix = np.zeros((self.NoE, self.NoE), dtype=nodenet.scipyfloatX)
            self.w = theano.shared(value=w_matrix.astype(T.config.floatX), name="w", borrow=True)

        a_array = np.zeros(self.NoE, dtype=nodenet.numpyfloatX)
        self.a = theano.shared(value=a_array.astype(T.config.floatX), name="a", borrow=True)

        a_shifted_matrix = np.lib.stride_tricks.as_strided(a_array, shape=(self.NoE, 7), strides=(nodenet.byte_per_float, nodenet.byte_per_float))
        self.a_shifted = theano.shared(value=a_shifted_matrix.astype(T.config.floatX), name="a_shifted", borrow=True)

        g_theta_array = np.zeros(self.NoE, dtype=nodenet.numpyfloatX)
        self.g_theta = theano.shared(value=g_theta_array.astype(T.config.floatX), name="theta", borrow=True)

        g_factor_array = np.ones(self.NoE, dtype=nodenet.numpyfloatX)
        self.g_factor = theano.shared(value=g_factor_array.astype(T.config.floatX), name="g_factor", borrow=True)

        g_threshold_array = np.zeros(self.NoE, dtype=nodenet.numpyfloatX)
        self.g_threshold = theano.shared(value=g_threshold_array.astype(T.config.floatX), name="g_threshold", borrow=True)

        g_amplification_array = np.ones(self.NoE, dtype=nodenet.numpyfloatX)
        self.g_amplification = theano.shared(value=g_amplification_array.astype(T.config.floatX), name="g_amplification", borrow=True)

        g_min_array = np.zeros(self.NoE, dtype=nodenet.numpyfloatX)
        self.g_min = theano.shared(value=g_min_array.astype(T.config.floatX), name="g_min", borrow=True)

        g_max_array = np.ones(self.NoE, dtype=nodenet.numpyfloatX)
        self.g_max = theano.shared(value=g_max_array.astype(T.config.floatX), name="g_max", borrow=True)

        g_function_selector_array = np.zeros(self.NoE, dtype=np.int8)
        self.g_function_selector = theano.shared(value=g_function_selector_array, name="gatefunction", borrow=True)

        g_expect_array = np.ones(self.NoE, dtype=nodenet.numpyfloatX)
        self.g_expect = theano.shared(value=g_expect_array, name="expectation", borrow=True)

        g_countdown_array = np.zeros(self.NoE, dtype=np.int8)
        self.g_countdown = theano.shared(value=g_countdown_array, name="countdown", borrow=True)

        g_wait_array = np.ones(self.NoE, dtype=np.int8)
        self.g_wait = theano.shared(value=g_wait_array, name="wait", borrow=True)

        n_function_selector_array = np.zeros(self.NoE, dtype=np.int8)
        self.n_function_selector = theano.shared(value=n_function_selector_array, name="nodefunction_per_gate", borrow=True)

        n_node_porlinked_array = np.zeros(self.NoE, dtype=np.int8)
        self.n_node_porlinked = theano.shared(value=n_node_porlinked_array, name="porlinked", borrow=True)

        n_node_retlinked_array = np.zeros(self.NoE, dtype=np.int8)
        self.n_node_retlinked = theano.shared(value=n_node_retlinked_array, name="retlinked", borrow=True)

        self.__has_new_usages = True
        self.__has_pipes = False
        self.__has_directional_activators = False
        self.__has_gatefunction_absolute = False
        self.__has_gatefunction_sigmoid = False
        self.__has_gatefunction_tanh = False
        self.__has_gatefunction_rect = False
        self.__has_gatefunction_one_over_x = False
