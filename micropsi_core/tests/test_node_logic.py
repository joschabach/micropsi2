#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""
Tests for node activation propagation and gate arithmetic
"""

from micropsi_core import runtime as micropsi


def prepare(fixed_nodenet):
    nodenet = micropsi.get_nodenet(fixed_nodenet)
    netapi = nodenet.netapi
    source = netapi.create_node("Register", "Root", "Source")
    netapi.link(source, "gen", source, "gen")
    source.activation = 1
    nodenet.step()
    return nodenet, netapi, source


def test_node_logic_loop(fixed_nodenet):
    # test gen looping behaviour
    net, netapi, source = prepare(fixed_nodenet)
    net.step()
    assert source.get_gate("gen").activation == 1
    net.step()
    assert source.get_gate("gen").activation == 1
    netapi.link(source, "gen", source, "gen", 0.5)
    net.step()
    assert source.get_gate("gen").activation == 0.5


def test_node_logic_die(fixed_nodenet):
    # without the link, activation ought to drop to 0
    net, netapi, source = prepare(fixed_nodenet)

    netapi.unlink(source, "gen", source, "gen")
    net.step()
    assert source.get_gate("gen").activation == 0


def test_node_logic_sum(fixed_nodenet):
    # propagate positive activation, expect sum
    net, netapi, source = prepare(fixed_nodenet)

    reg_a = netapi.create_node("Register", "Root", "RegA")
    reg_b = netapi.create_node("Register", "Root", "RegB")
    reg_result = netapi.create_node("Register", "Root", "RegResult")

    netapi.link(source, "gen", reg_a, "gen", 0.5)
    netapi.link(source, "gen", reg_b, "gen", 0.5)
    netapi.link(reg_a, "gen", reg_result, "gen")
    netapi.link(reg_b, "gen", reg_result, "gen")

    net.step()
    net.step()
    assert reg_result.get_gate("gen").activation == 1


def test_node_logic_cancel(fixed_nodenet):
    # propagate positive and negative activation, expect cancellation
    net, netapi, source = prepare(fixed_nodenet)

    reg_a = netapi.create_node("Register", "Root", "RegA")
    reg_b = netapi.create_node("Register", "Root", "RegB")
    reg_b.set_gate_parameters("gen", {"threshold": -100})
    reg_result = netapi.create_node("Register", "Root", "RegResult")

    netapi.link(source, "gen", reg_a, "gen", 1)
    netapi.link(source, "gen", reg_b, "gen", -1)
    netapi.link(reg_a, "gen", reg_result, "gen")
    netapi.link(reg_b, "gen", reg_result, "gen")

    net.step()
    net.step()
    assert reg_result.get_gate("gen").activation == 0


def test_node_logic_store_and_forward(fixed_nodenet):
    # collect activation in one node, go forward only if both dependencies are met
    net, netapi, source = prepare(fixed_nodenet)

    reg_a = netapi.create_node("Register", "Root", "RegA")
    reg_b = netapi.create_node("Register", "Root", "RegB")
    reg_b.set_gate_parameters("gen", {"threshold": -100})
    reg_result = netapi.create_node("Register", "Root", "RegResult")
    reg_b.set_gate_parameters("gen", {"threshold": 1})

    netapi.link(source, "gen", reg_a, "gen")
    netapi.link(reg_a, "gen", reg_result, "gen")
    netapi.link(reg_b, "gen", reg_result, "gen")
    net.step()
    assert reg_result.get_gate("gen").activation == 0

    netapi.link(source, "gen", reg_b, "gen")
    net.step()
    assert reg_result.get_gate("gen").activation == 1


def test_node_logic_store_and_forward(fixed_nodenet):
    #
    net, netapi, source = prepare(fixed_nodenet)

    reg_a = netapi.create_node("Register", "Root", "RegA")
    reg_b = netapi.create_node("Register", "Root", "RegB")
    reg_b.set_gate_parameters("gen", {"threshold": -100})
    reg_result = netapi.create_node("Register", "Root", "RegResult")
    reg_b.set_gate_parameters("gen", {"threshold": 1})

    netapi.link(source, "gen", reg_a, "gen")
    netapi.link(reg_a, "gen", reg_result, "gen")
    netapi.link(reg_b, "gen", reg_result, "gen")
    net.step()
    assert reg_result.get_gate("gen").activation == 0

    netapi.link(source, "gen", reg_b, "gen")
    net.step()
    assert reg_result.get_gate("gen").activation == 1
