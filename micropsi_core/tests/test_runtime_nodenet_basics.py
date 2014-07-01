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
    assert micropsi.nodenets[fixed_nodenet].nodes['A1'].user_feedback['foo_parameter'] == 42
    assert micropsi.nodenets[fixed_nodenet].is_active
    from micropsi_core.nodenet import nodefunctions
    nodefunc = mock.Mock()
    nodefunctions.concept = nodefunc
    micropsi.nodenets[fixed_nodenet].step()
    foo = micropsi.nodenets[fixed_nodenet].nodes['A1'].parameters.update({'foo_parameter': 42})
    assert nodefunc.called_with(micropsi.nodenets[fixed_nodenet].netapi, micropsi.nodenets[fixed_nodenet].nodes['A1'], foo)


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