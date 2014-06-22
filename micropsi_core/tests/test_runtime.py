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


def test_get_logger_messages():
    msg = "Attention passengers. The next redline train to braintree is now arriving!"
    micropsi.set_logging_levels(system='INFO')
    logging.getLogger('system').info(msg)
    res = micropsi.get_logger_messages('system')
    assert len(res['logs']) == 1
    assert res['logs'][0]['msg']
    assert res['logs'][0]['logger'] == 'system'
    assert res['logs'][0]['level'] == 'INFO'
    assert 'time' in res['logs'][0]


def test_get_multiple_logger_messages_are_sorted():
    logging.getLogger('nodenet').warning('First.')
    logging.getLogger('system').warning('Second')
    logging.getLogger('world').warning('Wat?')
    res = micropsi.get_logger_messages(['system', 'world', 'nodenet'])
    assert len(res['logs']) == 3
    assert res['logs'][0]['logger'] == 'nodenet'
    assert res['logs'][1]['logger'] == 'system'
    assert res['logs'][2]['logger'] == 'world'
