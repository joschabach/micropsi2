#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""
Tests for netapi, i.e. the interface native modules will be developed against
"""

from micropsi_core import runtime as micropsi
from micropsi_core.world.world import World
from micropsi_core.world.worldadapter import WorldAdapter, WorldObject


class DummyWorld(World):

    supported_worldadapters = ['DummyWorldAdapter']

    def __init__(self, filename, world_type="DummyWorld", name="", owner="", uid=None, version=1):
        World.__init__(self, filename, world_type=world_type, name=name, owner=owner, uid=uid, version=version)
        self.current_step = 0
        self.data['assets'] = {}


class DummyWorldAdapter(WorldAdapter):

    datasources = {'test_source': 0.7}
    datatargets = {'test_target': 0}
    datatarget_feedback = {'test_target': 0.3}

    def __init__(self, world, uid=None, **data):
        WorldObject.__init__(self, world, category='agents', uid=uid, **data)

    def update(self):
        self.world.test_target_value = self.datatargets['test_target']


def prepare(fixed_nodenet):
    nodenet = micropsi.get_nodenet(fixed_nodenet)
    netapi = nodenet.netapi
    source = netapi.create_node("Register", "Root", "Source")
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


def test_node_netapi_create_register_node(fixed_nodenet):
    # test gen looping behaviour
    net, netapi, source = prepare(fixed_nodenet)
    node = netapi.create_node("Register", "Root", "TestName")

    # basic logic tests
    assert node is not None
    assert node.parent_nodespace == "Root"
    assert node.type == "Register"
    assert node.uid is not None
    assert node.nodenet is net
    assert len(node.get_gate('gen').outgoing) == 0
    assert len(node.get_gate('gen').sheaves) == 1

    # frontend/persistency-oriented data dictionary test
    assert node.data['uid'] == node.uid
    assert node.data['gate_parameters']['gen'] == node.get_gate('gen').parameters
    assert node.data['name'] == node.name
    assert node.data['type'] == node.type
