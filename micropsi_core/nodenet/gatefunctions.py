
""" Collection of available gatefunctions """

import math

# identity, abs, sigmoid, "return 0.0 if x == 0.0 else 1.0 / x"


def identity(input_activation, rho, theta):
    return input_activation


def absolute(input_activation, rho, theta):
    return abs(input_activation)


def sigmoid(input_activation, rho, theta):
    return 1.0 / (1.0 + math.exp(-(theta + input_activation)))


def one_over_x(input_activation, rho, theta):
    return 0.0 if input_activation == 0.0 else 1.0 / input_activation
