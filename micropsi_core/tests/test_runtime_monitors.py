#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""
Basic tests for monitor api
"""
import pytest


def prepare(runtime, test_nodenet):
    net = runtime.nodenets[test_nodenet]
    netapi = net.netapi
    source = netapi.create_node("Neuron", None, "source")
    register = netapi.create_node("Neuron", None, "reg")
    netapi.link(source, 'gen', source, 'gen')
    netapi.link(source, 'gen', register, 'gen')
    return net, netapi, source, register


def test_add_gate_monitor(runtime, test_nodenet):
    net, netapi, source, _ = prepare(runtime, test_nodenet)
    uid = runtime.add_gate_monitor(test_nodenet, source.uid, 'gen')
    monitor = net.get_monitor(uid)
    assert monitor.name == 'gate gen @ Node source'
    assert monitor.node_uid == source.uid
    assert monitor.target == 'gen'
    assert monitor.type == 'gate'
    assert monitor.color.startswith('#')
    assert len(monitor.values) == 0
    runtime.step_nodenet(test_nodenet)
    monitor = net.get_monitor(uid)
    assert len(monitor.values) == 1


@pytest.mark.engine("dict_engine")
@pytest.mark.engine("numpy_engine")
def test_add_slot_monitor(runtime, test_nodenet):
    net, netapi, source, _ = prepare(runtime, test_nodenet)
    uid = runtime.add_slot_monitor(test_nodenet, source.uid, 'gen', name="FooBarMonitor", color="#112233")
    monitor = net.get_monitor(uid)
    assert monitor.name == 'FooBarMonitor'
    assert monitor.node_uid == source.uid
    assert monitor.target == 'gen'
    assert monitor.type == 'slot'
    assert monitor.color == '#112233'
    assert len(monitor.values) == 0
    runtime.step_nodenet(test_nodenet)
    monitor = net.get_monitor(uid)
    assert len(monitor.values) == 1


def test_add_link_monitor(runtime, test_nodenet):
    net, netapi, source, register = prepare(runtime, test_nodenet)
    uid = runtime.add_link_monitor(test_nodenet, source.uid, 'gen', register.uid, 'gen', 'Testmonitor', color="#112233")
    monitor = net.get_monitor(uid)
    assert monitor.name == 'Testmonitor'
    assert monitor.source_node_uid == source.uid
    assert monitor.target_node_uid == register.uid
    assert monitor.gate_type == 'gen'
    assert monitor.slot_type == 'gen'
    assert monitor.color == "#112233"
    assert len(monitor.values) == 0
    runtime.step_nodenet(test_nodenet)
    monitor = net.get_monitor(uid)
    assert round(monitor.values[1], 2) == 1
    net.set_link_weight(source.uid, 'gen', register.uid, 'gen', weight=0.7)
    runtime.step_nodenet(test_nodenet)
    monitor = net.get_monitor(uid)
    assert len(monitor.values) == 2
    assert round(monitor.values[2], 2) == 0.7


def test_add_modulator_monitor(runtime, test_nodenet):
    net, netapi, source, register = prepare(runtime, test_nodenet)
    uid = runtime.add_modulator_monitor(test_nodenet, 'base_test', 'Testmonitor', color="#112233")
    monitor = net.get_monitor(uid)
    assert monitor.name == 'Testmonitor'
    assert monitor.modulator == 'base_test'
    assert monitor.color == "#112233"
    assert len(monitor.values) == 0
    runtime.step_nodenet(test_nodenet)
    monitor = net.get_monitor(uid)
    assert monitor.values[1] == 1
    net.set_modulator('base_test', 0.7)
    runtime.step_nodenet(test_nodenet)
    monitor = net.get_monitor(uid)
    assert len(monitor.values) == 2
    assert monitor.values[2] == 0.7


def test_add_custom_monitor(runtime, test_nodenet):
    net, netapi, source, register = prepare(runtime, test_nodenet)
    code = """return len(netapi.get_nodes())"""
    uid = runtime.add_custom_monitor(test_nodenet, code, 'Nodecount', color="#112233")
    monitor = net.get_monitor(uid)
    assert monitor.name == 'Nodecount'
    assert monitor.compiled_function is not None
    assert monitor.function == code
    assert monitor.color == "#112233"
    assert len(monitor.values) == 0
    runtime.step_nodenet(test_nodenet)
    monitor = net.get_monitor(uid)
    assert len(monitor.values) == 1
    assert monitor.values[1] == len(net.netapi.get_nodes())


def test_remove_monitor(runtime, test_nodenet):
    net, netapi, source, register = prepare(runtime, test_nodenet)
    uid = runtime.add_gate_monitor(test_nodenet, source.uid, 'gen')
    assert net.get_monitor(uid) is not None
    runtime.remove_monitor(test_nodenet, uid)
    monitor = net.get_monitor(uid)
    assert monitor is None


def test_remove_monitored_node(runtime, test_nodenet):
    net, netapi, source, register = prepare(runtime, test_nodenet)
    nodenet = runtime.nodenets[test_nodenet]
    uid = runtime.add_gate_monitor(test_nodenet, source.uid, 'gen')
    runtime.delete_nodes(test_nodenet, [source.uid])
    runtime.step_nodenet(test_nodenet)
    monitor = nodenet.get_monitor(uid)
    assert monitor.values[1] is None


def test_remove_monitored_link(runtime, test_nodenet):
    net, netapi, source, register = prepare(runtime, test_nodenet)
    nodenet = runtime.nodenets[test_nodenet]
    uid = runtime.add_link_monitor(test_nodenet, source.uid, 'gen', register.uid, 'gen', 'Testmonitor')
    runtime.delete_link(test_nodenet, source.uid, 'gen', register.uid, 'gen')
    runtime.step_nodenet(test_nodenet)
    monitor = nodenet.get_monitor(uid)
    assert monitor.values[1] is None


def test_remove_monitored_link_via_delete_node(runtime, test_nodenet):
    net, netapi, source, register = prepare(runtime, test_nodenet)
    nodenet = runtime.nodenets[test_nodenet]
    uid = runtime.add_link_monitor(test_nodenet, source.uid, 'gen', register.uid, 'gen', 'Testmonitor')
    runtime.delete_nodes(test_nodenet, [register.uid])
    runtime.step_nodenet(test_nodenet)
    monitor = nodenet.get_monitor(uid)
    assert monitor.values[1] is None


def test_get_monitor_data(runtime, test_nodenet):
    net, netapi, source, register = prepare(runtime, test_nodenet)
    uid = runtime.add_gate_monitor(test_nodenet, source.uid, 'gen', name="Testmonitor")
    runtime.step_nodenet(test_nodenet)
    data = runtime.get_monitor_data(test_nodenet)
    assert data['current_step'] == 1
    assert data['monitors'][uid]['name'] == 'Testmonitor'
    values = data['monitors'][uid]['values']
    assert len(values.keys()) == 1
    assert [k for k in values.keys()] == [1]


def test_clear_monitor(runtime, test_nodenet):
    net, netapi, source, register = prepare(runtime, test_nodenet)
    uid = runtime.add_gate_monitor(test_nodenet, source.uid, 'gen')
    runtime.step_nodenet(test_nodenet)
    runtime.clear_monitor(test_nodenet, uid)
    data = runtime.get_monitor_data(test_nodenet)
    values = data['monitors'][uid]['values']
    assert len(values.keys()) == 0


def test_get_partial_monitor_data(runtime, test_nodenet):
    net, netapi, source, register = prepare(runtime, test_nodenet)
    uid = runtime.add_gate_monitor(test_nodenet, source.uid, 'gen')
    i = 0
    while i < 50:
        runtime.step_nodenet(test_nodenet)
        i += 1
    nodenet = runtime.nodenets[test_nodenet]
    assert nodenet.current_step == 50

    # get 10 items from [20 - 29]
    data = runtime.get_monitor_data(test_nodenet, from_step=20, count=10)
    values = data['monitors'][uid]['values']
    assert len(values.keys()) == 10
    assert set(list(values.keys())) == set(range(20, 30))

    # get 10 newest values [41-50]
    data = runtime.get_monitor_data(test_nodenet, count=10)
    values = data['monitors'][uid]['values']
    assert len(values.keys()) == 10
    assert set(list(values.keys())) == set(range(41, 51))

    # get 10 items, starting at 45 -- assert they are filled up to the left.
    data = runtime.get_monitor_data(test_nodenet, from_step=40, count=15)
    values = data['monitors'][uid]['values']
    assert len(values.keys()) == 15
    assert set(list(values.keys())) == set(range(36, 51))

    # get all items, starting at 10
    data = runtime.get_monitor_data(test_nodenet, from_step=10)
    values = data['monitors'][uid]['values']
    assert len(values.keys()) == 41
    assert set(list(values.keys())) == set(range(10, 51))


def test_add_group_monitor(runtime, test_nodenet):
    from random import shuffle
    nodenet = runtime.nodenets[test_nodenet]
    netapi = nodenet.netapi
    nodespace = netapi.get_nodespace(None)
    nodes = [None] * 10
    num = list(range(10))
    shuffle(num)
    for i in num:
        node = netapi.create_node('Neuron', None, "testnode_%d" % i)
        nodes[i] = node
    for i in num:
        if i > 0:
            netapi.link(nodes[i - 1], 'gen', nodes[i], 'gen')
    source = netapi.create_node("Neuron", None, "Source")
    netapi.link(source, 'gen', source, 'gen')
    netapi.link(source, 'gen', nodes[0], 'gen')
    source.activation = 1
    monitor_uid = netapi.add_group_monitor(nodespace.uid, 'testndoes', node_name_prefix='testnode', gate='gen', color='purple')
    for i in range(5):
        runtime.step_nodenet(test_nodenet)
    data = nodenet.get_monitor(monitor_uid).get_data()
    assert set(data['values'][4][:4]) == {1.0}  # first 4 active
    assert set(data['values'][4][4:]) == {0.0}  # rest off
    runtime.save_nodenet(test_nodenet)
    runtime.revert_nodenet(test_nodenet)
    nodenet = runtime.nodenets[test_nodenet]
    data2 = nodenet.get_monitor(monitor_uid).get_data()
    assert data2 == data
    runtime.step_nodenet(test_nodenet)
    data3 = nodenet.get_monitor(monitor_uid).get_data()
    assert set(data3['values'][6][:6]) == {1.0}  # first 6 active
    assert set(data3['values'][6][6:]) == {0.0}  # rest off


def test_adhoc_monitor(runtime, test_nodenet):
    nodenet = runtime.get_nodenet(test_nodenet)
    netapi = nodenet.netapi
    var = 13

    def valuefunc():
        return var
    netapi.add_adhoc_monitor(valuefunc, 'test')
    runtime.step_nodenet(test_nodenet)
    items = list(runtime.get_monitor_data(test_nodenet)['monitors'].items())
    assert len(items) == 1
    uid, data = items[0]
    assert uid != data['name']
    assert data['name'] == 'test'
    assert data['values'][1] == 13

    def doublefunc():
        return var * 2
    netapi.add_adhoc_monitor(doublefunc, 'test')
    runtime.step_nodenet(test_nodenet)
    items = list(runtime.get_monitor_data(test_nodenet)['monitors'].items())
    assert len(items) == 1
    uid, data = items[0]
    assert uid != data['name']
    assert data['name'] == 'test'
    assert data['values'][1] == 13
    assert data['values'][2] == 26

    def parameterfunc(foo):
        return var * foo
    netapi.add_adhoc_monitor(parameterfunc, 'test', {'foo': 2})
    runtime.step_nodenet(test_nodenet)
    items = list(runtime.get_monitor_data(test_nodenet)['monitors'].items())
    assert len(items) == 1
    uid, data = items[0]
    assert uid != data['name']
    assert data['name'] == 'test'
    assert data['values'][1] == 13
    assert data['values'][2] == 26

    runtime.save_nodenet(test_nodenet)
    runtime.revert_nodenet(test_nodenet)
    items = list(runtime.get_monitor_data(test_nodenet)['monitors'].items())
    assert len(items) == 0
