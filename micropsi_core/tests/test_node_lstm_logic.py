#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""
Tests for node activation propagation and gate arithmetic
"""

import math


def f(x):
    return 1 / (1 + math.exp(-x))


def h(x):
    return (2 / (1 + math.exp(-x))) - 1


def g(x):
    return (4 / (1 + math.exp(-x))) - 2


def prepare(runtime, test_nodenet):
    nodenet = runtime.get_nodenet(test_nodenet)
    netapi = nodenet.netapi
    source = netapi.create_node("Neuron", None, "Source")
    netapi.link(source, "gen", source, "gen")
    source.activation = 1
    nodenet.step()
    return nodenet, netapi, source


def prepare_lstm(runtime, test_nodenet):
    nodenet = runtime.get_nodenet(test_nodenet)
    netapi = nodenet.netapi
    lstm = netapi.create_node("LSTM", None, "Test")
    netapi.link(lstm, "gen", lstm, "gen")
    return lstm


def test_node_lstm_logic_passthrough(runtime, test_nodenet):
    # test for an LSTM node with only the cell slot connected
    net, netapi, source = prepare(runtime, test_nodenet)
    lstm = prepare_lstm(runtime, test_nodenet)

    x = 1

    netapi.link(source, "gen", lstm, "por")

    net.step()

    # first sample
    s = f(0) * 0 + f(0) * g(x)
    net.step()
    assert round(lstm.get_gate("por").activation, 4) == round(f(0) * h(s), 4)
    net.step()
    assert round(lstm.get_gate("por").activation, 4) == round(f(0) * h(s), 4)
    net.step()
    assert round(lstm.get_gate("por").activation, 4) == round(f(0) * h(s), 4)

    # 3 steps of second sample
    s = f(0) * s + f(0) * g(x)
    net.step()
    assert round(lstm.get_gate("por").activation, 4) == round(f(0) * h(s), 4)
    net.step()
    assert round(lstm.get_gate("por").activation, 4) == round(f(0) * h(s), 4)
    net.step()
    assert round(lstm.get_gate("por").activation, 4) == round(f(0) * h(s), 4)


def test_node_lstm_logic_active_in_gate(runtime, test_nodenet):
    # test lsm with cell and in connected
    net, netapi, source = prepare(runtime, test_nodenet)
    lstm = prepare_lstm(runtime, test_nodenet)

    x = 1

    netapi.link(source, "gen", lstm, "por")
    netapi.link(source, "gen", lstm, "gin")

    net.step()

    # first sample
    s = f(0) * 0 + f(1) * g(x)
    net.step()
    assert round(lstm.get_gate("por").activation, 4) == round(f(0) * h(s), 4)
    net.step()
    assert round(lstm.get_gate("por").activation, 4) == round(f(0) * h(s), 4)
    net.step()
    assert round(lstm.get_gate("por").activation, 4) == round(f(0) * h(s), 4)

    # 3 steps of second sample
    s = f(0) * s + f(1) * g(x)
    net.step()
    assert round(lstm.get_gate("por").activation, 4) == round(f(0) * h(s), 4)
    net.step()
    assert round(lstm.get_gate("por").activation, 4) == round(f(0) * h(s), 4)
    net.step()
    assert round(lstm.get_gate("por").activation, 4) == round(f(0) * h(s), 4)



def test_node_lstm_logic_active_in_out_gates(runtime, test_nodenet):
    # test lstm with in and out gates connected
    net, netapi, source = prepare(runtime, test_nodenet)
    lstm = prepare_lstm(runtime, test_nodenet)

    x = 1

    netapi.link(source, "gen", lstm, "por")
    netapi.link(source, "gen", lstm, "gin")
    netapi.link(source, "gen", lstm, "gou")

    net.step()

    # first sample
    s = f(0) * 0 + f(1) * g(x)
    net.step()
    assert round(lstm.get_gate("por").activation, 4) == round(f(1) * h(s), 4)
    net.step()
    assert round(lstm.get_gate("por").activation, 4) == round(f(1) * h(s), 4)
    net.step()
    assert round(lstm.get_gate("por").activation, 4) == round(f(1) * h(s), 4)

    # 3 steps of second sample
    s = f(0) * s + f(1) * g(x)
    net.step()
    assert round(lstm.get_gate("por").activation, 4) == round(f(1) * h(s), 4)
    net.step()
    assert round(lstm.get_gate("por").activation, 4) == round(f(1) * h(s), 4)
    net.step()
    assert round(lstm.get_gate("por").activation, 4) == round(f(1) * h(s), 4)


def test_node_lstm_logic_active_in_out_phi_gates(runtime, test_nodenet):
    # test lstm with in, out and forget gates connected
    net, netapi, source = prepare(runtime, test_nodenet)
    lstm = prepare_lstm(runtime, test_nodenet)

    x = 1

    netapi.link(source, "gen", lstm, "por")
    netapi.link(source, "gen", lstm, "gin")
    netapi.link(source, "gen", lstm, "gou")
    netapi.link(source, "gen", lstm, "gfg")

    net.step()

    # 3 steps of first sample
    s = f(1) * 0 + f(1) * g(x)
    net.step()
    assert round(lstm.get_gate("por").activation, 4) == round(f(1) * h(s), 4)
    net.step()
    assert round(lstm.get_gate("por").activation, 4) == round(f(1) * h(s), 4)
    net.step()
    assert round(lstm.get_gate("por").activation, 4) == round(f(1) * h(s), 4)

    # 3 steps of second sample
    s = f(1) * s + f(1) * g(x)
    net.step()
    assert round(lstm.get_gate("por").activation, 4) == round(f(1) * h(s), 4)
    net.step()
    assert round(lstm.get_gate("por").activation, 4) == round(f(1) * h(s), 4)
    net.step()
    assert round(lstm.get_gate("por").activation, 4) == round(f(1) * h(s), 4)


def test_node_lstm_logic_sampling_activator(runtime, test_nodenet):
    # test for an LSTM node that's not supposed to update itself as long as a sampling activator is present,
    # but inactive
    net, netapi, source = prepare(runtime, test_nodenet)
    lstm = prepare_lstm(runtime, test_nodenet)

    x = 1

    activator = netapi.create_node("Activator", None)
    activator.set_parameter("type", "sampling")

    netapi.link(source, "gen", lstm, "por")

    # first sample with activator 0
    s = f(0) * 0 + f(0) * g(x)
    net.step()
    assert round(lstm.get_gate("por").activation, 4) == 0
    net.step()
    assert round(lstm.get_gate("por").activation, 4) == 0
    net.step()
    assert round(lstm.get_gate("por").activation, 4) == 0

    # 3 steps of second sample with activator 0
    s = f(0) * s + f(0) * g(x)
    net.step()
    assert round(lstm.get_gate("por").activation, 4) == 0
    net.step()
    assert round(lstm.get_gate("por").activation, 4) == 0
    net.step()
    assert round(lstm.get_gate("por").activation, 4) == 0

    netapi.link(source, "gen", activator, "gen")

    net.step()

    # first sample
    s = f(0) * 0 + f(0) * g(x)
    net.step()
    assert round(lstm.get_gate("por").activation, 4) == round(f(0) * h(s), 4)
    net.step()
    assert round(lstm.get_gate("por").activation, 4) == round(f(0) * h(s), 4)
    net.step()
    assert round(lstm.get_gate("por").activation, 4) == round(f(0) * h(s), 4)

    # 3 steps of second sample
    s = f(0) * s + f(0) * g(x)
    net.step()
    assert round(lstm.get_gate("por").activation, 4) == round(f(0) * h(s), 4)
    net.step()
    assert round(lstm.get_gate("por").activation, 4) == round(f(0) * h(s), 4)
    net.step()
    assert round(lstm.get_gate("por").activation, 4) == round(f(0) * h(s), 4)

    netapi.unlink(source, "gen", activator, "gen")
    netapi.unlink(source, "gen", lstm, "por")

    # 3 steps of second sample that should remain unchanged
    net.step()
    assert round(lstm.get_gate("por").activation, 4) == round(f(0) * h(s), 4)
    net.step()
    assert round(lstm.get_gate("por").activation, 4) == round(f(0) * h(s), 4)
    net.step()
    assert round(lstm.get_gate("por").activation, 4) == round(f(0) * h(s), 4)
