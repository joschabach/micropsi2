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
    # test register node creation
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

    node = netapi.create_node("Register", "Root")
    #TODO: teh weirdness, server-internally, we return uids as names, clients don't see this, confusion ensues
    #assert node.data['name'] == node.name


def test_node_netapi_create_concept_node(fixed_nodenet):
    # test concept node generation
    net, netapi, source = prepare(fixed_nodenet)
    node = netapi.create_node("Concept", "Root", "TestName")

    # basic logic tests
    assert node is not None
    assert node.parent_nodespace == "Root"
    assert node.type == "Concept"
    assert node.uid is not None
    assert node.nodenet is net
    assert len(node.get_gate('gen').outgoing) == 0
    assert len(node.get_gate('gen').sheaves) == 1
    assert len(node.get_gate('sub').outgoing) == 0
    assert len(node.get_gate('sub').sheaves) == 1
    assert len(node.get_gate('sur').outgoing) == 0
    assert len(node.get_gate('sur').sheaves) == 1
    assert len(node.get_gate('por').outgoing) == 0
    assert len(node.get_gate('por').sheaves) == 1
    assert len(node.get_gate('ret').outgoing) == 0
    assert len(node.get_gate('ret').sheaves) == 1
    assert len(node.get_gate('cat').outgoing) == 0
    assert len(node.get_gate('cat').sheaves) == 1
    assert len(node.get_gate('exp').outgoing) == 0
    assert len(node.get_gate('exp').sheaves) == 1
    assert len(node.get_gate('sym').outgoing) == 0
    assert len(node.get_gate('sym').sheaves) == 1
    assert len(node.get_gate('ref').outgoing) == 0
    assert len(node.get_gate('ref').sheaves) == 1

    # frontend/persistency-oriented data dictionary test
    assert node.data['uid'] == node.uid
    assert node.data['gate_parameters']['gen'] == node.get_gate('gen').parameters
    assert node.data['gate_parameters']['sub'] == node.get_gate('sub').parameters
    assert node.data['gate_parameters']['sur'] == node.get_gate('sur').parameters
    assert node.data['gate_parameters']['por'] == node.get_gate('por').parameters
    assert node.data['gate_parameters']['ret'] == node.get_gate('ret').parameters
    assert node.data['gate_parameters']['cat'] == node.get_gate('cat').parameters
    assert node.data['gate_parameters']['exp'] == node.get_gate('exp').parameters
    assert node.data['gate_parameters']['sym'] == node.get_gate('sym').parameters
    assert node.data['gate_parameters']['ref'] == node.get_gate('ref').parameters
    assert node.data['name'] == node.name
    assert node.data['type'] == node.type

    node = netapi.create_node("Concept", "Root")
    #TODO: teh weirdness, server-internally, we return uids as names, clients don't see this, confusion ensues
    #assert node.data['name'] == node.name


def test_node_netapi_create_node_in_nodespace(fixed_nodenet):
    # test register node in nodespace creation
    net, netapi, source = prepare(fixed_nodenet)
    nodespace = netapi.create_node("Nodespace", "Root", "NestedNodespace")
    node = netapi.create_node("Register", nodespace.uid, "TestName")

    assert node.parent_nodespace == nodespace.uid
    assert node.data['parent_nodespace'] == nodespace.uid


def test_node_netapi_get_node(fixed_nodenet):
    # test register node creation
    net, netapi, source = prepare(fixed_nodenet)
    node = netapi.create_node("Register", "Root", "TestName")

    queried_node = netapi.get_node(node.uid)
    assert queried_node.uid == node.uid
    assert queried_node.name == node.name
    assert queried_node.data == node.data
    assert queried_node.type == node.type


def test_node_netapi_get_nodes(fixed_nodenet):
    # test get_nodes plain
    net, netapi, source = prepare(fixed_nodenet)
    node1 = netapi.create_node("Register", "Root", "TestName1")
    node2 = netapi.create_node("Register", "Root", "TestName2")

    nodes = netapi.get_nodes("Root")
    assert node1 in nodes
    assert node2 in nodes


def test_node_netapi_get_nodes_by_name(fixed_nodenet):
    # test get_nodes by name
    net, netapi, source = prepare(fixed_nodenet)
    node1 = netapi.create_node("Register", "Root", "TestName1")
    node2 = netapi.create_node("Register", "Root", "TestName2")

    nodes = netapi.get_nodes("Root", "TestName")
    assert len(nodes) == 2
    assert node1 in nodes
    assert node2 in nodes


def test_node_netapi_get_nodes_by_nodespace(fixed_nodenet):
    # test get_nodes by name and nodespace
    net, netapi, source = prepare(fixed_nodenet)
    nodespace = netapi.create_node("Nodespace", "Root", "NestedNodespace")
    node1 = netapi.create_node("Register", nodespace.uid, "TestName1")
    node2 = netapi.create_node("Register", nodespace.uid, "TestName2")

    nodes = netapi.get_nodes(nodespace.uid)
    assert len(nodes) == 2
    assert node1 in nodes
    assert node2 in nodes


def test_node_netapi_get_nodes_by_name_and_nodespace(fixed_nodenet):
    # test get_nodes by name and nodespace
    net, netapi, source = prepare(fixed_nodenet)
    nodespace = netapi.create_node("Nodespace", "Root", "NestedNodespace")
    node1 = netapi.create_node("Register", "Root", "TestName1")
    node2 = netapi.create_node("Register", nodespace.uid, "TestName2")

    nodes = netapi.get_nodes(nodespace.uid, "TestName")
    assert len(nodes) == 1
    assert node2 in nodes
