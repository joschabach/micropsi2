#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""
Basic tests for monitor api
"""
from micropsi_core import runtime as micropsi


def test_add_gate_monitor(fixed_nodenet):
    data = micropsi.add_gate_monitor(fixed_nodenet, 'A1', 'gen')
    assert data['uid'] is not None
    assert data['node_name'] == 'A1'
    assert data['node_uid'] == 'A1'
    assert data['target'] == 'gen'
    assert data['type'] == 'gate'
    assert data['uid'] in micropsi.nodenets[fixed_nodenet].monitors


def test_add_slot_monitor(fixed_nodenet):
    data = micropsi.add_slot_monitor(fixed_nodenet, 'A1', 'gen')
    assert data['uid'] is not None
    assert data['node_name'] == 'A1'
    assert data['node_uid'] == 'A1'
    assert data['target'] == 'gen'
    assert data['type'] == 'slot'
    assert data['uid'] in micropsi.nodenets[fixed_nodenet].monitors


def test_remove_monitor(fixed_nodenet):
    data = micropsi.add_slot_monitor(fixed_nodenet, 'A1', 'gen')
    assert data['uid'] in micropsi.nodenets[fixed_nodenet].monitors
    micropsi.remove_monitor(fixed_nodenet, data['uid'])
    assert data['uid'] not in micropsi.nodenets[fixed_nodenet].monitors


def test_get_monitor_data(fixed_nodenet):
    monitor = micropsi.add_gate_monitor(fixed_nodenet, 'A1', 'gen')
    micropsi.step_nodenet(fixed_nodenet)
    data = micropsi.get_monitor_data(fixed_nodenet)
    assert data['current_step'] == 1
    assert data['monitors'][monitor['uid']]['node_name'] == 'A1'
    values = data['monitors'][monitor['uid']]['values']
    assert len([k for k in values.keys()]) == 1


def test_export_monitor_data(fixed_nodenet):
    monitor1 = micropsi.add_gate_monitor(fixed_nodenet, 'A1', 'gen')
    monitor2 = micropsi.add_gate_monitor(fixed_nodenet, 'B1', 'gen')
    micropsi.step_nodenet(fixed_nodenet)
    data = micropsi.export_monitor_data(fixed_nodenet)
    assert monitor1['uid'] in data
    assert 'values' in data[monitor1['uid']]
    assert monitor2['uid'] in data


def test_export_monitor_data_with_id(fixed_nodenet):
    monitor1 = micropsi.add_gate_monitor(fixed_nodenet, 'A1', 'gen')
    micropsi.add_gate_monitor(fixed_nodenet, 'B1', 'gen')
    micropsi.step_nodenet(fixed_nodenet)
    data = micropsi.export_monitor_data(fixed_nodenet, monitor_uid=monitor1['uid'])
    assert data['node_name'] == 'A1'
    assert 'values' in data


def test_clear_monitor(fixed_nodenet):
    monitor = micropsi.add_gate_monitor(fixed_nodenet, 'A1', 'gen')
    micropsi.step_nodenet(fixed_nodenet)
    micropsi.clear_monitor(fixed_nodenet, monitor['uid'])
    data = micropsi.get_monitor_data(fixed_nodenet)
    values = data['monitors'][monitor['uid']]['values']
    assert len([k for k in values.keys()]) == 0
