#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""
Tests for node activation propagation and gate arithmetic
"""


def prepare(runtime, test_nodenet):
    nodenet = runtime.get_nodenet(test_nodenet)
    netapi = nodenet.netapi
    source = netapi.create_node("Neuron", None, "Source")
    netapi.link(source, "gen", source, "gen")
    source.activation = 1
    nodenet.step()
    register = netapi.create_node("Neuron", None)
    netapi.link(source, "gen", register, "gen")
    return nodenet, netapi, source, register


def test_gate_arithmetics_propagation(runtime, test_nodenet):
    # propagate activation, expect it to show up at the gen gate
    net, netapi, source, register = prepare(runtime, test_nodenet)
    net.step()
    assert register.get_gate("gen").activation == 1


def test_gate_arithmetics_maximum(runtime, test_nodenet):
    # set maximum, expect the cutoff to work
    net, netapi, source, register = prepare(runtime, test_nodenet)
    params = {'maximum': 0.5}
    register.set_gate_configuration("gen", "threshold", params)
    net.step()
    assert register.get_gate("gen").activation == 0.5


def test_gate_arithmetics_minimum(runtime, test_nodenet):
    # set minimum, expect it to show up
    net, netapi, source, register = prepare(runtime, test_nodenet)
    params = {
        "maximum": 2,
        "minimum": 1.5,
    }
    register.set_gate_configuration("gen", "threshold", params)
    runtime.save_nodenet(test_nodenet)
    net.step()
    assert register.get_gate("gen").activation == 1.5
    runtime.revert_nodenet(test_nodenet)
    net = runtime.nodenets[test_nodenet]
    net.step()
    assert net.get_node(register.uid).get_gate("gen").activation == 1.5


def test_gate_arithmetics_threshold(runtime, test_nodenet):
    # set threshold, expect it to mute the node
    net, netapi, source, register = prepare(runtime, test_nodenet)
    params = {
        "maximum": 2,
        "threshold": 1.5,
    }
    register.set_gate_configuration("gen", "threshold", params)
    net.step()
    assert register.get_gate("gen").activation == 0


def test_gate_arithmetics_amplification(runtime, test_nodenet):
    # set maximum and amplification, expect amplification to be applied after maximum
    net, netapi, source, register = prepare(runtime, test_nodenet)
    params = {
        "maximum": 10,
        "amplification": 10,
    }
    register.set_gate_configuration("gen", "threshold", params)
    net.step()
    assert register.get_gate("gen").activation == 10


def test_gate_arithmetics_amplification_and_threshold(runtime, test_nodenet):
    # set maximum, amplification and threshold, expect the threshold to mute the node despite amplification
    net, netapi, source, register = prepare(runtime, test_nodenet)
    params = {
        "maximum": 10,
        "amplification": 10,
        "threshold": 2,
    }
    register.set_gate_configuration("gen", "threshold", params)
    net.step()
    assert register.get_gate("gen").activation == 0


def test_gate_arithmetics_directional_activator_amplification(runtime, test_nodenet):
    # set maximum and threshold with a directional activator in place
    net, netapi, source, register = prepare(runtime, test_nodenet)
    activator = netapi.create_node("Activator", None)
    activator.set_parameter('type', 'sub')

    netapi.link(source, "gen", activator, "gen", 5)

    testpipe = netapi.create_node("Pipe", None)
    netapi.link(source, "gen", testpipe, "sub", 1)
    params = {
        "maximum": 10,
        "threshold": 0,
    }
    register.set_gate_configuration("gen", "threshold", params)
    net.step()
    assert testpipe.get_gate("sub").activation == 5


def test_gate_arithmetics_directional_activator_muting(runtime, test_nodenet):
    # have the directional activator mute the node
    net, netapi, source, register = prepare(runtime, test_nodenet)
    activator = netapi.create_node("Activator", None)
    activator.set_parameter('type', 'sub')

    netapi.link(source, "gen", activator, "gen", 0)

    testpipe = netapi.create_node("Pipe", None)
    netapi.link(source, "gen", testpipe, "sub", 1)
    params = {
        "maximum": 10,
        "threshold": 0,
    }
    register.set_gate_configuration("gen", "threshold", params)
    net.step()
    assert testpipe.get_gate("sub").activation == 0


def test_gate_arithmetics_directional_activator_threshold(runtime, test_nodenet):
    # have the directional activator amplify alpha above threshold
    net, netapi, source, register = prepare(runtime, test_nodenet)
    activator = netapi.create_node("Activator", None)
    activator.set_parameter('type', 'sub')

    netapi.link(source, "gen", activator, "gen", 2)

    testpipe = netapi.create_node("Pipe", None)
    netapi.link(source, "gen", testpipe, "sub", 1)
    params = {
        "maximum": 10,
        "threshold": 1,
    }
    register.set_gate_configuration("gen", "threshold", params)
    net.step()
    assert testpipe.get_gate("sub").activation == 2


def test_gatefunction_sigmoid(runtime, test_nodenet):
    # set a node function for gen gates, expect it to be used
    from micropsi_core.nodenet.gatefunctions import sigmoid
    net, netapi, source, register = prepare(runtime, test_nodenet)
    register.set_gate_configuration("gen", "sigmoid", {'bias': 1.2})
    runtime.save_nodenet(test_nodenet)
    net.step()
    assert round(register.get_gate("gen").activation, 5) == round(sigmoid(1, 1.2), 5)
    runtime.revert_nodenet(test_nodenet)
    net = runtime.nodenets[test_nodenet]
    net.step()
    assert round(net.get_node(register.uid).get_gate("gen").activation, 5) == round(sigmoid(1, 1.2), 5)


def test_gatefunction_elu(runtime, test_nodenet):
    from micropsi_core.nodenet.gatefunctions import elu
    net, netapi, source, register = prepare(runtime, test_nodenet)
    register.set_gate_configuration("gen", "elu", {'bias': 1.2})
    runtime.save_nodenet(test_nodenet)
    net.step()
    assert round(register.get_gate("gen").activation, 5) == round(elu(1, 1.2), 5)
    runtime.revert_nodenet(test_nodenet)
    net = runtime.nodenets[test_nodenet]
    net.step()
    assert round(net.get_node(register.uid).get_gate("gen").activation, 5) == round(elu(1, 1.2), 5)


def test_gatefunction_relu(runtime, test_nodenet):
    from micropsi_core.nodenet.gatefunctions import relu
    net, netapi, source, register = prepare(runtime, test_nodenet)
    register.set_gate_configuration("gen", "relu", {'bias': 1.2})
    runtime.save_nodenet(test_nodenet)
    net.step()
    assert round(register.get_gate("gen").activation, 5) == round(relu(1, 1.2), 5)
    runtime.revert_nodenet(test_nodenet)
    net = runtime.nodenets[test_nodenet]
    net.step()
    assert round(net.get_node(register.uid).get_gate("gen").activation, 5) == round(relu(1, 1.2), 5)


def test_gatefunction_on_over_x(runtime, test_nodenet):
    from micropsi_core.nodenet.gatefunctions import one_over_x
    net, netapi, source, register = prepare(runtime, test_nodenet)
    register.set_gate_configuration("gen", "one_over_x",)
    runtime.save_nodenet(test_nodenet)
    net.step()
    assert round(register.get_gate("gen").activation, 5) == round(one_over_x(1), 5)
    runtime.revert_nodenet(test_nodenet)
    net = runtime.nodenets[test_nodenet]
    net.step()
    assert round(net.get_node(register.uid).get_gate("gen").activation) == round(one_over_x(1), 5)


def test_gatefunction_absolute(runtime, test_nodenet):
    from micropsi_core.nodenet.gatefunctions import absolute
    net, netapi, source, register = prepare(runtime, test_nodenet)
    register.set_gate_configuration("gen", "absolute")
    runtime.save_nodenet(test_nodenet)
    net.step()
    assert round(register.get_gate("gen").activation, 5) == round(absolute(1), 5)
    runtime.revert_nodenet(test_nodenet)
    net = runtime.nodenets[test_nodenet]
    net.step()
    assert round(net.get_node(register.uid).get_gate("gen").activation, 5) == round(absolute(1), 5)


def test_gatefunction_none_is_identity(runtime, test_nodenet):
    from micropsi_core.nodenet.gatefunctions import identity
    net, netapi, source, register = prepare(runtime, test_nodenet)
    register.set_gate_configuration("gen", None)
    net.step()
    assert register.get_gate("gen").activation == identity(1)


def test_node_activation_is_gen_gate_activation(runtime, test_nodenet):
    from micropsi_core.nodenet.gatefunctions import sigmoid
    net, netapi, source, register = prepare(runtime, test_nodenet)
    register.set_gate_configuration('gen', 'sigmoid', {'bias': 1.3})
    sig = round(sigmoid(1, 1.3), 4)
    net.step()
    assert round(register.activation, 4) == sig
    assert round(register.get_gate('gen').activation, 4) == sig
