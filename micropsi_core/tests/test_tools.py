#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""

"""
import micropsi_core.tools

__author__ = 'joscha'
__date__ = '29.10.12'


def test_generate_uid():
    u1 = micropsi_core.tools.generate_uid()
    u2 = micropsi_core.tools.generate_uid()
    assert len(u1)
    assert len(u2)
    assert u1 != u2
