

import json
import os
import copy
import warnings

import theano
from theano import tensor as T
import numpy as np
import scipy.sparse as sp
import scipy
import theano.sparse as ST
from theano.tensor import nnet as N

from micropsi_core.nodenet.theano_engine.theano_definitions import *

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

    def __init__(self, nodenet, sid, sparse, initial_NoN, initial_NoE, initial_NoNS):

        self.native_module_instances = {}
        self.comment_instances = {}
        self.nodegroups = {}
        self.sid = sid

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
        self.por_ret_dirty = True

        # compile theano functions
        self.compile_propagate()
        self.compile_calculate_nodes()

    def compile_propagate(self):
        if self.sparse:
            self.propagate = theano.function([], None, updates={self.a: ST.dot(self.w, self.a)})
        else:
            self.propagate = theano.function([], None, updates={self.a: T.dot(self.w, self.a)})

    def compile_calculate_nodes(self):
        slots = self.a_shifted
        countdown = self.g_countdown
        por_linked = self.n_node_porlinked
        ret_linked = self.n_node_retlinked

        # node functions implemented with identity by default (native modules are calculated by python)
        nodefunctions = self.a

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
        pipe_gen_sur_exp = slots[:, 11] + slots[:, 13]                              # sum of sur and exp as default
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
        pipe_ret = -slots[:, 8] * T.ge(slots[:, 6], 0)                              # start with -sub if por >= 0
                                                                                    # add ret (for search) if sub=sur=0
        pipe_ret = pipe_ret + (slots[:, 7] * T.eq(slots[:, 8], 0) * T.eq(slots[:, 9], 0))

        ### sub plumbing
        pipe_sub_cond = T.switch(T.eq(por_linked, 1), T.gt(slots[:, 5], 0), 1)      # (if linked, por must be > 0)
        pipe_sub_cond = pipe_sub_cond * T.eq(slots[:, 4], 0)                        # and (gen == 0)

        pipe_sub = T.clip(slots[:, 8], 0, 1)                                        # bubble: start with sur if sur > 0
        pipe_sub = pipe_sub + slots[:, 7]                                           # add sub
        pipe_sub = pipe_sub + slots[:, 9]                                           # add cat
        pipe_sub = pipe_sub * pipe_sub_cond                                         # apply conditions

        ### sur plumbing
                                                                                    # reset if no sub, or por-linked but 0
        cd_reset_cond = T.le(slots[:, 6],0) + (T.eq(por_linked, 1) * T.le(slots[:, 4], 0))
                                                                                    # count down failure countdown
        countdown_sur = T.switch(cd_reset_cond, self.g_wait, T.maximum(countdown - 1, -1))

        pipe_sur_cond = T.eq(ret_linked, 0)                                         # (not ret-linked
        pipe_sur_cond = pipe_sur_cond + (T.ge(slots[:, 5],0) * T.gt(slots[:, 6], 0))# or (ret is 0, but sub > 0))
        pipe_sur_cond = pipe_sur_cond * (T.eq(por_linked, 0) + T.gt(slots[:, 4], 0))# and (not por-linked or por > 0)
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
        pipe_sur = pipe_sur * pipe_sur_cond                                         # apply conditions

        ### cat plumbing
        pipe_cat_cond = T.switch(T.eq(por_linked, 1), T.gt(slots[:, 3], 0), 1)      # (if linked, por must be > 0)
        pipe_cat_cond = pipe_cat_cond * T.eq(slots[:, 2], 0)                        # and (gen == 0)

        pipe_cat = T.clip(slots[:, 6], 0, 1)                                        # bubble: start with sur if sur > 0
        pipe_cat = pipe_cat + slots[:, 5]                                           # add sub
        pipe_cat = pipe_cat + slots[:, 7]                                           # add cat
        pipe_cat = pipe_cat * pipe_cat_cond                                         # apply conditions
                                                                                    # add cat (for search) if sub=sur=0
        pipe_cat = pipe_cat + (slots[:, 7] * T.eq(slots[:, 5], 0) * T.eq(slots[:, 6], 0))

        ### exp plumbing
        pipe_exp = slots[:, 5]                                                      # start with sur
        pipe_exp = pipe_exp + slots[:, 7]                                           # add exp

        if self.has_pipes:
            nodefunctions = T.switch(T.eq(self.n_function_selector, NFPG_PIPE_GEN), pipe_gen, nodefunctions)
            nodefunctions = T.switch(T.eq(self.n_function_selector, NFPG_PIPE_POR), pipe_por, nodefunctions)
            nodefunctions = T.switch(T.eq(self.n_function_selector, NFPG_PIPE_RET), pipe_ret, nodefunctions)
            nodefunctions = T.switch(T.eq(self.n_function_selector, NFPG_PIPE_SUB), pipe_sub, nodefunctions)
            nodefunctions = T.switch(T.eq(self.n_function_selector, NFPG_PIPE_SUR), pipe_sur, nodefunctions)
            nodefunctions = T.switch(T.eq(self.n_function_selector, NFPG_PIPE_CAT), pipe_cat, nodefunctions)
            nodefunctions = T.switch(T.eq(self.n_function_selector, NFPG_PIPE_EXP), pipe_exp, nodefunctions)
            countdown = T.switch(T.eq(self.n_function_selector, NFPG_PIPE_POR), countdown_por, countdown)
            countdown = T.switch(T.eq(self.n_function_selector, NFPG_PIPE_SUR), countdown_sur, countdown)

        # gate logic

        # multiply with gate factor for the node space
        if self.has_directional_activators:
            nodefunctions = nodefunctions * self.g_factor

        # apply actual gate functions
        gate_function_output = nodefunctions

        # apply GATE_FUNCTION_ABS to masked gates
        if self.has_gatefunction_absolute:
            gate_function_output = T.switch(T.eq(self.g_function_selector, GATE_FUNCTION_ABSOLUTE), abs(gate_function_output), gate_function_output)
        # apply GATE_FUNCTION_SIGMOID to masked gates
        if self.has_gatefunction_sigmoid:
            gate_function_output = T.switch(T.eq(self.g_function_selector, GATE_FUNCTION_SIGMOID), N.sigmoid(gate_function_output + self.g_theta), gate_function_output)
        # apply GATE_FUNCTION_TANH to masked gates
        if self.has_gatefunction_tanh:
            gate_function_output = T.switch(T.eq(self.g_function_selector, GATE_FUNCTION_TANH), T.tanh(gate_function_output + self.g_theta), gate_function_output)
        # apply GATE_FUNCTION_RECT to masked gates
        if self.has_gatefunction_rect:
            gate_function_output = T.switch(T.eq(self.g_function_selector, GATE_FUNCTION_RECT), T.switch(gate_function_output + self.g_theta > 0, gate_function_output - self.g_theta, 0), gate_function_output)
        # apply GATE_FUNCTION_DIST to masked gates
        if self.has_gatefunction_one_over_x:
            gate_function_output = T.switch(T.eq(self.g_function_selector, GATE_FUNCTION_DIST), T.switch(T.neq(0, gate_function_output), 1 / gate_function_output, 0), gate_function_output)

        # apply threshold
        thresholded_gate_function_output = \
            T.switch(T.ge(gate_function_output, self.g_threshold), gate_function_output, 0)

        # apply amplification
        amplified_gate_function_output = thresholded_gate_function_output * self.g_amplification

        # apply minimum and maximum
        limited_gate_function_output = T.clip(amplified_gate_function_output, self.g_min, self.g_max)

        gatefunctions = limited_gate_function_output

        # put the theano graph into a callable function to be executed
        self.calculate_nodes = theano.function([], None, updates=[(self.a, gatefunctions), (self.g_countdown, countdown)])

    def calculate(self):
        if self.has_new_usages:
            self.compile_calculate_nodes()
            self.has_new_usages = False

        self.__take_native_module_slot_snapshots()
        if self.has_pipes:
            self.__rebuild_shifted()
        if self.has_directional_activators:
            self.__calculate_g_factors()
        self.calculate_nodes()
        self.__calculate_native_modules()

    def por_ret_decay(self):

        #    por_cols = T.lvector("por_cols")
        #    por_rows = T.lvector("por_rows")
        #    new_w = T.set_subtensor(nodenet.w[por_rows, por_cols], nodenet.w[por_rows, por_cols] - 0.0001)
        #    self.decay = theano.function([por_cols, por_rows], None, updates={nodenet.w: new_w}, accept_inplace=True)

        porretdecay = self.nodenet.get_modulator('por_ret_decay')
        if self.has_pipes and porretdecay != 0:
            n_function_selector = self.n_function_selector.get_value(borrow=True)
            w = self.w.get_value(borrow=True)
            por_cols = np.where(n_function_selector == NFPG_PIPE_POR)[0]
            por_rows = np.nonzero(w[:, por_cols] > 0.)[0]
            cols, rows = np.meshgrid(por_cols, por_rows)
            w_update = w[rows, cols]
            w_update *= (1 - porretdecay)
            if self.nodenet.current_step % 1000 == 0:
                nullify_grid = np.nonzero(w_update < porretdecay**2)
                w_update[nullify_grid] = 0
            w[rows, cols] = w_update
            self.w.set_value(w, borrow=True)

    def __take_native_module_slot_snapshots(self):
        for uid, instance in self.native_module_instances.items():
            instance.take_slot_activation_snapshot()

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

    def rebuild_por_linked(self):

        n_node_porlinked_array = np.zeros(self.NoE, dtype=np.int8)

        n_function_selector_array = self.n_function_selector.get_value(borrow=True)
        w_matrix = self.w.get_value(borrow=True)

        por_indices = np.where(n_function_selector_array == NFPG_PIPE_POR)[0]

        slotrows = w_matrix[por_indices, :]
        if not self.sparse:
            linkedflags = np.any(slotrows, axis=1)
        else:
            # for some reason, sparse matrices won't do any with an axis parameter, so we need to do this...
            max_values = slotrows.max(axis=1).todense()
            linkedflags = max_values.astype(np.int8, copy=False)
            linkedflags = np.minimum(linkedflags, 1)

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
            # for some reason, sparse matrices won't do any with an axis parameter, so we need to do this...
            max_values = slotrows.max(axis=1).todense()
            linkedflags = max_values.astype(np.int8, copy=False)
            linkedflags = np.minimum(linkedflags, 1)

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
        new_allocated_node_parents = np.zeros(new_NoN, dtype=np.int32)
        new_allocated_node_offsets = np.zeros(new_NoN, dtype=np.int32)

        new_allocated_nodes[0:self.NoN] = self.allocated_nodes
        new_allocated_node_parents[0:self.NoN] = self.allocated_node_parents
        new_allocated_node_offsets[0:self.NoN] = self.allocated_node_offsets

        self.NoN = new_NoN
        self.allocated_nodes = new_allocated_nodes
        self.allocated_node_parents = new_allocated_node_parents
        self.allocated_node_offsets = new_allocated_node_offsets
        self.has_new_usages = True

    def grow_number_of_nodespaces(self, growby):

        new_NoNS = int(self.NoNS + growby)

        new_allocated_nodespaces = np.zeros(new_NoNS, dtype=np.int32)
        new_allocated_nodespaces_por_activators = np.zeros(new_NoNS, dtype=np.int32)
        new_allocated_nodespaces_ret_activators = np.zeros(new_NoNS, dtype=np.int32)
        new_allocated_nodespaces_sub_activators = np.zeros(new_NoNS, dtype=np.int32)
        new_allocated_nodespaces_sur_activators = np.zeros(new_NoNS, dtype=np.int32)
        new_allocated_nodespaces_cat_activators = np.zeros(new_NoNS, dtype=np.int32)
        new_allocated_nodespaces_exp_activators = np.zeros(new_NoNS, dtype=np.int32)

        new_allocated_nodespaces[0:self.NoNS] = self.allocated_nodespaces
        new_allocated_nodespaces_por_activators[0:self.NoNS] = self.allocated_nodespaces_por_activators
        new_allocated_nodespaces_ret_activators[0:self.NoNS] = self.allocated_nodespaces_ret_activators
        new_allocated_nodespaces_sub_activators[0:self.NoNS] = self.allocated_nodespaces_sub_activators
        new_allocated_nodespaces_sur_activators[0:self.NoNS] = self.allocated_nodespaces_sur_activators
        new_allocated_nodespaces_cat_activators[0:self.NoNS] = self.allocated_nodespaces_cat_activators
        new_allocated_nodespaces_exp_activators[0:self.NoNS] = self.allocated_nodespaces_exp_activators

        with self.nodenet.netlock:
            self.NoNS = new_NoNS
            self.allocated_nodespaces = new_allocated_nodespaces
            self.allocated_nodespaces_por_activators = new_allocated_nodespaces_por_activators
            self.allocated_nodespaces_ret_activators = new_allocated_nodespaces_ret_activators
            self.allocated_nodespaces_sub_activators = new_allocated_nodespaces_sub_activators
            self.allocated_nodespaces_sur_activators = new_allocated_nodespaces_sur_activators
            self.allocated_nodespaces_cat_activators = new_allocated_nodespaces_cat_activators
            self.allocated_nodespaces_exp_activators = new_allocated_nodespaces_exp_activators
            self.has_new_usages = True

    def grow_number_of_elements(self, growby):

        new_NoE = int(self.NoE + growby)

        new_allocated_elements_to_nodes = np.zeros(new_NoE, dtype=np.int32)
        new_allocated_elements_to_activators = np.zeros(new_NoE, dtype=np.int32)

        if self.sparse:
            new_w = sp.csr_matrix((new_NoE, new_NoE), dtype=self.nodenet.scipyfloatX)
        else:
            new_w = np.zeros((new_NoE, new_NoE), dtype=self.nodenet.scipyfloatX)

        new_a = np.zeros(new_NoE, dtype=self.nodenet.numpyfloatX)
        new_a_shifted = np.lib.stride_tricks.as_strided(new_a, shape=(new_NoE, 7), strides=(self.nodenet.byte_per_float, self.nodenet.byte_per_float))
        new_g_theta = np.zeros(new_NoE, dtype=self.nodenet.numpyfloatX)
        new_g_factor = np.ones(new_NoE, dtype=self.nodenet.numpyfloatX)
        new_g_threshold = np.zeros(new_NoE, dtype=self.nodenet.numpyfloatX)
        new_g_amplification = np.ones(new_NoE, dtype=self.nodenet.numpyfloatX)
        new_g_min = np.zeros(new_NoE, dtype=self.nodenet.numpyfloatX)
        new_g_max = np.ones(new_NoE, dtype=self.nodenet.numpyfloatX)
        new_g_function_selector = np.zeros(new_NoE, dtype=np.int8)
        new_g_expect = np.ones(new_NoE, dtype=self.nodenet.numpyfloatX)
        new_g_countdown = np.zeros(new_NoE, dtype=np.int8)
        new_g_wait = np.ones(new_NoE, dtype=np.int8)
        new_n_function_selector = np.zeros(new_NoE, dtype=np.int8)
        new_n_node_porlinked = np.zeros(new_NoE, dtype=np.int8)
        new_n_node_retlinked = np.zeros(new_NoE, dtype=np.int8)

        new_allocated_elements_to_nodes[0:self.NoE] = self.allocated_elements_to_nodes
        new_allocated_elements_to_activators[0:self.NoE] = self.allocated_elements_to_activators

        new_w[0:self.NoE, 0:self.NoE] = self.w.get_value(borrow=True)

        new_a[0:self.NoE] = self.a.get_value(borrow=True)
        new_g_theta[0:self.NoE] = self.g_theta.get_value(borrow=True)
        new_g_factor[0:self.NoE] = self.g_factor.get_value(borrow=True)
        new_g_threshold[0:self.NoE] = self.g_threshold.get_value(borrow=True)
        new_g_amplification[0:self.NoE] = self.g_amplification.get_value(borrow=True)
        new_g_min[0:self.NoE] = self.g_min.get_value(borrow=True)
        new_g_max[0:self.NoE] =  self.g_max.get_value(borrow=True)
        new_g_function_selector[0:self.NoE] = self.g_function_selector.get_value(borrow=True)
        new_g_expect[0:self.NoE] = self.g_expect.get_value(borrow=True)
        new_g_countdown[0:self.NoE] = self.g_countdown.get_value(borrow=True)
        new_g_wait[0:self.NoE] = self.g_wait.get_value(borrow=True)
        new_n_function_selector[0:self.NoE] = self.n_function_selector.get_value(borrow=True)

        with self.nodenet.netlock:
            self.NoE = new_NoE
            self.allocated_elements_to_nodes = new_allocated_elements_to_nodes
            self.allocated_elements_to_activators = new_allocated_elements_to_activators
            self.w.set_value(new_w, borrow=True)
            self.a.set_value(new_a, borrow=True)
            self.a_shifted.set_value(new_a_shifted, borrow=True)
            self.g_theta.set_value(new_g_theta, borrow=True)
            self.g_factor.set_value(new_g_factor, borrow=True)
            self.g_threshold.set_value(new_g_threshold, borrow=True)
            self.g_amplification.set_value(new_g_amplification, borrow=True)
            self.g_min.set_value(new_g_min, borrow=True)
            self.g_max.set_value(new_g_max, borrow=True)
            self.g_function_selector.set_value(new_g_function_selector, borrow=True)
            self.g_expect.set_value(new_g_expect, borrow=True)
            self.g_countdown.set_value(new_g_countdown, borrow=True)
            self.g_wait.set_value(new_g_wait, borrow=True)
            self.n_function_selector.set_value(new_n_function_selector, borrow=True)
            self.n_node_porlinked.set_value(new_n_node_porlinked, borrow=True)
            self.n_node_retlinked.set_value(new_n_node_retlinked, borrow=True)
            self.has_new_usages = True

        if self.has_pipes:
            self.por_ret_dirty = True

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
