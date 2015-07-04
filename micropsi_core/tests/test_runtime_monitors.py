#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""
Basic tests for monitor api
"""
import pytest
from micropsi_core import runtime as micropsi


def test_add_gate_monitor(fixed_nodenet):
    uid = micropsi.add_gate_monitor(fixed_nodenet, 'n0001', 'gen', sheaf='default')
    monitor = micropsi.nodenets[fixed_nodenet].get_monitor(uid)
    assert monitor.name == 'gate gen @ Node A1'
    assert monitor.node_uid == 'n0001'
    assert monitor.target == 'gen'
    assert monitor.type == 'gate'
    assert monitor.sheaf == 'default'
    assert monitor.color.startswith('#')
    assert len(monitor.values) == 0
    micropsi.step_nodenet(fixed_nodenet)
    monitor = micropsi.nodenets[fixed_nodenet].get_monitor(uid)
    assert len(monitor.values) == 1


@pytest.mark.engine("dict_engine")
def test_add_slot_monitor(fixed_nodenet):
    uid = micropsi.add_slot_monitor(fixed_nodenet, 'n0001', 'gen', name="FooBarMonitor", color="#112233")
    monitor = micropsi.nodenets[fixed_nodenet].get_monitor(uid)
    assert monitor.name == 'FooBarMonitor'
    assert monitor.node_uid == 'n0001'
    assert monitor.target == 'gen'
    assert monitor.type == 'slot'
    assert monitor.color == '#112233'
    assert len(monitor.values) == 0
    micropsi.step_nodenet(fixed_nodenet)
    monitor = micropsi.nodenets[fixed_nodenet].get_monitor(uid)
    assert len(monitor.values) == 1


def test_add_link_monitor(fixed_nodenet):
    uid = micropsi.add_link_monitor(fixed_nodenet, 'n0005', 'gen', 'n0003', 'gen', 'weight', 'Testmonitor', color="#112233")
    monitor = micropsi.nodenets[fixed_nodenet].get_monitor(uid)
    assert monitor.name == 'Testmonitor'
    assert monitor.property == 'weight'
    assert monitor.source_node_uid == 'n0005'
    assert monitor.target_node_uid == 'n0003'
    assert monitor.gate_type == 'gen'
    assert monitor.slot_type == 'gen'
    assert monitor.color == "#112233"
    assert len(monitor.values) == 0
    micropsi.step_nodenet(fixed_nodenet)
    monitor = micropsi.nodenets[fixed_nodenet].get_monitor(uid)
    assert round(monitor.values[1], 2) == 1
    micropsi.nodenets[fixed_nodenet].set_link_weight('n0005', 'gen', 'n0003', 'gen', weight=0.7)
    micropsi.step_nodenet(fixed_nodenet)
    monitor = micropsi.nodenets[fixed_nodenet].get_monitor(uid)
    assert len(monitor.values) == 2
    assert round(monitor.values[2], 2) == 0.7


def test_add_modulator_monitor(fixed_nodenet):
    uid = micropsi.add_modulator_monitor(fixed_nodenet, 'base_test', 'Testmonitor', color="#112233")
    monitor = micropsi.nodenets[fixed_nodenet].get_monitor(uid)
    assert monitor.name == 'Testmonitor'
    assert monitor.modulator == 'base_test'
    assert monitor.color == "#112233"
    assert len(monitor.values) == 0
    micropsi.step_nodenet(fixed_nodenet)
    monitor = micropsi.nodenets[fixed_nodenet].get_monitor(uid)
    assert monitor.values[1] == 1
    micropsi.nodenets[fixed_nodenet].set_modulator('base_test', 0.7)
    micropsi.step_nodenet(fixed_nodenet)
    monitor = micropsi.nodenets[fixed_nodenet].get_monitor(uid)
    assert len(monitor.values) == 2
    assert monitor.values[2] == 0.7


def test_add_custom_monitor(fixed_nodenet):
    code = """return len(netapi.get_nodes())"""
    uid = micropsi.add_custom_monitor(fixed_nodenet, code, 'Nodecount', color="#112233")
    monitor = micropsi.nodenets[fixed_nodenet].get_monitor(uid)
    assert monitor.name == 'Nodecount'
    assert monitor.compiled_function is not None
    assert monitor.function == code
    assert monitor.color == "#112233"
    assert len(monitor.values) == 0
    micropsi.step_nodenet(fixed_nodenet)
    monitor = micropsi.nodenets[fixed_nodenet].get_monitor(uid)
    assert len(monitor.values) == 1
    assert monitor.values[1] == len(micropsi.nodenets[fixed_nodenet].netapi.get_nodes())


def test_remove_monitor(fixed_nodenet):
    uid = micropsi.add_slot_monitor(fixed_nodenet, 'n0001', 'gen')
    assert micropsi.nodenets[fixed_nodenet].get_monitor(uid) is not None
    micropsi.remove_monitor(fixed_nodenet, uid)
    gone = False
    try:
        micropsi.nodenets[fixed_nodenet].get_monitor(uid)
    except KeyError:
        gone = True
    assert gone


def test_remove_monitored_node(fixed_nodenet):
    uid = micropsi.add_gate_monitor(fixed_nodenet, 'n0001', 'gen', sheaf='default')
    micropsi.delete_node(fixed_nodenet, 'n0001')
    micropsi.step_nodenet(fixed_nodenet)
    monitor = micropsi.export_monitor_data(fixed_nodenet)
    assert monitor[uid]['values'][1] is None


def test_remove_monitored_link(fixed_nodenet):
    uid = micropsi.add_link_monitor(fixed_nodenet, 'n0005', 'gen', 'n0003', 'gen', 'weight', 'Testmonitor')
    micropsi.delete_link(fixed_nodenet, 'n0005', 'gen', 'n0003', 'gen')
    micropsi.step_nodenet(fixed_nodenet)
    monitor = micropsi.export_monitor_data(fixed_nodenet)
    assert monitor[uid]['values'][1] is None


def test_remove_monitored_link_via_delete_node(fixed_nodenet):
    uid = micropsi.add_link_monitor(fixed_nodenet, 'n0005', 'gen', 'n0003', 'gen', 'weight', 'Testmonitor')
    micropsi.delete_node(fixed_nodenet, 'n0005')
    micropsi.step_nodenet(fixed_nodenet)
    monitor = micropsi.export_monitor_data(fixed_nodenet)
    assert monitor[uid]['values'][1] is None


def test_get_monitor_data(fixed_nodenet):
    uid = micropsi.add_gate_monitor(fixed_nodenet, 'n0001', 'gen', name="Testmonitor")
    micropsi.step_nodenet(fixed_nodenet)
    data = micropsi.get_monitor_data(fixed_nodenet)
    assert data['current_step'] == 1
    assert data['monitors'][uid]['name'] == 'Testmonitor'
    values = data['monitors'][uid]['values']
    assert len(values.keys()) == 1
    assert [k for k in values.keys()] == [1]


def test_export_monitor_data(fixed_nodenet):
    uid1 = micropsi.add_gate_monitor(fixed_nodenet, 'n0001', 'gen')
    uid2 = micropsi.add_gate_monitor(fixed_nodenet, 'n0003', 'gen')
    micropsi.step_nodenet(fixed_nodenet)
    data = micropsi.export_monitor_data(fixed_nodenet)
    assert uid1 in data
    assert 'values' in data[uid1]
    assert uid2 in data


def test_export_monitor_data_with_id(fixed_nodenet):
    uid1 = micropsi.add_gate_monitor(fixed_nodenet, 'n0001', 'gen', name="Testmonitor")
    micropsi.add_gate_monitor(fixed_nodenet, 'n0003', 'gen')
    micropsi.step_nodenet(fixed_nodenet)
    data = micropsi.export_monitor_data(fixed_nodenet, monitor_uid=uid1)
    assert data['name'] == 'Testmonitor'
    assert 'values' in data


def test_clear_monitor(fixed_nodenet):
    uid = micropsi.add_gate_monitor(fixed_nodenet, 'n0001', 'gen')
    micropsi.step_nodenet(fixed_nodenet)
    micropsi.clear_monitor(fixed_nodenet, uid)
    data = micropsi.get_monitor_data(fixed_nodenet)
    values = data['monitors'][uid]['values']
    assert len(values.keys()) == 0
