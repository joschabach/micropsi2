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


def test_get_nodespace_list_with_empty_nodespace(test_nodenet):
    micropsi.add_node(test_nodenet, "Nodespace", (200, 250), "Root", state=None, uid="foospace", name="Foospace")
    data = micropsi.get_nodespace_list(test_nodenet)
    assert data["foospace"]['nodes'] == {}


def test_add_link(test_nodenet):
    micropsi.add_link(test_nodenet, "node_a", "por", "node_b", "gen", 0.5, 1)
    micropsi.add_link(test_nodenet, "node_a", "por", "node_b", "gen", 1, 0.1)
    micropsi.add_link(test_nodenet, "node_c", "ret", "node_b", "gen", 1, 1)

    nodespace = micropsi.get_nodespace(test_nodenet, "Root", -1)
    assert len(nodespace["nodes"]) == 4
    assert len(nodespace["links"]) == 2
    link1 = nodespace["links"]["node_a:por:gen:node_b"]
    assert link1["weight"] == 1
    assert link1["certainty"] == 0.1
    assert link1["source_node_uid"] == "node_a"
    assert link1["target_node_uid"] == "node_b"
    assert link1["source_gate_name"] == "por"
    assert link1["target_slot_name"] == "gen"

    link2 = nodespace["links"]["node_c:ret:gen:node_b"]
    assert link2["source_node_uid"] == "node_c"
    assert link2["target_node_uid"] == "node_b"
    assert link2["source_gate_name"] == "ret"
    assert link2["target_slot_name"] == "gen"


def test_delete_link(test_nodenet):
    success, link = micropsi.add_link(test_nodenet, "node_a", "por", "node_b", "gen", 0.5, 1)

    micropsi.delete_link(test_nodenet, "node_a", "por", "node_b", "gen")
    nodespace = micropsi.get_nodespace(test_nodenet, "Root", -1)
    assert len(nodespace["links"]) == 1


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


def test_reload_native_modules(fixed_nodenet):
    data_before = micropsi.nodenets[fixed_nodenet].data
    micropsi.reload_native_modules(fixed_nodenet)
    data_after = micropsi.nodenets[fixed_nodenet].data
    assert data_before == data_after


def test_gate_defaults_change_with_nodetype(fixed_nodenet, resourcepath):
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
    micropsi.reload_native_modules(fixed_nodenet)
    micropsi.add_node(fixed_nodenet, "Testnode", [10, 10], uid="Testnode", name="Testnode")
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
    micropsi.reload_native_modules(fixed_nodenet)
    params = micropsi.nodenets[fixed_nodenet].get_node("Testnode").get_gate_parameters()
    assert params["foo"]["amplification"] == 5


def test_non_standard_gate_defaults(fixed_nodenet):
    nodenet = micropsi.nodenets[fixed_nodenet]
    micropsi.add_node(fixed_nodenet, 'Trigger', [30, 30], uid='testtrigger', name='test')
    node = nodenet.netapi.get_node('testtrigger')
    params = node.get_gate_parameters()
    genparams = params['gen']
    genparams['maximum'] = 1
    micropsi.set_gate_parameters(nodenet.uid, node.uid, 'gen', genparams)
    assert node.clone_non_default_gate_parameters()['gen']['maximum'] == 1


def test_remove_and_reload_native_module(fixed_nodenet, resourcepath):
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

    micropsi.reload_native_modules(fixed_nodenet)
    micropsi.add_node(fixed_nodenet, "Testnode", [10, 10], uid="Testnode", name="Testnode")
    remove(path.join(resourcepath, 'nodetypes.json'))
    remove(path.join(resourcepath, 'nodefunctions.py'))
    micropsi.reload_native_modules(fixed_nodenet)
    assert micropsi.get_available_native_module_types(fixed_nodenet) == {}


def test_node_parameters_none(fixed_nodenet):
    nodenet = micropsi.nodenets[fixed_nodenet]
    micropsi.add_node(fixed_nodenet, 'Trigger', [30, 30], uid='testtrigger', name='test')
    node = nodenet.netapi.get_node('testtrigger')
    micropsi.set_node_parameters(fixed_nodenet, node.uid, {'response': '', 'timeout': 0})
    assert node.get_parameter('response') is None
    assert node.get_parameter('timeout') == 0


def test_get_recipes(fixed_nodenet, resourcepath):
    from os import path, remove
    with open(path.join(resourcepath, 'recipes.py'), 'w') as fp:
        fp.write("""
def testfoo(netapi, count=23):
    return count
""")
    micropsi.reload_native_modules(fixed_nodenet)
    recipes = micropsi.get_available_recipes()
    assert 'testfoo' in recipes
    assert len(recipes['testfoo']['parameters']) == 1
    assert recipes['testfoo']['parameters'][0]['name'] == 'count'
    assert recipes['testfoo']['parameters'][0]['default'] == 23
    remove(path.join(resourcepath, 'recipes.py'))


def test_run_recipe(fixed_nodenet, resourcepath):
    from os import path, remove
    with open(path.join(resourcepath, 'recipes.py'), 'w') as fp:
        fp.write("""
def testfoo(netapi, count=23):
    return count
""")
    micropsi.reload_native_modules(fixed_nodenet)
    state, result = micropsi.run_recipe(fixed_nodenet, 'testfoo', {'count': 42})
    assert state
    assert result == 42
    remove(path.join(resourcepath, 'recipes.py'))
