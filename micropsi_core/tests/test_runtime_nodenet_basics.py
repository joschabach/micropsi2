#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""

"""
import os
from micropsi_core import runtime
from micropsi_core import runtime as micropsi
import mock

__author__ = 'joscha'
__date__ = '29.10.12'


def test_new_nodenet(test_nodenet, resourcepath):
    success, nodenet_uid = micropsi.new_nodenet("Test_Nodenet", "Default", owner="tester")
    assert success
    assert nodenet_uid != test_nodenet
    assert micropsi.get_available_nodenets("tester")[nodenet_uid].name == "Test_Nodenet"
    n_path = os.path.join(resourcepath, runtime.NODENET_DIRECTORY, nodenet_uid + ".json")
    assert os.path.exists(n_path)

    # get_available_nodenets
    nodenets = micropsi.get_available_nodenets()
    mynets = micropsi.get_available_nodenets("tester")
    assert test_nodenet in nodenets
    assert nodenet_uid in nodenets
    assert nodenet_uid in mynets
    assert test_nodenet not in mynets

    # delete_nodenet
    micropsi.delete_nodenet(nodenet_uid)
    assert nodenet_uid not in micropsi.get_available_nodenets()
    assert not os.path.exists(n_path)


def test_user_prompt(fixed_nodenet):
    options = [{'key': 'foo_parameter', 'label': 'Please give value for "foo"', 'values':  [23, 42]}]
    micropsi.nodenets[fixed_nodenet].netapi.ask_user_for_parameter(
        micropsi.nodenets[fixed_nodenet].nodes['A1'],
        "foobar",
        options
    )
    data = micropsi.get_nodespace(fixed_nodenet, 'Root', -1)
    assert 'user_prompt' in data
    assert data['user_prompt']['msg'] == 'foobar'
    assert data['user_prompt']['node']['uid'] == 'A1'
    assert data['user_prompt']['options'] == options
    # response
    micropsi.user_prompt_response(fixed_nodenet, 'A1', {'foo_parameter': 42}, True)
    assert micropsi.nodenets[fixed_nodenet].nodes['A1'].parameters['foo_parameter'] == 42
    assert micropsi.nodenets[fixed_nodenet].is_active
    from micropsi_core.nodenet import nodefunctions
    nodefunc = mock.Mock()
    nodefunctions.concept = nodefunc
    micropsi.nodenets[fixed_nodenet].step()
    foo = micropsi.nodenets[fixed_nodenet].nodes['A1'].parameters.copy()
    foo.update({'foo_parameter': 42})
    assert nodefunc.called_with(micropsi.nodenets[fixed_nodenet].netapi, micropsi.nodenets[fixed_nodenet].nodes['A1'], foo)
    micropsi.nodenets[fixed_nodenet].nodes['A1'].clear_parameter('foo_parameter')
    assert 'foo_parameter' not in micropsi.nodenets[fixed_nodenet].nodes['A1'].parameters


def test_nodespace_removal(fixed_nodenet):
    res, uid = micropsi.add_node(fixed_nodenet, 'Nodespace', [100,100], nodespace="Root", name="testspace", uid='ns1')
    res, n1_uid = micropsi.add_node(fixed_nodenet, 'Register', [100,100], nodespace=uid, name="sub1", uid='sub1')
    res, n2_uid = micropsi.add_node(fixed_nodenet, 'Register', [100,200], nodespace=uid, name="sub2", uid='sub2')
    micropsi.add_link(fixed_nodenet, n1_uid, 'gen', n2_uid, 'gen', weight=1, certainty=1, uid='sub1-sub2')
    res, sub_uid = micropsi.add_node(fixed_nodenet, 'Nodespace', [100,100], nodespace=uid, name="subsubspace", uid='ns2')
    micropsi.delete_node(fixed_nodenet, uid)
    assert uid not in micropsi.nodenets[fixed_nodenet].nodespaces
    assert uid not in micropsi.nodenets[fixed_nodenet].state['nodespaces']
    assert n1_uid not in micropsi.nodenets[fixed_nodenet].nodes
    assert n1_uid not in micropsi.nodenets[fixed_nodenet].state['nodes']
    assert n2_uid not in micropsi.nodenets[fixed_nodenet].nodes
    assert n2_uid not in micropsi.nodenets[fixed_nodenet].state['nodes']
    assert 'sub1-sub2' not in micropsi.nodenets[fixed_nodenet].links
    assert 'sub1-sub2' not in micropsi.nodenets[fixed_nodenet].state['links']
    assert sub_uid not in micropsi.nodenets[fixed_nodenet].nodespaces
    assert sub_uid not in micropsi.nodenets[fixed_nodenet].state['nodespaces']


def test_clone_nodes_nolinks(fixed_nodenet):
    nodenet = micropsi.get_nodenet(fixed_nodenet)
    success, result = micropsi.clone_nodes(fixed_nodenet, ['A1', 'A2'], 'none')
    assert success
    assert result['nodes'][0]['uid'] in nodenet.nodes
    assert result['nodes'][0]['name'] == nodenet.nodes['A1'].name + '_copy'
    assert result['nodes'][0]['uid'] != 'A1'
    assert result['nodes'][0]['type'] == nodenet.nodes['A1'].type
    assert result['nodes'][0]['parameters'] == nodenet.nodes['A1'].parameters
    assert result['nodes'][0]['position'][0] == nodenet.nodes['A1'].position[0] + 50
    assert result['nodes'][0]['position'][1] == nodenet.nodes['A1'].position[1] + 50
    assert result['nodes'][1]['uid'] in nodenet.nodes
    assert result['nodes'][1]['name'] == nodenet.nodes['A2'].name + '_copy'
    assert result['nodes'][1]['uid'] != 'A2'
    assert len(result['nodes']) == 2
    assert len(result['links']) == 0


def test_clone_nodes_all_links(fixed_nodenet):
    nodenet = micropsi.get_nodenet(fixed_nodenet)
    success, result = micropsi.clone_nodes(fixed_nodenet, ['A1', 'A2'], 'all')
    assert success
    assert len(result['nodes']) == 2
    assert len(result['links']) == 2

    a1_copy = nodenet.nodes[result['nodes'][0]['uid']]
    a2_copy = nodenet.nodes[result['nodes'][1]['uid']]
    l1_uid = [uid for uid in a1_copy.gates['por'].outgoing.keys()][0]
    l2_uid = [uid for uid in a1_copy.slots['gen'].incoming.keys()][0]

    assert nodenet.links[l1_uid].source_node.uid == a1_copy.uid
    assert nodenet.links[l1_uid].target_node.uid == a2_copy.uid
    assert nodenet.links[l1_uid].source_gate.type == 'por'
    assert nodenet.links[l1_uid].target_slot.type == 'gen'

    assert l1_uid in [l['uid'] for l in result['links']]

    assert nodenet.links[l2_uid].source_node.uid == 'S'
    assert nodenet.links[l2_uid].target_node.uid == a1_copy.uid
    assert nodenet.links[l2_uid].source_gate.type == 'gen'
    assert nodenet.links[l2_uid].target_slot.type == 'gen'

    assert l2_uid in [l['uid'] for l in result['links']]


def test_clone_nodes_internal_links(fixed_nodenet):
    nodenet = micropsi.get_nodenet(fixed_nodenet)
    success, result = micropsi.clone_nodes(fixed_nodenet, ['A1', 'A2'], 'internal')
    assert success
    assert len(result['nodes']) == 2
    assert len(result['links']) == 1

    a1_copy = nodenet.nodes[result['nodes'][0]['uid']]
    a2_copy = nodenet.nodes[result['nodes'][1]['uid']]
    l1_uid = result['links'][0]['uid']

    assert nodenet.links[l1_uid].source_node.uid == a1_copy.uid
    assert nodenet.links[l1_uid].target_node.uid == a2_copy.uid
    assert nodenet.links[l1_uid].source_gate.type == 'por'
    assert nodenet.links[l1_uid].target_slot.type == 'gen'


def test_clone_nodes_to_new_nodespace(fixed_nodenet):
    nodenet = micropsi.get_nodenet(fixed_nodenet)

    micropsi.add_node(fixed_nodenet, 'Nodespace', [100, 100], nodespace="Root", name="testspace", uid='ns1')

    success, result = micropsi.clone_nodes(fixed_nodenet, ['A1', 'A2'], 'internal', nodespace='ns1')

    assert success
    assert len(result['nodes']) == 2
    assert len(result['links']) == 1

    a1_copy = nodenet.nodes[result['nodes'][0]['uid']]
    a2_copy = nodenet.nodes[result['nodes'][1]['uid']]

    assert a1_copy.parent_nodespace == 'ns1'
    assert a2_copy.parent_nodespace == 'ns1'

"""
def test_set_nodenet_properties(micropsi, test_nodenet):
    assert 0

def test_init_runners(micropsi, test_nodenet):
    assert 0

def test_nodenetrunner(micropsi, test_nodenet):
    assert 0

def test__get_world_uid_for_nodenet_uid(micropsi, test_nodenet):
    assert 0

def test_unload_nodenet(micropsi, test_nodenet):
    assert 0

def test_get_nodenet_area(micropsi, test_nodenet):
    assert 0

def test_start_nodenetrunner(micropsi, test_nodenet):
    assert 0

def test_set_nodenetrunner_timestep(micropsi, test_nodenet):
    assert 0

def test_get_nodenetrunner_timestep(micropsi, test_nodenet):
    assert 0

def test_get_is_nodenet_running(micropsi, test_nodenet):
    assert 0

def test_stop_nodenetrunner(micropsi, test_nodenet):
    assert 0

def test_step_nodenet(micropsi, test_nodenet):
    assert 0

def test_revert_nodenet(micropsi, test_nodenet):
    assert 0

def test_export_nodenet(micropsi, test_nodenet):
    assert 0

def test_import_nodenet(micropsi, test_nodenet):
    assert 0

def test_merge_nodenet(micropsi, test_nodenet):
    assert 0

def test_add_gate_monitor(micropsi, test_nodenet):
    assert 0

def test_add_slot_monitor(micropsi, test_nodenet):
    assert 0

def test_remove_monitor(micropsi, test_nodenet):
    assert 0

def test_clear_monitor(micropsi, test_nodenet):
    assert 0

def test_export_monitor_data(micropsi, test_nodenet):
    assert 0

def test_get_monitor_data(micropsi, test_nodenet):
    assert 0
"""