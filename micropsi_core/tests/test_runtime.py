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
    micropsi.set_runner_properties(1, 1)
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
    micropsi.set_runner_properties(1, 1)
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
    data = micropsi.get_nodenet_data(uid, None)
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
