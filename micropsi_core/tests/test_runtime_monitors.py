#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""
Basic tests for monitor api
"""
from micropsi_core import runtime as micropsi


def test_add_gate_monitor(fixed_nodenet):
    uid = micropsi.add_gate_monitor(fixed_nodenet, 'A1', 'gen', sheaf='default')
    monitor = micropsi.nodenets[fixed_nodenet].get_monitor(uid)
    assert monitor.name == 'gate gen @ Node A1'
    assert monitor.node_uid == 'A1'
    assert monitor.target == 'gen'
    assert monitor.type == 'gate'
    assert monitor.sheaf == 'default'
    assert len(monitor.values) == 0
    micropsi.step_nodenet(fixed_nodenet)
    monitor = micropsi.nodenets[fixed_nodenet].get_monitor(uid)
    assert len(monitor.values) == 1


def test_add_slot_monitor(fixed_nodenet):
    uid = micropsi.add_slot_monitor(fixed_nodenet, 'A1', 'gen', name="FooBarMonitor")
    monitor = micropsi.nodenets[fixed_nodenet].get_monitor(uid)
    assert monitor.name == 'FooBarMonitor'
    assert monitor.node_uid == 'A1'
    assert monitor.target == 'gen'
    assert monitor.type == 'slot'
    assert len(monitor.values) == 0
    micropsi.step_nodenet(fixed_nodenet)
    monitor = micropsi.nodenets[fixed_nodenet].get_monitor(uid)
    assert len(monitor.values) == 1


def test_add_link_monitor(fixed_nodenet):
    uid = micropsi.add_link_monitor(fixed_nodenet, 'S', 'gen', 'B1', 'gen', 'weight', 'Testmonitor')
    monitor = micropsi.nodenets[fixed_nodenet].get_monitor(uid)
    assert monitor.name == 'Testmonitor'
    assert monitor.property == 'weight'
    assert monitor.source_node_uid == 'S'
    assert monitor.target_node_uid == 'B1'
    assert monitor.gate_type == 'gen'
    assert monitor.slot_type == 'gen'
    assert len(monitor.values) == 0
    micropsi.step_nodenet(fixed_nodenet)
    monitor = micropsi.nodenets[fixed_nodenet].get_monitor(uid)
    assert len(monitor.values) == 1


def test_add_custom_monitor(fixed_nodenet):
    code = """return len(netapi.get_nodes())"""
    uid = micropsi.add_custom_monitor(fixed_nodenet, code, 'Nodecount')
    monitor = micropsi.nodenets[fixed_nodenet].get_monitor(uid)
    assert monitor.name == 'Nodecount'
    assert monitor.compiled_function is not None
    assert monitor.function == code
    assert len(monitor.values) == 0
    micropsi.step_nodenet(fixed_nodenet)
    monitor = micropsi.nodenets[fixed_nodenet].get_monitor(uid)
    assert len(monitor.values) == 1
    assert monitor.values[1] == len(micropsi.nodenets[fixed_nodenet].netapi.get_nodes())


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
    uid = micropsi.add_gate_monitor(fixed_nodenet, 'A1', 'gen', name="Testmonitor")
    micropsi.step_nodenet(fixed_nodenet)
    data = micropsi.get_monitor_data(fixed_nodenet)
    assert data['current_step'] == 1
    assert data['monitors'][uid]['name'] == 'Testmonitor'
    values = data['monitors'][uid]['values']
    assert len(values.keys()) == 1
    assert [k for k in values.keys()] == [1]


def test_export_monitor_data(fixed_nodenet):
    uid1 = micropsi.add_gate_monitor(fixed_nodenet, 'A1', 'gen')
    uid2 = micropsi.add_gate_monitor(fixed_nodenet, 'B1', 'gen')
    micropsi.step_nodenet(fixed_nodenet)
    data = micropsi.export_monitor_data(fixed_nodenet)
    assert uid1 in data
    assert 'values' in data[uid1]
    assert uid2 in data


def test_export_monitor_data_with_id(fixed_nodenet):
    uid1 = micropsi.add_gate_monitor(fixed_nodenet, 'A1', 'gen', name="Testmonitor")
    micropsi.add_gate_monitor(fixed_nodenet, 'B1', 'gen')
    micropsi.step_nodenet(fixed_nodenet)
    data = micropsi.export_monitor_data(fixed_nodenet, monitor_uid=uid1)
    assert data['name'] == 'Testmonitor'
    assert 'values' in data


def test_clear_monitor(fixed_nodenet):
    uid = micropsi.add_gate_monitor(fixed_nodenet, 'A1', 'gen')
    micropsi.step_nodenet(fixed_nodenet)
    micropsi.clear_monitor(fixed_nodenet, uid)
    data = micropsi.get_monitor_data(fixed_nodenet)
    values = data['monitors'][uid]['values']
    assert len(values.keys()) == 0
