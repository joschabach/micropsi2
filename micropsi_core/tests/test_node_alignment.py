#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""

"""
import pytest

__author__ = 'joscha'
__date__ = '05.11.12'


@pytest.fixture
def nodenet():
    from micropsi_core.nodenet.nodenet import Nodenet
    return 1

def test_align(nodenet):
    assert nodenet == 1
