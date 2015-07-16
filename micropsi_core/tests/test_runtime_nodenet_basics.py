#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""

"""
import os
from micropsi_core import runtime
from micropsi_core import runtime as micropsi
import mock
import pytest

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
    assert data['nodes']['n0005']['gate_parameters'] == {}
    micropsi.set_gate_parameters(fixed_nodenet, 'n0005', 'gen', {'threshold': 1})
    data = micropsi.nodenets[fixed_nodenet].data
    assert data['nodes']['n0005']['gate_parameters'] == {'gen': {'threshold': 1}}
    defaults = Nodetype.GATE_DEFAULTS.copy()
    defaults.update({'threshold': 1})
    data = micropsi.nodenets[fixed_nodenet].get_node('n0005').data['gate_parameters']
    assert data == {'gen': {'threshold': 1}}


def test_user_prompt(fixed_nodenet, nodetype_def, nodefunc_def):
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
    res, uid = micropsi.add_node(fixed_nodenet, "Testnode", [10, 10], name="Test")
    nativemodule = micropsi.nodenets[fixed_nodenet].get_node(uid)

    options = [{'key': 'foo_parameter', 'label': 'Please give value for "foo"', 'values': [23, 42]}]
    micropsi.nodenets[fixed_nodenet].netapi.ask_user_for_parameter(
        nativemodule,
        "foobar",
        options
    )
    data = micropsi.get_nodenet_data(fixed_nodenet, 'Root')
    assert 'user_prompt' in data
    assert data['user_prompt']['msg'] == 'foobar'
    assert data['user_prompt']['node']['uid'] == uid
    assert data['user_prompt']['options'] == options
    # response
    micropsi.user_prompt_response(fixed_nodenet, uid, {'foo_parameter': 42}, True)
    assert micropsi.nodenets[fixed_nodenet].get_node(uid).get_parameter('foo_parameter') == 42
    assert micropsi.nodenets[fixed_nodenet].is_active
    from micropsi_core.nodenet import nodefunctions
    tmp = nodefunctions.concept
    nodefunc = mock.Mock()
    nodefunctions.concept = nodefunc
    micropsi.nodenets[fixed_nodenet].step()
    foo = micropsi.nodenets[fixed_nodenet].get_node('n0001').clone_parameters()
    foo.update({'foo_parameter': 42})
    assert nodefunc.called_with(micropsi.nodenets[fixed_nodenet].netapi, micropsi.nodenets[fixed_nodenet].get_node('n0001'), foo)
    micropsi.nodenets[fixed_nodenet].get_node('n0001').clear_parameter('foo_parameter')
    assert micropsi.nodenets[fixed_nodenet].get_node('n0001').get_parameter('foo_parameter') is None
    nodefunctions.concept = tmp


def test_nodespace_removal(fixed_nodenet):
    res, uid = micropsi.add_nodespace(fixed_nodenet, [100, 100], nodespace=None, name="testspace")
    res, n1_uid = micropsi.add_node(fixed_nodenet, 'Register', [100, 100], nodespace=uid, name="sub1")
    res, n2_uid = micropsi.add_node(fixed_nodenet, 'Register', [100, 200], nodespace=uid, name="sub2")
    micropsi.add_link(fixed_nodenet, n1_uid, 'gen', n2_uid, 'gen', weight=1, certainty=1)
    res, sub_uid = micropsi.add_nodespace(fixed_nodenet, [100, 100], nodespace=uid, name="subsubspace")
    micropsi.delete_nodespace(fixed_nodenet, uid)
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
    success, result = micropsi.clone_nodes(fixed_nodenet, ['n0001', 'n0002'], 'none', offset=[10, 20])
    assert success
    if result['nodes'][0]['name'] == 'A1_copy':
        a1_copy = result['nodes'][0]
        a2_copy = result['nodes'][1]
    else:
        a1_copy = result['nodes'][1]
        a2_copy = result['nodes'][0]

    assert nodenet.is_node(a1_copy['uid'])
    assert a1_copy['uid'] != 'n0001'
    assert a1_copy['type'] == nodenet.get_node('n0001').type
    assert a1_copy['parameters'] == nodenet.get_node('n0001').clone_parameters()
    assert a1_copy['position'][0] == nodenet.get_node('n0001').position[0] + 10
    assert a1_copy['position'][1] == nodenet.get_node('n0001').position[1] + 20
    assert nodenet.is_node(a2_copy['uid'])
    assert a2_copy['name'] == nodenet.get_node('n0002').name + '_copy'
    assert a2_copy['uid'] != 'n0002'
    assert len(result['nodes']) == 2
    assert len(result['links']) == 0


def test_clone_nodes_all_links(fixed_nodenet):
    nodenet = micropsi.get_nodenet(fixed_nodenet)
    success, result = micropsi.clone_nodes(fixed_nodenet, ['n0001', 'n0002'], 'all')
    assert success
    assert len(result['nodes']) == 2
    assert len(result['links']) == 2

    if result['nodes'][0]['name'] == 'A1_copy':
        a1_copy = result['nodes'][0]
        a2_copy = result['nodes'][1]
    else:
        a1_copy = result['nodes'][1]
        a2_copy = result['nodes'][0]

    sensor = nodenet.get_node('n0005')
    a1_copy = nodenet.get_node(a1_copy['uid'])
    a2_copy = nodenet.get_node(a2_copy['uid'])
    l1_uid = list(a1_copy.get_gate('por').get_links())[0].uid
    l2_uid = list(a1_copy.get_slot('gen').get_links())[0].uid

    links = a1_copy.get_associated_links()
    link = None
    for candidate in links:
        if candidate.source_node.uid == a1_copy.uid and \
                candidate.target_node.uid == a2_copy.uid and \
                candidate.source_gate.type == 'por' and \
                candidate.target_slot.type == 'gen':
            link = candidate
    assert link is not None

    assert l1_uid in [l['uid'] for l in result['links']]

    links = sensor.get_associated_links()
    link = None
    for candidate in links:
        if candidate.source_node.uid == sensor.uid and \
                candidate.target_node.uid == a1_copy.uid and \
                candidate.source_gate.type == 'gen' and \
                candidate.target_slot.type == 'gen':
            link = candidate
    assert link is not None

    assert l2_uid in [l['uid'] for l in result['links']]


def test_clone_nodes_internal_links(fixed_nodenet):
    nodenet = micropsi.get_nodenet(fixed_nodenet)
    success, result = micropsi.clone_nodes(fixed_nodenet, ['n0001', 'n0002'], 'internal')
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
        if candidate.source_node.uid == a1_copy.uid and \
                candidate.target_node.uid == a2_copy.uid and \
                candidate.source_gate.type == 'por' and \
                candidate.target_slot.type == 'gen':
            link = candidate
    assert link is not None


def test_clone_nodes_to_new_nodespace(fixed_nodenet):
    nodenet = micropsi.get_nodenet(fixed_nodenet)

    res, testspace_uid = micropsi.add_nodespace(fixed_nodenet, [100, 100], nodespace=None, name="testspace")

    success, result = micropsi.clone_nodes(fixed_nodenet, ['n0001', 'n0002'], 'internal', nodespace=testspace_uid)

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
    micropsi.set_gate_parameters(fixed_nodenet, 'n0001', 'gen', {'maximum': 0.1})
    success, result = micropsi.clone_nodes(fixed_nodenet, ['n0001'], 'internal')
    assert success
    copy = nodenet.get_node(result['nodes'][0]['uid'])
    assert round(copy.get_gate_parameters()['gen']['maximum'], 2) == 0.1


def test_modulators(fixed_nodenet):
    nodenet = micropsi.get_nodenet(fixed_nodenet)

    nodenet.netapi.change_modulator("test_modulator", 0.42)
    assert nodenet.netapi.get_modulator("test_modulator") == 0.42

    nodenet.set_modulator("test_modulator", -1)
    assert nodenet.netapi.get_modulator("test_modulator") == -1


def test_node_parameters(fixed_nodenet, nodetype_def, nodefunc_def):
    with open(nodetype_def, 'w') as fp:
        fp.write('{"Testnode": {\
            "name": "Testnode",\
            "slottypes": ["gen", "foo", "bar"],\
            "gatetypes": ["gen", "foo", "bar"],\
            "nodefunction_name": "testnodefunc",\
            "parameters": ["linktype", "threshold", "protocol_mode"],\
            "parameter_values": {\
                "linktype": ["catexp", "subsur"],\
                "protocol_mode": ["all_active", "most_active_one"]\
            },\
            "parameter_defaults": {\
                "linktype": "catexp",\
                "protocol_mode": "all_active"\
            }}\
        }')
    with open(nodefunc_def, 'w') as fp:
        fp.write("def testnodefunc(netapi, node=None, **prams):\r\n    return 17")

    assert micropsi.reload_native_modules()
    res, uid = micropsi.add_node(fixed_nodenet, "Testnode", [10, 10], name="Test", parameters={"linktype": "catexp", "threshold": "", "protocol_mode": "all_active"})
    # nativemodule = micropsi.nodenets[fixed_nodenet].get_node(uid)
    assert micropsi.save_nodenet(fixed_nodenet)


def test_multiple_nodenet_interference(engine, nodetype_def, nodefunc_def):

    with open(nodetype_def, 'w') as fp:
        fp.write('{"Testnode": {\
            "name": "Testnode",\
            "slottypes": ["gen", "foo", "bar"],\
            "gatetypes": ["gen", "foo", "bar"],\
            "nodefunction_name": "testnodefunc"\
        }}')
    with open(nodefunc_def, 'w') as fp:
        fp.write("def testnodefunc(netapi, node=None, **prams):\r\n    node.get_gate('gen').gate_function(17)")

    micropsi.reload_native_modules()

    result, n1_uid = micropsi.new_nodenet('Net1', engine=engine, owner='Pytest User')
    result, n2_uid = micropsi.new_nodenet('Net2', engine=engine, owner='Pytest User')

    n1 = micropsi.nodenets[n1_uid]
    n2 = micropsi.nodenets[n2_uid]

    nativemodule = n1.netapi.create_node("Testnode", None, "Testnode")
    register1 = n1.netapi.create_node("Register", None, "Register1")
    n1.netapi.link(nativemodule, 'gen', register1, 'gen', weight=1.2)

    source2 = n2.netapi.create_node("Register", None, "Source2")
    register2 = n2.netapi.create_node("Register", None, "Register2")
    n2.netapi.link(source2, 'gen', source2, 'gen')
    n2.netapi.link(source2, 'gen', register2, 'gen', weight=0.9)
    source2.activation = 0.7

    micropsi.step_nodenet(n2.uid)

    assert n1.current_step == 0
    assert register1.activation == 0
    assert register1.name == "Register1"
    assert nativemodule.name == "Testnode"
    assert round(register1.get_slot('gen').get_links()[0].weight, 2) == 1.2
    assert register1.get_slot('gen').get_links()[0].source_node.name == 'Testnode'
    assert n1.get_node(register1.uid).name == "Register1"

    assert n2.current_step == 1
    assert round(source2.activation, 2) == 0.7
    assert round(register2.activation, 2) == 0.63
    assert register2.name == "Register2"
    assert source2.name == "Source2"
    assert round(register2.get_slot('gen').get_links()[0].weight, 2) == 0.9
    assert register2.get_slot('gen').get_links()[0].source_node.name == 'Source2'
    assert n2.get_node(register2.uid).name == "Register2"
