#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""
Basic tests for monitor api
"""
from micropsi_core import runtime as micropsi


def test_add_gate_monitor(fixed_nodenet):
    data = micropsi.add_gate_monitor(fixed_nodenet, 'A1', 'gen')
    assert data['uid'] is not None
    assert data['node_name'] == 'A1'
    assert data['node_uid'] == 'A1'
    assert data['target'] == 'gen'
    assert data['type'] == 'gate'
    assert data['uid'] in micropsi.nodenets[fixed_nodenet].monitors


def test_add_slot_monitor(fixed_nodenet):
    data = micropsi.add_slot_monitor(fixed_nodenet, 'A1', 'gen')
    assert data['uid'] is not None
    assert data['node_name'] == 'A1'
    assert data['node_uid'] == 'A1'
    assert data['target'] == 'gen'
    assert data['type'] == 'slot'
    assert data['uid'] in micropsi.nodenets[fixed_nodenet].monitors


def test_remove_monitor(fixed_nodenet):
    data = micropsi.add_slot_monitor(fixed_nodenet, 'A1', 'gen')
    assert data['uid'] in micropsi.nodenets[fixed_nodenet].monitors
    micropsi.remove_monitor(fixed_nodenet, data['uid'])
    assert data['uid'] not in micropsi.nodenets[fixed_nodenet].monitors

