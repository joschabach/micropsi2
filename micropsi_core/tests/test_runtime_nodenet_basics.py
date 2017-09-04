#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""

"""
import os
import mock
import pytest

__author__ = 'joscha'
__date__ = '29.10.12'


def prepare(runtime, test_nodenet):
    net = runtime.nodenets[test_nodenet]
    netapi = net.netapi
    source = netapi.create_node("Neuron", None, "source")
    register = netapi.create_node("Neuron", None, "reg")
    netapi.link(source, 'gen', source, 'gen')
    netapi.link(source, 'gen', register, 'gen')
    return net, netapi, source, register


def test_new_nodenet(runtime, test_nodenet, default_world, resourcepath, engine):
    success, nodenet_uid = runtime.new_nodenet("Test_Nodenet", engine=engine, world_uid=default_world, worldadapter="Default", owner="tester")
    assert success
    runtime.revert_nodenet(nodenet_uid)
    nodenet = runtime.get_nodenet(nodenet_uid)
    assert nodenet.world == default_world
    assert nodenet.worldadapter == "Default"
    assert nodenet_uid != test_nodenet
    assert runtime.get_available_nodenets("tester")[nodenet_uid].name == "Test_Nodenet"
    n_path = os.path.join(resourcepath, runtime.NODENET_DIRECTORY, nodenet_uid, "nodenet.json")
    assert os.path.exists(n_path)

    # get_available_nodenets
    nodenets = runtime.get_available_nodenets()
    mynets = runtime.get_available_nodenets("tester")
    assert test_nodenet in nodenets
    assert nodenet_uid in nodenets
    assert nodenet_uid in mynets
    assert test_nodenet not in mynets

    # delete_nodenet
    runtime.delete_nodenet(nodenet_uid)
    assert nodenet_uid not in runtime.get_available_nodenets()
    assert not os.path.exists(n_path)


def test_user_prompt(runtime, test_nodenet, resourcepath):
    import os
    nodetype_file = os.path.join(resourcepath, 'nodetypes', 'Test', 'testnode.py')
    nodenet = runtime.nodenets[test_nodenet]
    with open(nodetype_file, 'w') as fp:
        fp.write("""nodetype_definition = {
    "name": "Testnode",
    "slottypes": ["gen", "foo", "bar"],
    "gatetypes": ["gen", "foo", "bar"],
    "nodefunction_name": "testnodefunc",
    "parameters": ["testparam"],
    "parameter_defaults": {
        "testparam": 13
    },
    "user_prompts": {
        "promptident": {
            "callback": "user_prompt_callback",
            "parameters": [
                {"name": "foo", "description": "value for foo", "default": 23},
                {"name": "bar", "description": "value for bar", "default": 42}
            ]
        }
    }
}

def testnodefunc(netapi, node=None, **prams):
    if not hasattr(node, 'foo'):
        node.foo = 0
        node.bar = 1
        netapi.show_user_prompt(node, "promptident")
    node.get_gate("foo").gate_function(node.foo)
    node.get_gate("bar").gate_function(node.bar)

def user_prompt_callback(netapi, node, user_prompt_params):
    \"\"\"Elaborate explanation as to what this user prompt is for\"\"\"
    node.foo = int(user_prompt_params['foo'])
    node.bar = int(user_prompt_params['bar'])
""")

    runtime.reload_code()
    res, node_uid = runtime.add_node(test_nodenet, "Testnode", [10, 10], name="Test")
    runtime.reload_code()  # this breaks, if the nodetype overwrites the definition
    nativemodule = nodenet.get_node(node_uid)
    runtime.step_nodenet(test_nodenet)
    result, data = runtime.get_calculation_state(test_nodenet, nodenet={})
    assert 'user_prompt' in data
    assert data['user_prompt']['key'] == "promptident"
    assert data['user_prompt']['msg'] == 'Elaborate explanation as to what this user prompt is for'
    assert data['user_prompt']['node']['uid'] == node_uid
    assert len(data['user_prompt']['parameters']) == 2
    assert nativemodule.get_gate('foo').activation == 0
    assert nativemodule.get_gate('bar').activation == 1

    # response
    runtime.user_prompt_response(test_nodenet, node_uid, "promptident", {'foo': '111', 'bar': '222'}, False)
    runtime.step_nodenet(test_nodenet)
    assert nativemodule.get_gate('foo').activation == 111
    assert nativemodule.get_gate('bar').activation == 222


def test_user_notification(runtime, test_nodenet, node):
    api = runtime.nodenets[test_nodenet].netapi
    node_obj = api.get_node(node)
    api.notify_user(node_obj, "Hello there")
    result, data = runtime.get_calculation_state(test_nodenet, nodenet={'nodespaces': [None]})
    assert 'user_prompt' in data
    assert data['user_prompt']['node']['uid'] == node
    assert data['user_prompt']['msg'] == "Hello there"


def test_nodespace_removal(runtime, test_nodenet):
    res, uid = runtime.add_nodespace(test_nodenet, nodespace=None, name="testspace")
    res, n1_uid = runtime.add_node(test_nodenet, 'Neuron', [100, 100], nodespace=uid, name="sub1")
    res, n2_uid = runtime.add_node(test_nodenet, 'Neuron', [100, 200], nodespace=uid, name="sub2")
    runtime.add_link(test_nodenet, n1_uid, 'gen', n2_uid, 'gen', weight=1)
    res, sub_uid = runtime.add_nodespace(test_nodenet, nodespace=uid, name="subsubspace")
    runtime.delete_nodespace(test_nodenet, uid)
    # assert that the nodespace is gone
    assert not runtime.nodenets[test_nodenet].is_nodespace(uid)
    assert uid not in runtime.nodenets[test_nodenet].get_data()['nodespaces']
    # assert that the nodes it contained are gone
    assert not runtime.nodenets[test_nodenet].is_node(n1_uid)
    assert n1_uid not in runtime.nodenets[test_nodenet].get_data()['nodes']
    assert not runtime.nodenets[test_nodenet].is_node(n2_uid)
    assert n2_uid not in runtime.nodenets[test_nodenet].get_data()['nodes']
    # assert that sub-nodespaces are gone as well
    assert not runtime.nodenets[test_nodenet].is_nodespace(sub_uid)
    assert sub_uid not in runtime.nodenets[test_nodenet].get_data()['nodespaces']


def test_clone_nodes_nolinks(runtime, test_nodenet):
    net, netapi, source, register = prepare(runtime, test_nodenet)
    nodenet = runtime.get_nodenet(test_nodenet)
    success, result = runtime.clone_nodes(test_nodenet, [source.uid, register.uid], 'none', offset=[10, 20, 2])
    assert success
    for n in result.values():
        if n['name'] == source.name:
            source_copy = n
        elif n['name'] == register.name:
            register_copy = n
    assert nodenet.is_node(source_copy['uid'])
    assert source_copy['uid'] != source.uid
    assert source_copy['type'] == nodenet.get_node(source.uid).type
    assert source_copy['parameters'] == nodenet.get_node(source.uid).clone_parameters()
    assert source_copy['position'][0] == nodenet.get_node(source.uid).position[0] + 10
    assert source_copy['position'][1] == nodenet.get_node(source.uid).position[1] + 20
    assert source_copy['position'][2] == nodenet.get_node(source.uid).position[2] + 2
    assert nodenet.is_node(register_copy['uid'])
    assert register_copy['name'] == nodenet.get_node(register.uid).name
    assert register_copy['uid'] != register.uid
    assert len(result.keys()) == 2
    assert source_copy['links'] == {}
    assert register_copy['links'] == {}


def test_clone_nodes_all_links(runtime, test_nodenet):
    net, netapi, source, register = prepare(runtime, test_nodenet)
    nodenet = runtime.get_nodenet(test_nodenet)
    thirdnode = netapi.create_node('Neuron', None, 'third')
    netapi.link(thirdnode, 'gen', register, 'gen')
    success, result = runtime.clone_nodes(test_nodenet, [source.uid, register.uid], 'all')
    assert success
    # expect 3 instead of two results, because thirdnode should be delivered
    # as a followupdnode to source_copy to render incoming links
    assert len(result.keys()) == 3
    for n in result.values():
        if n['name'] == source.name:
            source_copy = n
        elif n['name'] == register.name:
            register_copy = n

    # assert the links between the copied nodes exist:
    assert len(source_copy['links']['gen']) == 2
    assert set([l['target_node_uid'] for l in source_copy['links']['gen']]) == {source_copy['uid'], register_copy['uid']}

    # assert the link between thirdnode and register-copy exists
    third = nodenet.get_node(thirdnode.uid).get_data()
    assert len(third['links']['gen']) == 2
    assert set([l['target_node_uid'] for l in third['links']['gen']]) == {register.uid, register_copy['uid']}


def test_clone_nodes_internal_links(runtime, test_nodenet):
    net, netapi, source, register = prepare(runtime, test_nodenet)
    thirdnode = netapi.create_node('Neuron', None, 'third')
    netapi.link(thirdnode, 'gen', register, 'gen')
    success, result = runtime.clone_nodes(test_nodenet, [source.uid, register.uid], 'internal')
    assert success
    assert len(result.keys()) == 2
    for n in result.values():
        if n['name'] == source.name:
            source_copy = n
        elif n['name'] == register.name:
            register_copy = n

    # assert the links between the copied nodes exist:
    assert len(source_copy['links']['gen']) == 2
    assert set([l['target_node_uid'] for l in source_copy['links']['gen']]) == {source_copy['uid'], register_copy['uid']}

    # assert the link between thirdnode and register-copy does not exist
    third = net.get_node(thirdnode.uid).get_data()
    assert len(third['links']['gen']) == 1


def test_clone_nodes_to_new_nodespace(runtime, test_nodenet):
    net, netapi, source, register = prepare(runtime, test_nodenet)
    thirdnode = netapi.create_node('Neuron', None, 'third')
    netapi.link(thirdnode, 'gen', register, 'gen')
    success, result = runtime.clone_nodes(test_nodenet, [source.uid, register.uid], 'internal')

    res, testspace_uid = runtime.add_nodespace(test_nodenet, nodespace=None, name="testspace")

    success, result = runtime.clone_nodes(test_nodenet, [source.uid, register.uid], 'internal', nodespace=testspace_uid)
    assert success
    assert len(result.keys()) == 2
    for n in result.values():
        if n['name'] == source.name:
            source_copy = n
        elif n['name'] == register.name:
            register_copy = n

    source_copy = net.get_node(source_copy['uid'])
    register_copy = net.get_node(register_copy['uid'])

    assert source_copy.parent_nodespace == testspace_uid
    assert register_copy.parent_nodespace == testspace_uid


def test_modulators(runtime, test_nodenet, engine):
    nodenet = runtime.get_nodenet(test_nodenet)
    # assert modulators are instantiated from the beginning
    assert nodenet._modulators != {}
    assert nodenet.get_modulator('emo_activation') is not None

    # set a modulator
    nodenet.set_modulator("test_modulator", -1)
    assert nodenet.netapi.get_modulator("test_modulator") == -1

    # assert change_modulator sets diff.
    nodenet.netapi.change_modulator("test_modulator", 0.42)
    assert round(nodenet.netapi.get_modulator("test_modulator"), 4) == -0.58

    # no modulators should be set if we disable the emotional_parameter module
    res, uid = runtime.new_nodenet('foobar', engine, use_modulators=False)
    new_nodenet = runtime.get_nodenet(uid)
    assert new_nodenet._modulators == {}
    # and no Emo-stepoperator should be set.
    for item in new_nodenet.stepoperators:
        assert 'Emotional' not in item.__class__.__name__


def test_modulators_sensor_actuator_connection(runtime, test_nodenet, default_world):
    nodenet = runtime.get_nodenet(test_nodenet)
    runtime.set_nodenet_properties(test_nodenet, worldadapter="Default", world_uid=default_world)
    res, s1_id = runtime.add_node(test_nodenet, "Sensor", [10, 10], None, name="static_on", parameters={'datasource': 'static_on'})
    res, s2_id = runtime.add_node(test_nodenet, "Sensor", [20, 20], None, name="emo_activation", parameters={'datasource': 'emo_activation'})
    res, a1_id = runtime.add_node(test_nodenet, "Actuator", [30, 30], None, name="echo", parameters={'datatarget': 'echo'})
    res, a2_id = runtime.add_node(test_nodenet, "Actuator", [40, 40], None, name="base_importance_of_intention", parameters={'datatarget': 'base_importance_of_intention'})
    res, r1_id = runtime.add_node(test_nodenet, "Neuron", [10, 30], None, name="r1")
    res, r2_id = runtime.add_node(test_nodenet, "Neuron", [10, 30], None, name="r2")
    s1 = nodenet.get_node(s1_id)
    s2 = nodenet.get_node(s2_id)
    r1 = nodenet.get_node(r1_id)
    r2 = nodenet.get_node(r2_id)
    runtime.add_link(test_nodenet, r1_id, 'gen', a1_id, 'gen')
    runtime.add_link(test_nodenet, r2_id, 'gen', a2_id, 'gen')
    r1.activation = 0.3
    r2.activation = 0.7
    emo_val = nodenet.get_modulator("emo_activation")

    # patch reset method, to check if datatarget was written
    def nothing():
        pass
    nodenet.worldadapter_instance.reset_datatargets = nothing

    nodenet.step()
    assert round(nodenet.worldadapter_instance.datatargets['echo'], 3) == 0.3
    assert round(s1.activation, 3) == round(nodenet.worldadapter_instance.get_datasource_value('static_on'), 3)
    assert round(s2.activation, 3) == round(emo_val, 3)
    assert round(nodenet.get_modulator('base_importance_of_intention'), 3) == 0.7
    emo_val = nodenet.get_modulator("emo_activation")
    nodenet.step()
    assert round(s2.activation, 3) == round(emo_val, 3)


def test_node_parameters(runtime, test_nodenet, resourcepath):
    import os
    nodetype_file = os.path.join(resourcepath, 'nodetypes', 'Test', 'testnode.py')
    with open(nodetype_file, 'w') as fp:
        fp.write("""nodetype_definition = {
    "name": "Testnode",
    "slottypes": ["gen", "foo", "bar"],
    "gatetypes": ["gen", "foo", "bar"],
    "nodefunction_name": "testnodefunc",
    "parameters": ["linktype", "threshold", "protocol_mode"],
    "parameter_values": {
        "linktype": ["catexp", "subsur"],
        "protocol_mode": ["all_active", "most_active_one"]
    },
    "parameter_defaults": {
        "linktype": "catexp",
        "protocol_mode": "all_active"
    }
}
def testnodefunc(netapi, node=None, **prams):\r\n    return 17
""")

    assert runtime.reload_code()
    res, uid = runtime.add_node(test_nodenet, "Testnode", [10, 10], name="Test", parameters={"threshold": "", "protocol_mode": "most_active_one"})
    # nativemodule = runtime.nodenets[test_nodenet].get_node(uid)
    assert runtime.save_nodenet(test_nodenet)
    node = runtime.nodenets[test_nodenet].get_node(uid)
    assert node.get_parameter('linktype') == 'catexp'
    assert node.get_parameter('protocol_mode') == 'most_active_one'


@pytest.mark.engine("dict_engine")
def test_node_states(runtime, test_nodenet, node):
    nodenet = runtime.get_nodenet(test_nodenet)
    node = nodenet.get_node(node)
    assert node.get_state('foobar') is None
    node.set_state('foobar', 'bazbaz')
    assert node.get_state('foobar') == 'bazbaz'
    node.set_state('foobar', 42)
    assert node.get_state('foobar') == 42


@pytest.mark.engine("theano_engine")
def test_node_states_numpy(runtime, test_nodenet, node, resourcepath):
    import os
    import numpy as np

    nodenet = runtime.get_nodenet(test_nodenet)
    node = nodenet.get_node(node)
    assert node.get_state('foobar') is None
    node.set_state('foobar', 'bazbaz')
    assert node.get_state('foobar') == 'bazbaz'
    node.set_state('foobar', 42)
    assert node.get_state('foobar') == 42

    nodetype_file = os.path.join(resourcepath, 'nodetypes', 'Test', 'testnode.py')
    with open(nodetype_file, 'w') as fp:
        fp.write("""nodetype_definition = {
    "name": "Testnode",
    "slottypes": ["gen", "foo", "bar"],
    "gatetypes": ["gen", "foo", "bar"],
    "nodefunction_name": "testnodefunc",
}
def testnodefunc(netapi, node=None, **prams):\r\n    return 17
""")

    assert runtime.reload_code()
    res, uid = runtime.add_node(test_nodenet, "Testnode", [10, 10], name="Test")

    testnode = runtime.nodenets[test_nodenet].get_node(uid)
    testnode.set_state("string", "hugo")
    testnode.set_state("dict", {"eins": 1, "zwei": 2})
    testnode.set_state("list", [{"eins": 1, "zwei": 2}, "boing"])
    testnode.set_state("numpy", np.asarray([1, 2, 3, 4]))

    runtime.save_nodenet(test_nodenet)
    runtime.revert_nodenet(test_nodenet)

    testnode = runtime.nodenets[test_nodenet].get_node(uid)

    assert testnode.get_state("string") == "hugo"
    assert testnode.get_state("dict")["eins"] == 1
    assert testnode.get_state("list")[0]["eins"] == 1
    assert testnode.get_state("list")[1] == "boing"
    assert testnode.get_state("numpy").sum() == 10  # only numpy arrays have ".sum()"

    testnode.set_state("wrong", (np.asarray([1, 2, 3]), 'tuple'))

    with pytest.raises(ValueError):
        runtime.save_nodenet(test_nodenet)


def test_delete_linked_nodes(runtime, test_nodenet):

    nodenet = runtime.get_nodenet(test_nodenet)
    netapi = nodenet.netapi

    # create all evil (there will never be another dawn)
    root_of_all_evil = netapi.create_node("Pipe", None)
    evil_one = netapi.create_node("Pipe", None)
    evil_two = netapi.create_node("Pipe", None)

    netapi.link_with_reciprocal(root_of_all_evil, evil_one, "subsur")
    netapi.link_with_reciprocal(root_of_all_evil, evil_two, "subsur")

    for link in evil_one.get_gate("sub").get_links():
        link.source_node.name  # touch of evil
        link.target_node.name  # touch of evil

    for link in evil_two.get_gate("sur").get_links():
        link.source_node.name  # touch of evil
        link.target_node.name  # touch of evil

    # and the name of the horse was death
    netapi.delete_node(root_of_all_evil)
    netapi.delete_node(evil_one)
    netapi.delete_node(evil_two)


def test_multiple_nodenet_interference(runtime, engine, resourcepath):
    import os
    nodetype_file = os.path.join(resourcepath, 'nodetypes', 'Test', 'testnode.py')
    with open(nodetype_file, 'w') as fp:
        fp.write("""nodetype_definition = {
    "name": "Testnode",
    "slottypes": ["gen", "foo", "bar"],
    "gatetypes": ["gen", "foo", "bar"],
    "nodefunction_name": "testnodefunc"
}
def testnodefunc(netapi, node=None, **prams):\r\n    node.get_gate('gen').gate_function(17)
""")
    runtime.reload_code()

    result, n1_uid = runtime.new_nodenet('Net1', engine=engine, owner='Pytest User')
    result, n2_uid = runtime.new_nodenet('Net2', engine=engine, owner='Pytest User')

    n1 = runtime.nodenets[n1_uid]
    n2 = runtime.nodenets[n2_uid]

    nativemodule = n1.netapi.create_node("Testnode", None, "Testnode")
    register1 = n1.netapi.create_node("Neuron", None, "Neuron1")
    n1.netapi.link(nativemodule, 'gen', register1, 'gen', weight=1.2)

    source2 = n2.netapi.create_node("Neuron", None, "Source2")
    register2 = n2.netapi.create_node("Neuron", None, "Neuron2")
    n2.netapi.link(source2, 'gen', source2, 'gen')
    n2.netapi.link(source2, 'gen', register2, 'gen', weight=0.9)
    source2.activation = 0.7

    runtime.step_nodenet(n2.uid)

    assert n1.current_step == 0
    assert register1.activation == 0
    assert register1.name == "Neuron1"
    assert nativemodule.name == "Testnode"
    assert round(register1.get_slot('gen').get_links()[0].weight, 2) == 1.2
    assert register1.get_slot('gen').get_links()[0].source_node.name == 'Testnode'
    assert n1.get_node(register1.uid).name == "Neuron1"

    assert n2.current_step == 1
    assert round(source2.activation, 2) == 0.7
    assert round(register2.activation, 2) == 0.63
    assert register2.name == "Neuron2"
    assert source2.name == "Source2"
    assert round(register2.get_slot('gen').get_links()[0].weight, 2) == 0.9
    assert register2.get_slot('gen').get_links()[0].source_node.name == 'Source2'
    assert n2.get_node(register2.uid).name == "Neuron2"


def test_get_nodespace_changes(runtime, test_nodenet):
    net, netapi, source, register = prepare(runtime, test_nodenet)
    net.step()
    result = runtime.get_nodespace_changes(test_nodenet, [None], 0)
    assert set(result['nodes_dirty'].keys()) == set(net.get_node_uids())
    assert result['nodes_deleted'] == []
    assert result['nodespaces_dirty'] == {}
    assert result['nodespaces_deleted'] == []
    net.netapi.unlink(source, 'gen', register, 'gen')
    net.netapi.delete_node(register)
    newnode = net.netapi.create_node('Neuron', None, "new thing")
    net.netapi.link(newnode, 'gen', source, 'gen')
    newspace = net.netapi.create_nodespace(None, "nodespace")
    net.step()
    test = runtime.get_nodenet_activation_data(test_nodenet, [None], 1)
    assert test['has_changes']
    result = runtime.get_nodespace_changes(test_nodenet, [None], 1)
    assert register.uid in result['nodes_deleted']
    assert source.uid in result['nodes_dirty']
    assert newnode.uid in result['nodes_dirty']
    assert len(result['nodes_dirty'][source.uid]['links']) == 1
    assert len(result['nodes_dirty'][newnode.uid]['links']['gen']) == 1
    assert newspace.uid in result['nodespaces_dirty']
    assert len(result['nodes_dirty'].keys()) == 2
    assert len(result['nodespaces_dirty'].keys()) == 1
    net.step()
    test = runtime.get_nodenet_activation_data(test_nodenet, [None], 2)
    assert not test['has_changes']


def test_get_nodespace_changes_cycles(runtime, test_nodenet):
    net, netapi, source, register = prepare(runtime, test_nodenet)
    net.step()
    net.netapi.delete_node(register)
    net.step()
    result = runtime.get_nodespace_changes(test_nodenet, [None], 1)
    assert register.uid in result['nodes_deleted']
    for i in range(101):
        net.step()
    result = runtime.get_nodespace_changes(test_nodenet, [None], 1)
    assert register.uid not in result['nodes_deleted']


def test_nodespace_properties(runtime, test_nodenet):
    data = {'testvalue': 'foobar'}
    rootns = runtime.get_nodenet(test_nodenet).get_nodespace(None)
    runtime.set_nodespace_properties(test_nodenet, rootns.uid, data)
    assert runtime.nodenets[test_nodenet].metadata['nodespace_ui_properties'][rootns.uid] == data
    assert runtime.get_nodespace_properties(test_nodenet, rootns.uid) == data
    runtime.save_nodenet(test_nodenet)
    runtime.revert_nodenet(test_nodenet)
    assert runtime.get_nodespace_properties(test_nodenet, rootns.uid) == data
    properties = runtime.get_nodespace_properties(test_nodenet)
    assert properties[rootns.uid] == data


def test_native_module_reload_changes_gates(runtime, test_nodenet, resourcepath):
    import os
    nodetype_file = os.path.join(resourcepath, 'nodetypes', 'Test', 'testnode.py')
    with open(nodetype_file, 'w') as fp:
        fp.write("""nodetype_definition = {
    "name": "Testnode",
    "slottypes": ["gen", "foo", "bar"],
    "gatetypes": ["gen", "foo", "bar"],
    "nodefunction_name": "testnodefunc"
}
def testnodefunc(netapi, node=None, **prams):\r\n    return 17
""")

    assert runtime.reload_code()
    res, uid = runtime.add_node(test_nodenet, "Testnode", [10, 10], name="Test")
    res, neuron_uid = runtime.add_node(test_nodenet, 'Neuron', [10, 10])
    runtime.add_link(test_nodenet, neuron_uid, 'gen', uid, 'gen')
    runtime.add_link(test_nodenet, uid, 'gen', neuron_uid, 'gen')
    with open(nodetype_file, 'w') as fp:
        fp.write("""nodetype_definition = {
    "name": "Testnode",
    "slottypes": ["foo", "bar"],
    "gatetypes": ["foo", "bar"],
    "nodefunction_name": "testnodefunc"
}
def testnodefunc(netapi, node=None, **prams):\r\n    return 17
""")
    assert runtime.reload_code()
    nativemodule = runtime.nodenets[test_nodenet].get_node(uid)
    assert nativemodule.get_gate_types() == ["foo", "bar"]
    neuron = runtime.nodenets[test_nodenet].get_node(neuron_uid)
    assert neuron.get_gate('gen').get_links() == []
    assert neuron.get_slot('gen').get_links() == []


@pytest.mark.engine("dict_engine")
def test_runtime_autosave_dict(runtime, test_nodenet, resourcepath):
    import os
    import json
    import zipfile
    import tempfile
    from time import sleep
    runtime.set_runner_condition(test_nodenet, steps=100)
    runtime.start_nodenetrunner(test_nodenet)
    count = 0
    while runtime.nodenets[test_nodenet].is_active:
        sleep(.1)
        count += 1
        assert count < 20  # quit if not done after 2 sec
    filename = os.path.join(resourcepath, "nodenets", "__autosave__", "%s_%d.zip" % (test_nodenet, 100))
    assert os.path.isfile(filename)
    with zipfile.ZipFile(filename, 'r') as archive:
        assert set(archive.namelist()) == {"nodenet.json"}
        tmp = tempfile.TemporaryDirectory()
        archive.extractall(tmp.name)
        with open(os.path.join(tmp.name, "nodenet.json"), 'r') as fp:
            restored = json.load(fp)
        original = runtime.nodenets[test_nodenet].export_json()
        # step and runner_conditions might differ
        for key in ['nodes', 'links', 'modulators', 'uid', 'name', 'owner', 'world', 'worldadapter', 'version', 'monitors', 'nodespaces']:
            assert restored[key] == original[key]


@pytest.mark.engine("theano_engine")
def test_runtime_autosave_theano(runtime, test_nodenet, resourcepath):
    import os
    import tempfile
    import zipfile
    import numpy as np
    from time import sleep
    with open(os.path.join(resourcepath, "nodetypes", "Source.py"), 'w') as fp:
        fp.write("""nodetype_definition = {
    "flow_module": True,
    "implementation": "python",
    "name": "Source",
    "init_function_name": "source_init",
    "run_function_name": "source",
    "inputs": [],
    "outputs": ["X"]
}

def source_init(netapi, node, parameters):
    import numpy as np
    w_array = np.random.rand(8).astype(netapi.floatX)
    node.set_theta("weights", w_array)

def source(netapi, node, parameters):
    return node.get_theta("weights").get_value()
""")
    with open(os.path.join(resourcepath, "nodetypes", "Target.py"), 'w') as fp:
        fp.write("""nodetype_definition = {
    "flow_module": True,
    "implementation": "python",
    "name": "Target",
    "run_function_name": "target",
    "inputs": ["X"],
    "outputs": [],
    "inputdims": [1]
}

def target(X, netapi, node, parameters):
    node.set_state("incoming", X)
""")

    runtime.reload_code()
    nodenet = runtime.nodenets[test_nodenet]
    netapi = nodenet.netapi
    source = netapi.create_node("Source", None, "Source")
    target = netapi.create_node("Target", None, "Target")
    netapi.flow(source, "X", target, "X")
    neuron = netapi.create_node("Neuron", None, "Neuron")
    netapi.link(neuron, 'gen', target, 'sub')
    neuron.activation = 1
    runtime.set_runner_condition(test_nodenet, steps=100)
    runtime.start_nodenetrunner(test_nodenet)
    count = 0
    while runtime.nodenets[test_nodenet].is_active:
        sleep(.1)
        count += 1
        assert count < 20  # quit if not done after 2 sec
    filename = os.path.join(resourcepath, "nodenets", "__autosave__", "%s_%d.zip" % (test_nodenet, 100))
    assert os.path.isfile(filename)
    with zipfile.ZipFile(filename, 'r') as archive:
        assert set(archive.namelist()) == {"nodenet.json", "flowgraph.pickle", "partition-000.npz", "%s_numpystate.npz" % target.uid, "%s_thetas.npz" % source.uid}
        from micropsi_core.nodenet.theano_engine.theano_nodenet import TheanoNodenet
        tmp = tempfile.TemporaryDirectory()
        archive.extractall(tmp.name)
        net = TheanoNodenet(tmp.name, "restored", uid=test_nodenet, native_modules=runtime.native_modules)
        net.load()
        nsource = net.netapi.get_node(source.uid)
        ntarget = net.netapi.get_node(target.uid)
        nneuron = net.netapi.get_node(neuron.uid)
        assert nsource.name == "Source"
        assert nsource.outputmap == {'X': {(ntarget.uid, 'X')}}
        assert np.all(nsource.get_theta("weights").get_value() == source.get_theta("weights").get_value())
        assert np.all(ntarget.get_state("incoming") == target.get_state("incoming"))
        assert nneuron.get_gate('gen').get_links()[0].target_node == ntarget
