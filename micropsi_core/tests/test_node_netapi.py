#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""
Tests for netapi, i.e. the interface native modules will be developed against
"""

import pytest
from micropsi_core import runtime as micropsi
from micropsi_core.world.world import World
from micropsi_core.world.worldadapter import WorldAdapter, WorldObject

from micropsi_core.tests.test_node_logic import DummyWorld, DummyWorldAdapter
from micropsi_core.tests import test_node_logic


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
    assert len(node.get_gate('gen').get_links()) == 0
    assert len(node.get_gate('gen').sheaves) == 1

    # frontend/persistency-oriented data dictionary test
    assert node.data['uid'] == node.uid
    assert node.data['gate_parameters'] == {}
    assert node.get_gate('gen').parameters != {}
    assert node.data['name'] == node.name
    assert node.data['type'] == node.type

    node = netapi.create_node("Register", "Root")
    #TODO: teh weirdness, server-internally, we return uids as names, clients don't see this, confusion ensues
    #assert node.data['name'] == node.name


def test_node_netapi_create_concept_node(fixed_nodenet):
    # test concept node generation
    from micropsi_core.nodenet.node import Nodetype
    net, netapi, source = prepare(fixed_nodenet)
    node = netapi.create_node("Concept", "Root", "TestName")

    # basic logic tests
    assert node is not None
    assert node.parent_nodespace == "Root"
    assert node.type == "Concept"
    assert node.uid is not None
    assert node.nodenet is net
    assert len(node.get_gate('gen').get_links()) == 0
    assert len(node.get_gate('gen').sheaves) == 1
    assert len(node.get_gate('sub').get_links()) == 0
    assert len(node.get_gate('sub').sheaves) == 1
    assert len(node.get_gate('sur').get_links()) == 0
    assert len(node.get_gate('sur').sheaves) == 1
    assert len(node.get_gate('por').get_links()) == 0
    assert len(node.get_gate('por').sheaves) == 1
    assert len(node.get_gate('ret').get_links()) == 0
    assert len(node.get_gate('ret').sheaves) == 1
    assert len(node.get_gate('cat').get_links()) == 0
    assert len(node.get_gate('cat').sheaves) == 1
    assert len(node.get_gate('exp').get_links()) == 0
    assert len(node.get_gate('exp').sheaves) == 1
    assert len(node.get_gate('sym').get_links()) == 0
    assert len(node.get_gate('sym').sheaves) == 1
    assert len(node.get_gate('ref').get_links()) == 0
    assert len(node.get_gate('ref').sheaves) == 1

    # frontend/persistency-oriented data dictionary test
    assert node.data['uid'] == node.uid
    assert node.data['gate_parameters'] == {}
    assert node.get_gate('gen').parameters == Nodetype.GATE_DEFAULTS
    assert node.get_gate('sub').parameters == Nodetype.GATE_DEFAULTS
    assert node.get_gate('sur').parameters == Nodetype.GATE_DEFAULTS
    assert node.get_gate('por').parameters == Nodetype.GATE_DEFAULTS
    assert node.get_gate('ret').parameters == Nodetype.GATE_DEFAULTS
    assert node.get_gate('cat').parameters == Nodetype.GATE_DEFAULTS
    assert node.get_gate('exp').parameters == Nodetype.GATE_DEFAULTS
    assert node.get_gate('sym').parameters == Nodetype.GATE_DEFAULTS
    assert node.get_gate('ref').parameters == Nodetype.GATE_DEFAULTS
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


def test_node_netapi_get_nodespace(fixed_nodenet):
    # test single nodespace querying
    net, netapi, source = prepare(fixed_nodenet)
    nodespace = netapi.create_node("Nodespace", "Root", "TestName")

    queried_nodespace = netapi.get_nodespace(nodespace.uid)
    assert queried_nodespace.uid == nodespace.uid
    assert queried_nodespace.name == nodespace.name


def test_node_netapi_get_nodespace(fixed_nodenet):
    # test nodespace listing
    net, netapi, source = prepare(fixed_nodenet)
    nodespace1 = netapi.create_node("Nodespace", "Root", "TestName1")
    nodespace2 = netapi.create_node("Nodespace", "Root", "TestName2")
    nodespace3 = netapi.create_node("Nodespace", nodespace2.uid, "TestName3")

    queried_nodespaces = netapi.get_nodespaces("Root")
    assert len(queried_nodespaces) == 2
    assert nodespace1.uid in [x.uid for x in queried_nodespaces]
    assert nodespace2.uid in [x.uid for x in queried_nodespaces]
    assert nodespace3.uid not in [x.uid for x in queried_nodespaces]


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


def test_node_netapi_get_nodes_in_gate_field(fixed_nodenet):
    # test get_nodes_in_gate_field
    net, netapi, source = prepare(fixed_nodenet)
    node1 = netapi.create_node("Concept", "Root", "TestName1")
    node2 = netapi.create_node("Concept", "Root", "TestName2")
    node3 = netapi.create_node("Concept", "Root", "TestName3")
    node4 = netapi.create_node("Concept", "Root", "TestName4")
    netapi.link_with_reciprocal(node1, node2, "subsur")
    netapi.link_with_reciprocal(node1, node3, "subsur")
    netapi.link_with_reciprocal(node1, node4, "subsur")
    netapi.link_with_reciprocal(node2, node3, "porret")

    nodes = netapi.get_nodes_in_gate_field(node1, "sub")
    assert len(nodes) == 3
    assert node2 in nodes
    assert node3 in nodes
    assert node4 in nodes


def test_node_netapi_get_nodes_in_gate_field_all_links(fixed_nodenet):
    # test get_nodes_in_gate_field without specifying a gate parameter
    net, netapi, source = prepare(fixed_nodenet)
    node1 = netapi.create_node("Concept", "Root", "TestName1")
    node2 = netapi.create_node("Concept", "Root", "TestName2")
    node3 = netapi.create_node("Concept", "Root", "TestName3")
    node4 = netapi.create_node("Concept", "Root", "TestName4")
    netapi.link_with_reciprocal(node1, node2, "subsur")
    netapi.link_with_reciprocal(node1, node3, "subsur")
    netapi.link_with_reciprocal(node1, node4, "subsur")
    netapi.link_with_reciprocal(node2, node3, "porret")

    nodes = netapi.get_nodes_in_gate_field(node2)
    assert len(nodes) == 2
    assert node1 in nodes
    assert node3 in nodes


def test_node_netapi_get_nodes_in_gate_field_with_limitations(fixed_nodenet):
    # test get_nodes_in_gate_field with limitations: no por links
    net, netapi, source = prepare(fixed_nodenet)
    node1 = netapi.create_node("Concept", "Root", "TestName1")
    node2 = netapi.create_node("Concept", "Root", "TestName2")
    node3 = netapi.create_node("Concept", "Root", "TestName3")
    node4 = netapi.create_node("Concept", "Root", "TestName4")
    netapi.link_with_reciprocal(node1, node2, "subsur")
    netapi.link_with_reciprocal(node1, node3, "subsur")
    netapi.link_with_reciprocal(node1, node4, "subsur")
    netapi.link_with_reciprocal(node2, node3, "porret")

    nodes = netapi.get_nodes_in_gate_field(node1, "sub", ["por"])
    assert len(nodes) == 2
    assert node3 in nodes
    assert node4 in nodes


def test_node_netapi_get_nodes_in_gate_field_with_limitations_and_nodespace(fixed_nodenet):
    # test get_nodes_in_gate_field with limitations: no por links
    net, netapi, source = prepare(fixed_nodenet)
    nodespace = netapi.create_node("Nodespace", "Root", "NestedNodespace")
    node1 = netapi.create_node("Concept", "Root", "TestName1")
    node2 = netapi.create_node("Concept", "Root", "TestName2")
    node3 = netapi.create_node("Concept", "Root", "TestName3")
    node4 = netapi.create_node("Concept", nodespace.uid, "TestName4")
    netapi.link_with_reciprocal(node1, node2, "subsur")
    netapi.link_with_reciprocal(node1, node3, "subsur")
    netapi.link_with_reciprocal(node1, node4, "subsur")
    netapi.link_with_reciprocal(node2, node3, "porret")

    nodes = netapi.get_nodes_in_gate_field(node1, "sub", ["por"], "Root")
    assert len(nodes) == 1
    assert node3 in nodes


def test_node_netapi_get_nodes_in_slot_field(fixed_nodenet):
    # test get_nodes_in_slot_field
    net, netapi, source = prepare(fixed_nodenet)
    node1 = netapi.create_node("Register", "Root", "TestName1")
    node2 = netapi.create_node("Register", "Root", "TestName2")
    node3 = netapi.create_node("Register", "Root", "TestName3")
    node4 = netapi.create_node("Register", "Root", "TestName4")
    netapi.link(node2, "gen", node1, "gen")
    netapi.link(node3, "gen", node1, "gen")
    netapi.link(node3, "gen", node1, "gen")
    netapi.link(node4, "gen", node1, "gen")

    nodes = netapi.get_nodes_in_slot_field(node1, "gen")
    assert len(nodes) == 3
    assert node2 in nodes
    assert node3 in nodes
    assert node4 in nodes


def test_node_netapi_get_nodes_in_slot_field_all_links(fixed_nodenet):
    # test get_nodes_in_slot_field without a gate parameter
    net, netapi, source = prepare(fixed_nodenet)
    net, netapi, source = prepare(fixed_nodenet)
    node1 = netapi.create_node("Concept", "Root", "TestName1")
    node2 = netapi.create_node("Concept", "Root", "TestName2")
    node3 = netapi.create_node("Concept", "Root", "TestName3")
    node4 = netapi.create_node("Concept", "Root", "TestName4")
    netapi.link_with_reciprocal(node1, node2, "subsur")
    netapi.link_with_reciprocal(node1, node3, "subsur")
    netapi.link_with_reciprocal(node1, node4, "subsur")
    netapi.link_with_reciprocal(node2, node3, "porret")

    nodes = netapi.get_nodes_in_slot_field(node1)
    assert len(nodes) == 3
    assert node2 in nodes
    assert node3 in nodes
    assert node4 in nodes


def test_node_netapi_get_nodes_with_nodespace_limitation(fixed_nodenet):
    # test get_nodes_feed with nodespace limitation
    net, netapi, source = prepare(fixed_nodenet)
    nodespace = netapi.create_node("Nodespace", "Root", "NestedNodespace")
    node1 = netapi.create_node("Register", "Root", "TestName1")
    node2 = netapi.create_node("Register", "Root", "TestName2")
    node3 = netapi.create_node("Register", "Root", "TestName3")
    node4 = netapi.create_node("Register", nodespace.uid, "TestName4")
    netapi.link(node2, "gen", node1, "gen")
    netapi.link(node3, "gen", node1, "gen")
    netapi.link(node3, "gen", node1, "gen")
    netapi.link(node4, "gen", node1, "gen")

    nodes = netapi.get_nodes_in_slot_field(node1, "gen", None, "Root")
    assert len(nodes) == 2
    assert node2 in nodes
    assert node3 in nodes


def test_node_netapi_get_nodes_active(fixed_nodenet):
    # test get_nodes_active
    net, netapi, source = prepare(fixed_nodenet)
    nodespace = netapi.create_node("Nodespace", "Root", "NestedNodespace")
    node1 = netapi.create_node("Register", "Root", "TestName1")
    node2 = netapi.create_node("Register", "Root", "TestName2")
    node3 = netapi.create_node("Register", "Root", "TestName3")
    node4 = netapi.create_node("Register", nodespace.uid, "TestName4")
    netapi.link(node2, "gen", node1, "gen")
    netapi.link(node3, "gen", node1, "gen")
    netapi.link(node3, "gen", node1, "gen")
    netapi.link(node4, "gen", node1, "gen")
    netapi.link(source, "gen", node2, "gen", 0.5)
    netapi.link(source, "gen", node4, "gen", 0.5)

    net.step()
    net.step()

    nodes = netapi.get_nodes_active("Root", "Register", 0.7, "gen")
    assert len(nodes) == 2
    assert node1 in nodes
    assert source in nodes

    nodes = netapi.get_nodes_active("Root", "Register")
    assert len(nodes) == 2
    assert node1 in nodes
    assert source in nodes


def test_node_netapi_get_nodes_active_with_nodespace_limitation(fixed_nodenet):
    # test get_nodes_active with nodespace filtering
    net, netapi, source = prepare(fixed_nodenet)
    nodespace = netapi.create_node("Nodespace", "Root", "NestedNodespace")
    node1 = netapi.create_node("Register", "Root", "TestName1")
    node2 = netapi.create_node("Register", "Root", "TestName2")
    node3 = netapi.create_node("Register", "Root", "TestName3")
    node4 = netapi.create_node("Register", nodespace.uid, "TestName4")
    netapi.link(node2, "gen", node1, "gen")
    netapi.link(node3, "gen", node1, "gen")
    netapi.link(node3, "gen", node1, "gen")
    netapi.link(node4, "gen", node1, "gen")
    netapi.link(source, "gen", node2, "gen", 0.5)
    netapi.link(source, "gen", node4, "gen", 0.5)

    net.step()
    net.step()

    nodes = netapi.get_nodes_active(nodespace.uid, "Register", 0.4)
    assert len(nodes) == 1
    assert node4 in nodes


def test_node_netapi_delete_node(fixed_nodenet):
    # test simple delete node case
    net, netapi, source = prepare(fixed_nodenet)
    node1 = netapi.create_node("Register", "Root", "TestName1")
    node2 = netapi.create_node("Register", "Root", "TestName2")
    node3 = netapi.create_node("Register", "Root", "TestName3")
    netapi.link(node2, "gen", node1, "gen")
    netapi.link(node3, "gen", node1, "gen")
    netapi.link(node3, "gen", node1, "gen")

    olduid = node1.uid
    netapi.delete_node(node1)
    with pytest.raises(KeyError):
        netapi.get_node(olduid)
    assert len(node2.get_gate("gen").get_links()) == 0


def test_node_netapi_delete_node_for_nodespace(fixed_nodenet):
    # test delete node case deleting a nodespace
    net, netapi, source = prepare(fixed_nodenet)
    nodespace = netapi.create_node("Nodespace", "Root", "NestedNodespace")
    node1 = netapi.create_node("Register", "Root", "TestName1")
    node2 = netapi.create_node("Register", "Root", "TestName2")
    node3 = netapi.create_node("Register", "Root", "TestName3")
    node4 = netapi.create_node("Register", nodespace.uid, "TestName4")
    netapi.link(node2, "gen", node1, "gen")
    netapi.link(node3, "gen", node1, "gen")
    netapi.link(node3, "gen", node1, "gen")
    netapi.link(node4, "gen", node1, "gen")

    node4uid = node4.uid
    netapi.delete_node(nodespace)
    with pytest.raises(KeyError):
        netapi.get_node(node4uid)


def test_node_netapi_link(fixed_nodenet):
    # test linking nodes
    net, netapi, source = prepare(fixed_nodenet)
    node1 = netapi.create_node("Register", "Root", "TestName1")
    node2 = netapi.create_node("Register", "Root", "TestName2")
    netapi.link(node2, "gen", node1, "gen")

    assert len(node2.get_gate("gen").get_links()) == 1
    for link in node2.get_gate("gen").get_links():
        # basic internal logic
        assert link.source_node is node2
        assert link.target_node is node1
        assert link.weight == 1

        found = False
        for otherside_link in node1.get_slot("gen").get_links():
            if otherside_link.uid == link.uid:
                found = True
        assert found

        # frontend/persistency-facing
        assert link.data['weight'] == link.weight
        assert link.data['uid'] == link.uid
        assert link.data['source_node_uid'] == node2.uid
        assert link.data['target_node_uid'] == node1.uid


def test_node_netapi_link_change_weight(fixed_nodenet):
    # test linking nodes, the changing weights
    net, netapi, source = prepare(fixed_nodenet)
    node1 = netapi.create_node("Register", "Root", "TestName1")
    node2 = netapi.create_node("Register", "Root", "TestName2")
    netapi.link(node2, "gen", node1, "gen")

    net.step()

    netapi.link(node2, "gen", node1, "gen", 0.8)

    assert len(node2.get_gate("gen").get_links()) == 1
    for link in node2.get_gate("gen").get_links():
        # basic internal logic
        assert link.source_node is node2
        assert link.target_node is node1
        assert link.weight == 0.8

        found = False
        for otherside_link in node1.get_slot("gen").get_links():
            if otherside_link.uid == link.uid:
                found = True
        assert found

        # frontend/persistency-facing
        assert link.data['weight'] == link.weight
        assert link.data['uid'] == link.uid
        assert link.data['source_node_uid'] == node2.uid
        assert link.data['target_node_uid'] == node1.uid


def test_node_netapi_link_with_reciprocal(fixed_nodenet):
    # test linking pipe and concept nodes with reciprocal links
    net, netapi, source = prepare(fixed_nodenet)
    n_head = netapi.create_node("Pipe", "Root", "Head")
    n_a = netapi.create_node("Pipe", "Root", "A")
    n_b = netapi.create_node("Pipe", "Root", "B")
    n_c = netapi.create_node("Pipe", "Root", "C")
    n_d = netapi.create_node("Concept", "Root", "D")
    n_e = netapi.create_node("Concept", "Root", "E")
    netapi.link_with_reciprocal(n_head, n_a, "subsur")
    netapi.link_with_reciprocal(n_head, n_b, "subsur")
    netapi.link_with_reciprocal(n_head, n_c, "subsur")
    netapi.link_with_reciprocal(n_a, n_b, "porret", 0.5)
    netapi.link_with_reciprocal(n_b, n_c, "porret", 0.5)
    netapi.link_with_reciprocal(n_head, n_d, "catexp")
    netapi.link_with_reciprocal(n_d, n_e, "symref")

    assert len(n_head.get_gate("sub").get_links()) == 3
    assert len(n_head.get_slot("sur").get_links()) == 3
    assert len(n_a.get_gate("sur").get_links()) == 1
    assert len(n_a.get_slot("sub").get_links()) == 1
    assert len(n_b.get_gate("sur").get_links()) == 1
    assert len(n_b.get_slot("sub").get_links()) == 1
    assert len(n_c.get_gate("sur").get_links()) == 1
    assert len(n_c.get_slot("sub").get_links()) == 1
    assert len(n_a.get_gate("por").get_links()) == 1
    assert len(n_a.get_slot("ret").get_links()) == 1
    assert len(n_a.get_slot("por").get_links()) == 0
    assert len(n_b.get_gate("por").get_links()) == 1
    assert len(n_b.get_slot("ret").get_links()) == 1
    assert len(n_b.get_gate("ret").get_links()) == 1
    assert len(n_b.get_slot("por").get_links()) == 1
    assert len(n_c.get_gate("por").get_links()) == 0
    assert len(n_c.get_slot("ret").get_links()) == 0
    for link in n_b.get_gate("por").get_links():
        assert link.weight == 0.5

    assert len(n_head.get_gate("cat").get_links()) == 1
    assert len(n_head.get_slot("exp").get_links()) == 1

    assert len(n_d.get_gate("sym").get_links()) == 1
    assert len(n_d.get_slot("gen").get_links()) == 2


def test_node_netapi_link_full(fixed_nodenet):
    # test fully reciprocal-linking groups of nodes
    net, netapi, source = prepare(fixed_nodenet)
    n_head = netapi.create_node("Pipe", "Root", "Head")
    n_a = netapi.create_node("Pipe", "Root", "A")
    n_b = netapi.create_node("Pipe", "Root", "B")
    n_c = netapi.create_node("Pipe", "Root", "C")
    n_d = netapi.create_node("Pipe", "Root", "D")

    netapi.link_full([n_a, n_b, n_c, n_d])

    assert len(n_a.get_slot('por').get_links()) == 4
    assert len(n_b.get_slot('por').get_links()) == 4
    assert len(n_c.get_slot('por').get_links()) == 4
    assert len(n_d.get_slot('por').get_links()) == 4


def test_node_netapi_unlink(fixed_nodenet):
    # test completely unlinking a node
    net, netapi, source = prepare(fixed_nodenet)
    n_head = netapi.create_node("Pipe", "Root", "Head")
    n_a = netapi.create_node("Pipe", "Root", "A")
    n_b = netapi.create_node("Pipe", "Root", "B")
    n_c = netapi.create_node("Pipe", "Root", "C")
    n_d = netapi.create_node("Pipe", "Root", "D")

    netapi.link_full([n_a, n_b, n_c, n_d])

    netapi.unlink(n_b)

    assert len(n_a.get_slot('por').get_links()) == 3
    assert len(n_b.get_slot('por').get_links()) == 3
    assert len(n_c.get_slot('por').get_links()) == 3
    assert len(n_d.get_slot('por').get_links()) == 3


def test_node_netapi_unlink_specific_link(fixed_nodenet):
    # test removing a specific link
    net, netapi, source = prepare(fixed_nodenet)
    n_head = netapi.create_node("Pipe", "Root", "Head")
    n_a = netapi.create_node("Pipe", "Root", "A")
    n_b = netapi.create_node("Pipe", "Root", "B")
    n_c = netapi.create_node("Pipe", "Root", "C")
    n_d = netapi.create_node("Pipe", "Root", "D")

    netapi.link_full([n_a, n_b, n_c, n_d])

    netapi.unlink(n_b, "por", n_c, "por")

    assert len(n_a.get_slot('por').get_links()) == 4
    assert len(n_b.get_slot('por').get_links()) == 4
    assert len(n_c.get_slot('por').get_links()) == 3
    assert len(n_d.get_slot('por').get_links()) == 4


def test_node_netapi_unlink_gate(fixed_nodenet):
    # test unlinking a gate
    net, netapi, source = prepare(fixed_nodenet)
    n_head = netapi.create_node("Pipe", "Root", "Head")
    n_a = netapi.create_node("Pipe", "Root", "A")
    n_b = netapi.create_node("Pipe", "Root", "B")
    n_c = netapi.create_node("Pipe", "Root", "C")
    n_d = netapi.create_node("Pipe", "Root", "D")

    netapi.link_full([n_a, n_b, n_c, n_d])

    netapi.unlink(n_b, "por")

    assert len(n_a.get_slot('por').get_links()) == 3
    assert len(n_b.get_slot('por').get_links()) == 3
    assert len(n_c.get_slot('por').get_links()) == 3
    assert len(n_d.get_slot('por').get_links()) == 3


def test_node_netapi_unlink_direction(fixed_nodenet):
    # test unlinking a gate
    net, netapi, source = prepare(fixed_nodenet)
    n_head = netapi.create_node("Pipe", "Root", "Head")
    n_a = netapi.create_node("Pipe", "Root", "A")
    n_b = netapi.create_node("Pipe", "Root", "B")
    n_c = netapi.create_node("Pipe", "Root", "C")

    netapi.link_with_reciprocal(n_head, n_a, "subsur")
    netapi.link_with_reciprocal(n_head, n_b, "subsur")
    netapi.link_with_reciprocal(n_head, n_c, "subsur")
    netapi.link_full([n_a, n_b, n_c])

    netapi.unlink_direction(n_b, "por")

    assert len(n_head.get_gate('sub').get_links()) == 3
    assert len(n_head.get_slot('sur').get_links()) == 3

    assert len(n_a.get_slot('por').get_links()) == 2
    assert len(n_b.get_slot('por').get_links()) == 0
    assert len(n_c.get_slot('por').get_links()) == 2

    netapi.unlink_direction(n_head, "sub")

    assert len(n_head.get_gate('sub').get_links()) == 0
    assert len(n_head.get_slot('sur').get_links()) == 3

    assert len(n_a.get_slot('sub').get_links()) == 0
    assert len(n_b.get_slot('sub').get_links()) == 0
    assert len(n_c.get_slot('sub').get_links()) == 0


def test_node_netapi_import_actors(fixed_nodenet):
    # test importing data targets as actors
    net, netapi, source = prepare(fixed_nodenet)
    world = test_node_logic.add_dummyworld(fixed_nodenet)

    netapi.import_actors("Root", "test_")
    actors = netapi.get_nodes("Root", "test_")
    assert len(actors) == 1
    assert actors[0].get_parameter('datatarget') == "test_target"

    # do it again, make sure we can call import multiple times
    netapi.import_actors("Root", "test_")
    actors = netapi.get_nodes("Root", "test_")
    assert len(actors) == 1


def test_node_netapi_import_sensors(fixed_nodenet):
    # test importing data sources as sensors
    net, netapi, source = prepare(fixed_nodenet)
    world = test_node_logic.add_dummyworld(fixed_nodenet)

    netapi.import_sensors("Root", "test_")
    sensors = netapi.get_nodes("Root", "test_")
    assert len(sensors) == 1
    assert sensors[0].get_parameter('datasource') == "test_source"

    # do it again, make sure we can call import multiple times
    netapi.import_sensors("Root", "test_")
    sensors = netapi.get_nodes("Root", "test_")
    assert len(sensors) == 1


def test_set_gate_function(fixed_nodenet):
    # test setting a custom gate function
    net, netapi, source = prepare(fixed_nodenet)

    some_other_node_type = netapi.create_node("Concept", "Root")
    netapi.unlink(source, "gen")

    net.step()
    assert source.get_gate("gen").activation == 0

    netapi.set_gatefunction("Root", "Register", "gen", "return 1/(1+math.exp(-t*x))")

    source.get_gate('gen').parameters["theta"] = 1

    net.step()

    assert source.get_gate("gen").activation == 0.5
    assert some_other_node_type.get_gate("gen").activation == 0


def test_autoalign(fixed_nodenet):
    net, netapi, source = prepare(fixed_nodenet)
    for uid in net.get_node_uids():
        net.get_node(uid).position = (12, 13)
    netapi.autoalign_nodespace('Root')
    positions = []
    for uid in net.get_node_uids():
        if net.get_node(uid).parent_nodespace == 'Root':
            positions.extend(net.get_node(uid).position)
    assert set(positions) != set((12, 13))

    for uid in net.get_node_uids():
        net.get_node(uid).position = (12, 13)
    netapi.autoalign_nodespace('InVaLiD')
    positions = []
    for uid in net.get_node_uids():
        positions.extend(net.get_node(uid).position)
    assert set(positions) == set((12, 13))



#TODO: Add locking tests once we're sure we'll keep locking, and like it is implemented now