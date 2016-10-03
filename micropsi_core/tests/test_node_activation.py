#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""
Tests for node activation propagation and gate arithmetic
"""


def prepare(runtime, test_nodenet):
    nodenet = runtime.get_nodenet(test_nodenet)
    netapi = nodenet.netapi
    source = netapi.create_node("Register", None, "Source")
    netapi.link(source, "gen", source, "gen")
    source.activation = 1
    nodenet.step()
    register = netapi.create_node("Register", None)
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
    register.set_gate_parameter("gen", "maximum", 0.5)
    net.step()
    assert register.get_gate("gen").activation == 0.5


def test_gate_arithmetics_minimum(runtime, test_nodenet):
    # set minimum, expect it to show up
    net, netapi, source, register = prepare(runtime, test_nodenet)
    register.set_gate_parameter("gen", "maximum", 2)
    register.set_gate_parameter("gen", "minimum", 1.5)
    net.step()
    assert register.get_gate("gen").activation == 1.5


def test_gate_arithmetics_threshold(runtime, test_nodenet):
    # set threshold, expect it to mute the node
    net, netapi, source, register = prepare(runtime, test_nodenet)
    register.set_gate_parameter("gen", "maximum", 2)
    register.set_gate_parameter("gen", "threshold", 1.5)
    net.step()
    assert register.get_gate("gen").activation == 0


def test_gate_arithmetics_amplification(runtime, test_nodenet):
    # set maximum and amplification, expect amplification to be applied after maximum
    net, netapi, source, register = prepare(runtime, test_nodenet)
    register.set_gate_parameter("gen", "maximum", 10)
    register.set_gate_parameter("gen", "amplification", 10)
    net.step()
    assert register.get_gate("gen").activation == 10


def test_gate_arithmetics_amplification_and_threshold(runtime, test_nodenet):
    # set maximum, amplification and threshold, expect the threshold to mute the node despite amplification
    net, netapi, source, register = prepare(runtime, test_nodenet)
    register.set_gate_parameter("gen", "maximum", 10)
    register.set_gate_parameter("gen", "amplification", 10)
    register.set_gate_parameter("gen", "threshold", 2)
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
    testpipe.set_gate_parameter("sub", "maximum", 10)
    testpipe.set_gate_parameter("sub", "threshold", 0)
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
    testpipe.set_gate_parameter("sub", "maximum", 10)
    testpipe.set_gate_parameter("sub", "threshold", 0)
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
    testpipe.set_gate_parameter("sub", "maximum", 10)
    testpipe.set_gate_parameter("sub", "threshold", 1)
    net.step()
    assert testpipe.get_gate("sub").activation == 2


def test_gatefunction_sigmoid(runtime, test_nodenet):
    # set a node function for gen gates, expect it to be used
    from micropsi_core.nodenet.gatefunctions import sigmoid
    net, netapi, source, register = prepare(runtime, test_nodenet)
    register.set_gatefunction_name("gen", "sigmoid")
    net.step()
    assert round(register.get_gate("gen").activation, 5) == round(sigmoid(1, 0, 0), 5)


def test_gatefunction_threshold(runtime, test_nodenet):
    from micropsi_core.nodenet.gatefunctions import threshold
    net, netapi, source, register = prepare(runtime, test_nodenet)
    register.set_gatefunction_name("gen", "threshold")
    net.step()
    assert round(register.get_gate("gen").activation, 5) == round(threshold(1, 0, 0), 5)


def test_gatefunction_none_is_identity(runtime, test_nodenet):
    from micropsi_core.nodenet.gatefunctions import identity
    net, netapi, source, register = prepare(runtime, test_nodenet)
    register.set_gatefunction_name("gen", None)
    net.step()
    assert register.get_gate("gen").activation == identity(1, 0, 0)


def test_dict_gatefunctions(runtime, test_nodenet):
    # call every gatefunction once
    import micropsi_core.nodenet.gatefunctions as funcs
    assert funcs.absolute(-1., 0, 0) == 1
    assert funcs.one_over_x(2., 0, 0) == 0.5
    assert funcs.identity(1, 0, 0) == 1
    assert funcs.sigmoid(0, 0, 0) == 0.5
    assert funcs.threshold(0.5, threshold=1) == 0
    assert funcs.threshold(0.5, minimum=0.7) == 0.7
    assert funcs.threshold(0.5, maximum=0.4) == 0.4
    assert funcs.threshold(0.5, minimum=0.7, threshold=1) == 0
    assert funcs.threshold(0.6, minimum=0.7, maximum=1.1, amplification=2) == 1.1
    assert funcs.threshold(0.5, maximum=0.4, amplification=2) == 0.4
    assert funcs.threshold(0.5, threshold=1, amplification=2) == 0


def test_node_activation_is_gen_gate_activation(runtime, test_nodenet):
    from micropsi_core.nodenet.gatefunctions import sigmoid
    net, netapi, source, register = prepare(runtime, test_nodenet)
    register.set_gatefunction_name('gen', 'sigmoid')
    sig = round(sigmoid(1, 0, 0), 4)
    net.step()
    assert round(register.activation, 4) == sig
    assert round(register.get_gate('gen').activation, 4) == sig
