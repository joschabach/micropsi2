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
    return nodenet, netapi, source


def test_node_logic_loop(runtime, test_nodenet):
    # test gen looping behaviour
    net, netapi, source = prepare(runtime, test_nodenet)
    net.step()
    assert source.get_gate("gen").activation == 1
    net.step()
    assert source.get_gate("gen").activation == 1
    netapi.link(source, "gen", source, "gen", 0.5)
    net.step()
    assert source.get_gate("gen").activation == 0.5


def test_node_logic_die(runtime, test_nodenet):
    # without the link, activation ought to drop to 0
    net, netapi, source = prepare(runtime, test_nodenet)

    netapi.unlink(source, "gen", source, "gen")
    net.step()
    assert source.get_gate("gen").activation == 0


def test_node_logic_sum(runtime, test_nodenet):
    # propagate positive activation, expect sum
    net, netapi, source = prepare(runtime, test_nodenet)

    reg_a = netapi.create_node("Neuron", None, "RegA")
    reg_b = netapi.create_node("Neuron", None, "RegB")
    reg_result = netapi.create_node("Neuron", None, "RegResult")

    netapi.link(source, "gen", reg_a, "gen", 0.5)
    netapi.link(source, "gen", reg_b, "gen", 0.5)
    netapi.link(reg_a, "gen", reg_result, "gen")
    netapi.link(reg_b, "gen", reg_result, "gen")

    net.step()
    net.step()
    assert reg_result.get_gate("gen").activation == 1


def test_node_logic_cancel(runtime, test_nodenet):
    # propagate positive and negative activation, expect cancellation
    net, netapi, source = prepare(runtime, test_nodenet)

    reg_a = netapi.create_node("Neuron", None, "RegA")
    reg_b = netapi.create_node("Neuron", None, "RegB")
    reg_result = netapi.create_node("Neuron", None, "RegResult")

    netapi.link(source, "gen", reg_a, "gen", 1)
    netapi.link(source, "gen", reg_b, "gen", -1)
    netapi.link(reg_a, "gen", reg_result, "gen")
    netapi.link(reg_b, "gen", reg_result, "gen")

    net.step()
    net.step()
    assert reg_result.get_gate("gen").activation == 0


def test_node_logic_store_and_forward(runtime, test_nodenet):
    # collect activation in one node, go forward only if both dependencies are met
    net, netapi, source = prepare(runtime, test_nodenet)

    reg_a = netapi.create_node("Neuron", None, "RegA")
    reg_b = netapi.create_node("Neuron", None, "RegB")
    reg_result = netapi.create_node("Neuron", None, "RegResult")

    netapi.link(source, "gen", reg_a, "gen")
    netapi.link(reg_a, "gen", reg_result, "gen")
    netapi.link(reg_b, "gen", reg_result, "gen")
    net.step()
    assert reg_result.get_gate("gen").activation == 0

    netapi.link(source, "gen", reg_b, "gen")
    net.step()
    assert reg_result.get_gate("gen").activation == 1


def test_node_logic_activators(runtime, test_nodenet):
    net, netapi, source = prepare(runtime, test_nodenet)
    activator = netapi.create_node('Activator', None)
    activator.set_parameter('type', 'sub')
    activator.activation = 1

    testpipe = netapi.create_node("Pipe", None)
    netapi.link(source, "gen", testpipe, "sub", 0)
    net.step()
    net.step()
    assert testpipe.get_gate("sub").activation == 0


def test_node_logic_sensor_modulator(runtime, test_nodenet, default_world):
    net, netapi, source = prepare(runtime, test_nodenet)
    register = netapi.create_node("Neuron", None)
    netapi.link_sensor(register, "emo_activation", "gen")
    runtime.step_nodenet(test_nodenet)
    runtime.step_nodenet(test_nodenet)
    runtime.step_nodenet(test_nodenet)
    assert round(netapi.get_modulator("emo_activation"), 3) == round(register.activation, 3)


def test_node_logic_sensor_datasource(runtime, test_nodenet, default_world):
    net, netapi, source = prepare(runtime, test_nodenet)
    runtime.set_nodenet_properties(test_nodenet, worldadapter="Default", world_uid=default_world)
    register = netapi.create_node("Neuron", None)
    netapi.link_sensor(register, "static_on", "gen", weight=0.35)
    runtime.step_nodenet(test_nodenet)
    runtime.step_nodenet(test_nodenet)
    assert round(register.get_gate("gen").activation, 3) == 0.35


def test_node_logic_actuator_modulator(runtime, test_nodenet, default_world):
    net, netapi, source = prepare(runtime, test_nodenet)
    netapi.link_actuator(source, "base_porret_decay_factor", weight=0.3, gate="gen")
    runtime.step_nodenet(test_nodenet)
    assert round(netapi.get_modulator("base_porret_decay_factor"), 3) == 0.3


def test_node_logic_actuator_datatarget(runtime, test_nodenet, default_world):
    net, netapi, source = prepare(runtime, test_nodenet)
    runtime.set_nodenet_properties(test_nodenet, worldadapter="Default", world_uid=default_world)
    netapi.link_actuator(source, "echo", weight=0.5, gate="gen")
    register = netapi.create_node("Neuron", None)
    actuator = netapi.get_nodes(node_name_prefix="echo")[0]
    netapi.link(actuator, "gen", register, "gen")
    runtime.step_nodenet(test_nodenet)
    runtime.step_nodenet(test_nodenet)
    runtime.step_nodenet(test_nodenet)
    assert round(register.get_gate("gen").activation, 1) == 0.5


def test_node_logic_sensor_nomodulators(runtime, engine, default_world):
    result, nnuid = runtime.new_nodenet("adf", engine, "Default", world_uid=default_world, use_modulators=False)
    net, netapi, source = prepare(runtime, nnuid)
    register = netapi.create_node("Neuron", None)
    netapi.link_sensor(register, "static_on", "gen", weight=0.4)
    runtime.step_nodenet(nnuid)
    runtime.step_nodenet(nnuid)
    assert round(register.get_gate("gen").activation, 1) == 0.4


def test_node_logic_actuator_nomodulators(runtime, engine, default_world):
    result, nnuid = runtime.new_nodenet("adf", engine, "Default", world_uid=default_world, use_modulators=False)
    net, netapi, source = prepare(runtime, nnuid)
    netapi.link_actuator(source, "echo", weight=0.7, gate="gen")
    register = netapi.create_node("Neuron", None)
    actuator = netapi.get_nodes(node_name_prefix="echo")[0]
    netapi.link(actuator, "gen", register, "gen")
    runtime.step_nodenet(nnuid)
    runtime.step_nodenet(nnuid)
    runtime.step_nodenet(nnuid)
    assert round(register.get_gate("gen").activation, 1) == 0.7
