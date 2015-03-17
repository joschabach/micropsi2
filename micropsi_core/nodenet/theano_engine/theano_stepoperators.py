import math

from micropsi_core.nodenet.stepoperators import StepOperator, Propagate, Calculate
from theano import tensor as T
from theano import shared

class TheanoPropagate(Propagate):
    """
        theano implementation of the Propagate operator.

        Propagates activation from a across w back to a (a is the gate vector and becomes the slot vector)

        every entry in the target vector is the sum of the products of the corresponding input vector
        and the weight values, i.e. the dot product of weight matrix and activation vector

    """
    def execute(self, nodenet, nodes, netapi):
        nodenet.a = shared(T.dot(nodenet.w, nodenet.a).eval(), name="a", borrow=True)
