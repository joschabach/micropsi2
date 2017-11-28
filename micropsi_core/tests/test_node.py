#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""
Tests for node, nodefunction and the like
"""

from micropsi_core.nodenet.node import Nodetype
from micropsi_core.nodenet.nodefunctions import neuron, concept
import pytest


def test_node_name_defaults(runtime, test_nodenet, resourcepath):
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
    res, uid = runtime.add_node(test_nodenet, "Neuron", [10, 10, 10], None)
    assert netapi.get_node(uid).name == ""
    res, uid = runtime.add_node(test_nodenet, "Pipe", [10, 10, 10], None)
    assert netapi.get_node(uid).name == ""
    res, uid = runtime.add_node(test_nodenet, "Testnode", [10, 10, 10], None)
    assert netapi.get_node(uid).name == "Testnode"
    node = netapi.create_node("Neuron")
    assert node.name == ""
    node = netapi.create_node("Pipe")
    assert node.name == ""
    node = netapi.create_node("Testnode")
    assert node.name == "Testnode"


@pytest.mark.engine("theano_engine")
def test_nodetype_function_definition_overwrites_default_function_name_theano(runtime, test_nodenet):
    nodenet = runtime.get_nodenet(test_nodenet)
    nodetype = nodenet.get_standard_nodetype_definitions()['Neuron'].copy()
    foo = Nodetype(nodenet=nodenet, **nodetype)
    assert foo.nodefunction == neuron
    nodetype['nodefunction_definition'] = 'return 17'
    foo = Nodetype(nodenet=nodenet, **nodetype)
    assert foo.nodefunction != neuron
    assert foo.nodefunction(nodenet, None) == 17


@pytest.mark.engine("dict_engine")
@pytest.mark.engine("numpy_engine")
def test_nodetype_function_definition_overwrites_default_function_name(runtime, test_nodenet):
    nodenet = runtime.get_nodenet(test_nodenet)
    nodetype = nodenet.get_standard_nodetype_definitions()['Concept'].copy()
    foo = Nodetype(nodenet=nodenet, **nodetype)
    assert foo.nodefunction == concept
    nodetype['nodefunction_definition'] = 'return 17'
    foo = Nodetype(nodenet=nodenet, **nodetype)
    assert foo.nodefunction != concept
    assert foo.nodefunction(nodenet, None) == 17


def test_node_positions_as_tuples(runtime, test_nodenet):
    nodenet = runtime.get_nodenet(test_nodenet)
    api = nodenet.netapi
    node = api.create_node("Pipe", None, "node1")
    nodespace = api.create_nodespace(None, "nodespace1")
    node.position = (23, 42)
    assert node.position == [23, 42, 0]


@pytest.mark.engine("theano_engine")
def test_fat_native_modules(runtime, test_nodenet, resourcepath):
    import os
    import numpy as np
    with open(os.path.join(resourcepath, 'nodetypes', 'PhatNM.py'), 'w') as fp:
        fp.write("""
nodetype_definition = {
    "name": "PhatNM",
    "slottypes": ["gen", "sub", "sur", "A_in", "B_in"],
    "gatetypes": ["gen", "sub", "sur", "A_out", "B_out"],
    "nodefunction_name": "phatNM",
    "symbol": "F",
    "dimensionality": {
        "gates": {
            "A_out": 768,
            "B_out": 13
        },
        "slots": {
            "A_in": 1024,
            "B_in": 62
        }
    }
}

def phatNM(netapi, node, **_):
    pass
""")

    runtime.reload_code()
    netapi = runtime.nodenets[test_nodenet].netapi
    node = netapi.create_node("PhatNM", None, "phatty")
    node.take_slot_activation_snapshot()

    # test get_slot_activation
    data = node.get_slot_activations()
    assert len(data) == 1024 + 62 + 3  # fat_slots + gen/sub/sur
    new_activation = np.random.rand(768 + 13 + 3)  # fat gates + gen/sub/sur

    # test set_gate_activation
    node.set_gate_activations(new_activation)
    target = netapi.create_node("Neuron", None, "Target")
    for g in node.get_gate_types():
        netapi.link(node, g, target, 'gen')
    runtime.step_nodenet(test_nodenet)
    assert target.activation > 0

    # test saving/loading data
    node.save_data(new_activation)
    assert np.all(node.load_data() == new_activation)

    # test persistency
    runtime.save_nodenet(test_nodenet)
    runtime.revert_nodenet(test_nodenet)
    netapi = runtime.nodenets[test_nodenet].netapi
    node = netapi.get_node(node.uid)
    target = netapi.get_node(target.uid)
    assert np.all(node.load_data() == new_activation)

    # test setting gate details, get_gate_activation
    node.set_gate_configuration("A_out0", "sigmoid")
    config = node.get_gate_configuration()
    assert config['A_out0']['gatefunction'] == 'sigmoid'
    runtime.step_nodenet(test_nodenet)
    act = node.get_gate_activations()
    assert act[3] == 0.5
    assert np.all(act[4:] == 0)

    # test delivery to frontend
    netapi.link(target, 'gen', node, 'A_in580')
    pipe = netapi.create_node("Pipe", None, "pipe")
    netapi.link_with_reciprocal(pipe, node, 'subsur')
    data = runtime.nodenets[test_nodenet].get_nodes()
    nodedata = data['nodes'][node.uid]
    assert len(nodedata['gate_activations'].keys()) == 5
    assert 'gen' in nodedata['gate_activations']
    assert len(nodedata['links']['A_out0']) == 1  # all to same node
    assert 'A_out1' not in nodedata['links']
    assert data['nodes'][target.uid]['links']['gen'][0]['target_slot_name'] == 'A_in0'
    assert nodedata['links']['sur'][0]['target_node_uid'] == pipe.uid
    assert nodedata['links']['sur'][0]['target_slot_name'] == 'sur'
    assert data['nodes'][pipe.uid]['links']['sub'][0]['target_slot_name'] == 'sub'

    # test get nodetypes
    result = runtime.get_available_native_module_types(test_nodenet)['PhatNM']
    assert result['dimensionality']['gates']['A_out0'] == 768
    assert result['dimensionality']['gates']['B_out0'] == 13
    assert result['dimensionality']['slots']['A_in0'] == 1024
    assert result['dimensionality']['slots']['B_in0'] == 62
    assert result['gatetypes'] == ['gen', 'sub', 'sur', 'A_out0', 'B_out0']
    assert result['is_highdimensional']


def test_start_stop_hooks(runtime, test_nodenet, resourcepath):
    import os
    from time import sleep
    with open(os.path.join(resourcepath, 'nodetypes', 'foobar.py'), 'w') as fp:
        fp.write("""
nodetype_definition = {
    "name": "foobar",
    "slottypes": ["gen"],
    "gatetypes": ["gen"],
    "nodefunction_name": "foobar",
}

def hook(node):
    node.hook_runs += 1

def antihook(node):
    node.hook_runs -= 1

def foobar(netapi, node, **_):
    if not hasattr(node, 'initialized'):
        node.initialized = True
        node.hook_runs = 0
        node.on_start = hook
        node.on_stop = antihook
""")

    runtime.reload_code()
    netapi = runtime.nodenets[test_nodenet].netapi
    foobar = netapi.create_node('foobar')
    runtime.step_nodenet(test_nodenet)
    assert foobar.initialized
    runtime.start_nodenetrunner(test_nodenet)
    sleep(0.001)
    assert foobar.hook_runs == 1
    runtime.stop_nodenetrunner(test_nodenet)
    assert foobar.hook_runs == 0
