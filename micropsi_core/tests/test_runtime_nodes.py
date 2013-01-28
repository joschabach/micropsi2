#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""

"""
from micropsi_core import runtime as micropsi

__author__ = 'joscha'
__date__ = '29.10.12'


def test_add_node(test_nodenet):
    micropsi.load_nodenet(test_nodenet)
    # make sure nodenet is empty
    nodespace = micropsi.get_nodespace(test_nodenet, "Root", -1)
    try:
        for i in nodespace["nodes"]:
            micropsi.delete_node(test_nodenet, i)
    except:
        pass

    nodespace = micropsi.get_nodespace(test_nodenet, "Root", -1)
    assert len(nodespace.get("nodes", [])) == 0
    assert len(nodespace.get("links", [])) == 0
    micropsi.add_node(test_nodenet, "Concept", (200, 250), "Root", state=None, uid="node_a", name="A")
    nodespace = micropsi.get_nodespace(test_nodenet, "Root", -1)
    assert len(nodespace["nodes"]) == 1
    node1 = nodespace["nodes"]["node_a"]
    assert node1["name"] == "A"
    assert node1["position"] == (200, 250)

    micropsi.add_node(test_nodenet, "Concept", (500, 350), "Root", state=None, uid="node_b", name="B")
    micropsi.add_node(test_nodenet, "Concept", (300, 150), "Root", state=None, uid="node_c", name="C")
    micropsi.add_node(test_nodenet, "Sensor", (200, 450), "Root", state=None, uid="node_s", name="S")


def test_get_nodespace(test_nodenet):
    nodespace = micropsi.get_nodespace(test_nodenet, "Root", -1)
    assert len(nodespace["nodes"]) == 4
    node1 = nodespace["nodes"]["node_a"]
    assert node1["name"] == "A"
    assert node1["position"] == (200, 250)


def test_add_link(test_nodenet):
    micropsi.add_link(test_nodenet, "node_a", "por", "node_b", "gen", 0.5, 1, "por_ab")
    micropsi.add_link(test_nodenet, "node_a", "por", "node_b", "gen", 1, 0.1, "por_ab2")
    micropsi.add_link(test_nodenet, "node_c", "ret", "node_b", "gen", 1, 1, "ret_cb")

    nodespace = micropsi.get_nodespace(test_nodenet, "Root", -1)
    assert len(nodespace["nodes"]) == 4
    assert len(nodespace["links"]) == 2
    link1 = nodespace["links"]["por_ab"]
    assert link1["weight"] == 1
    assert link1["certainty"] == 0.1
    assert link1["source_node"] == "node_a"
    assert link1["target_node"] == "node_b"
    assert link1["source_gate_name"] == "por"
    assert link1["target_slot_name"] == "gen"

    link2 = nodespace["links"]["ret_cb"]
    assert link2["source_node"] == "node_c"
    assert link2["target_node"] == "node_b"
    assert link2["source_gate_name"] == "ret"
    assert link2["target_slot_name"] == "gen"


def test_delete_link(test_nodenet):
    micropsi.delete_link(test_nodenet, "ret_cb")
    nodespace = micropsi.get_nodespace(test_nodenet, "Root", -1)
    assert len(nodespace["links"]) == 1
    assert "ret_cb" not in nodespace["links"]


def test_save_nodenet(test_nodenet):
    # save_nodenet
    micropsi.save_nodenet(test_nodenet)
    # unload_nodenet
    micropsi.unload_nodenet(test_nodenet)
    try:
        micropsi.get_nodespace(test_nodenet, "Root", -1)
        assert False, "could fetch a Nodespace that should not have been in memory"
    except:
        pass
    # load_nodenet
    micropsi.load_nodenet(test_nodenet)
    nodespace = micropsi.get_nodespace(test_nodenet, "Root", -1)
    assert len(nodespace["nodes"]) == 4


def test_activation_setter_changes_nodenet_active_nodes(test_nodenet):
    micropsi.set_node_activation(test_nodenet, 'node_a', 0.7)
    assert 'node_a' in micropsi.get_nodenet(test_nodenet).active_nodes
    micropsi.set_node_activation(test_nodenet, 'node_a', 0)
    assert 'node_a' not in micropsi.get_nodenet(test_nodenet).active_nodes


"""


def test_get_node(micropsi, test_nodenet):
    assert 0

def test_set_node_position(micropsi, test_nodenet):
    assert 0

def test_set_node_name(micropsi, test_nodenet):
    assert 0

def test_set_node_state(micropsi, test_nodenet):
    assert 0

def test_set_node_activation(micropsi, test_nodenet):
    assert 0

def test_delete_node(micropsi, test_nodenet):
    assert 0

def test_get_available_node_types(micropsi, test_nodenet):
    assert 0

def test_get_available_native_module_types(micropsi, test_nodenet):
    assert 0

def test_get_nodefunction(micropsi, test_nodenet):
    assert 0

def test_set_nodefunction(micropsi, test_nodenet):
    assert 0

def test_set_node_parameters(micropsi, test_nodenet):
    assert 0

def test_add_node_type(micropsi, test_nodenet):
    assert 0

def test_delete_node_type(micropsi, test_nodenet):
    assert 0

def test_get_slot_types(micropsi, test_nodenet):
    assert 0

def test_get_gate_types(micropsi, test_nodenet):
    assert 0

def test_get_gate_function(micropsi, test_nodenet):
    assert 0

def test_set_gate_function(micropsi, test_nodenet):
    assert 0

def test_set_gate_parameters(micropsi, test_nodenet):
    assert 0

def test_get_available_datasources(micropsi, test_nodenet):
    assert 0

def test_get_available_datatargets(micropsi, test_nodenet):
    assert 0

def test_bind_datasource_to_sensor(micropsi, test_nodenet):
    assert 0

def test_bind_datatarget_to_actor(micropsi, test_nodenet):
    assert 0

def test_set_link_weight(micropsi, test_nodenet):
    assert 0

def test_get_link(micropsi, test_nodenet):
    assert 0

def test_delete_link(micropsi, test_nodenet):
    assert 0

"""