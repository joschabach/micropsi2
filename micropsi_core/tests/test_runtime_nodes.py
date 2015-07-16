#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""

"""
from micropsi_core import runtime as micropsi
import pytest

__author__ = 'joscha'
__date__ = '29.10.12'


def prepare_nodenet(test_nodenet):
    res, node_a_uid = micropsi.add_node(test_nodenet, "Pipe", (200, 250), None, state=None, name="A")
    res, node_b_uid = micropsi.add_node(test_nodenet, "Pipe", (500, 350), None, state=None, name="B")
    res, node_c_uid = micropsi.add_node(test_nodenet, "Pipe", (300, 150), None, state=None, name="C")
    res, node_s_uid = micropsi.add_node(test_nodenet, "Sensor", (200, 450), None, state=None, name="S")
    return {
        'a': node_a_uid,
        'b': node_b_uid,
        'c': node_c_uid,
        's': node_s_uid
    }


def test_add_node(test_nodenet):
    micropsi.load_nodenet(test_nodenet)
    # make sure nodenet is empty
    nodespace = micropsi.get_nodenet_data(test_nodenet, None)
    try:
        for i in nodespace["nodes"]:
            micropsi.delete_node(test_nodenet, i)
    except:
        pass

    nodespace = micropsi.get_nodenet_data(test_nodenet, None)
    assert len(nodespace.get("nodes", [])) == 0
    assert len(nodespace.get("links", [])) == 0
    res, uid = micropsi.add_node(test_nodenet, "Pipe", (200, 250), None, state=None, name="A")
    nodespace = micropsi.get_nodenet_data(test_nodenet, None)
    assert len(nodespace["nodes"]) == 1
    node1 = nodespace["nodes"][uid]
    assert node1["name"] == "A"
    assert node1["position"] == (200, 250)


def test_get_nodespace(test_nodenet):
    nodes = prepare_nodenet(test_nodenet)
    nodespace = micropsi.get_nodenet_data(test_nodenet, None)
    assert len(nodespace["nodes"]) == 4
    node1 = nodespace["nodes"][nodes['a']]
    assert node1["name"] == "A"
    assert node1["position"] == (200, 250)


def test_get_nodespace_list(test_nodenet):
    nodes = prepare_nodenet(test_nodenet)
    data = micropsi.get_nodespace_list(test_nodenet)
    uid = list(data.keys())[0]
    assert data[uid]['name'] == 'Root'
    assert nodes['a'] in data[uid]['nodes']
    node = data[uid]['nodes'][nodes['a']]
    assert node['name'] == 'A'
    assert node['type'] == 'Pipe'


def test_get_nodespace_list_with_empty_nodespace(test_nodenet):
    res, uid = micropsi.add_nodespace(test_nodenet, (200, 250), None, name="Foospace")
    data = micropsi.get_nodespace_list(test_nodenet)
    assert data[uid]['nodes'] == {}


def test_add_link(test_nodenet):
    nodes = prepare_nodenet(test_nodenet)
    micropsi.add_link(test_nodenet, nodes['a'], "por", nodes['b'], "gen", 0.5, 1)
    micropsi.add_link(test_nodenet, nodes['a'], "por", nodes['b'], "gen", 1, 0.1)
    micropsi.add_link(test_nodenet, nodes['c'], "ret", nodes['b'], "gen", 1, 1)

    nodespace = micropsi.get_nodenet_data(test_nodenet, None)
    assert len(nodespace["nodes"]) == 4
    assert len(nodespace["links"]) == 2
    link1 = None
    link2 = None
    for uid, data in nodespace["links"].items():
        if data['source_node_uid'] == nodes['a']:
            link1 = data
        else:
            link2 = data

    assert link1["weight"] == 1
    # assert link1["certainty"] == 0.1
    assert link1["source_node_uid"] == nodes['a']
    assert link1["target_node_uid"] == nodes['b']
    assert link1["source_gate_name"] == "por"
    assert link1["target_slot_name"] == "gen"

    assert link2["source_node_uid"] == nodes['c']
    assert link2["target_node_uid"] == nodes['b']
    assert link2["source_gate_name"] == "ret"
    assert link2["target_slot_name"] == "gen"


def test_delete_link(test_nodenet):
    nodes = prepare_nodenet(test_nodenet)
    success, link = micropsi.add_link(test_nodenet, nodes['a'], "por", nodes['b'], "gen", 0.5, 1)
    assert success
    micropsi.delete_link(test_nodenet, nodes['a'], "por", nodes['b'], "gen")
    nodespace = micropsi.get_nodenet_data(test_nodenet, None)
    assert len(nodespace["links"]) == 0


def test_save_nodenet(test_nodenet):
    prepare_nodenet(test_nodenet)
    # save_nodenet
    micropsi.save_nodenet(test_nodenet)
    # unload_nodenet
    micropsi.unload_nodenet(test_nodenet)
    try:
        micropsi.get_nodenet_data(test_nodenet, None)
        assert False, "could fetch a Nodespace that should not have been in memory"
    except:
        pass
    # load_nodenet
    micropsi.load_nodenet(test_nodenet)
    nodespace = micropsi.get_nodenet_data(test_nodenet, None)
    assert len(nodespace["nodes"]) == 4
    micropsi.delete_nodenet(test_nodenet)


def test_reload_native_modules(fixed_nodenet):
    data_before = micropsi.nodenets[fixed_nodenet].data
    micropsi.reload_native_modules()
    data_after = micropsi.nodenets[fixed_nodenet].data
    assert data_before == data_after


@pytest.mark.engine("dict_engine")
# This behavior is not available in theano_engine: Default inheritance at runtime is not implemented for
# performance reasons, changed defaults will only affect newly created nodes.
# This test will have to be replaced when the generic solution proposed in TOL-90 has been
# implemented.
def test_gate_defaults_change_with_nodetype(fixed_nodenet, resourcepath, nodetype_def, nodefunc_def):
    # gate_parameters are a property of the nodetype, and should change with
    # the nodetype definition if not explicitly overwritten for a given node
    with open(nodetype_def, 'w') as fp:
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
    with open(nodefunc_def, 'w') as fp:
        fp.write("def testnodefunc(netapi, node=None, **prams):\r\n    return 17")
    micropsi.reload_native_modules()
    res, uid = micropsi.add_node(fixed_nodenet, "Testnode", [10, 10], name="Testnode")
    with open(nodetype_def, 'w') as fp:
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
    micropsi.reload_native_modules()
    params = micropsi.nodenets[fixed_nodenet].get_node(uid).get_gate_parameters()
    assert params["foo"]["amplification"] == 5


def test_non_standard_gate_defaults(fixed_nodenet):
    nodenet = micropsi.nodenets[fixed_nodenet]
    res, uid = micropsi.add_node(fixed_nodenet, 'Register', [30, 30], name='test')
    node = nodenet.netapi.get_node(uid)
    genparams = {'maximum': 0.5}
    micropsi.set_gate_parameters(nodenet.uid, node.uid, 'gen', genparams)
    assert node.clone_non_default_gate_parameters()['gen']['maximum'] == 0.5
    assert node.data['gate_parameters'] == {'gen': {'maximum': 0.5}}
    assert nodenet.data['nodes'][uid]['gate_parameters'] == {'gen': {'maximum': 0.5}}
    data = micropsi.get_nodenet_data(fixed_nodenet, None, step=-1, include_links=False)
    assert data['nodes'][uid]['gate_parameters'] == {'gen': {'maximum': 0.5}}


def test_remove_and_reload_native_module(fixed_nodenet, resourcepath, nodetype_def, nodefunc_def):
    from os import remove
    with open(nodetype_def, 'w') as fp:
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
    with open(nodefunc_def, 'w') as fp:
        fp.write("def testnodefunc(netapi, node=None, **prams):\r\n    return 17")

    micropsi.reload_native_modules()
    res, uid = micropsi.add_node(fixed_nodenet, "Testnode", [10, 10], name="Testnode")
    remove(nodetype_def)
    remove(nodefunc_def)
    micropsi.reload_native_modules()
    assert micropsi.get_available_native_module_types(fixed_nodenet) == {}


@pytest.mark.engine("dict_engine")
def test_engine_specific_nodetype_dict(fixed_nodenet, resourcepath, nodetype_def, nodefunc_def):
    with open(nodetype_def, 'w') as fp:
        fp.write('{"Testnode": {\
            "engine": "theano_engine",\
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
    with open(nodefunc_def, 'w') as fp:
        fp.write("def testnodefunc(netapi, node=None, **prams):\r\n    return 17")

    micropsi.reload_native_modules()
    data = micropsi.get_nodenet_data(fixed_nodenet, nodespace='Root')
    assert "Testnode" not in data['native_modules']


@pytest.mark.engine("theano_engine")
def test_engine_specific_nodetype_theano(fixed_nodenet, resourcepath, nodetype_def, nodefunc_def):
    with open(nodetype_def, 'w') as fp:
        fp.write('{"Testnode": {\
            "engine": "dict_engine",\
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
    with open(nodefunc_def, 'w') as fp:
        fp.write("def testnodefunc(netapi, node=None, **prams):\r\n    return 17")

    micropsi.reload_native_modules()
    data = micropsi.get_nodenet_data(fixed_nodenet, nodespace='Root')
    assert "Testnode" not in data['native_modules']


def test_node_parameters_none_resets_to_default(fixed_nodenet):
    nodenet = micropsi.nodenets[fixed_nodenet]
    res, uid = micropsi.add_node(fixed_nodenet, 'Pipe', [30, 30], name='test')
    node = nodenet.netapi.get_node(uid)
    micropsi.set_node_parameters(fixed_nodenet, node.uid, {'expectation': '', 'wait': 0})
    assert node.get_parameter('expectation') == 1
    assert node.get_parameter('wait') == 0


def test_get_recipes(fixed_nodenet, resourcepath, recipes_def):
    with open(recipes_def, 'w') as fp:
        fp.write("""
def testfoo(netapi, count=23):
    return count
""")
    micropsi.reload_native_modules()
    recipes = micropsi.get_available_recipes()
    assert 'testfoo' in recipes
    assert len(recipes['testfoo']['parameters']) == 1
    assert recipes['testfoo']['parameters'][0]['name'] == 'count'
    assert recipes['testfoo']['parameters'][0]['default'] == 23


def test_run_recipe(fixed_nodenet, resourcepath, recipes_def):
    with open(recipes_def, 'w') as fp:
        fp.write("""
def testfoo(netapi, count=23):
    return count
""")
    micropsi.reload_native_modules()
    state, result = micropsi.run_recipe(fixed_nodenet, 'testfoo', {'count': 42})
    assert state
    assert result == 42


def test_node_parameter_defaults(fixed_nodenet, resourcepath, nodetype_def, nodefunc_def):
    with open(nodetype_def, 'w') as fp:
        fp.write('{"Testnode": {\
            "name": "Testnode",\
            "slottypes": ["gen", "foo", "bar"],\
            "gatetypes": ["gen", "foo", "bar"],\
            "nodefunction_name": "testnodefunc",\
            "parameters": ["testparam"],\
            "parameter_defaults": {\
                "testparam": 13\
              }\
            }}')
    with open(nodefunc_def, 'w') as fp:
        fp.write("def testnodefunc(netapi, node=None, **prams):\r\n    return 17")

    micropsi.reload_native_modules()
    data = micropsi.get_nodenet_data(fixed_nodenet, None)
    res, uid = micropsi.add_node(fixed_nodenet, "Testnode", [10, 10], name="Test")
    node = micropsi.nodenets[fixed_nodenet].get_node(uid)
    assert node.get_parameter("testparam") == 13
