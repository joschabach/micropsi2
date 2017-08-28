#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""

"""
import pytest

__author__ = 'joscha'
__date__ = '29.10.12'


def prepare_nodenet(runtime, test_nodenet):
    res, node_a_uid = runtime.add_node(test_nodenet, "Pipe", [200, 250, 10], None, state=None, name="A")
    res, node_b_uid = runtime.add_node(test_nodenet, "Pipe", [500, 350, 10], None, state=None, name="B")
    res, node_c_uid = runtime.add_node(test_nodenet, "Pipe", [300, 150, 10], None, state=None, name="C")
    res, node_s_uid = runtime.add_node(test_nodenet, "Sensor", [200, 450, 10], None, state=None, name="S")
    return {
        'a': node_a_uid,
        'b': node_b_uid,
        'c': node_c_uid,
        's': node_s_uid
    }


def test_add_node(runtime, test_nodenet):
    runtime.load_nodenet(test_nodenet)
    # make sure nodenet is empty
    nodespace = runtime.get_nodes(test_nodenet)
    try:
        for i in nodespace["nodes"]:
            runtime.delete_node(test_nodenet, i)
    except:
        pass

    nodespace = runtime.get_nodes(test_nodenet)
    assert len(nodespace.get("nodes", [])) == 0
    res, uid = runtime.add_node(test_nodenet, "Pipe", [200, 250, 10], None, state=None, name="A")
    nodespace = runtime.get_nodes(test_nodenet)
    assert len(nodespace["nodes"]) == 1
    node1 = nodespace["nodes"][uid]
    assert node1["name"] == "A"
    assert node1["position"] == [200, 250, 10]


def test_position_always_3d(runtime, test_nodenet):
    res, nuid = runtime.add_node(test_nodenet, "Pipe", [200], None, state=None, name="A")
    data = runtime.get_nodes(test_nodenet)
    assert data['nodes'][nuid]['position'] == [200, 0, 0]


def test_get_nodenet_activation_data(runtime, test_nodenet):
    nodes = prepare_nodenet(runtime, test_nodenet)
    uid = nodes['a']
    activation_data = runtime.get_nodenet_activation_data(test_nodenet, [None])
    uid not in activation_data["activations"]
    runtime.set_node_activation(test_nodenet, nodes['a'], 0.34556865)
    activation_data = runtime.get_nodenet_activation_data(test_nodenet, [None])
    assert activation_data["activations"][uid][0] == 0.3


def test_get_nodenet_activation_data_for_nodespace(runtime, test_nodenet):
    nodes = prepare_nodenet(runtime, test_nodenet)
    netapi = runtime.nodenets[test_nodenet].netapi
    uid = nodes['a']
    nodespace = runtime.nodenets[test_nodenet].get_nodespace_uids()[0]
    activation_data = runtime.get_nodenet_activation_data(test_nodenet, [nodespace])
    # zero activations are not sent anymore
    assert uid not in activation_data["activations"]
    netapi.get_node(uid).activation = 0.9
    activation_data = runtime.get_nodenet_activation_data(test_nodenet, [nodespace])
    assert activation_data["activations"][uid][0] == 0.9


def test_get_nodespace(runtime, test_nodenet):
    nodes = prepare_nodenet(runtime, test_nodenet)
    nodespace = runtime.get_nodes(test_nodenet)
    assert len(nodespace["nodes"]) == 4
    node1 = nodespace["nodes"][nodes['a']]
    assert node1["name"] == "A"
    assert node1["position"] == [200, 250, 10]


def test_get_nodespace_list(runtime, test_nodenet):
    nodes = prepare_nodenet(runtime, test_nodenet)
    data = runtime.get_nodespace_list(test_nodenet)
    uid = list(data.keys())[0]
    assert data[uid]['name'] == 'Root'
    assert nodes['a'] in data[uid]['nodes']
    node = data[uid]['nodes'][nodes['a']]
    assert node['name'] == 'A'
    assert node['type'] == 'Pipe'


def test_get_nodespace_list_with_empty_nodespace(runtime, test_nodenet):
    res, uid = runtime.add_nodespace(test_nodenet, None, name="Foospace")
    data = runtime.get_nodespace_list(test_nodenet)
    assert data[uid]['nodes'] == {}


def test_add_link(runtime, test_nodenet):
    nodes = prepare_nodenet(runtime, test_nodenet)
    runtime.add_link(test_nodenet, nodes['a'], "por", nodes['b'], "gen", 0.5)
    runtime.add_link(test_nodenet, nodes['a'], "por", nodes['b'], "gen", 1)
    runtime.add_link(test_nodenet, nodes['c'], "ret", nodes['b'], "gen", 1)

    nodespace = runtime.get_nodes(test_nodenet)
    assert len(nodespace["nodes"]) == 4

    link_a_b = nodespace["nodes"][nodes['a']]['links']['por'][0]
    assert link_a_b['target_node_uid'] == nodes['b']
    assert link_a_b['target_slot_name'] == 'gen'
    assert link_a_b['weight'] == 1

    link_c_b = nodespace['nodes'][nodes['c']]['links']['ret'][0]
    assert link_c_b["target_node_uid"] == nodes['b']
    assert link_c_b["target_slot_name"] == "gen"

    assert nodespace['nodes'][nodes['b']]['links'] == {}
    assert nodespace['nodes'][nodes['s']]['links'] == {}


def test_delete_link(runtime, test_nodenet):
    nodes = prepare_nodenet(runtime, test_nodenet)
    success, link = runtime.add_link(test_nodenet, nodes['a'], "por", nodes['b'], "gen", 0.5)
    assert success
    runtime.delete_link(test_nodenet, nodes['a'], "por", nodes['b'], "gen")
    nodespace = runtime.get_nodes(test_nodenet)
    assert nodespace['nodes'][nodes['a']]['links'] == {}


def test_save_nodenet(runtime, test_nodenet):
    prepare_nodenet(runtime, test_nodenet)
    # save_nodenet
    runtime.save_nodenet(test_nodenet)
    # unload_nodenet
    runtime.unload_nodenet(test_nodenet)
    try:
        runtime.get_nodes(test_nodenet)
        assert False, "could fetch a Nodespace that should not have been in memory"
    except:
        pass
    # load_nodenet
    runtime.get_nodenet(test_nodenet)
    nodespace = runtime.get_nodes(test_nodenet)
    assert len(nodespace["nodes"]) == 4
    runtime.delete_nodenet(test_nodenet)


def test_reload_code(runtime, test_nodenet, resourcepath):
    def hashlink(l):
        return "%s:%s:%s:%s" % (l['source_node_uid'], l['source_gate_name'], l['target_node_uid'], l['target_slot_name'])
    import os
    netapi = runtime.nodenets[test_nodenet].netapi
    nodetype_file = os.path.join(resourcepath, 'nodetypes', 'testnode.py')
    with open(nodetype_file, 'w') as fp:
        fp.write("""nodetype_definition = {
            "name": "Testnode",
            "slottypes": ["gen", "foo", "bar"],
            "nodefunction_name": "testnodefunc",
            "gatetypes": ["gen", "foo", "bar"]
            }
def testnodefunc(netapi, node=None, **prams):\r\n    return 17
""")
    runtime.reload_code()
    reg = netapi.create_node("Neuron", None, "reg")
    test = netapi.create_node("Testnode", None, "test")
    netapi.link(reg, 'gen', test, 'gen')
    netapi.link(test, 'bar', reg, 'gen')
    data_before = runtime.nodenets[test_nodenet].export_json()
    links_before = set([hashlink(l) for l in data_before.pop('links')])
    runtime.reload_code()
    data_after = runtime.nodenets[test_nodenet].export_json()
    links_after = set([hashlink(l) for l in data_after.pop('links')])
    assert data_before == data_after
    assert links_before == links_after


def test_native_module_and_recipe_categories(runtime, test_nodenet, resourcepath):
    import os
    os.makedirs(os.path.join(resourcepath, 'nodetypes', 'Test', 'Test2'))
    os.makedirs(os.path.join(resourcepath, 'recipes', 'Test', 'Test2'))
    nodetype_file = os.path.join(resourcepath, 'nodetypes', 'Test', 'testnode.py')
    recipe_file = os.path.join(resourcepath, 'recipes', 'Test', 'Test2', 'recipes.py')
    with open(nodetype_file, 'w') as fp:
        fp.write("""nodetype_definition = {
            "name": "Testnode",
            "slottypes": ["gen", "foo", "bar"],
            "nodefunction_name": "testnodefunc",
            "gatetypes": ["gen", "foo", "bar"]
            }
def testnodefunc(netapi, node=None, **prams):\r\n    return 17
""")
    with open(recipe_file, 'w') as fp:
        fp.write("def testrecipe(netapi):\r\n    pass")
    runtime.reload_code()
    res = runtime.get_available_native_module_types(test_nodenet)
    assert res['Testnode']['category'] == 'Test'
    assert res['Testnode']['line_number'] == 7
    res = runtime.get_available_recipes()
    assert res['testrecipe']['category'] == 'Test/Test2'


def test_ignore_links(runtime, test_nodenet):
    nodes = prepare_nodenet(runtime, test_nodenet)
    runtime.add_link(test_nodenet, nodes['a'], "por", nodes['b'], "gen", 0.5)

    nodespace = runtime.get_nodes(test_nodenet, [])
    assert len(nodespace["nodes"]) == 4
    assert 'links' not in nodespace

    assert len(nodespace["nodes"][nodes['a']]['links']['por']) == 1
    nodespace = runtime.get_nodes(test_nodenet, [], include_links=False)
    assert 'links' not in nodespace["nodes"][nodes['a']]


def test_remove_and_reload_native_module(runtime, test_nodenet, resourcepath):
    import os
    nodetype_file = os.path.join(resourcepath, 'nodetypes', 'Test', 'testnode.py')
    with open(nodetype_file, 'w') as fp:
        fp.write("""nodetype_definition = {
            "name": "Testnode",
            "slottypes": ["gen", "foo", "bar"],
            "nodefunction_name": "testnodefunc",
            "gatetypes": ["gen", "foo", "bar"],
            "symbol": "t"
            }
def testnodefunc(netapi, node=None, **prams):\r\n    return 17
""")

    runtime.reload_code()
    res, uid = runtime.add_node(test_nodenet, "Testnode", [10, 10, 10], name="Testnode")
    os.remove(nodetype_file)
    runtime.reload_code()
    assert 'Testnode' not in runtime.get_available_native_module_types(test_nodenet)


@pytest.mark.engine("dict_engine")
def test_engine_specific_nodetype_dict(runtime, test_nodenet, resourcepath):
    import os
    nodetype_file = os.path.join(resourcepath, 'nodetypes', 'Test', 'testnode.py')
    with open(nodetype_file, 'w') as fp:
        fp.write("""nodetype_definition = {
            "engine": "theano_engine",
            "name": "Testnode",
            "slottypes": ["gen", "foo", "bar"],
            "nodefunction_name": "testnodefunc",
            "gatetypes": ["gen", "foo", "bar"],
            "symbol": "t"
            }
def testnodefunc(netapi, node=None, **prams):\r\n    return 17
""")

    runtime.reload_code()
    res, data = runtime.get_nodenet_metadata(test_nodenet)
    assert "Testnode" not in data['native_modules']


@pytest.mark.engine("theano_engine")
def test_engine_specific_nodetype_theano(runtime, test_nodenet, resourcepath):
    import os
    nodetype_file = os.path.join(resourcepath, 'nodetypes', 'Test', 'testnode.py')
    with open(nodetype_file, 'w') as fp:
        fp.write("""nodetype_definition = {
            "engine": "dict_engine",
            "name": "Testnode",
            "slottypes": ["gen", "foo", "bar"],
            "nodefunction_name": "testnodefunc",
            "gatetypes": ["gen", "foo", "bar"],
            "symbol": "t"
            }
def testnodefunc(netapi, node=None, **prams):\r\n    return 17
""")

    runtime.reload_code()
    res, data = runtime.get_nodenet_metadata(test_nodenet)
    assert "Testnode" not in data['native_modules']


def test_node_parameters_none_resets_to_default(runtime, test_nodenet):
    nodenet = runtime.nodenets[test_nodenet]
    res, uid = runtime.add_node(test_nodenet, 'Pipe', [30, 30, 10], name='test')
    node = nodenet.netapi.get_node(uid)
    runtime.set_node_parameters(test_nodenet, node.uid, {'expectation': '', 'wait': 0})
    assert node.get_parameter('expectation') == 1
    assert node.get_parameter('wait') == 0


def test_get_recipes(runtime, test_nodenet, resourcepath):
    import os
    os.makedirs(os.path.join(resourcepath, 'recipes', 'Test'))
    recipe_file = os.path.join(resourcepath, 'recipes', 'Test', 'recipes.py')
    with open(recipe_file, 'w') as fp:
        fp.write("""
def testfoo(netapi, count=23):
    return {'count':count}
""")
    runtime.reload_code()
    recipes = runtime.get_available_recipes()
    assert 'testfoo' in recipes
    assert len(recipes['testfoo']['parameters']) == 1
    assert recipes['testfoo']['parameters'][0]['name'] == 'count'
    assert recipes['testfoo']['parameters'][0]['default'] == 23


def test_run_recipe(runtime, test_nodenet, resourcepath):
    import os
    os.makedirs(os.path.join(resourcepath, 'recipes', 'Test'))
    recipe_file = os.path.join(resourcepath, 'recipes', 'Test', 'recipes.py')
    with open(recipe_file, 'w') as fp:
        fp.write("""
def testfoo(netapi, count=23):
    return {'count':count}
""")
    runtime.reload_code()
    state, result = runtime.run_recipe(test_nodenet, 'testfoo', {'count': 42})
    assert state
    assert result['count'] == 42


def test_node_parameter_defaults(runtime, test_nodenet, resourcepath):
    import os
    nodetype_file = os.path.join(resourcepath, 'nodetypes', 'Test', 'testnode.py')
    with open(nodetype_file, 'w') as fp:
        fp.write("""nodetype_definition = {
            "name": "Testnode",
            "slottypes": ["gen", "foo", "bar"],
            "gatetypes": ["gen", "foo", "bar"],
            "nodefunction_name": "testnodefunc",
            "parameters": ["testparam"],
            "parameter_defaults": {
                "testparam": 13
              }
            }
def testnodefunc(netapi, node=None, **prams):\r\n    return 17
""")

    runtime.reload_code()
    res, uid = runtime.add_node(test_nodenet, "Testnode", [10, 10, 10], name="Test")
    node = runtime.nodenets[test_nodenet].get_node(uid)
    assert node.get_parameter("testparam") == 13


def test_node_parameters_from_persistence(runtime, test_nodenet, resourcepath):
    import os
    nodetype_file = os.path.join(resourcepath, 'nodetypes', 'Test', 'testnode.py')
    with open(nodetype_file, 'w') as fp:
        fp.write("""nodetype_definition = {
            "name": "Testnode",
            "slottypes": ["gen", "foo", "bar"],
            "gatetypes": ["gen", "foo", "bar"],
            "nodefunction_name": "testnodefunc",
            "parameters": ["testparam"],
            "parameter_defaults": {
                "testparam": 13
              }
            }
def testnodefunc(netapi, node=None, **prams):\r\n    return 17
""")
    runtime.reload_code()
    res, uid = runtime.add_node(test_nodenet, "Testnode", [10, 10, 10], name="Test")
    node = runtime.nodenets[test_nodenet].get_node(uid)
    node.set_parameter("testparam", 42)
    runtime.save_nodenet(test_nodenet)
    runtime.revert_nodenet(test_nodenet)
    node = runtime.nodenets[test_nodenet].get_node(uid)
    assert node.get_parameter("testparam") == 42


def test_change_node_parameters(runtime, test_nodenet, resourcepath):
    import os
    nodetype_file = os.path.join(resourcepath, 'nodetypes', 'Test', 'testnode.py')

    def write_nodetypedef(params=[]):
        with open(nodetype_file, 'w') as fp:
            fp.write("""nodetype_definition = {
                "name": "Testnode",
                "slottypes": ["gen", "foo", "bar"],
                "gatetypes": ["gen", "foo", "bar"],
                "nodefunction_name": "testnodefunc",
                "parameters": %s}
def testnodefunc(netapi, node=None, **prams):\r\n    return 17
    """ % str(params))

    write_nodetypedef(params=["foo", "bar"])
    runtime.reload_code()
    res, uid = runtime.add_node(test_nodenet, "Testnode", [10, 10, 10], name="Test")
    node = runtime.nodenets[test_nodenet].get_node(uid)
    keys = node.clone_parameters().keys()
    assert "foo" in keys
    assert "bar" in keys
    node.set_parameter("foo", 42)

    write_nodetypedef(params=["spam", "eggs"])
    runtime.reload_code()
    node = runtime.nodenets[test_nodenet].get_node(uid)
    keys = node.clone_parameters().keys()
    assert "foo" not in keys
    assert "bar" not in keys
    assert "spam" in keys
    assert "eggs" in keys
    assert node.get_parameter('spam') is None
    assert node.get_parameter('eggs') is None
