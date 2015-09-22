#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""
Tests for node activation propagation and gate arithmetic
"""

from micropsi_core import runtime as micropsi
import math


def f(x):
    return 1 / (1 + math.exp(-x))


def h(x):
    return (2 / (1 + math.exp(-x))) - 1


def g(x):
    return (4 / (1 + math.exp(-x))) - 2


def prepare(fixed_nodenet):
    nodenet = micropsi.get_nodenet(fixed_nodenet)
    netapi = nodenet.netapi
    netapi.delete_node(netapi.get_node("n0006"))
    source = netapi.create_node("Register", None, "Source")
    netapi.link(source, "gen", source, "gen")
    source.activation = 1
    nodenet.step()
    return nodenet, netapi, source


def prepare_lstm(fixed_nodenet):
    nodenet = micropsi.get_nodenet(fixed_nodenet)
    netapi = nodenet.netapi
    lstm = netapi.create_node("LSTM", None, "Test")
    netapi.link(lstm, "gen", lstm, "gen")
    return lstm


def test_node_lstm_logic_passthrough(fixed_nodenet):
    # test for an LSTM node with only the cell slot connected
    net, netapi, source = prepare(fixed_nodenet)
    lstm = prepare_lstm(fixed_nodenet)

    x = 1

    netapi.link(source, "gen", lstm, "por")

    # 2 steps of 0 until first sampling
    net.step()
    assert lstm.get_gate("por").activation == 0
    net.step()
    assert lstm.get_gate("por").activation == 0

    # 3 steps of first sample
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


def test_node_lstm_logic_active_in_gate(fixed_nodenet):
    # test lsm with cell and in connected
    net, netapi, source = prepare(fixed_nodenet)
    lstm = prepare_lstm(fixed_nodenet)

    x = 1

    netapi.link(source, "gen", lstm, "por")
    netapi.link(source, "gen", lstm, "gin")

    # 2 steps of 0 until first sampling
    net.step()
    assert lstm.get_gate("por").activation == 0
    net.step()
    assert lstm.get_gate("por").activation == 0

    # 3 steps of first sample
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



def test_node_lstm_logic_active_in_out_gates(fixed_nodenet):
    # test lstm with in and out gates connected
    net, netapi, source = prepare(fixed_nodenet)
    lstm = prepare_lstm(fixed_nodenet)

    x = 1

    netapi.link(source, "gen", lstm, "por")
    netapi.link(source, "gen", lstm, "gin")
    netapi.link(source, "gen", lstm, "gou")

    # 2 steps of 0 until first sampling
    net.step()
    assert lstm.get_gate("por").activation == 0
    net.step()
    assert lstm.get_gate("por").activation == 0

    # 3 steps of first sample
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


def test_node_lstm_logic_active_in_out_phi_gates(fixed_nodenet):
    # test lstm with in, out and forget gates connected
    net, netapi, source = prepare(fixed_nodenet)
    lstm = prepare_lstm(fixed_nodenet)

    x = 1

    netapi.link(source, "gen", lstm, "por")
    netapi.link(source, "gen", lstm, "gin")
    netapi.link(source, "gen", lstm, "gou")
    netapi.link(source, "gen", lstm, "gfg")

    # 2 steps of 0 until first sampling
    net.step()
    assert lstm.get_gate("por").activation == 0
    net.step()
    assert lstm.get_gate("por").activation == 0

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
