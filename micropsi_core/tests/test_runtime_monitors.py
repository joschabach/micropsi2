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
    uid = micropsi.add_gate_monitor(fixed_nodenet, 'n0001', 'gen')
    assert micropsi.nodenets[fixed_nodenet].get_monitor(uid) is not None
    micropsi.remove_monitor(fixed_nodenet, uid)
    monitor = micropsi.nodenets[fixed_nodenet].get_monitor(uid)
    assert monitor is None


def test_remove_monitored_node(fixed_nodenet):
    nodenet = micropsi.nodenets[fixed_nodenet]
    uid = micropsi.add_gate_monitor(fixed_nodenet, 'n0001', 'gen', sheaf='default')
    micropsi.delete_nodes(fixed_nodenet, ['n0001'])
    micropsi.step_nodenet(fixed_nodenet)
    monitor = nodenet.get_monitor(uid)
    assert monitor.values[1] is None


def test_remove_monitored_link(fixed_nodenet):
    nodenet = micropsi.nodenets[fixed_nodenet]
    uid = micropsi.add_link_monitor(fixed_nodenet, 'n0005', 'gen', 'n0003', 'gen', 'weight', 'Testmonitor')
    micropsi.delete_link(fixed_nodenet, 'n0005', 'gen', 'n0003', 'gen')
    micropsi.step_nodenet(fixed_nodenet)
    monitor = nodenet.get_monitor(uid)
    assert monitor.values[1] is None


def test_remove_monitored_link_via_delete_node(fixed_nodenet):
    nodenet = micropsi.nodenets[fixed_nodenet]
    uid = micropsi.add_link_monitor(fixed_nodenet, 'n0005', 'gen', 'n0003', 'gen', 'weight', 'Testmonitor')
    micropsi.delete_nodes(fixed_nodenet, ['n0005'])
    micropsi.step_nodenet(fixed_nodenet)
    monitor = nodenet.get_monitor(uid)
    assert monitor.values[1] is None


def test_get_monitor_data(fixed_nodenet):
    uid = micropsi.add_gate_monitor(fixed_nodenet, 'n0001', 'gen', name="Testmonitor")
    micropsi.step_nodenet(fixed_nodenet)
    data = micropsi.get_monitor_data(fixed_nodenet)
    assert data['current_step'] == 1
    assert data['monitors'][uid]['name'] == 'Testmonitor'
    values = data['monitors'][uid]['values']
    assert len(values.keys()) == 1
    assert [k for k in values.keys()] == [1]


def test_clear_monitor(fixed_nodenet):
    uid = micropsi.add_gate_monitor(fixed_nodenet, 'n0001', 'gen')
    micropsi.step_nodenet(fixed_nodenet)
    micropsi.clear_monitor(fixed_nodenet, uid)
    data = micropsi.get_monitor_data(fixed_nodenet)
    values = data['monitors'][uid]['values']
    assert len(values.keys()) == 0


def test_get_partial_monitor_data(fixed_nodenet):
    uid = micropsi.add_gate_monitor(fixed_nodenet, 'n0001', 'gen')
    i = 0
    while i < 50:
        micropsi.step_nodenet(fixed_nodenet)
        i += 1
    nodenet = micropsi.nodenets[fixed_nodenet]
    assert nodenet.current_step == 50

    # get 10 items from [20 - 29]
    data = micropsi.get_monitor_data(fixed_nodenet, from_step=20, count=10)
    values = data['monitors'][uid]['values']
    assert len(values.keys()) == 10
    assert set(list(values.keys())) == set(range(20, 30))

    # get 10 newest values [41-50]
    data = micropsi.get_monitor_data(fixed_nodenet, count=10)
    values = data['monitors'][uid]['values']
    assert len(values.keys()) == 10
    assert set(list(values.keys())) == set(range(41, 51))

    # get 10 items, starting at 45 -- assert they are filled up to the left.
    data = micropsi.get_monitor_data(fixed_nodenet, from_step=40, count=15)
    values = data['monitors'][uid]['values']
    assert len(values.keys()) == 15
    assert set(list(values.keys())) == set(range(36, 51))

    # get all items, starting at 10
    data = micropsi.get_monitor_data(fixed_nodenet, from_step=10)
    values = data['monitors'][uid]['values']
    assert len(values.keys()) == 41
    assert set(list(values.keys())) == set(range(10, 51))


def test_add_group_monitor(test_nodenet):
    nodenet = micropsi.nodenets[test_nodenet]
    netapi = nodenet.netapi
    nodespace = netapi.get_nodespace(None)
    nodes = []
    for i in range(10):
        node = netapi.create_node('Register', None, "testnode_%d" % i)
        nodes.append(node)
        if i > 0:
            netapi.link(nodes[i - 1], 'gen', node, 'gen')
    source = netapi.create_node("Register", None, "Source")
    netapi.link(source, 'gen', source, 'gen')
    netapi.link(source, 'gen', nodes[0], 'gen')
    source.activation = 1
    monitor_uid = netapi.add_group_monitor(nodespace.uid, 'testndoes', node_name_prefix='testnode', gate='gen', color='purple')
    for i in range(5):
        micropsi.step_nodenet(test_nodenet)
    data = nodenet.get_monitor(monitor_uid).get_data()
    assert set(data['values'][4][:4]) == {1.0}  # first 4 active
    assert set(data['values'][4][4:]) == {0.0}  # rest off
    micropsi.save_nodenet(test_nodenet)
    micropsi.revert_nodenet(test_nodenet)
    nodenet = micropsi.nodenets[test_nodenet]
    data2 = nodenet.get_monitor(monitor_uid).get_data()
    assert data2 == data
    micropsi.step_nodenet(test_nodenet)
    data3 = nodenet.get_monitor(monitor_uid).get_data()
    assert set(data3['values'][6][:6]) == {1.0}  # first 6 active
    assert set(data3['values'][6][6:]) == {0.0}  # rest off
