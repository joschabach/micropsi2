#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""

"""
import os
from micropsi_core import runtime
from micropsi_core import runtime as micropsi

__author__ = 'joscha'
__date__ = '29.10.12'

def test_new_world(resourcepath, test_world):
    success, world_uid = micropsi.new_world("Waterworld", "World", owner = "tester")
    assert success
    assert world_uid != test_world
    world_properties = micropsi.get_world_properties(world_uid)
    assert world_properties["name"] == "Waterworld"
    w_path = os.path.join(resourcepath, runtime.WORLD_DIRECTORY, world_uid+".json")
    assert os.path.exists(w_path)

    # get_available_worlds
    worlds = micropsi.get_available_worlds()
    myworlds = micropsi.get_available_worlds("tester")
    assert test_world in worlds
    assert world_uid in worlds
    assert world_uid in myworlds
    assert test_world not in myworlds

    # delete_world
    micropsi.delete_world(world_uid)
    assert world_uid not in micropsi.get_available_worlds()
    assert not os.path.exists(w_path)

def test_get_world_properties(test_world):
    wp = micropsi.get_world_properties(test_world)
    assert "World" == wp["world_type"]
    assert test_world == wp["uid"]

def test_get_worldadapters(test_world):
    wa = micropsi.get_worldadapters(test_world)
    assert 'Default' in wa
    assert "datasources" in wa["Default"]
    assert "datatargets" in wa["Default"]

"""
def test_get_world_objects(micropsi, test_world):
    assert 0

def test_get_world_view(micropsi, test_world):
    assert 0

def test_start_worldrunner(micropsi, test_world):
    assert 0

def test_get_worldrunner_timestep(micropsi):
    assert 0

def test_get_is_world_running(micropsi):
    assert 0

def test_set_worldrunner_timestep(micropsi):
    assert 0

def test_stop_worldrunner(micropsi):
    assert 0

def test_step_world(micropsi):
    assert 0

def test_revert_world(micropsi):
    assert 0

def test_save_world(micropsi):
    assert 0

def test_export_world(micropsi):
    assert 0

def test_import_world(micropsi):
    assert 0

"""