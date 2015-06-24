
from micropsi_core.nodenet.stepoperators import StepOperator, Propagate, Calculate
import theano
from theano import tensor as T
from theano import shared
from theano import function
from theano.tensor import nnet as N
import theano.sparse as ST
import numpy as np
from micropsi_core.nodenet.theano_engine.theano_node import *
from micropsi_core.nodenet.theano_engine.theano_definitions import *


class TheanoPropagate(Propagate):
    """
        theano implementation of the Propagate operator.

        Propagates activation from a across w back to a (a is the gate vector and becomes the slot vector)

        every entry in the target vector is the sum of the products of the corresponding input vector
        and the weight values, i.e. the dot product of weight matrix and activation vector

    """

    def __init__(self, nodenet):
        if nodenet.sparse:
            self.propagate = theano.function([], None, updates={nodenet.a: ST.dot(nodenet.rootsection.w, nodenet.a)})
        else:
            self.propagate = theano.function([], None, updates={nodenet.a: T.dot(nodenet.rootsection.w, nodenet.a)})

    def execute(self, nodenet, nodes, netapi):
        self.propagate()


class TheanoCalculate(Calculate):
    """
        theano implementation of the Calculate operator.

        implements node and gate functions as a theano graph.

    """

    def __init__(self, nodenet):
        self.calculate = None
        self.world = None
        self.nodenet = nodenet

    def compile_theano_functions(self, nodenet):
        slots = nodenet.a_shifted
        countdown = nodenet.g_countdown
        por_linked = nodenet.n_node_porlinked
        ret_linked = nodenet.n_node_retlinked

        # node functions implemented with identity by default (native modules are calculated by python)
        nodefunctions = nodenet.a

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
        countdown_por = T.switch(cdrc_por, self.nodenet.g_wait, T.maximum(countdown - 1, -1))

        pipe_por_cond = T.switch(T.eq(por_linked, 1), T.gt(slots[:, 7], 0), 1)      # (if linked, por must be > 0)
        pipe_por_cond = pipe_por_cond * T.gt(slots[:, 9], 0)                        # and (sub > 0)

        pipe_por = slots[:, 10]                                                     # start with sur
        pipe_por = pipe_por + T.gt(slots[:, 6], 0.1)                                # add gen-loop 1 if por > 0
                                                                                    # check if we're in timeout
        pipe_por = T.switch(T.le(countdown, 0) * T.lt(pipe_por, nodenet.g_expect), -1, pipe_por)
        pipe_por = pipe_por * pipe_por_cond                                         # apply conditions
                                                                                    # add por (for search) if sub=sur=0
        pipe_por = pipe_por + (slots[:, 7] * T.eq(slots[:, 9], 0) * T.eq(slots[:, 10], 0))
                                                                                    # reset failure countdown on confirm
        countdown_por = T.switch(T.ge(pipe_por, nodenet.g_expect), self.nodenet.g_wait, countdown_por)

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
        countdown_sur = T.switch(cd_reset_cond, self.nodenet.g_wait, T.maximum(countdown - 1, -1))

        pipe_sur_cond = T.eq(ret_linked, 0)                                         # (not ret-linked
        pipe_sur_cond = pipe_sur_cond + (T.ge(slots[:, 5],0) * T.gt(slots[:, 6], 0))# or (ret is 0, but sub > 0))
        pipe_sur_cond = pipe_sur_cond * (T.eq(por_linked, 0) + T.gt(slots[:, 4], 0))# and (not por-linked or por > 0)
        pipe_sur_cond = T.gt(pipe_sur_cond, 0)

        pipe_sur = slots[:, 7]                                                      # start with sur
        pipe_sur = pipe_sur + T.gt(slots[:, 3], 0.2)                                # add gen-loop 1
        pipe_sur = pipe_sur + slots[:, 9]                                           # add exp
                                                                                    # drop to zero if < expectation
        pipe_sur = T.switch(T.lt(pipe_sur, nodenet.g_expect) * T.gt(pipe_sur, 0), 0, pipe_sur)
                                                                                    # check if we're in timeout
        pipe_sur = T.switch(T.le(countdown, 0) * T.lt(pipe_sur, nodenet.g_expect), -1, pipe_sur)
                                                                                    # reset failure countdown on confirm
        countdown_sur = T.switch(T.ge(pipe_sur, nodenet.g_expect), self.nodenet.g_wait, countdown_sur)
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

        if nodenet.has_pipes:
            nodefunctions = T.switch(T.eq(nodenet.n_function_selector, NFPG_PIPE_GEN), pipe_gen, nodefunctions)
            nodefunctions = T.switch(T.eq(nodenet.n_function_selector, NFPG_PIPE_POR), pipe_por, nodefunctions)
            nodefunctions = T.switch(T.eq(nodenet.n_function_selector, NFPG_PIPE_RET), pipe_ret, nodefunctions)
            nodefunctions = T.switch(T.eq(nodenet.n_function_selector, NFPG_PIPE_SUB), pipe_sub, nodefunctions)
            nodefunctions = T.switch(T.eq(nodenet.n_function_selector, NFPG_PIPE_SUR), pipe_sur, nodefunctions)
            nodefunctions = T.switch(T.eq(nodenet.n_function_selector, NFPG_PIPE_CAT), pipe_cat, nodefunctions)
            nodefunctions = T.switch(T.eq(nodenet.n_function_selector, NFPG_PIPE_EXP), pipe_exp, nodefunctions)
            countdown = T.switch(T.eq(nodenet.n_function_selector, NFPG_PIPE_POR), countdown_por, countdown)
            countdown = T.switch(T.eq(nodenet.n_function_selector, NFPG_PIPE_SUR), countdown_sur, countdown)

        # gate logic

        # multiply with gate factor for the node space
        if nodenet.has_directional_activators:
            nodefunctions = nodefunctions * nodenet.g_factor

        # apply actual gate functions
        gate_function_output = nodefunctions

        # apply GATE_FUNCTION_ABS to masked gates
        if nodenet.has_gatefunction_absolute:
            gate_function_output = T.switch(T.eq(nodenet.g_function_selector, GATE_FUNCTION_ABSOLUTE), abs(gate_function_output), gate_function_output)
        # apply GATE_FUNCTION_SIGMOID to masked gates
        if nodenet.has_gatefunction_sigmoid:
            gate_function_output = T.switch(T.eq(nodenet.g_function_selector, GATE_FUNCTION_SIGMOID), N.sigmoid(gate_function_output + nodenet.g_theta), gate_function_output)
        # apply GATE_FUNCTION_TANH to masked gates
        if nodenet.has_gatefunction_tanh:
            gate_function_output = T.switch(T.eq(nodenet.g_function_selector, GATE_FUNCTION_TANH), T.tanh(gate_function_output + nodenet.g_theta), gate_function_output)
        # apply GATE_FUNCTION_RECT to masked gates
        if nodenet.has_gatefunction_rect:
            gate_function_output = T.switch(T.eq(nodenet.g_function_selector, GATE_FUNCTION_RECT), T.switch(gate_function_output + nodenet.g_theta > 0, gate_function_output - nodenet.g_theta, 0), gate_function_output)
        # apply GATE_FUNCTION_DIST to masked gates
        if nodenet.has_gatefunction_one_over_x:
            gate_function_output = T.switch(T.eq(nodenet.g_function_selector, GATE_FUNCTION_DIST), T.switch(T.neq(0, gate_function_output), 1 / gate_function_output, 0), gate_function_output)

        # apply threshold
        thresholded_gate_function_output = \
            T.switch(T.ge(gate_function_output, nodenet.g_threshold), gate_function_output, 0)

        # apply amplification
        amplified_gate_function_output = thresholded_gate_function_output * nodenet.g_amplification

        # apply minimum and maximum
        limited_gate_function_output = T.clip(amplified_gate_function_output, nodenet.g_min, nodenet.g_max)

        gatefunctions = limited_gate_function_output

        # put the theano graph into a callable function to be executed
        self.calculate = theano.function([], None, updates=[(nodenet.a, gatefunctions), (nodenet.g_countdown, countdown)])

    def read_sensors_and_actuator_feedback(self):
        if self.world is None:
            return

        datasource_to_value_map = {}
        for datasource in self.world.get_available_datasources(self.nodenet.uid):
            datasource_to_value_map[datasource] = self.world.get_datasource(self.nodenet.uid, datasource)

        datatarget_to_value_map = {}
        for datatarget in self.world.get_available_datatargets(self.nodenet.uid):
            datatarget_to_value_map[datatarget] = self.world.get_datatarget_feedback(self.nodenet.uid, datatarget)

        self.nodenet.set_sensors_and_actuator_feedback_to_values(datasource_to_value_map, datatarget_to_value_map)

    def write_actuators(self):
        if self.world is None:
            return

        values_to_write = self.nodenet.read_actuators()
        for datatarget in values_to_write:
            self.world.add_to_datatarget(self.nodenet.uid, datatarget, values_to_write[datatarget])

    def take_native_module_slot_snapshots(self):
        for uid, instance in self.nodenet.native_module_instances.items():
            instance.take_slot_activation_snapshot()

    def calculate_native_modules(self):
        for uid, instance in self.nodenet.native_module_instances.items():
            instance.node_function()

    def calculate_g_factors(self):
        a = self.nodenet.a.get_value(borrow=True)
        a[0] = 1.
        g_factor = a[self.nodenet.rootsection.allocated_elements_to_activators]
        self.nodenet.g_factor.set_value(g_factor, borrow=True)

    def count_success_and_failure(self, nodenet):
        nays = len(np.where((nodenet.n_function_selector.get_value(borrow=True) == NFPG_PIPE_SUR) & (nodenet.a.get_value(borrow=True) <= -1))[0])
        yays = len(np.where((nodenet.n_function_selector.get_value(borrow=True) == NFPG_PIPE_SUR) & (nodenet.a.get_value(borrow=True) >= 1))[0])
        nodenet.set_modulator('base_number_of_expected_events', yays)
        nodenet.set_modulator('base_number_of_unexpected_events', nays)

    def execute(self, nodenet, nodes, netapi):
        self.world = nodenet.world
        if nodenet.has_new_usages:
            self.compile_theano_functions(nodenet)
            nodenet.has_new_usages = False

        self.take_native_module_slot_snapshots()
        self.write_actuators()
        self.read_sensors_and_actuator_feedback()
        if nodenet.has_pipes:
            self.nodenet.rebuild_shifted()
        if nodenet.has_directional_activators:
            self.calculate_g_factors()
        self.calculate()
        if nodenet.has_pipes:
            self.count_success_and_failure(nodenet)
        self.calculate_native_modules()


class TheanoPORRETDecay(StepOperator):
    """
    Implementation of POR/RET link decaying.
    This is a pure numpy implementation right now, as theano doesn't like setting subtensors with fancy indexing
    on sparse matrices.
    """

    @property
    def priority(self):
        return 100

    def __init__(self, nodenet):
        self.nodenet = nodenet

    #def compile_theano_functions(self, nodenet):
    #    por_cols = T.lvector("por_cols")
    #    por_rows = T.lvector("por_rows")
    #    new_w = T.set_subtensor(nodenet.w[por_rows, por_cols], nodenet.w[por_rows, por_cols] - 0.0001)
    #    self.decay = theano.function([por_cols, por_rows], None, updates={nodenet.w: new_w}, accept_inplace=True)

    def execute(self, nodenet, nodes, netapi):
        porretdecay = nodenet.get_modulator('por_ret_decay')
        if nodenet.has_pipes and porretdecay != 0:
            n_function_selector = nodenet.n_function_selector.get_value(borrow=True)
            w = nodenet.rootsection.w.get_value(borrow=True)
            por_cols = np.where(n_function_selector == NFPG_PIPE_POR)[0]
            por_rows = np.nonzero(w[:, por_cols] > 0.)[0]
            cols, rows = np.meshgrid(por_cols, por_rows)
            w_update = w[rows, cols]
            w_update *= (1 - porretdecay)
            if nodenet.current_step % 1000 == 0:
                nullify_grid = np.nonzero(w_update < porretdecay**2)
                w_update[nullify_grid] = 0
            w[rows, cols] = w_update
            nodenet.rootsection.w.set_value(w, borrow=True)
