#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""

"""
import os
from micropsi_core import runtime
from micropsi_core import runtime as micropsi

__author__ = 'joscha'
__date__ = '29.10.12'


def test_new_nodenet(test_nodenet, resourcepath):
    success, nodenet_uid = micropsi.new_nodenet("Test_Nodenet", "Default", owner="tester")
    assert success
    assert nodenet_uid != test_nodenet
    assert micropsi.get_available_nodenets("tester")[nodenet_uid].name == "Test_Nodenet"
    n_path = os.path.join(resourcepath, runtime.NODENET_DIRECTORY, nodenet_uid + ".json")
    assert os.path.exists(n_path)

    # get_available_nodenets
    nodenets = micropsi.get_available_nodenets()
    mynets = micropsi.get_available_nodenets("tester")
    assert test_nodenet in nodenets
    assert nodenet_uid in nodenets
    assert nodenet_uid in mynets
    assert test_nodenet not in mynets

    # delete_nodenet
    micropsi.delete_nodenet(nodenet_uid)
    assert nodenet_uid not in micropsi.get_available_nodenets()
    assert not os.path.exists(n_path)

"""
def test_set_nodenet_properties(micropsi, test_nodenet):
    assert 0

def test_init_runners(micropsi, test_nodenet):
    assert 0

def test_nodenetrunner(micropsi, test_nodenet):
    assert 0

def test__get_world_uid_for_nodenet_uid(micropsi, test_nodenet):
    assert 0

def test_unload_nodenet(micropsi, test_nodenet):
    assert 0

def test_get_nodenet_area(micropsi, test_nodenet):
    assert 0

def test_start_nodenetrunner(micropsi, test_nodenet):
    assert 0

def test_set_nodenetrunner_timestep(micropsi, test_nodenet):
    assert 0

def test_get_nodenetrunner_timestep(micropsi, test_nodenet):
    assert 0

def test_get_is_nodenet_running(micropsi, test_nodenet):
    assert 0

def test_stop_nodenetrunner(micropsi, test_nodenet):
    assert 0

def test_step_nodenet(micropsi, test_nodenet):
    assert 0

def test_revert_nodenet(micropsi, test_nodenet):
    assert 0

def test_export_nodenet(micropsi, test_nodenet):
    assert 0

def test_import_nodenet(micropsi, test_nodenet):
    assert 0

def test_merge_nodenet(micropsi, test_nodenet):
    assert 0

def test_add_gate_monitor(micropsi, test_nodenet):
    assert 0

def test_add_slot_monitor(micropsi, test_nodenet):
    assert 0

def test_remove_monitor(micropsi, test_nodenet):
    assert 0

def test_clear_monitor(micropsi, test_nodenet):
    assert 0

def test_export_monitor_data(micropsi, test_nodenet):
    assert 0

def test_get_monitor_data(micropsi, test_nodenet):
    assert 0
"""