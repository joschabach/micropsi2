

import io
import os

import theano
from theano import tensor as T
import numpy as np
import scipy.sparse as sp
import theano.sparse as ST
from theano.tensor import nnet as N

from micropsi_core.nodenet.node import FlowNodetype, HighdimensionalNodetype
from micropsi_core.nodenet.theano_engine.theano_definitions import *


class TheanoPartition():

    @property
    def spid(self):
        return "%03i" % self.pid

    @property
    def rootnodespace_uid(self):
        return "s%s1" % self.spid

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
    def has_lstms(self):
        return self.__has_lstms

    @has_lstms.setter
    def has_lstms(self, value):
        if value != self.__has_lstms:
            self.__has_new_usages = True
            self.__has_lstms = value

    @property
    def has_directional_activators(self):
        return self.__has_directional_activators

    @has_directional_activators.setter
    def has_directional_activators(self, value):
        if value != self.__has_directional_activators:
            self.__has_new_usages = True
            self.__has_directional_activators = value

    @property
    def has_sampling_activators(self):
        return self.__has_sampling_activators

    @has_sampling_activators.setter
    def has_sampling_activators(self, value):
        if value != self.__has_sampling_activators:
            self.__has_new_usages = True
            self.__has_sampling_activators = value

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
    def has_gatefunction_relu(self):
        return self.__has_gatefunction_relu

    @has_gatefunction_relu.setter
    def has_gatefunction_relu(self, value):
        if value != self.__has_gatefunction_relu:
            self.__has_new_usages = True
            self.__has_gatefunction_relu = value

    @property
    def has_gatefunction_one_over_x(self):
        return self.__has_gatefunction_one_over_x

    @has_gatefunction_one_over_x.setter
    def has_gatefunction_one_over_x(self, value):
        if value != self.__has_gatefunction_one_over_x:
            self.__has_new_usages = True
            self.__has_gatefunction_one_over_x = value

    @property
    def has_gatefunction_elu(self):
        return self.__has_gatefunction_elu

    @has_gatefunction_elu.setter
    def has_gatefunction_elu(self, value):
        if value != self.__has_gatefunction_elu:
            self.__has_new_usages = True
            self.__has_gatefunction_elu = value

    @property
    def has_gatefunction_threshold(self):
        return self.__has_gatefunction_threshold

    @has_gatefunction_threshold.setter
    def has_gatefunction_threshold(self, value):
        if value != self.__has_gatefunction_threshold:
            self.__has_new_usages = True
            self.__has_gatefunction_threshold = value

    def __init__(self, nodenet, pid, sparse=True, initial_number_of_nodes=2000, average_elements_per_node_assumption=5, initial_number_of_nodespaces=10):

        # logger used by this partition
        self.logger = nodenet.logger

        # uids to instances of TheanoNode objects for living native modules
        self.native_module_instances = {}

        # uids to TheanoNode objects for comments
        self.comment_instances = {}

        # noddespace_uids to map map. level-2 map is groupname to list of numeric IDs
        self.nodegroups = {}

        # nodenet partition ID
        self.pid = pid

        # number of nodes allocated in this partition
        self.NoN = initial_number_of_nodes

        # numer of elements allocated in this partition
        self.NoE = initial_number_of_nodes * average_elements_per_node_assumption

        # numer of nodespaces allocated in this partition
        self.NoNS = initial_number_of_nodespaces

        # the nodenet this partition belongs to
        self.nodenet = nodenet

        # sparsity flag for this partition
        self.sparse = sparse

        # array, index is node id, value is numeric node type
        self.allocated_nodes = None

        # array, index is node id, value is nodenet-step where node was last modified
        self.nodes_last_changed = np.zeros(self.NoN, dtype=np.int32) - 1

        # array, index is node id, value is offset in a and w
        self.allocated_node_offsets = None

        # array, index is element index, value is node id
        self.allocated_elements_to_nodes = None

        # array, index is node id, value is nodespace id
        self.allocated_node_parents = None

        # array, index is nodespace id, value is parent nodespace id
        self.allocated_nodespaces = None

        # array, index is nodespace id, value is nodenet-step where nodespace was last modified
        self.nodespaces_last_changed = np.zeros(self.NoNS, dtype=np.int32) - 1

        # array, index is nodespace id, value is nodenet-step where the immediate children of this nodespace were last modified
        self.nodespaces_contents_last_changed = np.zeros(self.NoNS, dtype=np.int32) - 1

        # directional activator assignment, key is nodespace ID, value is activator ID
        self.allocated_nodespaces_por_activators = None
        self.allocated_nodespaces_ret_activators = None
        self.allocated_nodespaces_sub_activators = None
        self.allocated_nodespaces_sur_activators = None
        self.allocated_nodespaces_cat_activators = None
        self.allocated_nodespaces_exp_activators = None

        self.allocated_nodespaces_sampling_activators = None

        # directional activators map, index is element id, value is the directional activator's element id
        self.allocated_elements_to_activators = None

        # theano tensors for performing operations
        self.w = None            # matrix of weights
        self.a = None            # vector of activations
        self.a_shifted = None    # matrix with each row defined as [a[n], a[n+1], a[n+2], a[n+3], a[n+4], a[n+5], a[n+6]]
                            # this is a view on the activation values instrumental in calculating concept node functions

        self.a_in = None         # vector of activations coming in from the outside (other partitions typically)
        self.a_prev = None       # vector of output activations at t-1 (not all gate types maintain this)

        self.g_factor = None     # vector of gate factors, controlled by activators, semantics differ by node type

        # gatefunction parameters
        self.g_bias = None      # vector of biases
        self.g_threshold = None  # vector of thresholds
        self.g_amplification = None  # vector of amplification factors
        self.g_min = None        # vector of lower bounds
        self.g_max = None        # vector of upper bounds

        self.g_function_selector = None  # vector of gate function selectors

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

        self.allocated_nodespaces_sampling_activators = np.zeros(self.NoNS, dtype=np.int32)

        self.allocated_elements_to_activators = np.zeros(self.NoE, dtype=np.int32)

        self.sensor_indices = np.zeros(0, dtype=np.int32)  # index := datasource, value:=element index
        self.actuator_indices = np.zeros(0, dtype=np.int32)  # index := datatarget, value:=element index

        self.inlinks = {}

        self.deleted_items = {}

        # instantiate theano data structures
        if self.sparse:
            self.w = theano.shared(sp.csr_matrix((self.NoE, self.NoE), dtype=nodenet.numpyfloatX), name="w")
        else:
            w_matrix = np.zeros((self.NoE, self.NoE), dtype=nodenet.numpyfloatX)
            self.w = theano.shared(value=w_matrix.astype(T.config.floatX), name="w", borrow=True)

        self.t = theano.shared(value=np.int32(0), name="t")

        a_array = np.zeros(self.NoE, dtype=nodenet.numpyfloatX)
        self.a = theano.shared(value=a_array.astype(T.config.floatX), name="a", borrow=True)

        a_shifted_matrix = np.lib.stride_tricks.as_strided(a_array, shape=(self.NoE, 7), strides=(nodenet.byte_per_float, nodenet.byte_per_float))
        self.a_shifted = theano.shared(value=a_shifted_matrix.astype(T.config.floatX), name="a_shifted", borrow=True)

        a_in_array = np.zeros(self.NoE, dtype=nodenet.numpyfloatX)
        self.a_in = theano.shared(value=a_in_array.astype(T.config.floatX), name="a_in", borrow=True)

        a_prev_array = np.zeros(self.NoE, dtype=nodenet.numpyfloatX)
        self.a_prev = theano.shared(value=a_prev_array.astype(T.config.floatX), name="a_prev", borrow=True)

        g_bias_array = np.zeros(self.NoE, dtype=nodenet.numpyfloatX)
        self.g_bias = theano.shared(value=g_bias_array.astype(T.config.floatX), name="bias", borrow=True)

        g_bias_shifted_matrix = np.lib.stride_tricks.as_strided(g_bias_array, shape=(self.NoE, 7), strides=(nodenet.byte_per_float, nodenet.byte_per_float))
        self.g_bias_shifted = theano.shared(value=g_bias_shifted_matrix.astype(T.config.floatX), name="g_bias_shifted_shifted", borrow=True)

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

        g_countdown_array = np.zeros(self.NoE, dtype=np.int16)
        self.g_countdown = theano.shared(value=g_countdown_array, name="countdown", borrow=True)

        g_wait_array = np.ones(self.NoE, dtype=np.int16)
        self.g_wait = theano.shared(value=g_wait_array, name="wait", borrow=True)

        n_function_selector_array = np.zeros(self.NoE, dtype=np.int8)
        self.n_function_selector = theano.shared(value=n_function_selector_array, name="nodefunction_per_gate", borrow=True)

        n_node_porlinked_array = np.zeros(self.NoE, dtype=np.int8)
        self.n_node_porlinked = theano.shared(value=n_node_porlinked_array, name="porlinked", borrow=True)

        n_node_retlinked_array = np.zeros(self.NoE, dtype=np.int8)
        self.n_node_retlinked = theano.shared(value=n_node_retlinked_array, name="retlinked", borrow=True)

        self.__has_new_usages = True
        self.__has_pipes = False
        self.__has_lstms = False
        self.__has_directional_activators = False
        self.__has_sampling_activators = False
        self.__has_gatefunction_absolute = False
        self.__has_gatefunction_sigmoid = False
        self.__has_gatefunction_tanh = False
        self.__has_gatefunction_one_over_x = False
        self.__has_gatefunction_elu = False
        self.__has_gatefunction_relu = False
        self.__has_gatefunction_threshold = False
        self.por_ret_dirty = True

        self.last_allocated_node = 0
        self.last_allocated_offset = 0
        self.last_allocated_nodespace = 0

        self.compile_propagate()

    def compile_propagate(self):
        if self.sparse:
            self.propagate = theano.function([], None, updates=[(self.a_prev, self.a), (self.a, self.a_in + ST.dot(self.w, self.a)),
                                                                          (self.a_in, T.zeros_like(self.a_in))])
        else:
            self.propagate = theano.function([], None, updates=[(self.a_prev, self.a), (self.a, self.a_in + T.dot(self.w, self.a)),
                                                                          (self.a_in, T.zeros_like(self.a_in))])

    def compile_calculate_nodes(self):
        slots = self.a_shifted
        biases = self.g_bias_shifted
        countdown = self.g_countdown
        por_linked = self.n_node_porlinked
        ret_linked = self.n_node_retlinked

        # node functions implemented with identity by default (native modules are calculated by python)
        nodefunctions = self.a
        a_prev = self.a_prev
        t = self.t

        # pipe logic

        ###############################################################
        # lookup table for source activation in a_shifted
        # when calculating the gate on the y axis...
        # ... find the slot at the given index on the x axis
        #
        #       0   1   2   3   4   5   6   7   8   9   10  11  12  13
        # gen                               gen por ret sub sur cat exp
        # por                           gen por ret sub sur cat exp
        # ret                       gen por ret sub sur cat exp
        # sub                   gen por ret sub sur cat exp
        # sur               gen por ret sub sur cat exp
        # cat           gen por ret sub sur cat exp
        # exp       gen por ret sub sur cat exp
        #

        ### gen plumbing
        pipe_gen_sur_exp = (slots[:, 11] + slots[:, 13]) * slots[:, 10]             # sum of sur and exp as default
                                                                                    # drop to 0 if < expectation
        pipe_gen_sur_exp = T.switch(T.lt(pipe_gen_sur_exp, self.g_expect) * T.gt(pipe_gen_sur_exp, 0), 0, pipe_gen_sur_exp)

        pipe_gen = slots[:, 7] * slots[:, 10]                                       # gen * sub
        pipe_gen = T.switch(abs(pipe_gen) > 0.1, pipe_gen, pipe_gen_sur_exp)        # drop to def. if below 0.1
                                                                                    # drop to def. if por == 0 and por slot is linked
        pipe_gen = T.switch(T.eq(slots[:, 8], 0) * T.eq(por_linked, 1), pipe_gen_sur_exp, pipe_gen)

        ### por plumbing
                                                                                    # reset if no sub, or por-linked but 0
        cdrc_por = T.le(slots[:, 9], 0) + (T.eq(por_linked, 1) * T.le(slots[:, 7], 0))
                                                                                    # count down failure countdown
        countdown_por = T.switch(cdrc_por, self.g_wait, T.maximum(countdown - 1, -1))

        pipe_por_cond = T.switch(T.eq(por_linked, 1), T.gt(slots[:, 7], 0), 1)      # (if linked, por must be > 0)
        pipe_por_cond = pipe_por_cond * T.gt(slots[:, 9], 0)                        # and (sub > 0)

        pipe_por = slots[:, 10]                                                     # start with sur
        pipe_por = pipe_por + T.gt(slots[:, 6], 0.1)                                # add gen-loop 1 if por > 0
                                                                                    # check if we're in timeout
        pipe_por = T.switch(T.le(countdown, 0) * T.lt(pipe_por, self.g_expect), -1, pipe_por)
        pipe_por = pipe_por * pipe_por_cond                                         # apply conditions
                                                                                    # add por (for search) if sub=sur=0
        pipe_por = pipe_por + (slots[:, 7] * T.eq(slots[:, 9], 0) * T.eq(slots[:, 10], 0))
                                                                                    # reset failure countdown on confirm
        countdown_por = T.switch(T.ge(pipe_por, self.g_expect), self.g_wait, countdown_por)

        ### ret plumbing
        pipe_ret = T.lt(slots[:, 6], 0)                                             # 1 if por is negative
                                                                                    # add ret (for search) if sub=sur=0
        pipe_ret = pipe_ret + (slots[:, 7] * T.eq(slots[:, 8], 0) * T.eq(slots[:, 9], 0))

        ### sub plumbing
        pipe_sub_cond = T.switch(T.eq(por_linked, 1), T.gt(slots[:, 5], 0), 1)      # (if linked, por must be > 0)
        pipe_sub_cond = pipe_sub_cond * T.eq(slots[:, 4], 0)                        # and (gen == 0)

        pipe_sub = slots[:, 7]                                                      # start with sub
        pipe_sub = pipe_sub + slots[:, 9]                                           # add cat
        pipe_sub = pipe_sub * pipe_sub_cond                                         # apply conditions

        ### sur plumbing
                                                                                    # reset if no sub, or por-linked but 0
        cd_reset_cond = T.le(slots[:, 6],0) + (T.eq(por_linked, 1) * T.le(slots[:, 4], 0))
                                                                                    # count down failure countdown
        countdown_sur = T.switch(cd_reset_cond, self.g_wait, T.maximum(countdown - 1, -1))

        pipe_sur_cond = T.eq(por_linked, 0) + T.gt(slots[:, 4], 0)                  # not por-linked or por > 0
        pipe_sur_cond *= slots[:, 6]                                                # and sub > 0
        pipe_sur_cond = T.gt(pipe_sur_cond, 0)

        pipe_sur = slots[:, 7]                                                      # start with sur
        pipe_sur = pipe_sur + T.gt(slots[:, 3], 0.2)                                # add gen-loop 1
        pipe_sur = pipe_sur + slots[:, 9]                                           # add exp
                                                                                    # drop to zero if < expectation
        pipe_sur = T.switch(T.lt(pipe_sur, self.g_expect) * T.gt(pipe_sur, 0), 0, pipe_sur)
                                                                                    # check if we're in timeout
        pipe_sur = T.switch(T.le(countdown, 0) * T.lt(pipe_sur, self.g_expect), -1, pipe_sur)
                                                                                    # reset failure countdown on confirm
        countdown_sur = T.switch(T.ge(pipe_sur, self.g_expect), self.g_wait, countdown_sur)

        pipe_sur = pipe_sur * T.switch(T.eq(ret_linked, 1), slots[:, 5], 1)         # multiply ret if ret-linked
        pipe_sur = pipe_sur * pipe_sur_cond                                         # apply conditions

        ### cat plumbing
        pipe_cat_cond = T.switch(T.eq(por_linked, 1), T.gt(slots[:, 3], 0), 1)      # (if linked, por must be > 0)
        pipe_cat_cond = pipe_cat_cond * T.eq(slots[:, 2], 0)                        # and (gen == 0)

        pipe_cat = slots[:, 5]                                                      # start with sub
        pipe_cat = pipe_cat + slots[:, 7]                                           # add cat
        pipe_cat = pipe_cat * pipe_cat_cond                                         # apply conditions
                                                                                    # add cat (for search) if sub=sur=0
        pipe_cat = pipe_cat + (slots[:, 7] * T.eq(slots[:, 5], 0) * T.eq(slots[:, 6], 0) * T.eq(pipe_cat, 0))

        ### exp plumbing
        pipe_exp = slots[:, 5]                                                      # start with sur
        pipe_exp = pipe_exp + slots[:, 7]                                           # add exp
        pipe_exp = pipe_exp + T.gt(slots[:, 1] * slots[:, 4], 0.2)                  # add gen-loop 1

        if self.has_pipes:
            if self.has_directional_activators:
                nodefunctions = T.switch(T.eq(self.n_function_selector, NFPG_PIPE_GEN), pipe_gen, nodefunctions)
                nodefunctions = T.switch(T.eq(self.n_function_selector, NFPG_PIPE_POR), pipe_por * self.g_factor, nodefunctions)
                nodefunctions = T.switch(T.eq(self.n_function_selector, NFPG_PIPE_RET), pipe_ret * self.g_factor, nodefunctions)
                nodefunctions = T.switch(T.eq(self.n_function_selector, NFPG_PIPE_SUB), pipe_sub * self.g_factor, nodefunctions)
                nodefunctions = T.switch(T.eq(self.n_function_selector, NFPG_PIPE_SUR), pipe_sur * self.g_factor, nodefunctions)
                nodefunctions = T.switch(T.eq(self.n_function_selector, NFPG_PIPE_CAT), pipe_cat * self.g_factor, nodefunctions)
                nodefunctions = T.switch(T.eq(self.n_function_selector, NFPG_PIPE_EXP), pipe_exp * self.g_factor, nodefunctions)
            else:
                nodefunctions = T.switch(T.eq(self.n_function_selector, NFPG_PIPE_GEN), pipe_gen, nodefunctions)
                nodefunctions = T.switch(T.eq(self.n_function_selector, NFPG_PIPE_POR), pipe_por, nodefunctions)
                nodefunctions = T.switch(T.eq(self.n_function_selector, NFPG_PIPE_RET), pipe_ret, nodefunctions)
                nodefunctions = T.switch(T.eq(self.n_function_selector, NFPG_PIPE_SUB), pipe_sub, nodefunctions)
                nodefunctions = T.switch(T.eq(self.n_function_selector, NFPG_PIPE_SUR), pipe_sur, nodefunctions)
                nodefunctions = T.switch(T.eq(self.n_function_selector, NFPG_PIPE_CAT), pipe_cat, nodefunctions)
                nodefunctions = T.switch(T.eq(self.n_function_selector, NFPG_PIPE_EXP), pipe_exp, nodefunctions)
            countdown = T.switch(T.eq(self.n_function_selector, NFPG_PIPE_POR), countdown_por, countdown)
            countdown = T.switch(T.eq(self.n_function_selector, NFPG_PIPE_SUR), countdown_sur, countdown)

        # lstm logic

        ###############################################################
        # lookup table for source activation in a_shifted
        # when calculating the gate on the y axis...
        # ... find the slot at the given index on the x axis
        #
        #       0   1   2   3   4   5   6   7   8   9   10  11  12  13
        # gen                               gen por gin gou gfg
        # por                           gen por gin gou gfg
        # gin                       gen por gin gou gfg
        # gou                   gen por gin gou gfg
        # gfg               gen por gin gou gfg
        #

        sample = T.eq(T.mod(t, 3), 0)
        if self.has_sampling_activators:
            sample = sample * T.gt(self.g_factor, 0.99)

        ### gen
        s = slots[:, 7]
        net_c = slots[:, 8] + biases[:, 8]
        net_in = slots[:, 9] + biases[:, 9]
        net_phi = slots[:, 11] + biases[:, 11]
        y_in = T.nnet.sigmoid(net_in)
        y_phi = T.nnet.sigmoid(net_phi)
        g = (4 * T.nnet.sigmoid(net_c)-2)
        lstm_gen = s * y_phi + g * y_in                                          # gen is next step's s
        lstm_gen = T.switch(sample, lstm_gen, a_prev)

        ### por
        s = slots[:, 6]
        net_c = slots[:, 7] + biases[:, 7]
        net_in = slots[:, 8] + biases[:, 8]
        net_out = slots[:, 9] + biases[:, 9]
        net_phi = slots[:, 10] + biases[:, 10]
        y_in = T.nnet.sigmoid(net_in)
        y_out = T.nnet.sigmoid(net_out)
        y_phi = T.nnet.sigmoid(net_phi)
        g = (4 * T.nnet.sigmoid(net_c)-2)
        s = s * y_phi + g * y_in
        h = (2 * T.nnet.sigmoid(s)-1)                                            # por biases will be ignored
        lstm_por = h * y_out
        lstm_por = T.switch(sample, lstm_por, a_prev)

        ### gin
        lstm_gin = T.nnet.sigmoid(slots[:, 7] + biases[:, 7])
        lstm_gin = T.switch(sample, lstm_gin, a_prev)

        ### gou
        lstm_gou = T.nnet.sigmoid(slots[:, 7] + biases[:, 7])
        lstm_gou = T.switch(sample, lstm_gou, a_prev)

        ### gfg
        lstm_gfg = T.nnet.sigmoid(slots[:, 7] + biases[:, 7])
        lstm_gfg = T.switch(sample, lstm_gfg, a_prev)

        if self.has_lstms:
            nodefunctions = T.switch(T.eq(self.n_function_selector, NFPG_LSTM_GEN), lstm_gen, nodefunctions)
            nodefunctions = T.switch(T.eq(self.n_function_selector, NFPG_LSTM_POR), lstm_por, nodefunctions)
            nodefunctions = T.switch(T.eq(self.n_function_selector, NFPG_LSTM_GIN), lstm_gin, nodefunctions)
            nodefunctions = T.switch(T.eq(self.n_function_selector, NFPG_LSTM_GOU), lstm_gou, nodefunctions)
            nodefunctions = T.switch(T.eq(self.n_function_selector, NFPG_LSTM_GFG), lstm_gfg, nodefunctions)

        # gate logic

        # apply actual gate functions
        gate_function_output = nodefunctions

        # apply GATE_FUNCTION_ABS to masked gates
        if self.has_gatefunction_absolute:
            gate_function_output = T.switch(T.eq(self.g_function_selector, GATE_FUNCTION_ABSOLUTE), abs(gate_function_output), gate_function_output)
        # apply GATE_FUNCTION_SIGMOID to masked gates
        if self.has_gatefunction_sigmoid:
            x = gate_function_output + self.g_bias
            gate_function_output = T.switch(T.eq(self.g_function_selector, GATE_FUNCTION_SIGMOID), N.sigmoid(x), gate_function_output)
        # apply GATE_FUNCTION_ELU to masked gates
        if self.has_gatefunction_elu:
            x = gate_function_output + self.g_bias
            gate_function_output = T.switch(T.eq(self.g_function_selector, GATE_FUNCTION_ELU), T.switch(gate_function_output > 0., x, T.exp(x) - 1.), gate_function_output)
        # apply GATE_FUNCTION_RELU to masked gates
        if self.has_gatefunction_relu:
            x = gate_function_output + self.g_bias
            gate_function_output = T.switch(T.eq(self.g_function_selector, GATE_FUNCTION_RELU), T.maximum(x, 0.), gate_function_output)
            # wait for theano 0.7.1 for this to work
            #gate_function_output = T.switch(T.eq(self.g_function_selector, GATE_FUNCTION_RELU), T.nnet.relu(x), gate_function_output)
        # apply GATE_FUNCTION_DIST to masked gates
        if self.has_gatefunction_one_over_x:
            gate_function_output = T.switch(T.eq(self.g_function_selector, GATE_FUNCTION_DIST), T.switch(T.neq(0, gate_function_output), 1 / gate_function_output, 0), gate_function_output)

        if self.has_gatefunction_threshold:

            # apply threshold
            thresholded_gate_function_output = T.switch(T.eq(self.g_function_selector, GATE_FUNCTION_THRESHOLD), \
                T.switch(T.ge(gate_function_output, self.g_threshold), gate_function_output, 0), gate_function_output)

            # apply amplification
            amplified_gate_function_output = T.switch(T.eq(self.g_function_selector, GATE_FUNCTION_THRESHOLD), thresholded_gate_function_output * self.g_amplification, thresholded_gate_function_output)

            # apply minimum and maximum
            limited_gate_function_output = T.switch(T.eq(self.g_function_selector, GATE_FUNCTION_THRESHOLD), T.clip(amplified_gate_function_output, self.g_min, self.g_max), amplified_gate_function_output)

            gatefunctions = limited_gate_function_output
        else:
            gatefunctions = gate_function_output

        # put the theano graph into a callable function to be executed
        if self.has_pipes:
            self.calculate_nodes = theano.function([], None, updates=[(self.a, gatefunctions), (self.g_countdown, countdown)])
        else:
            self.calculate_nodes = theano.function([], None, updates=[(self.a, gatefunctions)])

    def get_compiled_propagate_inlinks(self, from_partition, from_elements, to_elements, weights):
        propagated_a = T.dot(weights, from_partition.a[from_elements])
        a_in = T.inc_subtensor(self.a_in[to_elements], propagated_a, inplace=True, tolerate_inplace_aliasing=True)
        return theano.function([], None, updates=[(self.a_in, a_in)], accept_inplace=True)

    def get_compiled_propagate_identity_inlinks(self, from_partition, from_elements, to_elements):
        a_in = T.inc_subtensor(self.a_in[to_elements], from_partition.a[from_elements], inplace=True, tolerate_inplace_aliasing=True)
        return theano.function([], None, updates=[(self.a_in, a_in)], accept_inplace=True)

    def calculate(self):

        self.t.set_value(np.int32(self.nodenet.current_step))

        if self.has_new_usages:
            self.compile_propagate()
            self.compile_calculate_nodes()
            self.has_new_usages = False

        if self.por_ret_dirty:
            self.rebuild_por_linked()
            self.rebuild_ret_linked()
            self.por_ret_dirty = False

        self.__take_native_module_slot_snapshots()
        if self.has_pipes or self.has_lstms:
            self.__rebuild_shifted()
        if self.has_directional_activators or self.__has_sampling_activators:
            self.__calculate_g_factors()
        self.__clean_native_module_gates()
        self.calculate_nodes()
        self.__calculate_native_modules()

    def __take_native_module_slot_snapshots(self):
        for uid, instance in self.native_module_instances.items():
            instance.take_slot_activation_snapshot()

    def __clean_native_module_gates(self):
        for uid, instance in self.native_module_instances.items():
            for gate_type in instance.get_gate_types():
                instance.get_gate(gate_type).activation = 0

    def __calculate_native_modules(self):
        for uid, instance in self.native_module_instances.items():
            instance.node_function()

    def __calculate_g_factors(self):
        a = self.a.get_value(borrow=True)
        a[0] = 1.
        g_factor = a[self.allocated_elements_to_activators]
        self.g_factor.set_value(g_factor, borrow=True)

    def __rebuild_shifted(self):
        a_array = self.a.get_value(borrow=True)
        a_rolled_array = np.roll(a_array, 7)
        a_shifted_matrix = np.lib.stride_tricks.as_strided(a_rolled_array, shape=(self.NoE, 14), strides=(self.nodenet.byte_per_float, self.nodenet.byte_per_float))
        self.a_shifted.set_value(a_shifted_matrix, borrow=True)

        g_bias_array = self.g_bias.get_value(borrow=True)
        g_bias_rolled_array = np.roll(g_bias_array, 7)
        g_bias_shifted_matrix = np.lib.stride_tricks.as_strided(g_bias_rolled_array, shape=(self.NoE, 14), strides=(self.nodenet.byte_per_float, self.nodenet.byte_per_float))
        self.g_bias_shifted.set_value(g_bias_shifted_matrix, borrow=True)

    def rebuild_por_linked(self):

        n_node_porlinked_array = np.zeros(self.NoE, dtype=np.int8)

        n_function_selector_array = self.n_function_selector.get_value(borrow=True)
        w_matrix = self.w.get_value(borrow=True)

        por_indices = np.where(n_function_selector_array == NFPG_PIPE_POR)[0]

        slotrows = w_matrix[por_indices, :]
        if not self.sparse:
            linkedflags = np.any(slotrows, axis=1)
        else:
            linkedflags = np.zeros_like(por_indices)
            linkedflags[np.nonzero(slotrows)[0]] = 1

        n_node_porlinked_array[por_indices - 1] = linkedflags       # gen
        n_node_porlinked_array[por_indices] = linkedflags           # por
        n_node_porlinked_array[por_indices + 1] = linkedflags       # ret
        n_node_porlinked_array[por_indices + 2] = linkedflags       # sub
        n_node_porlinked_array[por_indices + 3] = linkedflags       # sur
        n_node_porlinked_array[por_indices + 4] = linkedflags       # sub
        n_node_porlinked_array[por_indices + 5] = linkedflags       # sur

        self.n_node_porlinked.set_value(n_node_porlinked_array)

    def rebuild_ret_linked(self):

        n_node_retlinked_array = np.zeros(self.NoE, dtype=np.int8)

        n_function_selector_array = self.n_function_selector.get_value(borrow=True)
        w_matrix = self.w.get_value(borrow=True)

        ret_indices = np.where(n_function_selector_array == NFPG_PIPE_RET)[0]

        slotrows = w_matrix[ret_indices, :]
        if not self.sparse:
            linkedflags = np.any(slotrows, axis=1)
        else:
            linkedflags = np.zeros_like(ret_indices)
            linkedflags[np.nonzero(slotrows)[0]] = 1

        n_node_retlinked_array[ret_indices - 2] = linkedflags       # gen
        n_node_retlinked_array[ret_indices - 1] = linkedflags       # por
        n_node_retlinked_array[ret_indices] = linkedflags           # ret
        n_node_retlinked_array[ret_indices + 1] = linkedflags       # sub
        n_node_retlinked_array[ret_indices + 2] = linkedflags       # sur
        n_node_retlinked_array[ret_indices + 3] = linkedflags       # cat
        n_node_retlinked_array[ret_indices + 4] = linkedflags       # exp

        self.n_node_retlinked.set_value(n_node_retlinked_array)

    def grow_number_of_nodes(self, growby):
        new_NoN = int(self.NoN + growby)

        new_allocated_nodes = np.zeros(new_NoN, dtype=np.int32)
        new_allocated_nodes[0:self.NoN] = self.allocated_nodes
        self.allocated_nodes = new_allocated_nodes

        new_allocated_node_parents = np.zeros(new_NoN, dtype=np.int32)
        new_allocated_node_parents[0:self.NoN] = self.allocated_node_parents
        self.allocated_node_parents = new_allocated_node_parents

        new_allocated_node_offsets = np.zeros(new_NoN, dtype=np.int32)
        new_allocated_node_offsets[0:self.NoN] = self.allocated_node_offsets
        self.allocated_node_offsets = new_allocated_node_offsets

        new_node_changed_offsets = np.zeros(new_NoN, dtype=np.int32)
        new_node_changed_offsets[0:self.NoN] = self.nodes_last_changed
        self.nodes_last_changed = new_node_changed_offsets

        self.NoN = new_NoN
        self.has_new_usages = True

    def save(self, base_path=None, zipfile=None):
        if base_path is None:
            base_path = self.nodenet.persistency_path

        allocated_nodes = self.allocated_nodes
        allocated_node_offsets = self.allocated_node_offsets
        allocated_elements_to_nodes = self.allocated_elements_to_nodes
        allocated_node_parents = self.allocated_node_parents
        allocated_nodespaces = self.allocated_nodespaces
        allocated_elements_to_activators = self.allocated_elements_to_activators

        allocated_nodespaces_por_activators = self.allocated_nodespaces_por_activators
        allocated_nodespaces_ret_activators = self.allocated_nodespaces_ret_activators
        allocated_nodespaces_sub_activators = self.allocated_nodespaces_sub_activators
        allocated_nodespaces_sur_activators = self.allocated_nodespaces_sur_activators
        allocated_nodespaces_cat_activators = self.allocated_nodespaces_cat_activators
        allocated_nodespaces_exp_activators = self.allocated_nodespaces_exp_activators

        allocated_nodespaces_sampling_activators = self.allocated_nodespaces_sampling_activators

        w = self.w.get_value(borrow=True)

        # if we're sparse, convert to sparse matrix for persistency
        if not self.sparse:
            w = sp.csr_matrix(w)

        a = self.a.get_value(borrow=True)
        g_bias = self.g_bias.get_value(borrow=True)
        g_factor = self.g_factor.get_value(borrow=True)
        g_threshold = self.g_threshold.get_value(borrow=True)
        g_amplification = self.g_amplification.get_value(borrow=True)
        g_min = self.g_min.get_value(borrow=True)
        g_max = self.g_max.get_value(borrow=True)
        g_function_selector = self.g_function_selector.get_value(borrow=True)
        g_expect = self.g_expect.get_value(borrow=True)
        g_countdown = self.g_countdown.get_value(borrow=True)
        g_wait = self.g_wait.get_value(borrow=True)
        n_function_selector = self.n_function_selector.get_value(borrow=True)

        sizeinformation = [self.NoN, self.NoE, self.NoNS]

        for spid, inlinks in self.inlinks.items():
            filename = "inlinks-%s-from-%s.npz" % (self.spid, spid)
            data = {
                'from_partition_id': spid,
                'from_ids': inlinks[0].get_value(borrow=True),
                'to_ids': inlinks[1].get_value(borrow=True),
                'weights': inlinks[2].get_value(borrow=True) if inlinks[2] else None,
                'inlink_type': inlinks[4]
            }
            if zipfile:
                stream = io.BytesIO()
                np.savez(stream, **data)
                stream.seek(0)
                zipfile.writestr(filename, stream.getvalue())
            else:
                np.savez(os.path.join(base_path, filename), **data)
        filename = "partition-%s.npz" % self.spid
        data = {
            'allocated_nodes': allocated_nodes,
            'allocated_node_offsets': allocated_node_offsets,
            'allocated_elements_to_nodes': allocated_elements_to_nodes,
            'allocated_node_parents': allocated_node_parents,
            'allocated_nodespaces': allocated_nodespaces,
            'w_data': w.data,
            'w_indices': w.indices,
            'w_indptr': w.indptr,
            'a': a,
            'g_bias': g_bias,
            'g_factor': g_factor,
            'g_threshold': g_threshold,
            'g_amplification': g_amplification,
            'g_min': g_min,
            'g_max': g_max,
            'g_function_selector': g_function_selector,
            'g_expect': g_expect,
            'g_countdown': g_countdown,
            'g_wait': g_wait,
            'n_function_selector': n_function_selector,
            'sizeinformation': sizeinformation,
            'allocated_elements_to_activators': allocated_elements_to_activators,
            'allocated_nodespaces_por_activators': allocated_nodespaces_por_activators,
            'allocated_nodespaces_ret_activators': allocated_nodespaces_ret_activators,
            'allocated_nodespaces_sub_activators': allocated_nodespaces_sub_activators,
            'allocated_nodespaces_sur_activators': allocated_nodespaces_sur_activators,
            'allocated_nodespaces_cat_activators': allocated_nodespaces_cat_activators,
            'allocated_nodespaces_exp_activators': allocated_nodespaces_exp_activators,
            'allocated_nodespaces_sampling_activators': allocated_nodespaces_sampling_activators
        }
        if zipfile:
            stream = io.BytesIO()
            np.savez(stream, **data)
            stream.seek(0)
            zipfile.writestr(filename, stream.getvalue())
        else:
            np.savez(os.path.join(base_path, filename), **data)

    def load_data(self, nodes_data, invalid_uids=[]):
        """Load the node net from a file"""
        # try to access file

        base_path = self.nodenet.persistency_path
        filename = os.path.join(base_path, "partition-%s.npz" % self.spid)
        datafile = None
        if os.path.isfile(filename):
            try:
                self.logger.info("Loading nodenet %s partition %i bulk data from file %s" % (self.nodenet.name, self.pid, filename))
                datafile = np.load(filename)
            except ValueError:  # pragma: no cover
                self.logger.warning("Could not read partition data from file %s" % filename)
                return False
            except IOError:  # pragma: no cover
                self.logger.warning("Could not open partition file %s" % filename)
                return False

        if not datafile:
            return

        if 'sizeinformation' in datafile:
            self.NoN = datafile['sizeinformation'][0]
            self.NoE = datafile['sizeinformation'][1]
            self.NoNS = datafile['sizeinformation'][2]

            # rebuild the ephemerals
            self.nodes_last_changed = np.zeros(self.NoN, dtype=np.int32) - 1
            self.nodespaces_last_changed = np.zeros(self.NoNS, dtype=np.int32) - 1
            self.nodespaces_contents_last_changed = np.zeros(self.NoNS, dtype=np.int32) - 1

            a_prev_array = np.zeros(self.NoE, dtype=self.nodenet.numpyfloatX)
            self.a_prev = theano.shared(value=a_prev_array.astype(T.config.floatX), name="a_prev", borrow=True)

        else:
            self.logger.warning("no sizeinformation in file, falling back to defaults")  # pragma: no cover

        # the load bulk data into numpy arrays
        if 'allocated_nodes' in datafile:
            self.allocated_nodes = datafile['allocated_nodes']
        else:
            self.logger.warning("no allocated_nodes in file, falling back to defaults")  # pragma: no cover

        if 'allocated_node_offsets' in datafile:
            self.allocated_node_offsets = datafile['allocated_node_offsets']
        else:
            self.logger.warning("no allocated_node_offsets in file, falling back to defaults")  # pragma: no cover

        if 'allocated_elements_to_nodes' in datafile:
            self.allocated_elements_to_nodes = datafile['allocated_elements_to_nodes']
        else:
            self.logger.warning("no allocated_elements_to_nodes in file, falling back to defaults")  # pragma: no cover

        if 'allocated_nodespaces' in datafile:
            self.allocated_nodespaces = datafile['allocated_nodespaces']
        else:
            self.logger.warning("no allocated_nodespaces in file, falling back to defaults")  # pragma: no cover

        if 'allocated_node_parents' in datafile:
            self.allocated_node_parents = datafile['allocated_node_parents']
        else:
            self.logger.warning("no allocated_node_parents in file, falling back to defaults")  # pragma: no cover

        if 'allocated_elements_to_activators' in datafile:
            self.allocated_elements_to_activators = datafile['allocated_elements_to_activators']
        else:
            self.logger.warning("no allocated_elements_to_activators in file, falling back to defaults")  # pragma: no cover

        if 'allocated_nodespaces_por_activators' in datafile:
            self.allocated_nodespaces_por_activators = datafile['allocated_nodespaces_por_activators']
        else:
            self.logger.warning("no allocated_nodespaces_por_activators in file, falling back to defaults")  # pragma: no cover

        if 'allocated_nodespaces_ret_activators' in datafile:
            self.allocated_nodespaces_ret_activators = datafile['allocated_nodespaces_ret_activators']
        else:
            self.logger.warning("no allocated_nodespaces_ret_activators in file, falling back to defaults")  # pragma: no cover

        if 'allocated_nodespaces_sub_activators' in datafile:
            self.allocated_nodespaces_sub_activators = datafile['allocated_nodespaces_sub_activators']
        else:
            self.logger.warning("no allocated_nodespaces_sub_activators in file, falling back to defaults")  # pragma: no cover

        if 'allocated_nodespaces_sur_activators' in datafile:
            self.allocated_nodespaces_sur_activators = datafile['allocated_nodespaces_sur_activators']
        else:
            self.logger.warning("no allocated_nodespaces_sur_activators in file, falling back to defaults")  # pragma: no cover

        if 'allocated_nodespaces_cat_activators' in datafile:
            self.allocated_nodespaces_cat_activators = datafile['allocated_nodespaces_cat_activators']
        else:
            self.logger.warning("no allocated_nodespaces_cat_activators in file, falling back to defaults")  # pragma: no cover

        if 'allocated_nodespaces_exp_activators' in datafile:
            self.allocated_nodespaces_exp_activators = datafile['allocated_nodespaces_exp_activators']
        else:
            self.logger.warning("no allocated_nodespaces_exp_activators in file, falling back to defaults")  # pragma: no cover

        if 'allocated_nodespaces_sampling_activators' in datafile:
            self.allocated_nodespaces_sampling_activators = datafile['allocated_nodespaces_sampling_activators']
        else:
            self.logger.warning("no allocated_nodespaces_por_activators in file, falling back to defaults")  # pragma: no cover

        if 'w_data' in datafile and 'w_indices' in datafile and 'w_indptr' in datafile:
            w = sp.csr_matrix((datafile['w_data'], datafile['w_indices'], datafile['w_indptr']), shape = (self.NoE, self.NoE))
            # if we're configured to be dense, convert from csr
            if not self.sparse:
                w = w.todense()
            self.w = theano.shared(value=w.astype(T.config.floatX), name="w", borrow=False)
            self.a = theano.shared(value=datafile['a'].astype(T.config.floatX), name="a", borrow=False)
            self.a_in = theano.shared(value=np.zeros_like(datafile['a']).astype(T.config.floatX), name="a_in", borrow=False)
        else:
            self.logger.warning("no w_data, w_indices or w_indptr in file, falling back to defaults")  # pragma: no cover

        if 'g_bias' in datafile:
            self.g_bias = theano.shared(value=datafile['g_bias'].astype(T.config.floatX), name="bias", borrow=False)
        else:
            self.logger.warning("no g_bias in file, falling back to defaults")  # pragma: no cover

        if 'g_factor' in datafile:
            self.g_factor = theano.shared(value=datafile['g_factor'].astype(T.config.floatX), name="g_factor", borrow=False)
        else:
            self.logger.warning("no g_factor in file, falling back to defaults")  # pragma: no cover

        if 'g_threshold' in datafile:
            self.g_threshold = theano.shared(value=datafile['g_threshold'].astype(T.config.floatX), name="g_threshold", borrow=False)
        else:
            self.logger.warning("no g_threshold in file, falling back to defaults")  # pragma: no cover

        if 'g_amplification' in datafile:
            self.g_amplification = theano.shared(value=datafile['g_amplification'].astype(T.config.floatX), name="g_amplification", borrow=False)
        else:
            self.logger.warning("no g_amplification in file, falling back to defaults")  # pragma: no cover

        if 'g_min' in datafile:
            self.g_min = theano.shared(value=datafile['g_min'].astype(T.config.floatX), name="g_min", borrow=False)
        else:
            self.logger.warning("no g_min in file, falling back to defaults")  # pragma: no cover

        if 'g_max' in datafile:
            self.g_max = theano.shared(value=datafile['g_max'].astype(T.config.floatX), name="g_max", borrow=False)
        else:
            self.logger.warning("no g_max in file, falling back to defaults")  # pragma: no cover

        if 'g_function_selector' in datafile:
            self.g_function_selector = theano.shared(value=datafile['g_function_selector'], name="gatefunction", borrow=False)
        else:
            self.logger.warning("no g_function_selector in file, falling back to defaults")  # pragma: no cover

        if 'g_expect' in datafile:
            self.g_expect = theano.shared(value=datafile['g_expect'], name="expectation", borrow=False)
        else:
            self.logger.warning("no g_expect in file, falling back to defaults")  # pragma: no cover

        if 'g_countdown' in datafile:
            self.g_countdown = theano.shared(value=datafile['g_countdown'], name="countdown", borrow=False)
        else:
            self.logger.warning("no g_countdown in file, falling back to defaults")  # pragma: no cover

        if 'g_wait' in datafile:
            self.g_wait = theano.shared(value=datafile['g_wait'], name="wait", borrow=False)
        else:
            self.logger.warning("no g_wait in file, falling back to defaults")  # pragma: no cover

        if 'n_function_selector' in datafile:
            self.n_function_selector = theano.shared(value=datafile['n_function_selector'], name="nodefunction_per_gate", borrow=False)
        else:
            self.logger.warning("no n_function_selector in file, falling back to defaults")  # pragma: no cover

        # reconstruct other states
        self.por_ret_dirty = True

        if 'g_function_selector' in datafile:
            g_function_selector = datafile['g_function_selector']
            self.has_new_usages = True
            self.has_pipes = PIPE in self.allocated_nodes
            self.has_lstms = LSTM in self.allocated_nodes
            self.has_directional_activators = \
                np.sum(self.allocated_nodespaces_por_activators) > 0 or \
                np.sum(self.allocated_nodespaces_ret_activators) > 0 or \
                np.sum(self.allocated_nodespaces_sub_activators) > 0 or \
                np.sum(self.allocated_nodespaces_sur_activators) > 0 or \
                np.sum(self.allocated_nodespaces_cat_activators) > 0 or \
                np.sum(self.allocated_nodespaces_exp_activators) > 0

            self.has_sampling_activators = np.sum(self.allocated_nodespaces_sampling_activators) > 0
            self.has_gatefunction_absolute = GATE_FUNCTION_ABSOLUTE in g_function_selector
            self.has_gatefunction_sigmoid = GATE_FUNCTION_SIGMOID in g_function_selector
            self.has_gatefunction_relu = GATE_FUNCTION_RELU in g_function_selector
            self.has_gatefunction_one_over_x = GATE_FUNCTION_DIST in g_function_selector
            self.has_gatefunction_elu = GATE_FUNCTION_ELU in g_function_selector
            self.has_gatefunction_threshold = GATE_FUNCTION_THRESHOLD in g_function_selector
        else:
            self.logger.warning("no g_function_selector in file, falling back to defaults")

        datafile.close()

        for uid in invalid_uids:
            if self.nodenet.get_partition(uid) == self:
                w_matrix = self.w.get_value()
                id = node_from_id(uid)
                self.allocated_nodes[id] = 0
                self.allocated_node_parents[id] = 0
                els = self.allocated_elements_to_nodes[np.where(self.allocated_elements_to_nodes == id)]
                w_matrix[els] = 0
                self.allocated_elements_to_nodes[np.where(self.allocated_elements_to_nodes == id)] = 0
                self.w.set_value(w_matrix)

        for id in np.nonzero(self.allocated_nodes)[0]:
            if self.allocated_nodes[id] > MAX_STD_NODETYPE:
                uid = node_to_id(id, self.pid)
                if uid in nodes_data:
                    try:
                        self.allocated_nodes[id] = get_numerical_node_type(nodes_data[uid]['type'], self.nodenet.native_modules)
                    except ValueError:
                        self.allocated_nodes[id] = 0
                        self.allocated_elements_to_nodes[np.where(self.allocated_elements_to_nodes == id)] = 0
            if self.allocated_nodes[id] > MAX_STD_NODETYPE:
                self.native_module_instances[uid] = self.nodenet.get_node(uid)
            elif self.allocated_nodes[id] == COMMENT:
                uid = node_to_id(id, self.pid)
                self.comment_instances[uid] = self.nodenet.get_node(uid)

        # initialize early
        self.t.set_value(np.int32(self.nodenet.current_step))

        if self.has_new_usages:
            self.compile_propagate()
            self.compile_calculate_nodes()
            self.has_new_usages = False

        if self.por_ret_dirty:
            self.rebuild_por_linked()
            self.rebuild_ret_linked()
            self.por_ret_dirty = False

        self.__take_native_module_slot_snapshots()
        if self.has_pipes or self.has_lstms:
            self.__rebuild_shifted()
        if self.has_directional_activators or self.__has_sampling_activators:
            self.__calculate_g_factors()

    def load_inlinks(self):
        base_path = self.nodenet.persistency_path
        for spid in self.nodenet.partitions:
            filename = os.path.join(base_path, "inlinks-%s-from-%s.npz" % (self.spid, spid))
            if os.path.isfile(filename):
                datafile = np.load(filename)

                if str(datafile['inlink_type']) == 'identity':
                    weights = 1
                else:
                    weights = datafile['weights']

                self.set_inlink_weights(
                    str(datafile['from_partition_id']),
                    datafile['from_ids'],
                    datafile['to_ids'],
                    weights)
                datafile.close()

    def grow_number_of_nodespaces(self, growby):

        new_NoNS = int(self.NoNS + growby)

        new_allocated_nodespaces = np.zeros(new_NoNS, dtype=np.int32)
        new_allocated_nodespaces[0:self.NoNS] = self.allocated_nodespaces
        self.allocated_nodespaces = new_allocated_nodespaces

        new_allocated_nodespaces_por_activators = np.zeros(new_NoNS, dtype=np.int32)
        new_allocated_nodespaces_por_activators[0:self.NoNS] = self.allocated_nodespaces_por_activators
        self.allocated_nodespaces_por_activators = new_allocated_nodespaces_por_activators

        new_allocated_nodespaces_ret_activators = np.zeros(new_NoNS, dtype=np.int32)
        new_allocated_nodespaces_ret_activators[0:self.NoNS] = self.allocated_nodespaces_ret_activators
        self.allocated_nodespaces_ret_activators = new_allocated_nodespaces_ret_activators

        new_allocated_nodespaces_sub_activators = np.zeros(new_NoNS, dtype=np.int32)
        new_allocated_nodespaces_sub_activators[0:self.NoNS] = self.allocated_nodespaces_sub_activators
        self.allocated_nodespaces_sub_activators = new_allocated_nodespaces_sub_activators

        new_allocated_nodespaces_sur_activators = np.zeros(new_NoNS, dtype=np.int32)
        new_allocated_nodespaces_sur_activators[0:self.NoNS] = self.allocated_nodespaces_sur_activators
        self.allocated_nodespaces_sur_activators = new_allocated_nodespaces_sur_activators

        new_allocated_nodespaces_cat_activators = np.zeros(new_NoNS, dtype=np.int32)
        new_allocated_nodespaces_cat_activators[0:self.NoNS] = self.allocated_nodespaces_cat_activators
        self.allocated_nodespaces_cat_activators = new_allocated_nodespaces_cat_activators

        new_allocated_nodespaces_exp_activators = np.zeros(new_NoNS, dtype=np.int32)
        new_allocated_nodespaces_exp_activators[0:self.NoNS] = self.allocated_nodespaces_exp_activators
        self.allocated_nodespaces_exp_activators = new_allocated_nodespaces_exp_activators

        new_allocated_nodespaces_sampling_activators = np.zeros(new_NoNS, dtype=np.int32)
        new_allocated_nodespaces_sampling_activators[0:self.NoNS] = self.allocated_nodespaces_sampling_activators
        self.allocated_nodespaces_sampling_activators = new_allocated_nodespaces_sampling_activators

        new_nodespaces_last_changed = np.zeros(new_NoNS, dtype=np.int32)
        new_nodespaces_last_changed[0:self.NoNS] = self.nodespaces_last_changed
        self.nodespaces_last_changed = new_nodespaces_last_changed

        new_nodespaces_contents_last_changed = np.zeros(new_NoNS, dtype=np.int32)
        new_nodespaces_contents_last_changed[0:self.NoNS] = self.nodespaces_contents_last_changed
        self.nodespaces_contents_last_changed = new_nodespaces_contents_last_changed

        self.has_new_usages = True
        self.NoNS = new_NoNS

    def grow_number_of_elements(self, growby):

        new_NoE = int(self.NoE + growby)

        new_allocated_elements_to_nodes = np.zeros(new_NoE, dtype=np.int32)
        new_allocated_elements_to_nodes[0:self.NoE] = self.allocated_elements_to_nodes
        self.allocated_elements_to_nodes = new_allocated_elements_to_nodes

        new_allocated_elements_to_activators = np.zeros(new_NoE, dtype=np.int32)
        new_allocated_elements_to_activators[0:self.NoE] = self.allocated_elements_to_activators
        self.allocated_elements_to_activators = new_allocated_elements_to_activators

        if self.sparse:
            new_w = sp.csr_matrix((new_NoE, new_NoE), dtype=self.nodenet.numpyfloatX)
        else:
            new_w = np.zeros((new_NoE, new_NoE), dtype=self.nodenet.numpyfloatX)
        new_w[0:self.NoE, 0:self.NoE] = self.w.get_value(borrow=True)
        self.w.set_value(new_w, borrow=True)

        new_a = np.zeros(new_NoE, dtype=self.nodenet.numpyfloatX)
        new_a[0:self.NoE] = self.a.get_value(borrow=True)
        self.a.set_value(new_a, borrow=True)

        new_a_shifted = np.lib.stride_tricks.as_strided(new_a, shape=(new_NoE, 7), strides=(self.nodenet.byte_per_float, self.nodenet.byte_per_float))
        self.a_shifted.set_value(new_a_shifted, borrow=True)

        new_a_in = np.zeros(new_NoE, dtype=self.nodenet.numpyfloatX)
        new_a_in[0:self.NoE] = self.a_in.get_value(borrow=True)
        self.a_in.set_value(new_a_in, borrow=True)

        new_a_prev = np.zeros(new_NoE, dtype=self.nodenet.numpyfloatX)
        new_a_prev[0:self.NoE] = self.a_prev.get_value(borrow=True)
        self.a_prev.set_value(new_a_prev, borrow=True)

        new_g_bias = np.zeros(new_NoE, dtype=self.nodenet.numpyfloatX)
        new_g_bias[0:self.NoE] = self.g_bias.get_value(borrow=True)
        self.g_bias.set_value(new_g_bias, borrow=True)

        new_g_bias_shifted = np.lib.stride_tricks.as_strided(new_g_bias, shape=(self.NoE, 7), strides=(self.nodenet.byte_per_float, self.nodenet.byte_per_float))
        self.g_bias_shifted.set_value(new_g_bias_shifted, borrow=True)

        new_g_factor = np.ones(new_NoE, dtype=self.nodenet.numpyfloatX)
        new_g_factor[0:self.NoE] = self.g_factor.get_value(borrow=True)
        self.g_factor.set_value(new_g_factor, borrow=True)

        new_g_threshold = np.zeros(new_NoE, dtype=self.nodenet.numpyfloatX)
        new_g_threshold[0:self.NoE] = self.g_threshold.get_value(borrow=True)
        self.g_threshold.set_value(new_g_threshold, borrow=True)

        new_g_amplification = np.ones(new_NoE, dtype=self.nodenet.numpyfloatX)
        new_g_amplification[0:self.NoE] = self.g_amplification.get_value(borrow=True)
        self.g_amplification.set_value(new_g_amplification, borrow=True)

        new_g_min = np.zeros(new_NoE, dtype=self.nodenet.numpyfloatX)
        new_g_min[0:self.NoE] = self.g_min.get_value(borrow=True)
        self.g_min.set_value(new_g_min, borrow=True)

        new_g_max = np.ones(new_NoE, dtype=self.nodenet.numpyfloatX)
        new_g_max[0:self.NoE] = self.g_max.get_value(borrow=True)
        self.g_max.set_value(new_g_max, borrow=True)

        new_g_function_selector = np.zeros(new_NoE, dtype=np.int8)
        new_g_function_selector[0:self.NoE] = self.g_function_selector.get_value(borrow=True)
        self.g_function_selector.set_value(new_g_function_selector, borrow=True)

        new_g_expect = np.ones(new_NoE, dtype=self.nodenet.numpyfloatX)
        new_g_expect[0:self.NoE] = self.g_expect.get_value(borrow=True)
        self.g_expect.set_value(new_g_expect, borrow=True)

        new_g_countdown = np.zeros(new_NoE, dtype=np.int16)
        new_g_countdown[0:self.NoE] = self.g_countdown.get_value(borrow=True)
        self.g_countdown.set_value(new_g_countdown, borrow=True)

        new_g_wait = np.ones(new_NoE, dtype=np.int16)
        new_g_wait[0:self.NoE] = self.g_wait.get_value(borrow=True)
        self.g_wait.set_value(new_g_wait, borrow=True)

        new_n_function_selector = np.zeros(new_NoE, dtype=np.int8)
        new_n_function_selector[0:self.NoE] = self.n_function_selector.get_value(borrow=True)
        self.n_function_selector.set_value(new_n_function_selector, borrow=True)

        new_n_node_porlinked = np.zeros(new_NoE, dtype=np.int8)
        self.n_node_porlinked.set_value(new_n_node_porlinked, borrow=True)

        new_n_node_retlinked = np.zeros(new_NoE, dtype=np.int8)
        self.n_node_retlinked.set_value(new_n_node_retlinked, borrow=True)

        self.NoE = new_NoE
        self.has_new_usages = True

        if self.has_pipes:
            self.por_ret_dirty = True

    def announce_nodes(self, number_of_nodes, average_elements_per_node):

        free_nodes = self.NoN - np.count_nonzero(self.allocated_nodes)
        free_elements = self.NoE - np.count_nonzero(self.allocated_elements_to_nodes)

        if number_of_nodes > free_nodes:
            gap = number_of_nodes - free_nodes
            growby = gap + (gap // 3)
            self.logger.info("Per announcement in partition %i, growing ID vectors by %d elements" % (self.pid, growby))
            self.grow_number_of_nodes(growby)

        number_of_elements = number_of_nodes*average_elements_per_node
        if number_of_elements > free_elements:
            gap = number_of_elements - free_elements
            growby = gap + (gap // 3)
            self.logger.info("Per announcement in partition %i, growing elements vectors by %d elements" % (self.pid, growby))
            self.grow_number_of_elements(gap + (gap //3))

    def create_node(self, nodetype, nodespace_id, id=None, parameters=None, gate_configuration=None):

        # find a free ID / index in the allocated_nodes vector to hold the node type
        if id is None:
            id = 0
            for i in range((self.last_allocated_node + 1), self.NoN):
                if self.allocated_nodes[i] == 0:
                    id = i
                    break

            if id < 1:
                for i in range(self.last_allocated_node - 1):
                    if self.allocated_nodes[i] == 0:
                        id = i
                        break

            if id < 1:
                growby = self.NoN // 2
                self.logger.info("All %d node IDs in partition %i in use, growing id vectors by %d elements" % (self.NoN, self.pid, growby))
                id = self.NoN
                self.grow_number_of_nodes(growby)

        else:
            if id > self.NoN:
                growby = id - (self.NoN - 2)
                self.logger.info("Requested ID larger than current size in partition %i, growing id vectors by %d elements" % (self.pid, growby))
                self.grow_number_of_nodes(growby)

        # now find a range of free elements to be used by this node
        number_of_elements = get_elements_per_type(get_numerical_node_type(nodetype, self.nodenet.native_modules), self.nodenet.native_modules)
        has_restarted_from_zero = False
        offset = 0
        i = self.last_allocated_offset + 1
        while offset < 1:
            freecount = 0
            for j in range(0, number_of_elements):
                if i+j < len(self.allocated_elements_to_nodes) and self.allocated_elements_to_nodes[i+j] == 0:
                    freecount += 1
                else:
                    break
            if freecount >= number_of_elements:
                offset = i
                break
            else:
                i += freecount+1

            if i >= self.NoE:
                if not has_restarted_from_zero:
                    i = 0
                    has_restarted_from_zero = True
                else:
                    growby = max(number_of_elements +1, self.NoE // 2)
                    self.logger.info("All %d elements in use in partition %i, growing elements vectors by %d elements" % (self.NoE, self.pid, growby))
                    offset = self.NoE
                    self.grow_number_of_elements(growby)

        uid = node_to_id(id, self.pid)

        self.last_allocated_node = id
        self.last_allocated_offset = offset
        self.allocated_nodes[id] = get_numerical_node_type(nodetype, self.nodenet.native_modules)
        self.nodes_last_changed[id] = self.nodenet.current_step
        self.allocated_node_parents[id] = nodespace_id
        self.allocated_node_offsets[id] = offset
        if nodespace_id < len(self.nodespaces_contents_last_changed):
            # due to the order of initializing, nodespaces might just not be here yet.
            self.nodespaces_contents_last_changed[nodespace_id] = self.nodenet.current_step

        if number_of_elements > 0:
            elrange = np.asarray(range(offset, offset + number_of_elements))
            self.allocated_elements_to_nodes[elrange] = id

        if parameters is None:
            parameters = {}
        if gate_configuration is None:
            gate_configuration = {}

        nto = self.nodenet.get_nodetype(nodetype)

        if nodetype == "Pipe":
            self.has_pipes = True
            n_function_selector_array = self.n_function_selector.get_value(borrow=True)
            n_function_selector_array[offset + GEN] = NFPG_PIPE_GEN
            n_function_selector_array[offset + POR] = NFPG_PIPE_POR
            n_function_selector_array[offset + RET] = NFPG_PIPE_RET
            n_function_selector_array[offset + SUB] = NFPG_PIPE_SUB
            n_function_selector_array[offset + SUR] = NFPG_PIPE_SUR
            n_function_selector_array[offset + CAT] = NFPG_PIPE_CAT
            n_function_selector_array[offset + EXP] = NFPG_PIPE_EXP
            self.n_function_selector.set_value(n_function_selector_array, borrow=True)
            self.allocated_elements_to_activators[offset + POR] = \
                self.allocated_node_offsets[self.allocated_nodespaces_por_activators[nodespace_id]]
            self.allocated_elements_to_activators[offset + RET] = \
                self.allocated_node_offsets[self.allocated_nodespaces_ret_activators[nodespace_id]]
            self.allocated_elements_to_activators[offset + SUB] = \
                self.allocated_node_offsets[self.allocated_nodespaces_sub_activators[nodespace_id]]
            self.allocated_elements_to_activators[offset + SUR] = \
                self.allocated_node_offsets[self.allocated_nodespaces_sur_activators[nodespace_id]]
            self.allocated_elements_to_activators[offset + CAT] = \
                self.allocated_node_offsets[self.allocated_nodespaces_cat_activators[nodespace_id]]
            self.allocated_elements_to_activators[offset + EXP] = \
                self.allocated_node_offsets[self.allocated_nodespaces_exp_activators[nodespace_id]]

            if nto.parameter_defaults.get('expectation'):
                value = float(parameters.get('expectation', nto.parameter_defaults['expectation']))
                g_expect_array = self.g_expect.get_value(borrow=True)
                g_expect_array[offset + GEN] = float(value)
                g_expect_array[offset + SUR] = float(value)
                g_expect_array[offset + POR] = float(value)
                self.g_expect.set_value(g_expect_array, borrow=True)

            if nto.parameter_defaults.get('wait'):
                value = int(parameters.get('wait', nto.parameter_defaults['wait']))
                g_wait_array = self.g_wait.get_value(borrow=True)
                g_wait_array[offset + SUR] = int(min(value, 128))
                g_wait_array[offset + POR] = int(min(value, 128))
                self.g_wait.set_value(g_wait_array, borrow=True)
        elif nodetype == "LSTM":
            self.has_lstms = True
            n_function_selector_array = self.n_function_selector.get_value(borrow=True)
            n_function_selector_array[offset + GEN] = NFPG_LSTM_GEN
            n_function_selector_array[offset + POR] = NFPG_LSTM_POR
            n_function_selector_array[offset + GIN] = NFPG_LSTM_GIN
            n_function_selector_array[offset + GOU] = NFPG_LSTM_GOU
            n_function_selector_array[offset + GFG] = NFPG_LSTM_GFG
            self.n_function_selector.set_value(n_function_selector_array, borrow=True)

            self.allocated_elements_to_activators[offset + GEN] = \
                self.allocated_node_offsets[self.allocated_nodespaces_sampling_activators[nodespace_id]]
            self.allocated_elements_to_activators[offset + POR] = \
                self.allocated_node_offsets[self.allocated_nodespaces_sampling_activators[nodespace_id]]
            self.allocated_elements_to_activators[offset + GIN] = \
                self.allocated_node_offsets[self.allocated_nodespaces_sampling_activators[nodespace_id]]
            self.allocated_elements_to_activators[offset + GOU] = \
                self.allocated_node_offsets[self.allocated_nodespaces_sampling_activators[nodespace_id]]
            self.allocated_elements_to_activators[offset + GFG] = \
                self.allocated_node_offsets[self.allocated_nodespaces_sampling_activators[nodespace_id]]

        elif nodetype == "Activator":
            self.has_directional_activators = True
            activator_type = parameters.get("type")
            if activator_type is not None and len(activator_type) > 0:
                if activator_type != "sampling":
                    self.set_nodespace_gatetype_activator(nodespace_id, activator_type, id)
                else:
                    self.set_nodespace_sampling_activator(nodespace_id, id)

        if nodetype not in self.nodenet.get_standard_nodetype_definitions():
            node_proxy = self.nodenet.get_node(uid)
            self.native_module_instances[uid] = node_proxy
            for key, value in parameters.items():
                node_proxy.set_parameter(key, value)
        elif nodetype == "Comment":
            node_proxy = self.nodenet.get_node(uid)
            self.comment_instances[uid] = node_proxy
            for key in self.nodenet.get_standard_nodetype_definitions()[nodetype]['parameters']:
                node_proxy.set_parameter(key, parameters.get(key, ''))

        for gate, conf in gate_configuration.items():
            idx = offset + get_numerical_gate_type(gate)
            for param, value in conf['gatefunction_parameters'].items():
                self._set_gate_config_for_elements([idx], conf['gatefunction'], param, [value])

        # initialize activation to zero
        a_array = self.a.get_value(borrow=True)
        for element in range(0, get_elements_per_type(get_numerical_node_type(nodetype, self.nodenet.native_modules), self.nodenet.native_modules)):
            a_array[offset + element] = 0
        self.a.set_value(a_array)

        return id

    def delete_node(self, node_id):

        type = self.allocated_nodes[node_id]
        offset = self.allocated_node_offsets[node_id]
        parent = self.allocated_node_parents[node_id]

        self.unlink_node_completely(node_id)
        self.nodenet._track_deletion('nodes', node_to_id(node_id, self.pid))
        self.nodespaces_contents_last_changed[self.allocated_node_parents[node_id]] = self.nodenet.current_step

        # forget
        self.allocated_nodes[node_id] = 0
        self.allocated_node_offsets[node_id] = 0
        self.allocated_node_parents[node_id] = 0
        g_function_selector_array = self.g_function_selector.get_value(borrow=True)

        element = 0
        while self.allocated_elements_to_nodes[offset + element] == node_id:
            self.allocated_elements_to_nodes[offset + element] = 0
            g_function_selector_array[offset + element] = 0
            element += 1

        self.g_function_selector.set_value(g_function_selector_array, borrow=True)

        if type == SENSOR:
            sensor_index = np.where(self.sensor_indices == offset)[0]
            self.sensor_indices[sensor_index] = -1

        if type == ACTUATOR:
            actuator_index = np.where(self.actuator_indices == offset)[0]
            self.actuator_indices[actuator_index] = -1

        if type == PIPE:
            n_function_selector_array = self.n_function_selector.get_value(borrow=True)
            n_function_selector_array[offset + GEN] = NFPG_PIPE_NON
            n_function_selector_array[offset + POR] = NFPG_PIPE_NON
            n_function_selector_array[offset + RET] = NFPG_PIPE_NON
            n_function_selector_array[offset + SUB] = NFPG_PIPE_NON
            n_function_selector_array[offset + SUR] = NFPG_PIPE_NON
            n_function_selector_array[offset + CAT] = NFPG_PIPE_NON
            n_function_selector_array[offset + EXP] = NFPG_PIPE_NON
            self.n_function_selector.set_value(n_function_selector_array, borrow=True)

        if type == LSTM:
            n_function_selector_array = self.n_function_selector.get_value(borrow=True)
            n_function_selector_array[offset + GEN] = NFPG_PIPE_NON
            n_function_selector_array[offset + POR] = NFPG_PIPE_NON
            n_function_selector_array[offset + GIN] = NFPG_PIPE_NON
            n_function_selector_array[offset + GOU] = NFPG_PIPE_NON
            n_function_selector_array[offset + GFG] = NFPG_PIPE_NON
            self.n_function_selector.set_value(n_function_selector_array, borrow=True)

        # hint at the free ID
        self.last_allocated_node = node_id - 1

        # remove the native module or comment instance if there should be one
        uid = node_to_id(node_id, self.pid)
        if uid in self.native_module_instances:
            del self.native_module_instances[uid]
        if uid in self.comment_instances:
            del self.comment_instances[uid]

        # clear activator usage if there should be one
        used_as_activator_by = np.where(self.allocated_elements_to_activators == offset)
        if len(used_as_activator_by) > 0:
            self.allocated_elements_to_activators[used_as_activator_by] = 0

        if self.allocated_nodespaces_por_activators[parent] == node_id:
            self.allocated_nodespaces_por_activators[parent] = 0
        elif self.allocated_nodespaces_ret_activators[parent] == node_id:
            self.allocated_nodespaces_ret_activators[parent] = 0
        elif self.allocated_nodespaces_sub_activators[parent] == node_id:
            self.allocated_nodespaces_sub_activators[parent] = 0
        elif self.allocated_nodespaces_sur_activators[parent] == node_id:
            self.allocated_nodespaces_sur_activators[parent] = 0
        elif self.allocated_nodespaces_cat_activators[parent] == node_id:
            self.allocated_nodespaces_cat_activators[parent] = 0
        elif self.allocated_nodespaces_exp_activators[parent] == node_id:
            self.allocated_nodespaces_exp_activators[parent] = 0
        if self.allocated_nodespaces_sampling_activators[parent] == node_id:
            self.allocated_nodespaces_sampling_activators[parent] = 0

    def node_changed(self, uid):
        node_id = node_from_id(uid)
        self.nodes_last_changed[node_id] = self.nodenet.current_step
        self.nodespaces_contents_last_changed[self.allocated_node_parents[node_id]] = self.nodenet.current_step

    def unlink_node_completely(self, node_id):
        type = self.allocated_nodes[node_id]
        offset = self.allocated_node_offsets[node_id]
        w_matrix = self.w.get_value(borrow=True)
        number_of_elements = get_elements_per_type(type, self.nodenet.native_modules)
        connecting_elements = np.nonzero(w_matrix[offset:offset+number_of_elements, :])[1]
        connected_elements = np.nonzero(w_matrix[:, offset:offset+number_of_elements])[0]
        w_matrix[offset:offset+number_of_elements, connecting_elements] = 0
        w_matrix[connected_elements, offset:offset+number_of_elements] = 0
        self.w.set_value(w_matrix, borrow=True)
        connecting_nodes = self.allocated_elements_to_nodes[connecting_elements]
        connected_nodes = self.allocated_elements_to_nodes[connected_elements]
        # update all involved elements' changed-steps
        self.nodes_last_changed[node_id] = self.nodenet.current_step
        self.nodes_last_changed[connected_nodes] = self.nodenet.current_step
        self.nodes_last_changed[connecting_nodes] = self.nodenet.current_step
        # update all involved elements' parents' changed-steps
        self.nodespaces_contents_last_changed[self.allocated_node_parents[node_id]] = self.nodenet.current_step
        self.nodespaces_contents_last_changed[self.allocated_node_parents[connected_nodes]] = self.nodenet.current_step
        self.nodespaces_contents_last_changed[self.allocated_node_parents[connecting_nodes]] = self.nodenet.current_step

    def get_associated_elements(self, node_id):
        type = self.allocated_nodes[node_id]
        offset = self.allocated_node_offsets[node_id]
        w_matrix = self.w.get_value(borrow=True)
        number_of_elements = get_elements_per_type(type, self.nodenet.native_modules)
        connecting_elements = np.nonzero(w_matrix[offset:offset+number_of_elements, :])[1]
        connected_elements = np.nonzero(w_matrix[:, offset:offset+number_of_elements])[0]
        return connecting_elements, connected_elements

    def get_associated_node_ids(self, node_id):
        connecting_elements, connected_elements = self.get_associated_elements(node_id)
        connecting_nodes = np.unique(self.allocated_elements_to_nodes[connecting_elements])
        connected_nodes = np.unique(self.allocated_elements_to_nodes[connected_elements])
        return np.unique(np.concatenate((connecting_nodes, connected_nodes)))

    def create_nodespace(self, parent_id, id=None):

        # find a free ID / index in the allocated_nodespaces vector to hold the nodespaces's parent
        if id is None:
            id = 0
            for i in range((self.last_allocated_nodespace + 1), self.NoNS):
                if self.allocated_nodespaces[i] == 0:
                    id = i
                    break

            if id < 1:
                for i in range(self.last_allocated_nodespace - 1):
                    if self.allocated_nodespaces[i] == 0:
                        id = i
                        break

            if id < 1:
                growby = self.NoNS // 2 or 1
                self.logger.info("All %d nodespace IDs in use in partition %i, growing nodespace ID vector by %d elements" % (self.NoNS, self.pid, growby))
                id = self.NoNS
                self.grow_number_of_nodespaces(growby)

        self.last_allocated_nodespace = id
        self.allocated_nodespaces[id] = parent_id
        self.nodespaces_last_changed[id] = self.nodenet.current_step
        self.nodespaces_contents_last_changed[parent_id] = self.nodenet.current_step
        return id

    def delete_nodespace(self, nodespace_id):
        children_ids = np.where(self.allocated_nodespaces == nodespace_id)[0]
        for child_id in children_ids:
            self.nodenet.delete_nodespace(nodespace_to_id(child_id, self.pid))
        node_ids = np.where(self.allocated_node_parents == nodespace_id)[0]
        for node_id in node_ids:
            self.nodenet.delete_node(node_to_id(node_id, self.pid))
            self.nodenet.clear_supplements(node_to_id(node_id, self.pid))

        self.nodenet.clear_supplements(nodespace_to_id(nodespace_id, self.pid))
        self.allocated_nodespaces[nodespace_id] = 0
        self.last_allocated_nodespace = nodespace_id
        self.nodenet._track_deletion('nodespaces', nodespace_to_id(nodespace_id, self.pid))
        self.nodespaces_contents_last_changed[self.allocated_nodespaces[nodespace_id]] = self.nodenet.current_step

    def set_nodespace_gatetype_activator(self, nodespace_id, gate_type, activator_id):
        if gate_type == "por":
            self.allocated_nodespaces_por_activators[nodespace_id] = activator_id
            self.has_directional_activators = True
        elif gate_type == "ret":
            self.allocated_nodespaces_ret_activators[nodespace_id] = activator_id
            self.has_directional_activators = True
        elif gate_type == "sub":
            self.allocated_nodespaces_sub_activators[nodespace_id] = activator_id
            self.has_directional_activators = True
        elif gate_type == "sur":
            self.allocated_nodespaces_sur_activators[nodespace_id] = activator_id
            self.has_directional_activators = True
        elif gate_type == "cat":
            self.allocated_nodespaces_cat_activators[nodespace_id] = activator_id
            self.has_directional_activators = True
        elif gate_type == "exp":
            self.allocated_nodespaces_exp_activators[nodespace_id] = activator_id
            self.has_directional_activators = True

        nodes_in_nodespace = np.where(self.allocated_node_parents == nodespace_id)[0]
        for nid in nodes_in_nodespace:
            if self.allocated_nodes[nid] == PIPE:
                self.allocated_elements_to_activators[self.allocated_node_offsets[nid] +
                                                      get_numerical_gate_type(gate_type)] = self.allocated_node_offsets[activator_id]

    def set_nodespace_sampling_activator(self, nodespace_id, activator_id):
        self.allocated_nodespaces_sampling_activators[nodespace_id] = activator_id
        self.has_sampling_activators = True

        nodes_in_nodespace = np.where(self.allocated_node_parents == nodespace_id)[0]
        for nid in nodes_in_nodespace:
            if self.allocated_nodes[nid] == LSTM:
                self.allocated_elements_to_activators[self.allocated_node_offsets[nid] + GEN] = self.allocated_node_offsets[activator_id]
                self.allocated_elements_to_activators[self.allocated_node_offsets[nid] + POR] = self.allocated_node_offsets[activator_id]
                self.allocated_elements_to_activators[self.allocated_node_offsets[nid] + GIN] = self.allocated_node_offsets[activator_id]
                self.allocated_elements_to_activators[self.allocated_node_offsets[nid] + GOU] = self.allocated_node_offsets[activator_id]
                self.allocated_elements_to_activators[self.allocated_node_offsets[nid] + GFG] = self.allocated_node_offsets[activator_id]

    def set_link_weight(self, source_node_id, gate_type, target_node_id, slot_type, weight=1):
        source_nodetype = None
        target_nodetype = None
        if self.allocated_nodes[source_node_id] > MAX_STD_NODETYPE:
            source_nodetype = self.nodenet.get_nodetype(get_string_node_type(self.allocated_nodes[source_node_id], self.nodenet.native_modules))
        if self.allocated_nodes[target_node_id] > MAX_STD_NODETYPE:
            target_nodetype = self.nodenet.get_nodetype(get_string_node_type(self.allocated_nodes[target_node_id], self.nodenet.native_modules))

        ngt = get_numerical_gate_type(gate_type, source_nodetype)
        nst = get_numerical_slot_type(slot_type, target_nodetype)

        if ngt > get_gates_per_type(self.allocated_nodes[source_node_id], self.nodenet.native_modules):
            raise ValueError("Node %s does not have a gate of type %s" % (node_to_id(source_node_id, self.pid), gate_type))

        if nst > get_slots_per_type(self.allocated_nodes[target_node_id], self.nodenet.native_modules):
            raise ValueError("Node %s does not have a slot of type %s" % (node_to_id(target_node_id, self.pid), slot_type))

        w_matrix = self.w.get_value(borrow=True)
        x = self.allocated_node_offsets[target_node_id] + nst
        y = self.allocated_node_offsets[source_node_id] + ngt
        if self.sparse:
            w_matrix[x, y] = weight
        else:
            w_matrix[x][y] = weight
        self.w.set_value(w_matrix, borrow=True)

        self.nodes_last_changed[source_node_id] = self.nodenet.current_step
        self.nodes_last_changed[target_node_id] = self.nodenet.current_step
        self.nodespaces_contents_last_changed[self.allocated_node_parents[source_node_id]] = self.nodenet.current_step
        self.nodespaces_contents_last_changed[self.allocated_node_parents[target_node_id]] = self.nodenet.current_step

        # if (slot_type == "por" or slot_type == "ret") and self.allocated_nodes[node_from_id(target_node_uid)] == PIPE:
        #     self.__por_ret_dirty = False

        if slot_type == "por" and self.allocated_nodes[target_node_id] == PIPE:
            n_node_porlinked_array = self.n_node_porlinked.get_value(borrow=True)
            if weight == 0:
                for g in range(7):
                    n_node_porlinked_array[self.allocated_node_offsets[target_node_id] + g] = 0
            else:
                for g in range(7):
                    n_node_porlinked_array[self.allocated_node_offsets[target_node_id] + g] = 1
            self.n_node_porlinked.set_value(n_node_porlinked_array, borrow=True)
        if slot_type == "ret" and self.allocated_nodes[target_node_id] == PIPE:
            n_node_retlinked_array = self.n_node_retlinked.get_value(borrow=True)
            if weight == 0:
                for g in range(7):
                    n_node_retlinked_array[self.allocated_node_offsets[target_node_id] + g] = 0
            else:
                for g in range(7):
                    n_node_retlinked_array[self.allocated_node_offsets[target_node_id] + g] = 1
            self.n_node_retlinked.set_value(n_node_retlinked_array, borrow=True)

    def group_nodes_by_ids(self, nodespace_uid, ids, group_name, gatetype="gen"):

        if nodespace_uid not in self.nodegroups:
            self.nodegroups[nodespace_uid] = {}
        parent_id = nodespace_from_id(nodespace_uid)

        non_children = np.where(self.allocated_node_parents[ids] != parent_id)[0]
        if len(non_children) > 0:
            raise ValueError("One ore more given nodes are not in nodespace %s" % nodespace_uid)

        gate = get_numerical_gate_type(gatetype)
        self.nodegroups[nodespace_uid][group_name] = self.allocated_node_offsets[ids] + gate

    def group_highdimensional_elements(self, node_uid, gate=None, slot=None, group_name=None):
        node_id = node_from_id(node_uid)
        nodespace_id = self.allocated_node_parents[node_id]
        nodespace_uid = nodespace_to_id(nodespace_id, self.pid)
        if nodespace_uid not in self.nodegroups:
            self.nodegroups[nodespace_uid] = {}
        strnodetype = get_string_node_type(self.allocated_nodes[node_id], self.nodenet.native_modules)
        nodetype = self.nodenet.get_nodetype(strnodetype)
        if gate:
            element = get_numerical_gate_type("%s0" % gate, nodetype)
            dimensionality = nodetype.get_gate_dimensionality(gate)
        elif slot:
            element = get_numerical_slot_type("%s0" % slot, nodetype)
            dimensionality = nodetype.get_slot_dimensionality(slot)
        start = self.allocated_node_offsets[node_id] + element
        stop = start + dimensionality
        self.nodegroups[nodespace_uid][group_name] = np.arange(start, stop)

    def ungroup_nodes(self, nodespace_uid, group):
        if nodespace_uid in self.nodegroups and group in self.nodegroups[nodespace_uid]:
            del self.nodegroups[nodespace_uid][group]

    def get_activations(self, nodespace_uid, group):
        if nodespace_uid not in self.nodegroups or group not in self.nodegroups[nodespace_uid]:
            raise ValueError("Group %s does not exist in nodespace %s." % (group, nodespace_uid))
        a_array = self.a.get_value(borrow=True)
        return a_array[self.nodegroups[nodespace_uid][group]]

    def set_activations(self, nodespace_uid, group, new_activations):
        if nodespace_uid not in self.nodegroups or group not in self.nodegroups[nodespace_uid]:
            raise ValueError("Group %s does not exist in nodespace %s." % (group, nodespace_uid))
        a_array = self.a.get_value(borrow=True)
        a_array[self.nodegroups[nodespace_uid][group]] = new_activations
        self.a.set_value(a_array, borrow=True)

    def get_gate_configurations(self, nodespace_uid, group, gatefunction_parameter=None):
        if nodespace_uid not in self.nodegroups or group not in self.nodegroups[nodespace_uid]:
            raise ValueError("Group %s does not exist in nodespace %s." % (group, nodespace_uid))

        groupindexes = self.nodegroups[nodespace_uid][group]
        g_function_selector = self.g_function_selector.get_value(borrow=True)
        num_gatefunc = g_function_selector[groupindexes]
        if len(np.unique(num_gatefunc)) > 1:
            raise("Heterogenous gatefunction configuration") 
        data = {'gatefunction': get_string_gatefunction_type(np.unique(num_gatefunc)[0])}
        if gatefunction_parameter == 'bias':
            g_bias = self.g_bias.get_value(borrow=True)
            data['parameter_values'] = g_bias[groupindexes]
        if gatefunction_parameter == 'minimum':
            g_min = self.g_min.get_value(borrow=True)
            data['parameter_values'] = g_min[groupindexes]
        if gatefunction_parameter == 'maximum':
            g_max = self.g_max.get_value(borrow=True)
            data['parameter_values'] = g_max[groupindexes]
        if gatefunction_parameter == 'amplification':
            g_amplification = self.g_amplification.get_value(borrow=True)
            data['parameter_values'] = g_amplification[groupindexes]
        if gatefunction_parameter == 'threshold':
            g_threshold = self.g_threshold.get_value(borrow=True)
            data['parameter_values'] = g_threshold[groupindexes]
        return data

    def set_gate_configurations(self, nodespace_uid, group, gatefunction, gatefunction_parameter=None, parameter_values=None):
        if nodespace_uid not in self.nodegroups or group not in self.nodegroups[nodespace_uid]:
            raise ValueError("Group %s does not exist in nodespace %s." % (group, nodespace_uid))

        groupindexes = self.nodegroups[nodespace_uid][group]
        self._set_gate_config_for_elements(groupindexes, gatefunction, gatefunction_parameter, parameter_values)

    def _set_gate_config_for_elements(self, elements, gatefunction, gatefunction_parameter=None, parameter_values=None):
        g_function_selector = self.g_function_selector.get_value(borrow=True)
        g_bias = self.g_bias.get_value(borrow=True)
        g_threshold = self.g_threshold.get_value(borrow=True)
        g_amplification = self.g_amplification.get_value(borrow=True)
        g_min = self.g_min.get_value(borrow=True)
        g_max = self.g_max.get_value(borrow=True)

        # set gatefunction
        num_gatefunc = get_numerical_gatefunction_type(gatefunction)
        g_function_selector[elements] = num_gatefunc
        self.g_function_selector.set_value(g_function_selector, borrow=True)

        # first, unset any old values
        g_bias[elements] = 0
        if num_gatefunc != GATE_FUNCTION_THRESHOLD:
            g_threshold[elements] = 0
            g_amplification[elements] = 1
            g_min[elements] = 0
            g_max[elements] = 1

        if num_gatefunc == GATE_FUNCTION_SIGMOID or num_gatefunc == GATE_FUNCTION_ELU or num_gatefunc == GATE_FUNCTION_RELU:
            if gatefunction_parameter == 'bias':
                g_bias[elements] = parameter_values
            if num_gatefunc == GATE_FUNCTION_ELU:
                self.has_gatefunction_elu = True
            elif num_gatefunc == GATE_FUNCTION_RELU:
                self.has_gatefunction_relu = True
            elif num_gatefunc == GATE_FUNCTION_SIGMOID:
                self.has_gatefunction_sigmoid = True

        elif num_gatefunc == GATE_FUNCTION_THRESHOLD:
            self.has_gatefunction_threshold = True
            if gatefunction_parameter == 'threshold':
                g_threshold[elements] = parameter_values
            if gatefunction_parameter == 'amplification':
                g_amplification[elements] = parameter_values
            if gatefunction_parameter == 'minimum':
                g_min[elements] = parameter_values
            if gatefunction_parameter == 'maximum':
                g_max[elements] = parameter_values

        self.g_function_selector.set_value(g_function_selector, borrow=True)
        self.g_bias.set_value(g_bias, borrow=True)
        self.g_threshold.set_value(g_threshold, borrow=True)
        self.g_amplification.set_value(g_amplification, borrow=True)
        self.g_min.set_value(g_min, borrow=True)
        self.g_max.set_value(g_max, borrow=True)

    def get_link_weights(self, nodespace_from_uid, group_from, nodespace_to_uid, group_to):
        if nodespace_from_uid not in self.nodegroups or group_from not in self.nodegroups[nodespace_from_uid]:
            raise ValueError("Group %s does not exist in nodespace %s." % (group_from, nodespace_from_uid))
        if nodespace_to_uid not in self.nodegroups or group_to not in self.nodegroups[nodespace_to_uid]:
            raise ValueError("Group %s does not exist in nodespace %s." % (group_to, nodespace_to_uid))
        w_matrix = self.w.get_value(borrow=True)
        cols, rows = np.meshgrid(self.nodegroups[nodespace_from_uid][group_from], self.nodegroups[nodespace_to_uid][group_to])
        if self.sparse:
            return w_matrix[rows,cols].toarray()
        else:
            return w_matrix[rows,cols]

    def set_link_weights(self, nodespace_from_uid, group_from, nodespace_to_uid, group_to, new_w):
        #if nodespace_from_uid not in self.nodegroups or group_from not in self.nodegroups[nodespace_from_uid]:
        #    raise ValueError("Group %s does not exist in nodespace %s." % (group_from, nodespace_from_uid))
        #if nodespace_to_uid not in self.nodegroups or group_to not in self.nodegroups[nodespace_to_uid]:
        #    raise ValueError("Group %s does not exist in nodespace %s." % (group_to, nodespace_to_uid))
        #if len(self.nodegroups[nodespace_from_uid][group_from]) != new_w.shape[1]:
        #    raise ValueError("group_from %s has length %i, but new_w.shape[1] is %i" % (group_from, len(self.nodegroups[nodespace_from_uid][group_from]), new_w.shape[1]))
        #if len(self.nodegroups[nodespace_to_uid][group_to]) != new_w.shape[0]:
        #    raise ValueError("group_to %s has length %i, but new_w.shape[0] is %i" % (group_to, len(self.nodegroups[nodespace_to_uid][group_to]), new_w.shape[0]))

        grp_from = self.nodegroups[nodespace_from_uid][group_from]
        grp_to = self.nodegroups[nodespace_to_uid][group_to]
        if np.isscalar(new_w) and new_w == 1:
            if len(grp_from) != len(grp_to):
                raise ValueError("from_elements and to_elements need to have equal lengths for identity links")
            new_w = np.eye(len(grp_from))
        w_matrix = self.w.get_value(borrow=True)
        cols, rows = np.meshgrid(grp_from, grp_to)
        w_matrix[rows, cols] = new_w
        self.w.set_value(w_matrix, borrow=True)

        cstep = self.nodenet.current_step
        self.nodes_last_changed[self.allocated_elements_to_nodes[grp_from]] = cstep
        self.nodespaces_contents_last_changed[self.allocated_node_parents[self.allocated_elements_to_nodes[grp_from]]] = cstep
        self.nodes_last_changed[self.allocated_elements_to_nodes[grp_to]] = cstep
        self.nodespaces_contents_last_changed[self.allocated_node_parents[self.allocated_elements_to_nodes[grp_to]]] = cstep

        self.por_ret_dirty = self.has_pipes

    def set_inlink_weights(self, partition_from_spid, new_from_elements, new_to_elements, new_weights):

        inlink_type = None

        from_partition = self.nodenet.partitions[partition_from_spid]
        if partition_from_spid in self.inlinks:
            inlink_type = self.inlinks[partition_from_spid][4]
            if inlink_type != "dense":
                raise NotImplementedError("Update of non-dense partition connections not yet implemented: "+inlink_type)

            theano_from_elements = self.inlinks[partition_from_spid][0]
            theano_to_elements = self.inlinks[partition_from_spid][1]
            theano_weights = self.inlinks[partition_from_spid][2]

            old_from_elements = theano_from_elements.get_value(borrow=True)
            old_to_elements = theano_to_elements.get_value(borrow=True)
            old_weights = theano_weights.get_value(borrow=True)
            propagation_function = self.inlinks[partition_from_spid][3]

            from_elements = np.union1d(old_from_elements, new_from_elements)
            to_elements = np.union1d(old_to_elements, new_to_elements)
            weights = np.zeros((len(to_elements), len(from_elements)), dtype=T.config.floatX)

            old_from_indices = np.searchsorted(from_elements, old_from_elements)
            old_to_indices = np.searchsorted(to_elements, old_to_elements)
            oldcols, oldrows = np.meshgrid(old_from_indices, old_to_indices)
            weights[oldrows, oldcols] = old_weights

            new_from_indices = np.searchsorted(from_elements, new_from_elements)
            new_to_indices = np.searchsorted(to_elements, new_to_elements)
            newcols, newrows = np.meshgrid(new_from_indices, new_to_indices)
            weights[newrows, newcols] = new_weights

            theano_from_elements.set_value(from_elements, borrow=True)
            theano_to_elements.set_value(to_elements, borrow=True)
            theano_weights.set_value(weights, borrow=True)

        else:
            weightsname = "w_%s_%s" % (partition_from_spid, self.spid)
            fromname = "in_from_%s_%s" % (partition_from_spid, self.spid)
            toname = "in_to_%s_%s" % (partition_from_spid, self.spid)
            theano_from_elements = theano.shared(value=new_from_elements, name=fromname, borrow=True)
            theano_to_elements = theano.shared(value=new_to_elements, name=toname, borrow=True)

            if np.isscalar(new_weights) and new_weights == 1:
                if len(new_from_elements) != len(new_to_elements):
                    raise ValueError("from_elements and to_elements need to have equal lengths for identity links")
                inlink_type = "identity"
                theano_weights = None
                propagation_function = self.get_compiled_propagate_identity_inlinks(
                    from_partition,
                    theano_from_elements,
                    theano_to_elements)
            else:
                inlink_type = "dense"
                theano_weights = theano.shared(value=new_weights.astype(T.config.floatX), name=weightsname, borrow=True)
                propagation_function = self.get_compiled_propagate_inlinks(
                    from_partition,
                    theano_from_elements,
                    theano_to_elements,
                    theano_weights)

        for id in from_partition.allocated_elements_to_nodes[theano_from_elements.get_value()]:
            from_partition.nodes_last_changed[id] = self.nodenet.current_step
            from_partition.nodespaces_contents_last_changed[from_partition.allocated_node_parents[id]] = self.nodenet.current_step
        for id in self.allocated_elements_to_nodes[theano_to_elements.get_value()]:
            self.nodes_last_changed[id] = self.nodenet.current_step
            self.nodespaces_contents_last_changed[self.allocated_node_parents[id]] = self.nodenet.current_step

        self.inlinks[partition_from_spid] = (
            theano_from_elements,
            theano_to_elements,
            theano_weights,
            propagation_function,
            inlink_type)

    def has_nodespace_changes(self, nodespace_uid, since_step):
        ns_id = nodespace_from_id(nodespace_uid)
        return (self.nodespaces_contents_last_changed[ns_id] >= since_step).__bool__()

    def get_nodespace_changes(self, nodespace_uid, since_step):
        ns_id = nodespace_from_id(nodespace_uid)
        node_ids = np.where(self.nodes_last_changed >= since_step)[0]
        node_ids = node_ids[np.where(self.allocated_node_parents[node_ids] == ns_id)[0]]
        nodespace_ids = np.where(self.nodespaces_last_changed >= since_step)[0]
        nodespace_ids = nodespace_ids[np.where(self.allocated_nodespaces[nodespace_ids] == ns_id)[0]]
        return node_ids, nodespace_ids

    def get_node_data(self, ids=None, nodespaces_by_partition=None, complete=False, include_links=True, linked_nodespaces_by_partition={}):
        a = self.a.get_value(borrow=True)
        g_threshold = self.g_threshold.get_value(borrow=True)
        g_amplification = self.g_amplification.get_value(borrow=True)
        g_min = self.g_min.get_value(borrow=True)
        g_max = self.g_max.get_value(borrow=True)
        g_bias = self.g_bias.get_value(borrow=True)
        g_function_selector = self.g_function_selector.get_value(borrow=True)
        w = self.w.get_value(borrow=True)

        if nodespaces_by_partition is not None:
            fetchall = False
            node_ids = np.where(self.allocated_node_parents == nodespaces_by_partition[self.spid])[0]
        else:
            fetchall = True
            node_ids = np.nonzero(self.allocated_nodes)[0]

        if ids is not None:
            fetchall = False
            node_ids = np.intersect1d(node_ids, ids)
            if len(node_ids) and linked_nodespaces_by_partition == {}:
                linked_nodespaces_by_partition[self.spid] = self.allocated_node_parents[node_ids]

        nodes = {}
        node_numpy_data = {}
        highdim_nodes = []
        additional_links = []

        for id in node_ids:
            uid = node_to_id(id, self.pid)
            strtype = get_string_node_type(self.allocated_nodes[id], self.nodenet.native_modules)
            nodetype = self.nodenet.get_nodetype(strtype)

            gate_configurations = {}
            gate_activations = {}

            if type(nodetype) == HighdimensionalNodetype:
                gates = nodetype.gategroups
                highdim_nodes.append(uid)
            else:
                gates = nodetype.gatetypes

            for gate in gates:
                numericalgate = get_numerical_gate_type(gate, nodetype)
                element = self.allocated_node_offsets[id] + numericalgate
                num_gatefunc = g_function_selector[element]
                if num_gatefunc != GATE_FUNCTION_IDENTITY:
                    gate_configurations[gate] = {
                        'gatefunction': get_string_gatefunction_type(num_gatefunc),
                        'gatefunction_parameters': {}
                    }
                    if num_gatefunc == GATE_FUNCTION_SIGMOID or num_gatefunc == GATE_FUNCTION_ELU or num_gatefunc == GATE_FUNCTION_RELU:
                        gate_configurations[gate]['gatefunction_parameters'] = {'bias': float(g_bias[element])}
                    elif num_gatefunc == GATE_FUNCTION_THRESHOLD:
                        gate_configurations[gate]['gatefunction_parameters'] = {
                            'minimum': float(g_min[element]),
                            'maximum': float(g_max[element]),
                            'threshold': float(g_threshold[element]),
                            'amplification': float(g_amplification[element])
                        }

                gate_activations[gate] = float(a[element])

            activation = float(a[self.allocated_node_offsets[id] + GEN])

            state = None
            if uid in self.native_module_instances:
                state, numpy_state = self.native_module_instances[uid].get_persistable_state()
                node_numpy_data[uid] = numpy_state
                activation = self.native_module_instances[uid].activation

            parameters = {}
            if strtype == "Sensor":
                sensor_element = self.allocated_node_offsets[id] + GEN
                datasource_index = np.where(self.sensor_indices == sensor_element)[0]
                if len(datasource_index) == 0:
                    parameters['datasource'] = None
                else:
                    parameters['datasource'] = self.nodenet.get_datasources()[datasource_index[0]]
            elif strtype == "Actuator":
                actuator_element = self.allocated_node_offsets[id] + GEN
                datatarget_index = np.where(self.actuator_indices == actuator_element)[0]
                if len(datatarget_index) == 0:
                    parameters['datatarget'] = None
                else:
                    parameters['datatarget'] = self.nodenet.get_datatargets()[datatarget_index[0]]
            elif strtype == "Activator":
                activator_type = None
                if id in self.allocated_nodespaces_por_activators:
                    activator_type = "por"
                elif id in self.allocated_nodespaces_ret_activators:
                    activator_type = "ret"
                elif id in self.allocated_nodespaces_sub_activators:
                    activator_type = "sub"
                elif id in self.allocated_nodespaces_sur_activators:
                    activator_type = "sur"
                elif id in self.allocated_nodespaces_cat_activators:
                    activator_type = "cat"
                elif id in self.allocated_nodespaces_exp_activators:
                    activator_type = "exp"
                elif id in self.allocated_nodespaces_sampling_activators:
                    activator_type = "sampling"
                parameters['type'] = activator_type
            elif strtype == "Pipe":
                g_expect_array = self.g_expect.get_value(borrow=True)
                value = g_expect_array[self.allocated_node_offsets[id] + get_numerical_gate_type("sur")].item()
                parameters['expectation'] = value
                g_wait_array = self.g_wait.get_value(borrow=True)
                parameters['wait'] = g_wait_array[self.allocated_node_offsets[id] + get_numerical_gate_type("sur")].item()
            elif strtype == "Comment":
                parameters = self.comment_instances[uid].clone_parameters()
            elif strtype in self.nodenet.native_modules:
                parameters = self.native_module_instances[uid].clone_parameters()

            data = {"uid": uid,
                    "name": self.nodenet.names.get(uid, uid),
                    "position": self.nodenet.positions.get(uid, (10, 10, 10)),
                    "parent_nodespace": nodespace_to_id(self.allocated_node_parents[id], self.pid),
                    "type": strtype,
                    "parameters": parameters,
                    "state": state,
                    "activation": activation,
                    "gate_activations": gate_activations,
                    "gate_configuration": gate_configurations,
                    "is_highdimensional": type(nodetype) == HighdimensionalNodetype}
            if type(nodetype) == FlowNodetype:
                data.update(self.nodenet.flow_module_instances[uid].get_flow_data())
            if complete:
                data['index'] = int(id)
            if include_links:
                data['links'] = {}
                data['outlinks'] = 0
                data['inlinks'] = 0

            nodes[uid] = data

        # fill in links if requested
        if include_links:
            slots, gates = np.nonzero(w)
            for index, gate_index in enumerate(gates):
                source_id = self.allocated_elements_to_nodes[gate_index]
                source_uid = node_to_id(source_id, self.pid)
                slot_index = slots[index]
                target_id = self.allocated_elements_to_nodes[slot_index]
                target_uid = node_to_id(target_id, self.pid)

                if not fetchall:
                    if source_uid not in nodes and target_uid in nodes:
                        if self.allocated_node_parents[source_id] not in linked_nodespaces_by_partition.get(self.spid, []):
                            nodes[target_uid]['inlinks'] += 1
                            continue
                    elif target_uid not in nodes and source_uid in nodes:
                        if self.allocated_node_parents[target_id] not in linked_nodespaces_by_partition.get(self.spid, []):
                            nodes[source_uid]['outlinks'] += 1
                            continue
                    elif source_uid not in nodes or target_uid not in nodes:
                        # links between two nodes outside this nodespace.
                        continue

                source_type = self.allocated_nodes[source_id]
                source_nodetype = self.nodenet.get_nodetype(get_string_node_type(source_type, self.nodenet.native_modules))
                source_gate_numerical = gate_index - self.allocated_node_offsets[source_id]
                source_gate_type = get_string_gate_type(source_gate_numerical, source_nodetype)
                if source_uid in highdim_nodes:
                    if source_gate_type.rstrip('0123456789') in source_nodetype.dimensionality['gates']:
                        source_gate_type = source_gate_type.rstrip('0123456789') + '0'

                target_type = self.allocated_nodes[target_id]
                target_nodetype = self.nodenet.get_nodetype(get_string_node_type(target_type, self.nodenet.native_modules))
                target_slot_numerical = slot_index - self.allocated_node_offsets[target_id]
                target_slot_type = get_string_slot_type(target_slot_numerical, target_nodetype)
                if target_uid in highdim_nodes:
                    if target_slot_type.rstrip('0123456789') in target_nodetype.dimensionality['slots']:
                        target_slot_type = target_slot_type.rstrip('0123456789') + '0'
                linkdict = {"weight": float(w[slot_index, gate_index]),
                            "target_slot_name": target_slot_type,
                            "target_node_uid": target_uid}

                if source_uid in nodes:
                    if source_gate_type not in nodes[source_uid]["links"]:
                        nodes[source_uid]["links"][source_gate_type] = []
                    if source_uid in highdim_nodes:
                        if linkdict not in nodes[source_uid]['links'][source_gate_type]:
                            nodes[source_uid]["links"][source_gate_type].append(linkdict)  # Doik: why is this check needed? possibly expensive. /Doik
                    else:
                        nodes[source_uid]["links"][source_gate_type].append(linkdict)
                elif target_uid in nodes:
                    linkdict['source_node_uid'] = source_uid
                    linkdict['source_gate_name'] = source_gate_type
                    additional_links.append(linkdict)

            # outgoing cross-partition links
            for partition_to_spid, to_partition in self.nodenet.partitions.items():
                if self.spid in to_partition.inlinks:
                    inlinks = to_partition.inlinks[self.spid]
                    from_elements = inlinks[0].get_value(borrow=True)

                    if not fetchall and partition_to_spid not in nodespaces_by_partition and linked_nodespaces_by_partition.get(partition_to_spid, []) == []:
                        nids = self.allocated_elements_to_nodes[from_elements]
                        if inlinks[4] == 'identity':
                            for nid in nids:
                                uid = node_to_id(nid, self.pid)
                                if uid in nodes:
                                    nodes[uid]['outlinks'] += 1
                        elif inlinks[4] == 'dense':
                            w = inlinks[2].get_value(borrow=True).transpose()
                            for idx, el in enumerate(from_elements):
                                uid = node_to_id(self.allocated_elements_to_nodes[el], self.pid)
                                if uid in nodes:
                                    nodes[uid]['outlinks'] += np.count_nonzero(w[idx])
                        continue

                    to_elements = inlinks[1].get_value(borrow=True)
                    inlink_type = inlinks[4]
                    if inlink_type == "dense":
                        w = inlinks[2].get_value(borrow=True)
                        slots, gates = np.nonzero(w)
                    elif inlink_type == "identity":
                        slots = np.arange(len(from_elements))
                        gates = np.arange(len(from_elements))

                    for index, gate_index in enumerate(gates):
                        source_id = self.allocated_elements_to_nodes[from_elements[gate_index]]
                        source_uid = node_to_id(source_id, self.pid)
                        if source_uid not in nodes:
                            continue

                        source_type = self.allocated_nodes[source_id]
                        source_nodetype = self.nodenet.get_nodetype(get_string_node_type(source_type, self.nodenet.native_modules))
                        source_gate_numerical = from_elements[gate_index] - self.allocated_node_offsets[source_id]
                        source_gate_type = get_string_gate_type(source_gate_numerical, source_nodetype)
                        if source_uid in highdim_nodes:
                            if source_gate_type.rstrip('0123456789') in source_nodetype.dimensionality['gates']:
                                source_gate_type = source_gate_type.rstrip('0123456789') + '0'

                        slot_index = slots[index]
                        target_id = to_partition.allocated_elements_to_nodes[to_elements[slot_index]]
                        target_uid = node_to_id(target_id, to_partition.pid)
                        target_type = to_partition.allocated_nodes[target_id]
                        target_nodetype = to_partition.nodenet.get_nodetype(get_string_node_type(target_type, to_partition.nodenet.native_modules))
                        target_slot_numerical = to_elements[slot_index] - to_partition.allocated_node_offsets[target_id]
                        target_slot_type = get_string_slot_type(target_slot_numerical, target_nodetype)
                        if target_uid in highdim_nodes:
                            if target_slot_type.rstrip('0123456789') in target_nodetype.dimensionality['slots']:
                                target_slot_type = target_slot_type.rstrip('0123456789') + '0'

                        if inlink_type == "dense":
                            weight = float(w[slot_index, gate_index])
                        elif inlink_type == "identity":
                            weight = 1.

                        linkdict = {"weight": weight,
                                    "target_slot_name": target_slot_type,
                                    "target_node_uid": target_uid}
                        if source_gate_type not in nodes[source_uid]["links"]:
                            nodes[source_uid]["links"][source_gate_type] = []
                        if type(target_nodetype) == HighdimensionalNodetype:
                            target_slot_type = target_slot_type.rstrip('0123456789')
                            if target_slot_type.rstrip('0123456789') in target_nodetype.dimensionality['slots']:
                                target_slot_type = target_slot_type + '0'

                        nodes[source_uid]["links"][source_gate_type].append(linkdict)

            # incoming cross-partition-links:
            if not fetchall:
                # incoming cross-partition links
                for from_partition_id, inlinks in self.inlinks.items():
                    if from_partition_id not in nodespaces_by_partition and linked_nodespaces_by_partition.get(from_partition_id, []) == []:
                        to_elements = inlinks[1].get_value(borrow=True)
                        nids = self.allocated_elements_to_nodes[to_elements]
                        if inlinks[4] == 'identity':
                            for nid in nids:
                                uid = node_to_id(nid, self.pid)
                                if uid in nodes:
                                    nodes[uid]['inlinks'] += 1
                        elif inlinks[4] == 'dense':
                            w = inlinks[2].get_value(borrow=True)
                            for idx, el in enumerate(to_elements):
                                uid = node_to_id(self.allocated_elements_to_nodes[el], self.pid)
                                if uid in nodes:
                                    nodes[uid]['inlinks'] += np.count_nonzero(w[idx])
                    else:
                        from_partition = self.nodenet.partitions[from_partition_id]
                        from_elements = inlinks[0].get_value(borrow=True)
                        to_elements = inlinks[1].get_value(borrow=True)

                        inlink_type = inlinks[4]
                        if inlink_type == "dense":
                            w = inlinks[2].get_value(borrow=True)
                            slots, gates = np.nonzero(w)
                        elif inlink_type == "identity":
                            slots = np.arange(len(from_elements))
                            gates = np.arange(len(from_elements))

                        for index, gate_index in enumerate(gates):
                            source_id = from_partition.allocated_elements_to_nodes[from_elements[gate_index]]
                            source_uid = node_to_id(source_id, from_partition.pid)

                            source_type = from_partition.allocated_nodes[source_id]
                            source_nodetype = from_partition.nodenet.get_nodetype(get_string_node_type(source_type, from_partition.nodenet.native_modules))
                            source_gate_numerical = from_elements[gate_index] - from_partition.allocated_node_offsets[source_id]
                            source_gate_type = get_string_gate_type(source_gate_numerical, source_nodetype)

                            slot_index = slots[index]
                            target_id = self.allocated_elements_to_nodes[to_elements[slot_index]]
                            target_uid = node_to_id(target_id, self.pid)

                            target_type = self.allocated_nodes[target_id]
                            target_nodetype = self.nodenet.get_nodetype(get_string_node_type(target_type, self.nodenet.native_modules))
                            target_slot_numerical = to_elements[slot_index] - self.allocated_node_offsets[target_id]
                            target_slot_type = get_string_slot_type(target_slot_numerical, target_nodetype)

                            if inlink_type == 'dense':
                                weight = float(w[slot_index][gate_index])
                            elif inlink_type == 'identity':
                                weight = 1

                            if type(target_nodetype) == HighdimensionalNodetype:
                                if target_slot_type.rstrip('0123456789') in target_nodetype.dimensionality['slots']:
                                    target_slot_type = target_slot_type.rstrip('0123456789') + '0'
                            if type(source_nodetype) == HighdimensionalNodetype:
                                if source_gate_type.rstrip('0123456789') in source_nodetype.dimensionality['gates']:
                                    source_gate_type = source_gate_type.rstrip('0123456789') + '0'

                            additional_links.append({"weight": weight,
                                        "target_slot_name": target_slot_type,
                                        "target_node_uid": target_uid,
                                        "source_node_uid": source_uid,
                                        "source_gate_name": source_gate_type})

        return nodes, additional_links, node_numpy_data

    def integrity_check(self):

        for nid in range(self.NoN):
            nodetype = self.allocated_nodes[nid]

            if nodetype == 0:
                continue

            number_of_elements = get_elements_per_type(nodetype, self.nodenet.native_modules)

            elements = np.where(self.allocated_elements_to_nodes == nid)[0]
            if len(elements) != number_of_elements:
                self.logger.error("Integrity check error: Number of elements for node n%i should be %i, but is %i" % (nid, number_of_elements, len(elements)))

            if number_of_elements > 0:
                offset = self.allocated_node_offsets[nid]
                if elements[0] != offset:
                    self.logger.error("Integrity check error: First element for node n%i should be at %i, but is at %i" % (nid, offset, elements[0]))

                for eid in range(number_of_elements):
                    if self.allocated_elements_to_nodes[offset+eid] != nid:
                        self.logger.error("Integrity check error: Element %i of node n%i is allocated to node n%i" % (eid, nid, self.allocated_elements_to_nodes[offset+eid]))

                for snid in range(self.NoN):

                    if snid == nid:
                        continue

                    snodetype = self.allocated_nodes[snid]

                    if snodetype == 0:
                        continue

                    soffset = self.allocated_node_offsets[snid]
                    snumber_of_elements = get_elements_per_type(snodetype, self.nodenet.native_modules)

                    for selement in range(soffset, snumber_of_elements):
                        for element in range(offset, number_of_elements):
                            if element == selement:
                                self.logger.error("Integrity check error: Overlap at element %i, claimed by nodes n%i and n%i" % (element, nid, snid))
