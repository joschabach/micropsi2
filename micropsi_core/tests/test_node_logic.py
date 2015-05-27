#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""
Tests for node activation propagation and gate arithmetic
"""

from micropsi_core import runtime as micropsi
from micropsi_core.world.world import World
from micropsi_core.world.worldadapter import WorldAdapter


class DummyWorld(World):

    supported_worldadapters = ['DummyWorldAdapter']

    def __init__(self, filename, world_type="DummyWorld", name="", owner="", uid=None, version=1):
        World.__init__(self, filename, world_type=world_type, name=name, owner=owner, uid=uid, version=version)
        self.current_step = 0
        self.data['assets'] = {}


class DummyWorldAdapter(WorldAdapter):

    supported_datasources = ['test_source']
    supported_datatargets = ['test_target']

    def __init__(self, world, uid=None, **data):
        WorldAdapter.__init__(self, world, uid=uid, **data)
        self.datasources = {'test_source': 0.7}
        self.datatargets = {'test_target': 0}
        self.datatarget_feedback = {'test_target': 0.3}

    def update_data_sources_and_targets(self):
        self.world.test_target_value = self.datatargets['test_target']


def prepare(fixed_nodenet):
    nodenet = micropsi.get_nodenet(fixed_nodenet)
    netapi = nodenet.netapi
    source = netapi.create_node("Register", None, "Source")
    netapi.link(source, "gen", source, "gen")
    source.activation = 1
    nodenet.step()
    return nodenet, netapi, source


def add_dummyworld(fixed_nodenet):
    nodenet = micropsi.get_nodenet(fixed_nodenet)
    if nodenet.world:
        nodenet.world.unregister_nodenet(nodenet.uid)

    worlduid = micropsi.new_world("DummyWorld", "DummyWorld", "DummyOwner")[1]

    nodenet.world = micropsi.worlds[worlduid]
    nodenet.worldadapter = "DummyWorldAdapter"
    nodenet.world.register_nodenet("DummyWorldAdapter", nodenet)
    return nodenet.world


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

    reg_a = netapi.create_node("Register", None, "RegA")
    reg_b = netapi.create_node("Register", None, "RegB")
    reg_result = netapi.create_node("Register", None, "RegResult")

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

    reg_a = netapi.create_node("Register", None, "RegA")
    reg_b = netapi.create_node("Register", None, "RegB")
    reg_b.set_gate_parameter("gen", "threshold", -100)
    reg_result = netapi.create_node("Register", None, "RegResult")

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

    reg_a = netapi.create_node("Register", None, "RegA")
    reg_b = netapi.create_node("Register", None, "RegB")
    reg_b.set_gate_parameter("gen", "threshold", -100)
    reg_result = netapi.create_node("Register", None, "RegResult")
    reg_b.set_gate_parameter("gen", "threshold", 1)

    netapi.link(source, "gen", reg_a, "gen")
    netapi.link(reg_a, "gen", reg_result, "gen")
    netapi.link(reg_b, "gen", reg_result, "gen")
    net.step()
    assert reg_result.get_gate("gen").activation == 0

    netapi.link(source, "gen", reg_b, "gen")
    net.step()
    assert reg_result.get_gate("gen").activation == 1


def test_node_logic_activators(fixed_nodenet):
    net, netapi, source = prepare(fixed_nodenet)
    activator = netapi.create_node('Activator', None)
    activator.set_parameter('type', 'sub')
    activator.activation = 1

    testpipe = netapi.create_node("Pipe", None)
    netapi.link(source, "gen", testpipe, "sub", 0)
    net.step()
    net.step()
    assert testpipe.get_gate("sub").activation == 0


def test_node_logic_sensor(fixed_nodenet):
    # read a sensor value from the dummy world adapter
    net, netapi, source = prepare(fixed_nodenet)
    world = add_dummyworld(fixed_nodenet)

    register = netapi.create_node("Register", None)
    netapi.link_sensor(register, "test_source", "gen")
    world.step()
    net.step()
    net.step()
    assert round(register.get_gate("gen").activation, 1) == 0.7


def test_node_logic_actor(fixed_nodenet):
    # write a value to the dummy world adapter
    net, netapi, source = prepare(fixed_nodenet)
    world = add_dummyworld(fixed_nodenet)

    register = netapi.create_node("Register", None)
    netapi.link_actor(source, "test_target", 0.5, 1, "gen", "gen")
    actor = netapi.get_nodes(node_name_prefix="test_target")[0]
    netapi.link(actor, "gen", register, "gen")
    net.step()
    world.step()
    assert world.test_target_value == 0.5
    net.step()
    assert round(register.get_gate("gen").activation, 1) == 0.3
