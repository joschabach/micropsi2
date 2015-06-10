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


def test_get_links_for_nodes(test_nodenet, node):
    api = micropsi.nodenets[test_nodenet].netapi
    ns = api.create_node('Nodespace', None)
    node = api.get_node(node)
    pipe1 = api.create_node("Pipe", ns.uid, "pipe1")
    pipe2 = api.create_node("Pipe", ns.uid, "pipe2")
    pipe3 = api.create_node("Pipe", ns.uid, "pipe3")
    api.link(node, 'gen', pipe1, 'gen')
    api.link(pipe2, 'sub', node, 'sub')
    data = micropsi.get_links_for_nodes(test_nodenet, [node.uid])
    assert len(data['links'].values()) == 3  # node has a genloop
    assert len(data['nodes'].values()) == 2
    assert pipe1.uid in data['nodes']
    assert pipe2.uid in data['nodes']
    assert pipe3.uid not in data['nodes']
