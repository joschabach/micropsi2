#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""

"""
from micropsi_core import runtime as micropsi
import pytest

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


def test_get_nodespace_list(test_nodenet):
    data = micropsi.get_nodespace_list(test_nodenet)
    assert data['Root']['name'] == 'Root'
    assert 'node_a' in data['Root']['nodes']
    node = data['Root']['nodes']['node_a']
    assert node['name'] == 'A'
    assert node['type'] == 'Concept'
    assert node['slots'] == ['gen']
    assert len(node['gates']) == 9


def test_get_nodespace_list_with_empty_nodespace(test_nodenet):
    micropsi.add_node(test_nodenet, "Nodespace", (200, 250), "Root", state=None, uid="foospace", name="Foospace")
    data = micropsi.get_nodespace_list(test_nodenet)
    assert data["foospace"]['nodes'] == {}


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
    assert link1["source_node_uid"] == "node_a"
    assert link1["target_node_uid"] == "node_b"
    assert link1["source_gate_name"] == "por"
    assert link1["target_slot_name"] == "gen"

    link2 = nodespace["links"]["ret_cb"]
    assert link2["source_node_uid"] == "node_c"
    assert link2["target_node_uid"] == "node_b"
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


def test_remove_nodes_linking_to_themselves(fixed_nodenet):
    micropsi.add_link(fixed_nodenet, 'A1', 'gen', 'A1', 'gen')
    assert micropsi.delete_node(fixed_nodenet, 'A1')


@pytest.mark.xfail(reason="data-dicts prevent us from handling this correctly")
def xxx_test_gate_defaults_change_with_nodetype(test_nodenet, resourcepath):
    # gate_parameters are a property of the nodetype, and should change with
    # the nodetype definition if not explicitly overwritten for a given node
    from os import path
    with open(path.join(resourcepath, 'nodetypes.json'), 'w') as fp:
        fp.write('{"Testnode": {\
            "name": "Testnode",\
            "slottypes": ["gen", "foo", "bar"],\
            "nodefunction_name": "testnodefunc",\
            "gatetypes": ["gen", "foo", "bar"],\
            "symbol": "t",\
            "gate_defaults":{\
              "foo": {\
                "amplification": 13\
              }\
            }}}')
    with open(path.join(resourcepath, 'nodefunctions.py'), 'w') as fp:
        fp.write("def testnodefunc(netapi, node=None, **prams):\r\n    return 17")

    micropsi.reload_native_modules(test_nodenet)
    micropsi.add_node(test_nodenet, "Testnode", [10, 10], uid="Testnode", name="Testnode")
    with open(path.join(resourcepath, 'nodetypes.json'), 'w') as fp:
        fp.write('{"Testnode": {\
            "name": "Testnode",\
            "slottypes": ["gen", "foo", "bar"],\
            "nodefunction_name": "testnodefunc",\
            "gatetypes": ["gen", "foo", "bar"],\
            "symbol": "t",\
            "gate_defaults":{\
              "foo": {\
                "amplification": 5\
              }\
            }}}')
    micropsi.reload_native_modules(test_nodenet)
    params = micropsi.nodenets[test_nodenet].nodes["Testnode"].get_gate_parameters()
    assert params["foo"]["amplification"] == 5


@pytest.mark.xfail(reason="removing a loaded native module is currently undefined.")
def xxx_test_remove_and_reload_native_module(test_nodenet, resourcepath):
    from os import path, remove
    with open(path.join(resourcepath, 'nodetypes.json'), 'w') as fp:
        fp.write('{"Testnode": {\
            "name": "Testnode",\
            "slottypes": ["gen", "foo", "bar"],\
            "nodefunction_name": "testnodefunc",\
            "gatetypes": ["gen", "foo", "bar"],\
            "symbol": "t",\
            "gate_defaults":{\
              "foo": {\
                "amplification": 13\
              }\
            }}}')
    with open(path.join(resourcepath, 'nodefunctions.py'), 'w') as fp:
        fp.write("def testnodefunc(netapi, node=None, **prams):\r\n    return 17")

    micropsi.reload_native_modules(test_nodenet)
    remove(path.join(resourcepath, 'nodetypes.json'))
    remove(path.join(resourcepath, 'nodefunctions.py'))
    micropsi.reload_native_modules(test_nodenet)
    assert micropsi.get_available_native_module_types(test_nodenet) == {}


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