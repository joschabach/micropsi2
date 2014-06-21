#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""


"""

from micropsi_core import runtime as micropsi
import logging


def test_add_logger():
    res = micropsi.start_capture_logger('system', 'DEBUG')
    assert res
    logging.get_logger('system').info("BadgerBadgerBadgerBadger! Mushroom! Mushroom!")
    res, msg = micropsi.get_logger_messages('system')
    assert msg == "BadgerBadgerBadgerBadger! Mushroom! Mushroom!"
    res, msg = micropsi.stop_capture_logger('system')
    assert res
