#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""


"""

import logging
import pytest


def test_set_logging_level(runtime):
    assert logging.getLogger('system').getEffectiveLevel() == logging.WARNING
    runtime.set_logging_levels({'system': 'DEBUG', 'world': 'DEBUG', 'agent': 'DEBUG'})
    assert logging.getLogger('system').getEffectiveLevel() == logging.DEBUG
    assert logging.getLogger('world').getEffectiveLevel() == logging.DEBUG
    assert runtime.runner_config['log_level_agent'] == 'DEBUG'


def test_get_logging_levels(runtime):
    logging.getLogger('system').setLevel(logging.INFO)
    logging.getLogger('world').setLevel(logging.WARNING)
    res = runtime.get_logging_levels()
    assert res['system'] == 'INFO'
    assert res['world'] == 'WARNING'


def test_set_logfile(runtime, resourcepath):
    import os
    logfile = os.path.join(resourcepath, 'mpsi_test.log')
    runtime.set_runner_properties(23,
        log_levels={'system': 'debug', 'agent': 'debug', 'world': 'debug'},
        log_file=logfile)
    logging.getLogger('system').info("Some message")
    assert os.path.isfile(logfile)
    os.remove(logfile)
    runtime.set_runner_properties(42, log_file='')
    logging.getLogger('system').info("Some message")
    assert not os.path.isfile(logfile)


def test_get_logger_messages(runtime):
    msg = "Attention passengers. The next redline train to braintree is now arriving!"
    runtime.set_logging_levels({'system': 'INFO'})
    logging.getLogger('system').info(msg)
    res = runtime.get_logger_messages('system')
    item = res['logs'][-1]
    assert item['msg']
    assert item['logger'] == 'system'
    assert item['level'] == 'INFO'
    assert 'time' in item
    assert item['step'] is None


def test_nodenet_specific_loggers(runtime):
    res, uid1 = runtime.new_nodenet("test1")
    res, uid2 = runtime.new_nodenet("test2")
    assert "agent.%s" % uid1 in logging.Logger.manager.loggerDict
    assert "agent.%s" % uid2 in logging.Logger.manager.loggerDict
    logging.getLogger("agent.%s" % uid1).warning("hello!")
    res = runtime.get_logger_messages("agent.%s" % uid1)
    item = res['logs'][-1]
    assert item['msg'] == "hello!"
    assert item['step'] == 0


def test_single_agent_mode(runtime):
    mode = runtime.runtime_config['micropsi2'].get('single_agent_mode')
    runtime.runtime_config['micropsi2'].update({'single_agent_mode': '1'})
    res, uid1 = runtime.new_nodenet("test1")
    res, uid2 = runtime.new_nodenet("test2")
    assert uid1 not in runtime.nodenets
    runtime.runtime_config['micropsi2'].update({'single_agent_mode': mode})


def test_unregister_logger(runtime):
    res, uid1 = runtime.new_nodenet("test1")
    logging.getLogger("agent.%s" % uid1).warning('hello!')
    runtime.delete_nodenet(uid1)
    assert "agent.%s" % uid1 not in runtime.logger.loggers
    assert "agent.%s" % uid1 not in runtime.logger.record_storage
    assert "agent.%s" % uid1 not in runtime.logger.handlers


def test_get_multiple_logger_messages_are_sorted(runtime):
    from time import sleep
    logging.getLogger('world').warning('First.')
    sleep(0.01)
    logging.getLogger('system').warning('Second')
    sleep(0.01)
    logging.getLogger('world').warning('Wat?')
    res = runtime.get_logger_messages(['system', 'world'])
    assert len(res['logs']) == 3
    assert res['logs'][0]['logger'] == 'world'
    assert res['logs'][1]['logger'] == 'system'
    assert res['logs'][2]['logger'] == 'world'


def test_register_runner_condition_step(runtime, test_nodenet):
    import time
    success, data = runtime.set_runner_condition(test_nodenet, steps=7)
    assert data['step'] == 7
    assert data['step_amount'] == 7
    runtime.start_nodenetrunner(test_nodenet)
    assert runtime.nodenets[test_nodenet].is_active
    time.sleep(1)
    assert runtime.nodenets[test_nodenet].current_step == 7
    assert not runtime.nodenets[test_nodenet].is_active
    # test that the condition stays active.
    runtime.start_nodenetrunner(test_nodenet)
    assert runtime.nodenets[test_nodenet].is_active
    time.sleep(1)
    assert runtime.nodenets[test_nodenet].current_step == 14
    assert not runtime.nodenets[test_nodenet].is_active


def test_register_runner_condition_monitor(runtime, test_nodenet):
    import time
    nn = runtime.nodenets[test_nodenet]
    node = nn.netapi.create_node('Neuron', None)
    nn.netapi.link(node, 'gen', node, 'gen', weight=2)
    node.activation = 0.1
    uid = runtime.add_gate_monitor(test_nodenet, node.uid, 'gen')
    runtime.set_runner_condition(test_nodenet, monitor={
        'uid': uid,
        'value': 0.8
    })
    runtime.start_nodenetrunner(test_nodenet)
    assert runtime.nodenets[test_nodenet].is_active
    time.sleep(1)
    assert not runtime.nodenets[test_nodenet].is_active
    assert runtime.nodenets[test_nodenet].current_step == 3
    assert round(nn.get_node(node.uid).get_gate('gen').activation, 4) == 0.8


def test_runner_condition_persists(runtime, test_nodenet):
    runtime.set_runner_condition(test_nodenet, steps=7)
    runtime.save_nodenet(test_nodenet)
    runtime.revert_nodenet(test_nodenet)
    assert runtime.nodenets[test_nodenet].get_runner_condition()['step'] == 7


def test_get_links_for_nodes(runtime, test_nodenet, node):
    api = runtime.nodenets[test_nodenet].netapi
    ns = api.create_nodespace(None)
    node = api.get_node(node)
    pipe1 = api.create_node("Pipe", ns.uid, "pipe1")
    pipe2 = api.create_node("Pipe", ns.uid, "pipe2")
    pipe3 = api.create_node("Pipe", ns.uid, "pipe3")
    api.link(node, 'gen', pipe1, 'gen')
    api.link(pipe2, 'sub', node, 'sub')
    data = runtime.get_links_for_nodes(test_nodenet, [node.uid])
    assert len(data['links']) == 3  # node has a genloop
    assert len(data['nodes'].values()) == 2
    assert pipe1.uid in data['nodes']
    assert pipe2.uid in data['nodes']
    assert pipe3.uid not in data['nodes']


def test_create_nodenet_from_template(runtime, test_nodenet, node, engine):
    mode = runtime.runtime_config['micropsi2'].get('single_agent_mode')
    runtime.runtime_config['micropsi2'].update({'single_agent_mode': '1'})
    api = runtime.nodenets[test_nodenet].netapi
    node1 = api.get_node(node)
    node2 = api.create_node("Neuron", None, "node2")
    api.link(node1, 'gen', node2, 'gen')
    runtime.save_nodenet(test_nodenet)
    result, uid = runtime.new_nodenet('copynet', engine=engine, template=test_nodenet)
    data = runtime.get_nodes(uid)
    for uid, n in data['nodes'].items():
        if n['name'] == node1.name:
            assert len(n['links']['gen']) == 2
        else:
            assert n['name'] == node2.name
    runtime.runtime_config['micropsi2'].update({'single_agent_mode': mode})


def test_export_json_does_not_send_duplicate_links(runtime, test_nodenet):
    import json
    _, uid1 = runtime.add_node(test_nodenet, "Neuron", [10, 10], None)
    _, uid2 = runtime.add_node(test_nodenet, "Neuron", [20, 20], None)
    runtime.add_link(test_nodenet, uid1, 'gen', uid2, 'gen')
    runtime.add_link(test_nodenet, uid1, 'gen', uid2, 'gen')
    runtime.add_link(test_nodenet, uid2, 'gen', uid1, 'gen')
    result = json.loads(runtime.export_nodenet(test_nodenet))
    assert len(result['links']) == 2


def test_generate_netapi_fragment(runtime, test_nodenet, engine, resourcepath):
    import os
    netapi = runtime.nodenets[test_nodenet].netapi
    # create a bunch of nodes and link them
    linktypes = ['subsur', 'porret', 'catexp']
    nodes = []
    for t in linktypes:
        p1 = netapi.create_node('Pipe', None, t)
        p2 = netapi.create_node('Pipe', None, t + '2')
        nodes.extend([p1, p2])
        netapi.link_with_reciprocal(p1, p2, t)
    reg = netapi.create_node('Neuron', None, 'reg')
    reg.set_gate_configuration('gen', 'threshold', {'amplification': 2})
    netapi.link(reg, 'gen', nodes[0], 'gen')
    nodes.append(reg)
    # remember their names
    names = [n.name for n in nodes]
    fragment = runtime.generate_netapi_fragment(test_nodenet, [n.uid for n in nodes])
    res, pastenet = runtime.new_nodenet('pastnet', engine)
    code = "def foo(netapi):\n    " + "\n    ".join(fragment.split('\n'))
    # save the fragment as recipe & run
    with open(os.path.join(resourcepath, 'recipes', 'test.py'), 'w+') as fp:
        fp.write(code)
    runtime.reload_code()
    runtime.run_recipe(pastenet, 'foo', {})
    pastnetapi = runtime.get_nodenet(pastenet).netapi
    # assert that all the nodes are there again
    assert set(names) == set([n.name for n in pastnetapi.get_nodes()])


def test_get_nodes(runtime, engine, test_nodenet):
    nodenet = runtime.nodenets[test_nodenet]
    netapi = nodenet.netapi
    ns1 = netapi.create_nodespace(None, "ns1")
    ns2 = netapi.create_nodespace(None, "ns2")
    ns3 = netapi.create_nodespace(ns1.uid, "ns3")
    n1 = netapi.create_node("Pipe", ns1.uid, "n1")
    n2 = netapi.create_node("Pipe", ns2.uid, "n2")
    n3 = netapi.create_node("Pipe", ns3.uid, "n3")
    result = runtime.get_nodes(test_nodenet)
    rootuid = nodenet.get_nodespace(None).uid
    assert set(result['nodes'].keys()) == {n1.uid, n2.uid, n3.uid}
    assert set(result['nodespaces'].keys()) == {rootuid, ns1.uid, ns2.uid, ns3.uid}
    result = runtime.get_nodes(test_nodenet, [None])
    assert result['nodes'] == {}
    assert set(result['nodespaces'].keys()) == {ns1.uid, ns2.uid}
    result = runtime.get_nodes(test_nodenet, [ns1.uid])
    assert set(result['nodes'].keys()) == {n1.uid}
    assert set(result['nodespaces'].keys()) == {ns3.uid}
    if engine == "dict_engine":
        # test with followupnodes:
        netapi.link_with_reciprocal(n1, n2, 'subsur')
        result = runtime.get_nodes(test_nodenet, [ns1.uid])
        assert n2.uid in result['nodes']


def test_get_nodenet_by_name(runtime, test_nodenet):
    assert runtime.get_nodenet_uid_by_name("Foobar") is None
    assert runtime.get_nodenet_uid_by_name("Testnet") == test_nodenet


@pytest.mark.engine("theano_engine")
def test_system_benchmark(runtime, test_nodenet):
    from micropsi_core.benchmark_system import benchmark_system
    result = benchmark_system(n=10, repeat=1)
    assert "numpy version" in result
    assert "scipy version" in result
    assert "tensorflow version" in result
    assert "numpy dot" in result
    assert "scipy dot" in result
    assert "tf matmul" in result
