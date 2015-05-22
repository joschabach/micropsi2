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


def test_new_nodenet(test_nodenet, resourcepath, engine):
    success, nodenet_uid = micropsi.new_nodenet("Test_Nodenet", engine=engine, worldadapter="Default", owner="tester")
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


def test_nodenet_data_gate_parameters(fixed_nodenet):
    from micropsi_core.nodenet.node import Nodetype
    data = micropsi.nodenets[fixed_nodenet].data
    assert data['nodes']['n5']['gate_parameters'] == {}
    micropsi.set_gate_parameters(fixed_nodenet, 'n5', 'gen', {'threshold': 1})
    data = micropsi.nodenets[fixed_nodenet].data
    assert data['nodes']['n5']['gate_parameters'] == {'gen': {'threshold': 1}}
    defaults = Nodetype.GATE_DEFAULTS
    defaults.update({'threshold': 1})
    data = micropsi.nodenets[fixed_nodenet].get_node('n5').data['gate_parameters']
    assert data == {'gen': {'threshold': 1}}


def test_user_prompt(fixed_nodenet):
    options = [{'key': 'foo_parameter', 'label': 'Please give value for "foo"', 'values': [23, 42]}]
    micropsi.nodenets[fixed_nodenet].netapi.ask_user_for_parameter(
        micropsi.nodenets[fixed_nodenet].get_node('n1'),
        "foobar",
        options
    )
    data = micropsi.get_nodenet_data(fixed_nodenet, 'Root')
    assert 'user_prompt' in data
    assert data['user_prompt']['msg'] == 'foobar'
    assert data['user_prompt']['node']['uid'] == 'n1'
    assert data['user_prompt']['options'] == options
    # response
    micropsi.user_prompt_response(fixed_nodenet, 'n1', {'foo_parameter': 42}, True)
    assert micropsi.nodenets[fixed_nodenet].get_node('n1').get_parameter('foo_parameter') == 42
    assert micropsi.nodenets[fixed_nodenet].is_active
    from micropsi_core.nodenet import nodefunctions
    nodefunc = mock.Mock()
    nodefunctions.concept = nodefunc
    micropsi.nodenets[fixed_nodenet].step()
    foo = micropsi.nodenets[fixed_nodenet].get_node('n1').clone_parameters()
    foo.update({'foo_parameter': 42})
    assert nodefunc.called_with(micropsi.nodenets[fixed_nodenet].netapi, micropsi.nodenets[fixed_nodenet].get_node('n1'), foo)
    micropsi.nodenets[fixed_nodenet].get_node('n1').clear_parameter('foo_parameter')
    assert micropsi.nodenets[fixed_nodenet].get_node('n1').get_parameter('foo_parameter') is None


def test_nodespace_removal(fixed_nodenet):
    res, uid = micropsi.add_node(fixed_nodenet, 'Nodespace', [100, 100], nodespace=None, name="testspace")
    res, n1_uid = micropsi.add_node(fixed_nodenet, 'Register', [100, 100], nodespace=uid, name="sub1")
    res, n2_uid = micropsi.add_node(fixed_nodenet, 'Register', [100, 200], nodespace=uid, name="sub2")
    micropsi.add_link(fixed_nodenet, n1_uid, 'gen', n2_uid, 'gen', weight=1, certainty=1)
    res, sub_uid = micropsi.add_node(fixed_nodenet, 'Nodespace', [100, 100], nodespace=uid, name="subsubspace")
    micropsi.delete_node(fixed_nodenet, uid)
    # assert that the nodespace is gone
    assert not micropsi.nodenets[fixed_nodenet].is_nodespace(uid)
    assert uid not in micropsi.nodenets[fixed_nodenet].data['nodespaces']
    # assert that the nodes it contained are gone
    assert not micropsi.nodenets[fixed_nodenet].is_node(n1_uid)
    assert n1_uid not in micropsi.nodenets[fixed_nodenet].data['nodes']
    assert not micropsi.nodenets[fixed_nodenet].is_node(n2_uid)
    assert n2_uid not in micropsi.nodenets[fixed_nodenet].data['nodes']
    # assert that the links between the deleted nodes are gone
    linked_node_uids = []
    for uid, link in micropsi.nodenets[fixed_nodenet].data['links'].items():
        linked_node_uids.append(link['source_node_uid'])
        linked_node_uids.append(link['target_node_uid'])
    assert n1_uid not in linked_node_uids
    assert n2_uid not in linked_node_uids
    # assert that sub-nodespaces are gone as well
    assert not micropsi.nodenets[fixed_nodenet].is_nodespace(sub_uid)
    assert sub_uid not in micropsi.nodenets[fixed_nodenet].data['nodespaces']


def test_clone_nodes_nolinks(fixed_nodenet):
    nodenet = micropsi.get_nodenet(fixed_nodenet)
    success, result = micropsi.clone_nodes(fixed_nodenet, ['n1', 'n2'], 'none', offset=[10, 20])
    assert success
    if result['nodes'][0]['name'] == 'A1_copy':
        a1_copy = result['nodes'][0]
        a2_copy = result['nodes'][1]
    else:
        a1_copy = result['nodes'][1]
        a2_copy = result['nodes'][0]

    assert nodenet.is_node(a1_copy['uid'])
    assert a1_copy['uid'] != 'n1'
    assert a1_copy['type'] == nodenet.get_node('n1').type
    assert a1_copy['parameters'] == nodenet.get_node('n1').clone_parameters()
    assert a1_copy['position'][0] == nodenet.get_node('n1').position[0] + 10
    assert a1_copy['position'][1] == nodenet.get_node('n1').position[1] + 20
    assert nodenet.is_node(a2_copy['uid'])
    assert a2_copy['name'] == nodenet.get_node('n2').name + '_copy'
    assert a2_copy['uid'] != 'n2'
    assert len(result['nodes']) == 2
    assert len(result['links']) == 0


def test_clone_nodes_all_links(fixed_nodenet):
    nodenet = micropsi.get_nodenet(fixed_nodenet)
    success, result = micropsi.clone_nodes(fixed_nodenet, ['n1', 'n2'], 'all')
    assert success
    assert len(result['nodes']) == 2
    assert len(result['links']) == 2

    if result['nodes'][0]['name'] == 'A1_copy':
        a1_copy = result['nodes'][0]
        a2_copy = result['nodes'][1]
    else:
        a1_copy = result['nodes'][1]
        a2_copy = result['nodes'][0]

    sensor = nodenet.get_node('n5')
    a1_copy = nodenet.get_node(a1_copy['uid'])
    a2_copy = nodenet.get_node(a2_copy['uid'])
    l1_uid = list(a1_copy.get_gate('por').get_links())[0].uid
    l2_uid = list(a1_copy.get_slot('gen').get_links())[0].uid

    links = a1_copy.get_associated_links()
    link = None
    for candidate in links:
        if candidate.source_node == a1_copy and \
                candidate.target_node == a2_copy and \
                candidate.source_gate.type == 'por' and \
                candidate.target_slot.type == 'gen':
            link = candidate
    assert link is not None

    assert l1_uid in [l['uid'] for l in result['links']]

    links = sensor.get_associated_links()
    link = None
    for candidate in links:
        if candidate.source_node == sensor and \
                candidate.target_node == a1_copy and \
                candidate.source_gate.type == 'gen' and \
                candidate.target_slot.type == 'gen':
            link = candidate
    assert link is not None

    assert l2_uid in [l['uid'] for l in result['links']]


def test_clone_nodes_internal_links(fixed_nodenet):
    nodenet = micropsi.get_nodenet(fixed_nodenet)
    success, result = micropsi.clone_nodes(fixed_nodenet, ['n1', 'n2'], 'internal')
    assert success
    assert len(result['nodes']) == 2
    assert len(result['links']) == 1

    if result['nodes'][0]['name'] == 'A1_copy':
        a1_copy = result['nodes'][0]
        a2_copy = result['nodes'][1]
    else:
        a1_copy = result['nodes'][1]
        a2_copy = result['nodes'][0]

    a1_copy = nodenet.get_node(a1_copy['uid'])
    a2_copy = nodenet.get_node(a2_copy['uid'])
    l1_uid = result['links'][0]['uid']

    links = a1_copy.get_associated_links()
    link = None
    for candidate in links:
        if candidate.source_node == a1_copy and \
                candidate.target_node == a2_copy and \
                candidate.source_gate.type == 'por' and \
                candidate.target_slot.type == 'gen':
            link = candidate
    assert link is not None


def test_clone_nodes_to_new_nodespace(fixed_nodenet):
    nodenet = micropsi.get_nodenet(fixed_nodenet)

    res, testspace_uid = micropsi.add_node(fixed_nodenet, 'Nodespace', [100, 100], nodespace=None, name="testspace")

    success, result = micropsi.clone_nodes(fixed_nodenet, ['n1', 'n2'], 'internal', nodespace=testspace_uid)

    assert success
    assert len(result['nodes']) == 2
    assert len(result['links']) == 1

    if result['nodes'][0]['name'] == 'A1_copy':
        a1_copy = result['nodes'][0]
        a2_copy = result['nodes'][1]
    else:
        a1_copy = result['nodes'][1]
        a2_copy = result['nodes'][0]

    a1_copy = nodenet.get_node(a1_copy['uid'])
    a2_copy = nodenet.get_node(a2_copy['uid'])

    assert a1_copy.parent_nodespace == testspace_uid
    assert a2_copy.parent_nodespace == testspace_uid


def test_clone_nodes_copies_gate_params(fixed_nodenet):
    nodenet = micropsi.get_nodenet(fixed_nodenet)
    micropsi.set_gate_parameters(fixed_nodenet, 'n1', 'gen', {'decay': 0.1})
    success, result = micropsi.clone_nodes(fixed_nodenet, ['n1'], 'internal')
    assert success
    copy = nodenet.get_node(result['nodes'][0]['uid'])
    assert copy.get_gate_parameters()['gen']['decay'] == 0.1


def test_modulators(fixed_nodenet):
    nodenet = micropsi.get_nodenet(fixed_nodenet)

    nodenet.netapi.change_modulator("test_modulator", 0.42)
    assert nodenet.netapi.get_modulator("test_modulator") == 0.42

    nodenet.set_modulator("test_modulator", -1)
    assert nodenet.netapi.get_modulator("test_modulator") == -1
