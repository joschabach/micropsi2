
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
            self.propagate = theano.function([], [nodenet.w, nodenet.a], updates={nodenet.a: ST.dot(nodenet.w, nodenet.a)})
        else:
            self.propagate = theano.function([], [nodenet.w, nodenet.a], updates={nodenet.a: T.dot(nodenet.w, nodenet.a)})

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

        # node functions implemented with identity by default (native modules are calculated by python)
        nodefunctions = nodenet.a

        # pipe logic

        sur_exp = nodenet.a_shifted[:, 4] + nodenet.a_shifted[:, 6]     # sum of sur and exp
        pipe_gen = nodenet.a_shifted[:, 0] * nodenet.a_shifted[:, 3]    # gen * sub
        pipe_gen = T.switch(abs(pipe_gen) > 0.1, pipe_gen, sur_exp)     # drop to 0 if below 0.1
                                                                        # drop to 0 if por == 0 and por slot is linked
        pipe_gen = T.switch(T.eq(nodenet.a_shifted[:, 1], 0) and T.eq(nodenet.n_node_porlinked, 1), sur_exp, pipe_gen)

        pipe_por = 0
        pipe_ret = 0
        pipe_sub = 0
        pipe_sur = 0
        pipe_cat = 0
        pipe_exp = 0

        nodefunctions = T.switch(T.eq(nodenet.n_function_selector, NFPG_PIPE_GEN), pipe_gen, nodefunctions)
        nodefunctions = T.switch(T.eq(nodenet.n_function_selector, NFPG_PIPE_POR), pipe_por, nodefunctions)
        nodefunctions = T.switch(T.eq(nodenet.n_function_selector, NFPG_PIPE_RET), pipe_ret, nodefunctions)
        nodefunctions = T.switch(T.eq(nodenet.n_function_selector, NFPG_PIPE_SUB), pipe_sub, nodefunctions)
        nodefunctions = T.switch(T.eq(nodenet.n_function_selector, NFPG_PIPE_SUR), pipe_sur, nodefunctions)
        nodefunctions = T.switch(T.eq(nodenet.n_function_selector, NFPG_PIPE_CAT), pipe_cat, nodefunctions)
        nodefunctions = T.switch(T.eq(nodenet.n_function_selector, NFPG_PIPE_EXP), pipe_exp, nodefunctions)

        # gate logic

        # multiply with gate factor for the node space
        gated_nodefunctions = nodefunctions * nodenet.g_factor

        # apply actual gate functions
        gate_function_output = gated_nodefunctions

        # apply GATE_FUNCTION_ABS to masked gates
        gate_function_output = T.switch(T.eq(nodenet.g_function_selector, GATE_FUNCTION_ABSOLUTE), abs(gate_function_output), gate_function_output)
        # apply GATE_FUNCTION_SIGMOID to masked gates
        gate_function_output = T.switch(T.eq(nodenet.g_function_selector, GATE_FUNCTION_SIGMOID), N.sigmoid(gate_function_output - nodenet.g_theta), gate_function_output)
        # apply GATE_FUNCTION_TANH to masked gates
        gate_function_output = T.switch(T.eq(nodenet.g_function_selector, GATE_FUNCTION_TANH), T.tanh(gate_function_output - nodenet.g_theta), gate_function_output)
        # apply GATE_FUNCTION_RECT to masked gates
        gate_function_output = T.switch(T.eq(nodenet.g_function_selector, GATE_FUNCTION_RECT), T.switch(gate_function_output - nodenet.g_theta >0, gate_function_output - nodenet.g_theta, 0), gate_function_output)
        # apply GATE_FUNCTION_DIST to masked gates
        gate_function_output = T.switch(T.eq(nodenet.g_function_selector, GATE_FUNCTION_DIST), T.switch(T.neq(0, gate_function_output), 1/gate_function_output, 0), gate_function_output)

        # apply threshold
        thresholded_gate_function_output = \
            T.switch(T.ge(gate_function_output, nodenet.g_threshold), gate_function_output, 0)

        # apply amplification
        amplified_gate_function_output = thresholded_gate_function_output * nodenet.g_amplification

        # apply minimum and maximum
        limited_gate_function_output = T.clip(amplified_gate_function_output, nodenet.g_min, nodenet.g_max)

        gatefunctions = limited_gate_function_output

        # put the theano graph into a callable function to be executed
        self.calculate = theano.function([], nodenet.a, updates={nodenet.a: gatefunctions})

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

    def calculate_native_modules(self):
        for uid, instance in self.nodenet.native_module_instances.items():
            instance.take_slot_activation_snapshot()
            instance.node_function()

    def execute(self, nodenet, nodes, netapi):
        self.write_actuators()
        self.calculate_native_modules()

        self.nodenet.rebuild_shifted()

        self.calculate()
        self.read_sensors_and_actuator_feedback()

