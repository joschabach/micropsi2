
from micropsi_core.nodenet.stepoperators import Propagate, Calculate
import theano
from theano import tensor as T
from theano import shared
from theano.tensor import nnet as N
import theano.sparse as ST


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

        # node functions implemented with identity for now
        nodefunctions = nodenet.a

        # gate logic

        # multiply with gate factor for the node space
        gated_nodefunctions = nodefunctions * nodenet.g_factor

        # apply actual gate function
        # implemented with identity for now
        gate_function_output = gated_nodefunctions

        # apply threshold
        thresholded_gate_function_output = \
            T.switch(T.ge(gate_function_output, nodenet.g_threshold), gate_function_output, 0)

        # apply amplification
        amplified_gate_function_output = thresholded_gate_function_output * nodenet.g_amplification

        # apply minimum
        min_limited_gate_function_output = T.minimum(amplified_gate_function_output, nodenet.g_max)

        # apply maximum
        max_limited_gate_function_output = T.maximum(min_limited_gate_function_output, nodenet.g_min)

        gatefunctions = max_limited_gate_function_output

        # put the theano graph into a callable function to be executed
        self.calculate = theano.function([], nodenet.a, updates={nodenet.a: gatefunctions})

    def read_sensors(self):
        if self.worldadapter is None:
            return
        datasource_to_value_map = {}
        for datasource in self.worldadapter.get_available_datasources(self.nodenet.uid):
            datasource_to_value_map[datasource] = self.worldadapter.get_datasource(self.nodenet.uid, datasource)

        self.nodenet.set_sensors_to_values(datasource_to_value_map)

    def execute(self, nodenet, nodes, netapi):

        self.calculate()
        self.read_sensors()
