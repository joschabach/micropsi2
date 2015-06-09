#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""


"""

from micropsi_core import runtime as micropsi
import logging


def test_set_logging_level():
    assert logging.getLogger('system').getEffectiveLevel() == logging.WARNING
    micropsi.set_logging_levels(system='DEBUG', world='DEBUG', nodenet='DEBUG')
    assert logging.getLogger('system').getEffectiveLevel() == logging.DEBUG
    assert logging.getLogger('world').getEffectiveLevel() == logging.DEBUG
    assert logging.getLogger('nodenet').getEffectiveLevel() == logging.DEBUG


def test_get_logging_levels():
    logging.getLogger('system').setLevel(logging.INFO)
    logging.getLogger('world').setLevel(logging.WARNING)
    logging.getLogger('nodenet').setLevel(logging.DEBUG)
    res = micropsi.get_logging_levels()
    assert res['system'] == 'INFO'
    assert res['world'] == 'WARNING'
    assert res['nodenet'] == 'DEBUG'


def test_get_logger_messages():
    msg = "Attention passengers. The next redline train to braintree is now arriving!"
    micropsi.set_logging_levels(system='INFO')
    logging.getLogger('system').info(msg)
    res = micropsi.get_logger_messages('system')
    item = res['logs'][-1]
    assert item['msg']
    assert item['logger'] == 'system'
    assert item['level'] == 'INFO'
    assert 'time' in item


def test_get_multiple_logger_messages_are_sorted():
    logging.getLogger('nodenet').warning('First.')
    logging.getLogger('system').warning('Second')
    logging.getLogger('world').warning('Wat?')
    res = micropsi.get_logger_messages(['system', 'world', 'nodenet'])
    assert len(res['logs']) == 3
    assert res['logs'][0]['logger'] == 'nodenet'
    assert res['logs'][1]['logger'] == 'system'
    assert res['logs'][2]['logger'] == 'world'


def test_register_runner_condition_step(test_nodenet):
    import time
    micropsi.set_runner_properties(1, 1)
    micropsi.start_nodenetrunner_with_condition(test_nodenet, steps=7)
    assert micropsi.nodenets[test_nodenet].is_active
    time.sleep(1)
    assert not micropsi.nodenets[test_nodenet].is_active
    assert micropsi.nodenets[test_nodenet].current_step == 7
    assert micropsi.MicropsiRunner.conditions[test_nodenet] == {}


def test_register_runner_condition_monitor(test_nodenet):
    import time
    micropsi.set_runner_properties(1, 1)
    nn = micropsi.nodenets[test_nodenet]
    node = nn.netapi.create_node('Register', None)
    nn.netapi.link(node, 'gen', node, 'gen', weight=2)
    node.activation = 0.1
    uid = micropsi.add_gate_monitor(test_nodenet, node.uid, 'gen')
    micropsi.start_nodenetrunner_with_condition(test_nodenet, monitor={
        'uid': uid,
        'value': 0.8
    })
    assert micropsi.nodenets[test_nodenet].is_active
    time.sleep(1)
    assert round(nn.get_node(node.uid).get_gate('gen').activation, 4) == 0.8
    assert not micropsi.nodenets[test_nodenet].is_active
    assert micropsi.nodenets[test_nodenet].current_step == 3
    assert micropsi.MicropsiRunner.conditions[test_nodenet] == {}
