
""" Collection of available gatefunctions """

import math

# identity, abs, sigmoid, "return 0.0 if x == 0.0 else 1.0 / x"


def identity(input_activation):
    return input_activation


def absolute(input_activation):
    return abs(input_activation)


def sigmoid(input_activation, bias=0):
    return 1.0 / (1.0 + math.exp(-(bias + input_activation)))


def elu(input_activation, bias=0):
    input_activation += bias
    if input_activation <= 0:
        return math.exp(input_activation) - 1.
    else:
        return input_activation


def relu(input_activation, bias=0):
    return max(0, input_activation + bias)


def one_over_x(input_activation):
    return 0.0 if input_activation == 0.0 else 1.0 / input_activation


def threshold(input_activation, minimum=0.0, maximum=1.0, threshold=0.0, amplification=1.0):
    act = input_activation
    if act < threshold:
        return 0
    act *= amplification
    act = min(maximum, max(act, minimum))
    return act
