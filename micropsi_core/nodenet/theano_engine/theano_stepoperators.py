
from micropsi_core.nodenet.stepoperators import Propagate, Calculate
import theano
from theano import tensor as T
from theano import shared
from theano import function
from theano.tensor import nnet as N
import theano.sparse as ST
from micropsi_core.nodenet.theano_engine.theano_node import *

GATE_FUNCTION_IDENTITY = 0
GATE_FUNCTION_ABSOLUTE = 1
GATE_FUNCTION_SIGMOID = 2
GATE_FUNCTION_TANH = 3
GATE_FUNCTION_RECT = 4
GATE_FUNCTION_DIST = 5

NFPG_PIPE_NON = 0
NFPG_PIPE_GEN = 1
NFPG_PIPE_POR = 2
NFPG_PIPE_RET = 3
NFPG_PIPE_SUB = 4
NFPG_PIPE_SUR = 5
NFPG_PIPE_CAT = 6
NFPG_PIPE_EXP = 7


class TheanoPropagate(Propagate):
    """
        theano implementation of the Propagate operator.

        Propagates activation from a across w back to a (a is the gate vector and becomes the slot vector)

        every entry in the target vector is the sum of the products of the corresponding input vector
        and the weight values, i.e. the dot product of weight matrix and activation vector

    """

    propagate = None

    def __init__(self, nodenet):
        if nodenet.sparse:
            self.propagate = theano.function([], None, updates={nodenet.a: ST.dot(nodenet.w, nodenet.a)})
        else:
            self.propagate = theano.function([], None, updates={nodenet.a: T.dot(nodenet.w, nodenet.a)})

    def execute(self, nodenet, nodes, netapi):
        self.propagate()


class TheanoCalculate(Calculate):
    """
        theano implementation of the Calculate operator.

        implements node and gate functions as a theano graph.

    """

    worldadapter = None
    nodenet = None
    calculate = None

    def __init__(self, nodenet):
        self.nodenet = nodenet
        self.worldadapter = nodenet.world

    def compile_theano_functions(self, nodenet):
        slots = nodenet.a_shifted
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
        pipe_por_cond = T.switch(T.eq(por_linked, 1), T.gt(slots[:, 7], 0), 1)      # (if linked, por must be > 0)
        pipe_por_cond = pipe_por_cond * T.gt(slots[:, 9], 0)                        # and (sub > 0)

        pipe_por = slots[:, 10]                                                     # start with sur
        pipe_por = pipe_por + T.gt(slots[:, 6], 0.1)                                # add gen-loop 1 if por > 0
        pipe_por = pipe_por * pipe_por_cond                                         # apply conditions
                                                                                    # add por (for search) if sub=sur=0
        pipe_por = pipe_por + (slots[:, 7] * T.eq(slots[:, 9], 0) * T.eq(slots[:, 10], 0))

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
        pipe_sur_cond = T.switch(T.eq(por_linked, 1), T.gt(slots[:, 4], 0), 1)      # (if linked, por must be > 0)
                                                                                    # and we aren't first in a script
        pipe_sur_cond = pipe_sur_cond * T.switch(T.eq(ret_linked, 1), T.eq(por_linked, 1), 1)
        pipe_sur_cond = pipe_sur_cond * T.ge(slots[:, 5], 0)                        # and (ret >= 0)

        pipe_sur = slots[:, 7]                                                      # start with sur
        pipe_sur = pipe_sur + T.gt(slots[:, 3], 0.2)                                # add gen-loop 1
        pipe_sur = pipe_sur + slots[:, 9]                                           # add exp
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
        self.calculate = theano.function([], None, updates={nodenet.a: gatefunctions})


    def read_sensors_and_actuator_feedback(self):
        if self.worldadapter is None:
            return

        datasource_to_value_map = {}
        for datasource in self.worldadapter.get_available_datasources(self.nodenet.uid):
            datasource_to_value_map[datasource] = self.worldadapter.get_datasource(self.nodenet.uid, datasource)

        datatarget_to_value_map = {}
        for datatarget in self.worldadapter.get_available_datatargets(self.nodenet.uid):
            datatarget_to_value_map[datatarget] = self.worldadapter.get_datatarget_feedback(self.nodenet.uid, datatarget)

        self.nodenet.set_sensors_and_actuator_feedback_to_values(datasource_to_value_map, datatarget_to_value_map)

    def write_actuators(self):
        if self.worldadapter is None:
            return

        values_to_write = self.nodenet.read_actuators()
        for datatarget in values_to_write:
            self.worldadapter.add_to_datatarget(self.nodenet.uid, datatarget, values_to_write[datatarget])

    def take_native_module_slot_snapshots(self):
        for uid, instance in self.nodenet.native_module_instances.items():
            instance.take_slot_activation_snapshot()

    def calculate_native_modules(self):
        for uid, instance in self.nodenet.native_module_instances.items():
            instance.node_function()

    def calculate_g_factors(self):
        a = self.nodenet.a.get_value(borrow=True, return_internal_type=True)
        a[0] = 1.
        g_factor = a[self.nodenet.allocated_elements_to_activators]
        self.nodenet.g_factor.set_value(g_factor, borrow=True)

    def execute(self, nodenet, nodes, netapi):

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
        self.calculate_native_modules()
