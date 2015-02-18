#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""
Tests for node activation propagation and gate arithmetic
"""

from micropsi_core import runtime as micropsi


def prepare(fixed_nodenet):
    nodenet = micropsi.get_nodenet(fixed_nodenet)
    netapi = nodenet.netapi
    netapi.delete_node(netapi.get_node("ACTA"))
    netapi.delete_node(netapi.get_node("ACTB"))
    source = netapi.create_node("Register", "Root", "Source")
    netapi.link(source, "gen", source, "gen")
    source.activation = 1
    nodenet.step()
    return nodenet, netapi, source


def test_node_trigger_logic_good_after_five_steps(fixed_nodenet):
    # test a trigger that replies as expected after five steps
    net, netapi, source = prepare(fixed_nodenet)
    n_trigger = netapi.create_node("Trigger", "Root", "Trigger")

    netapi.link(source, "gen", n_trigger, "sub", 1)
    net.step()

    assert n_trigger.get_gate("sur").activation == 0

    net.step()
    net.step()
    net.step()
    netapi.link(source, "gen", n_trigger, "sur", 1)
    net.step()

    assert n_trigger.get_gate("sur").activation == 1

    netapi.unlink(source, "gen", n_trigger, "sur")
    net.step()
    net.step()

    assert n_trigger.get_gate("sur").activation == 0


def test_node_trigger_logic_good_after_five_steps_despite_timeout(fixed_nodenet):
    # test a trigger that succeeds beyond the timeout because the response matches
    net, netapi, source = prepare(fixed_nodenet)
    n_trigger = netapi.create_node("Trigger", "Root", "Trigger")
    n_trigger.set_parameter("timeout", 5)
    n_trigger.set_parameter("response", 42)

    netapi.link(source, "gen", n_trigger, "sub", 1)
    net.step()

    assert n_trigger.get_gate("sur").activation == 0

    net.step()
    net.step()
    net.step()
    netapi.link(source, "gen", n_trigger, "sur", 42)
    net.step()
    net.step()
    net.step()
    net.step()
    net.step()

    assert n_trigger.get_gate("sur").activation == 1


def test_node_trigger_logic_fail_after_five_steps(fixed_nodenet):
    # test a trigger that fails after the configured five steps
    net, netapi, source = prepare(fixed_nodenet)
    n_trigger = netapi.create_node("Trigger", "Root", "Trigger")
    n_trigger.set_parameter("timeout", 5)

    netapi.link(source, "gen", n_trigger, "sub", 1)
    net.step()

    assert n_trigger.get_gate("sur").activation == 0

    net.step()
    net.step()
    net.step()
    net.step()
    net.step()
    net.step()

    assert n_trigger.get_gate("sur").activation == -1


def test_node_trigger_logic_fail_after_five_steps_despite_response(fixed_nodenet):
    # test a trigger that fails after the configured five steps, despite some non-matching activation
    net, netapi, source = prepare(fixed_nodenet)
    n_trigger = netapi.create_node("Trigger", "Root", "Trigger")
    n_trigger.set_parameter("timeout", 5)
    n_trigger.set_parameter("response", 42)

    netapi.link(source, "gen", n_trigger, "sub", 1)
    net.step()

    assert n_trigger.get_gate("sur").activation == 0

    net.step()
    net.step()
    net.step()
    netapi.link(source, "gen", n_trigger, "sur", 41)
    net.step()
    net.step()
    net.step()

    assert n_trigger.get_gate("sur").activation == -1


def test_node_trigger_logic_good_after_fail(fixed_nodenet):
    # test a trigger that goes back to good after failing
    net, netapi, source = prepare(fixed_nodenet)
    n_trigger = netapi.create_node("Trigger", "Root", "Trigger")
    n_trigger.set_parameter("timeout", 5)
    n_trigger.set_parameter("response", 42)

    netapi.link(source, "gen", n_trigger, "sub", 1)
    net.step()

    assert n_trigger.get_gate("sur").activation == 0

    net.step()
    net.step()
    net.step()
    net.step()
    net.step()
    net.step()

    assert n_trigger.get_gate("sur").activation == -1

    netapi.link(source, "gen", n_trigger, "sur", 42)

    net.step()
    net.step()

    assert n_trigger.get_gate("sur").activation == 1
