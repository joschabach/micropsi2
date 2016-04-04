#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""


"""

from micropsi_core import runtime as micropsi
import logging


def test_set_logging_level():
    assert logging.getLogger('system').getEffectiveLevel() == logging.WARNING
    micropsi.set_logging_levels({'system': 'DEBUG', 'world': 'DEBUG', 'agent': 'DEBUG'})
    assert logging.getLogger('system').getEffectiveLevel() == logging.DEBUG
    assert logging.getLogger('world').getEffectiveLevel() == logging.DEBUG
    assert micropsi.cfg['logging']['level_agent'] == 'DEBUG'


def test_get_logging_levels():
    logging.getLogger('system').setLevel(logging.INFO)
    logging.getLogger('world').setLevel(logging.WARNING)
    res = micropsi.get_logging_levels()
    assert res['system'] == 'INFO'
    assert res['world'] == 'WARNING'


def test_get_logger_messages():
    msg = "Attention passengers. The next redline train to braintree is now arriving!"
    micropsi.set_logging_levels({'system': 'INFO'})
    logging.getLogger('system').info(msg)
    res = micropsi.get_logger_messages('system')
    item = res['logs'][-1]
    assert item['msg']
    assert item['logger'] == 'system'
    assert item['level'] == 'INFO'
    assert 'time' in item
    assert item['step'] is None


def test_nodenet_specific_loggers():
    res, uid1 = micropsi.new_nodenet("test1")
    res, uid2 = micropsi.new_nodenet("test2")
    assert "agent.%s" % uid1 in logging.Logger.manager.loggerDict
    assert "agent.%s" % uid2 in logging.Logger.manager.loggerDict
    logging.getLogger("agent.%s" % uid1).warning("hello!")
    res = micropsi.get_logger_messages("agent.%s" % uid1)
    item = res['logs'][-1]
    assert item['msg'] == "hello!"
    assert item['step'] == 0


def test_single_agent_mode():
    mode = micropsi.cfg['micropsi2'].get('single_agent_mode')
    micropsi.cfg['micropsi2'].update({'single_agent_mode': '1'})
    res, uid1 = micropsi.new_nodenet("test1")
    res, uid2 = micropsi.new_nodenet("test2")
    assert uid1 not in micropsi.nodenets
    micropsi.cfg['micropsi2'].update({'single_agent_mode': mode})


def test_unregister_logger():
    res, uid1 = micropsi.new_nodenet("test1")
    logging.getLogger("agent.%s" % uid1).warning('hello!')
    micropsi.delete_nodenet(uid1)
    assert "agent.%s" % uid1 not in micropsi.logger.loggers
    assert "agent.%s" % uid1 not in micropsi.logger.record_storage
    assert "agent.%s" % uid1 not in micropsi.logger.handlers


def test_get_multiple_logger_messages_are_sorted():
    from time import sleep
    logging.getLogger('world').warning('First.')
    sleep(0.01)
    logging.getLogger('system').warning('Second')
    sleep(0.01)
    logging.getLogger('world').warning('Wat?')
    res = micropsi.get_logger_messages(['system', 'world'])
    assert len(res['logs']) == 3
    assert res['logs'][0]['logger'] == 'world'
    assert res['logs'][1]['logger'] == 'system'
    assert res['logs'][2]['logger'] == 'world'


def test_register_runner_condition_step(test_nodenet):
    import time
    success, data = micropsi.set_runner_condition(test_nodenet, steps=7)
    assert data['step'] == 7
    assert data['step_amount'] == 7
    micropsi.start_nodenetrunner(test_nodenet)
    assert micropsi.nodenets[test_nodenet].is_active
    time.sleep(1)
    assert micropsi.nodenets[test_nodenet].current_step == 7
    assert not micropsi.nodenets[test_nodenet].is_active
    # test that the condition stays active.
    micropsi.start_nodenetrunner(test_nodenet)
    assert micropsi.nodenets[test_nodenet].is_active
    time.sleep(1)
    assert micropsi.nodenets[test_nodenet].current_step == 14
    assert not micropsi.nodenets[test_nodenet].is_active


def test_register_runner_condition_monitor(test_nodenet):
    import time
    nn = micropsi.nodenets[test_nodenet]
    node = nn.netapi.create_node('Register', None)
    nn.netapi.link(node, 'gen', node, 'gen', weight=2)
    node.activation = 0.1
    uid = micropsi.add_gate_monitor(test_nodenet, node.uid, 'gen')
    micropsi.set_runner_condition(test_nodenet, monitor={
        'uid': uid,
        'value': 0.8
    })
    micropsi.start_nodenetrunner(test_nodenet)
    assert micropsi.nodenets[test_nodenet].is_active
    time.sleep(1)
    assert not micropsi.nodenets[test_nodenet].is_active
    assert micropsi.nodenets[test_nodenet].current_step == 3
    assert round(nn.get_node(node.uid).get_gate('gen').activation, 4) == 0.8


def test_runner_condition_persists(test_nodenet):
    micropsi.set_runner_condition(test_nodenet, steps=7)
    micropsi.save_nodenet(test_nodenet)
    micropsi.revert_nodenet(test_nodenet)
    assert micropsi.nodenets[test_nodenet].get_runner_condition()['step'] == 7


def test_get_links_for_nodes(test_nodenet, node):
    api = micropsi.nodenets[test_nodenet].netapi
    ns = api.create_nodespace(None)
    node = api.get_node(node)
    pipe1 = api.create_node("Pipe", ns.uid, "pipe1")
    pipe2 = api.create_node("Pipe", ns.uid, "pipe2")
    pipe3 = api.create_node("Pipe", ns.uid, "pipe3")
    api.link(node, 'gen', pipe1, 'gen')
    api.link(pipe2, 'sub', node, 'sub')
    data = micropsi.get_links_for_nodes(test_nodenet, [node.uid])
    assert len(data['links']) == 3  # node has a genloop
    assert len(data['nodes'].values()) == 2
    assert pipe1.uid in data['nodes']
    assert pipe2.uid in data['nodes']
    assert pipe3.uid not in data['nodes']


def test_create_nodenet_from_template(test_nodenet, node, engine):
    mode = micropsi.cfg['micropsi2'].get('single_agent_mode')
    micropsi.cfg['micropsi2'].update({'single_agent_mode': '1'})
    api = micropsi.nodenets[test_nodenet].netapi
    node1 = api.get_node(node)
    node2 = api.create_node("Register", None, "node2")
    api.link(node1, 'gen', node2, 'gen')
    micropsi.save_nodenet(test_nodenet)
    result, uid = micropsi.new_nodenet('copynet', engine=engine, template=test_nodenet)
    data = micropsi.get_nodes(uid)
    for uid, n in data['nodes'].items():
        if n['name'] == node1.name:
            assert len(n['links']['gen']) == 2
        else:
            assert n['name'] == node2.name
    micropsi.cfg['micropsi2'].update({'single_agent_mode': mode})


def test_export_json_does_not_send_duplicate_links(fixed_nodenet):
    import json
    result = json.loads(micropsi.export_nodenet(fixed_nodenet))
    assert len(result['links']) == 4


def test_generate_netapi_fragment(test_nodenet, resourcepath):
    import os
    netapi = micropsi.nodenets[test_nodenet].netapi
    # create a bunch of nodes and link them
    linktypes = ['subsur', 'porret', 'catexp']
    nodes = []
    for t in linktypes:
        p1 = netapi.create_node('Pipe', None, t)
        p2 = netapi.create_node('Pipe', None, t + '2')
        nodes.extend([p1, p2])
        netapi.link_with_reciprocal(p1, p2, t)
    reg = netapi.create_node('Register', None, 'reg')
    netapi.link(reg, 'gen', nodes[0], 'gen')
    ns = netapi.create_nodespace(None, 'ns1')
    nodes.extend([reg, ns])
    # remember their names
    names = [n.name for n in nodes]
    fragment = micropsi.generate_netapi_fragment(test_nodenet, [n.uid for n in nodes])
    micropsi.nodenets[test_nodenet].clear()
    code = "def foo(netapi):\n    " + "\n    ".join(fragment.split('\n'))
    # save the fragment as recipe & run
    with open(os.path.join(resourcepath, 'recipes.py'), 'w+') as fp:
        fp.write(code)
    micropsi.reload_native_modules()
    micropsi.run_recipe(test_nodenet, 'foo', {})
    # assert that all the nodes are there again
    assert set(names) == set([n.name for n in netapi.get_nodes()] + ['ns1'])


def test_get_nodes(test_nodenet):
    nodenet = micropsi.nodenets[test_nodenet]
    netapi = nodenet.netapi
    ns1 = netapi.create_nodespace(None, "ns1")
    ns2 = netapi.create_nodespace(None, "ns2")
    ns3 = netapi.create_nodespace(ns1.uid, "ns3")
    n1 = netapi.create_node("Pipe", ns1.uid, "n1")
    n2 = netapi.create_node("Pipe", ns2.uid, "n2")
    n3 = netapi.create_node("Pipe", ns3.uid, "n3")
    result = micropsi.get_nodes(test_nodenet)
    rootuid = nodenet.get_nodespace(None).uid
    assert set(result['nodes'].keys()) == {n1.uid, n2.uid, n3.uid}
    assert set(result['nodespaces'].keys()) == {rootuid, ns1.uid, ns2.uid, ns3.uid}
    result = micropsi.get_nodes(test_nodenet, [None])
    assert result['nodes'] == {}
    assert set(result['nodespaces'].keys()) == {ns1.uid, ns2.uid}
    result = micropsi.get_nodes(test_nodenet, [ns1.uid])
    assert set(result['nodes'].keys()) == {n1.uid}
    assert set(result['nodespaces'].keys()) == {ns3.uid}


def test_run_netapi_command(test_nodenet):
    nodenet = micropsi.nodenets[test_nodenet]
    netapi = nodenet.netapi
    command = "foo = netapi.create_node('Pipe', None, 'foo')"
    result, _ = micropsi.run_netapi_command(test_nodenet, command)
    assert result
    command = "netapi.link(foo, 'gen', foo, 'gen')"
    result, _ = micropsi.run_netapi_command(test_nodenet, command)
    assert result
    nodes = netapi.get_nodes()
    assert len(nodes) == 1
    assert nodes[0].get_gate('gen').get_links()[0].target_node == nodes[0]
    command = "netapi.get_node('%s')" % nodes[0].uid
    result, node = micropsi.run_netapi_command(test_nodenet, command)
    assert node == str(nodes[0])
    command = "[n.name for n in netapi.get_nodes()]"
    result, node = micropsi.run_netapi_command(test_nodenet, command)
    assert node == "['foo']"
    command = "netapi.create_node()"
    result, msg = micropsi.run_netapi_command(test_nodenet, command)
    assert not result
    assert msg.startswith("TypeError")
    command = "for i in range(3): netapi.create_node('Register', None, 'test%d' % i)"
    result, msg = micropsi.run_netapi_command(test_nodenet, command)
    assert result
    assert len(netapi.get_nodes()) == 4


def test_get_netapi_autocomplete(test_nodenet):
    micropsi.run_netapi_command(test_nodenet, "foonode = netapi.create_node('Pipe', None, 'foo')")
    micropsi.run_netapi_command(test_nodenet, "foogate = foonode.get_gate('gen')")
    micropsi.run_netapi_command(test_nodenet, "fooslot = foonode.get_slot('gen')")
    micropsi.run_netapi_command(test_nodenet, "nodespace = netapi.create_nodespace(None, 'foospace')")
    micropsi.run_netapi_command(test_nodenet, "barnode = netapi.create_node('Register', None, 'foo')")
    data = micropsi.get_netapi_autocomplete_data(test_nodenet)
    data['types']['foonode'] = 'Node'
    data['types']['foogate'] = 'Gate'
    data['types']['fooslot'] = 'Slot'
    data['types']['nodespace'] = 'Nodespace'
    data['types']['barnode'] = 'Node'
    assert data['autocomplete_options']['Node']["get_gate"][0]['name'] == 'type'
    assert data['autocomplete_options']['Gate']["get_links"] == []
    assert data['autocomplete_options']['Slot']["get_links"] == []
    assert data['autocomplete_options']['Nodespace']["get_known_ids"][0]['name'] == 'entitytype'
    data = micropsi.get_netapi_autocomplete_data(test_nodenet, name='foonode')
    assert list(data['types'].keys()) == ['foonode']
    assert list(data['autocomplete_options'].keys()) == ['Node']
