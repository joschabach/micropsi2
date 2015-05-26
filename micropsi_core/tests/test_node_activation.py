#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""
Tests for node activation propagation and gate arithmetic
"""

from micropsi_core import runtime as micropsi


def prepare(fixed_nodenet):
    nodenet = micropsi.get_nodenet(fixed_nodenet)
    netapi = nodenet.netapi
    source = netapi.create_node("Register", None, "Source")
    netapi.link(source, "gen", source, "gen")
    source.activation = 1
    nodenet.step()
    register = netapi.create_node("Register", None)
    netapi.link(source, "gen", register, "gen")
    return nodenet, netapi, source, register


def test_gate_arithmetics_propagation(fixed_nodenet):
    # propagate activation, expect it to show up at the gen gate
    net, netapi, source, register = prepare(fixed_nodenet)
    net.step()
    assert register.get_gate("gen").activation == 1


def test_gate_arithmetics_maximum(fixed_nodenet):
    # set maximum, expect the cutoff to work
    net, netapi, source, register = prepare(fixed_nodenet)
    register.set_gate_parameter("gen", "maximum", 0.5)
    net.step()
    assert register.get_gate("gen").activation == 0.5


def test_gate_arithmetics_minimum(fixed_nodenet):
    # set minimum, expect it to show up
    net, netapi, source, register = prepare(fixed_nodenet)
    register.set_gate_parameter("gen", "maximum", 2)
    register.set_gate_parameter("gen", "minimum", 1.5)
    net.step()
    assert register.get_gate("gen").activation == 1.5


def test_gate_arithmetics_threshold(fixed_nodenet):
    # set threshold, expect it to mute the node
    net, netapi, source, register = prepare(fixed_nodenet)
    register.set_gate_parameter("gen", "maximum", 2)
    register.set_gate_parameter("gen", "threshold", 1.5)
    net.step()
    assert register.get_gate("gen").activation == 0


def test_gate_arithmetics_amplification(fixed_nodenet):
    # set maximum and amplification, expect amplification to be applied after maximum
    net, netapi, source, register = prepare(fixed_nodenet)
    register.set_gate_parameter("gen", "maximum", 10)
    register.set_gate_parameter("gen", "amplification", 10)
    net.step()
    assert register.get_gate("gen").activation == 10


def test_gate_arithmetics_amplification_and_threshold(fixed_nodenet):
    # set maximum, amplification and threshold, expect the threshold to mute the node despite amplification
    net, netapi, source, register = prepare(fixed_nodenet)
    register.set_gate_parameter("gen", "maximum", 10)
    register.set_gate_parameter("gen", "amplification", 10)
    register.set_gate_parameter("gen", "threshold", 2)
    net.step()
    assert register.get_gate("gen").activation == 0


def test_gate_arithmetics_directional_activator_amplification(fixed_nodenet):
    # set maximum and threshold with a directional activator in place
    net, netapi, source, register = prepare(fixed_nodenet)
    activator = netapi.create_node("Activator", None)
    activator.set_parameter('type', 'sub')

    netapi.link(source, "gen", activator, "gen", 5)

    testpipe = netapi.create_node("Pipe", None)
    netapi.link(source, "gen", testpipe, "sub", 1)
    testpipe.set_gate_parameter("sub", "maximum", 10)
    testpipe.set_gate_parameter("sub", "threshold", 0)
    net.step()
    assert testpipe.get_gate("sub").activation == 5


def test_gate_arithmetics_directional_activator_muting(fixed_nodenet):
    # have the directional activator mute the node
    net, netapi, source, register = prepare(fixed_nodenet)
    activator = netapi.create_node("Activator", None)
    activator.set_parameter('type', 'sub')

    netapi.link(source, "gen", activator, "gen", 0)

    testpipe = netapi.create_node("Pipe", None)
    netapi.link(source, "gen", testpipe, "sub", 1)
    testpipe.set_gate_parameter("sub", "maximum", 10)
    testpipe.set_gate_parameter("sub", "threshold", 0)
    net.step()
    assert testpipe.get_gate("sub").activation == 0


def test_gate_arithmetics_directional_activator_threshold(fixed_nodenet):
    # have the directional activator amplify alpha above threshold
    net, netapi, source, register = prepare(fixed_nodenet)
    activator = netapi.create_node("Activator", None)
    activator.set_parameter('type', 'sub')

    netapi.link(source, "gen", activator, "gen", 2)

    testpipe = netapi.create_node("Pipe", None)
    netapi.link(source, "gen", testpipe, "sub", 1)
    testpipe.set_gate_parameter("sub", "maximum", 10)
    testpipe.set_gate_parameter("sub", "threshold", 1)
    net.step()
    assert testpipe.get_gate("sub").activation == 2


def test_gatefunction_sigmoid(fixed_nodenet):
    # set a node function for gen gates, expect it to be used
    from micropsi_core.nodenet.gatefunctions import sigmoid
    net, netapi, source, register = prepare(fixed_nodenet)
    register.set_gatefunction_name("gen", "sigmoid")
    net.step()
    assert round(register.get_gate("gen").activation, 5) == round(sigmoid(1, 0, 0), 5)


def test_gatefunction_none_is_identity(fixed_nodenet):
    from micropsi_core.nodenet.gatefunctions import identity
    net, netapi, source, register = prepare(fixed_nodenet)
    register.set_gatefunction_name("gen", None)
    net.step()
    assert register.get_gate("gen").activation == identity(1, 0, 0)


def test_gatefunctions(fixed_nodenet):
    # call every gatefunction once
    import micropsi_core.nodenet.gatefunctions as funcs
    assert funcs.absolute(-1., 0, 0) == 1
    assert funcs.one_over_x(2., 0, 0) == 0.5
    assert funcs.identity(1, 0, 0) == 1
    assert funcs.sigmoid(0, 0, 0) == 0.5


def test_node_activation_is_gen_gate_activation(fixed_nodenet):
    from micropsi_core.nodenet.gatefunctions import sigmoid
    net, netapi, source, register = prepare(fixed_nodenet)
    register.set_gatefunction_name('gen', 'sigmoid')
    sig = round(sigmoid(1, 0, 0), 4)
    net.step()
    assert round(register.activation, 4) == sig
    assert round(register.get_gate('gen').activation, 4) == sig
