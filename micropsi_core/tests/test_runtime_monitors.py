#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""
Basic tests for monitor api
"""
from micropsi_core import runtime as micropsi


def test_add_gate_monitor(fixed_nodenet):
    uid = micropsi.add_gate_monitor(fixed_nodenet, 'A1', 'gen')
    monitor = micropsi.nodenets[fixed_nodenet].get_monitor(uid)
    assert monitor.node_name == 'A1'
    assert monitor.node_uid == 'A1'
    assert monitor.target == 'gen'
    assert monitor.type == 'gate'


def test_add_slot_monitor(fixed_nodenet):
    uid = micropsi.add_slot_monitor(fixed_nodenet, 'A1', 'gen')
    monitor = micropsi.nodenets[fixed_nodenet].get_monitor(uid)
    assert monitor.node_name == 'A1'
    assert monitor.node_uid == 'A1'
    assert monitor.target == 'gen'
    assert monitor.type == 'slot'


def test_remove_monitor(fixed_nodenet):
    uid = micropsi.add_slot_monitor(fixed_nodenet, 'A1', 'gen')
    assert micropsi.nodenets[fixed_nodenet].get_monitor(uid) is not None
    micropsi.remove_monitor(fixed_nodenet, uid)
    gone = False
    try:
        micropsi.nodenets[fixed_nodenet].get_monitor(uid)
    except KeyError:
        gone = True
    assert gone
    

def test_get_monitor_data(fixed_nodenet):
    uid = micropsi.add_gate_monitor(fixed_nodenet, 'A1', 'gen')
    micropsi.step_nodenet(fixed_nodenet)
    data = micropsi.get_monitor_data(fixed_nodenet)
    assert data['current_step'] == 1
    assert data['monitors'][uid]['node_name'] == 'A1'
    values = data['monitors'][uid]['values']
    assert len(values.keys()) == 1


def test_export_monitor_data(fixed_nodenet):
    uid1 = micropsi.add_gate_monitor(fixed_nodenet, 'A1', 'gen')
    uid2 = micropsi.add_gate_monitor(fixed_nodenet, 'B1', 'gen')
    micropsi.step_nodenet(fixed_nodenet)
    data = micropsi.export_monitor_data(fixed_nodenet)
    assert uid1 in data
    assert 'values' in data[uid1]
    assert uid2 in data


def test_export_monitor_data_with_id(fixed_nodenet):
    uid1 = micropsi.add_gate_monitor(fixed_nodenet, 'A1', 'gen')
    micropsi.add_gate_monitor(fixed_nodenet, 'B1', 'gen')
    micropsi.step_nodenet(fixed_nodenet)
    data = micropsi.export_monitor_data(fixed_nodenet, monitor_uid=uid1)
    assert data['node_name'] == 'A1'
    assert 'values' in data


def test_clear_monitor(fixed_nodenet):
    uid = micropsi.add_gate_monitor(fixed_nodenet, 'A1', 'gen')
    micropsi.step_nodenet(fixed_nodenet)
    micropsi.clear_monitor(fixed_nodenet, uid)
    data = micropsi.get_monitor_data(fixed_nodenet)
    values = data['monitors'][uid]['values']
    assert len(values.keys()) == 0
