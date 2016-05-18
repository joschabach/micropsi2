#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""
Tests for node, nodefunction and the like
"""

from micropsi_core.nodenet.node import Nodetype
from micropsi_core.nodenet.nodefunctions import register, concept
from micropsi_core import runtime as micropsi
import pytest


@pytest.mark.engine("theano_engine")
def test_nodetype_function_definition_overwrites_default_function_name_theano(fixed_nodenet):
    nodenet = micropsi.get_nodenet(fixed_nodenet)
    nodetype = nodenet.get_standard_nodetype_definitions()['Register'].copy()
    foo = Nodetype(nodenet=nodenet, **nodetype)
    assert foo.nodefunction == register
    nodetype['nodefunction_definition'] = 'return 17'
    foo = Nodetype(nodenet=nodenet, **nodetype)
    assert foo.nodefunction != register
    assert foo.nodefunction(nodenet, None) == 17


@pytest.mark.engine("dict_engine")
def test_nodetype_function_definition_overwrites_default_function_name(fixed_nodenet):
    nodenet = micropsi.get_nodenet(fixed_nodenet)
    nodetype = nodenet.get_standard_nodetype_definitions()['Concept'].copy()
    foo = Nodetype(nodenet=nodenet, **nodetype)
    assert foo.nodefunction == concept
    nodetype['nodefunction_definition'] = 'return 17'
    foo = Nodetype(nodenet=nodenet, **nodetype)
    assert foo.nodefunction != concept
    assert foo.nodefunction(nodenet, None) == 17


def test_node_states(test_nodenet, node):
    nodenet = micropsi.get_nodenet(test_nodenet)
    node = nodenet.get_node(node)
    assert node.get_state('foobar') is None
    node.set_state('foobar', 'bazbaz')
    assert node.get_state('foobar') == 'bazbaz'
    node.set_state('foobar', 42)
    assert node.get_state('foobar') == 42


def test_entity_positions_as_tuples(test_nodenet):
    nodenet = micropsi.get_nodenet(test_nodenet)
    api = nodenet.netapi
    node = api.create_node("Pipe", None, "node1")
    nodespace = api.create_nodespace(None, "nodespace1")
    node.position = (23, 42)
    nodespace.position = (13, 23, 42)
    assert node.position == [23, 42, 0]
    assert nodespace.position == [13, 23, 42]


@pytest.mark.engine("theano_engine")
def test_fat_native_modules(test_nodenet, resourcepath):
    import os
    import numpy as np
    with open(os.path.join(resourcepath, 'nodetypes.json'), 'w') as fp:
        fp.write("""
    {"PhatNM": {
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
    }}""")
    with open(os.path.join(resourcepath, 'nodefunctions.py'), 'w') as fp:
        fp.write("""
def phatNM(netapi, node, **_):
    pass""")

    micropsi.reload_native_modules()
    netapi = micropsi.nodenets[test_nodenet].netapi
    node = netapi.create_node("PhatNM", None, "phatty")
    node.take_slot_activation_snapshot()

    # test get_slot_activation
    data = node.get_slot_activation_array()
    assert len(data) == 1024 + 62 + 3  # fat_slots + gen/sub/sur
    new_activation = np.random.rand(768 + 13 + 3)  # fat gates + gen/sub/sur

    # test set_gate_activation
    node.set_gate_activation_array(new_activation)
    target = netapi.create_node("Register", None, "Target")
    for g in node.get_gate_types():
        netapi.link(node, g, target, 'gen')
    micropsi.step_nodenet(test_nodenet)
    assert target.activation > 0

    # test saving/loading data
    node.save_data(new_activation)
    assert np.all(node.load_data() == new_activation)

    # test persistency
    micropsi.save_nodenet(test_nodenet)
    micropsi.revert_nodenet(test_nodenet)
    netapi = micropsi.nodenets[test_nodenet].netapi
    node = netapi.get_node(node.uid)
    target = netapi.get_node(target.uid)
    assert np.all(node.load_data() == new_activation)

    # test setting gate details, get_gate_activation
    node.set_gatefunction_name("A_out0", "sigmoid")
    micropsi.step_nodenet(test_nodenet)
    act = node.get_gate_activation_array()
    assert act[3] == 0.5
    assert np.all(act[4:] == 0)

    # test delivery to frontend
    netapi.link(target, 'gen', node, 'A_in580')
    pipe = netapi.create_node("Pipe", None, "pipe")
    netapi.link_with_reciprocal(pipe, node, 'subsur')
    data = micropsi.nodenets[test_nodenet].get_nodes()
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
    result = micropsi.get_available_native_module_types(test_nodenet)['PhatNM']
    assert result['dimensionality']['gates']['A_out0'] == 768
    assert result['dimensionality']['gates']['B_out0'] == 13
    assert result['dimensionality']['slots']['A_in0'] == 1024
    assert result['dimensionality']['slots']['B_in0'] == 62
    assert result['gatetypes'] == ['gen', 'sub', 'sur', 'A_out0', 'B_out0']
    assert set(result['gate_defaults'].keys()) == set(result['gatetypes'])
    assert result['is_highdimensional']
