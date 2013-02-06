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
    success, world_uid = micropsi.new_world("Waterworld", "World", owner="tester")
    assert success
    assert world_uid != test_world
    world_properties = micropsi.get_world_properties(world_uid)
    assert world_properties["name"] == "Waterworld"
    w_path = os.path.join(resourcepath, runtime.WORLD_DIRECTORY, world_uid + ".json")
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


def test_add_worldobject(test_world):
    world = runtime.get_available_worlds()[test_world]
    runtime.add_worldobject(test_world, "Default", (10, 10), uid='foobar', name='foobar', parameters={})
    assert "foobar" in world.data['objects']
    assert "foobar" in world.objects
    runtime.save_world(test_world)
    runtime.revert_world(test_world)
    assert "foobar" in world.data['objects']
    assert "foobar" in world.objects


def test_add_worldobject_without_id(test_world):
    world = runtime.get_available_worlds()[test_world]
    count = len(world.objects.keys())
    runtime.add_worldobject(test_world, "Default", (10, 10), name='bazbaz', parameters={})
    assert count + 1 == len(world.objects.keys())
    assert count + 1 == len(world.data['objects'].keys())


def test_get_worldobjects(test_world):
    runtime.add_worldobject(test_world, "Default", (10, 10), uid='foobar', name='foobar', parameters={})
    objects = runtime.get_world_objects(test_world)
    assert 'foobar' in objects
    runtime.save_world(test_world)
    runtime.revert_world(test_world)
    objects = runtime.get_world_objects(test_world)
    assert 'foobar' in objects


def test_register_agent(test_world, test_nodenet):
    world = runtime.worlds[test_world]
    nodenet = runtime.get_nodenet(test_nodenet)
    assert nodenet.uid not in world.data['agents']
    nodenet.world = world
    runtime.load_nodenet(test_nodenet)
    assert nodenet.uid in world.data['agents']
    assert nodenet.uid in world.agents
    runtime.save_world(test_world)
    runtime.revert_world(test_world)
    assert nodenet.uid in world.data['agents']
    assert nodenet.uid in world.agents


def test_set_object_properties(test_world):
    world = runtime.get_available_worlds()[test_world]
    runtime.add_worldobject(test_world, "Default", (10, 10), uid='foobar', name='foobar', parameters={})
    runtime.set_worldobject_properties(test_world, "foobar", position=(5, 5))
    assert world.objects["foobar"].position == (5, 5)
    assert world.data['objects']['foobar']['position'] == (5, 5)
    assert runtime.get_world_view(test_world, -1)['objects']['foobar']['position'] == (5, 5)


def test_set_agent_properties(test_world, test_nodenet):
    world = runtime.worlds[test_world]
    nodenet = runtime.get_nodenet(test_nodenet)
    nodenet.world = world
    runtime.load_nodenet(test_nodenet)
    runtime.set_worldagent_properties(test_world, test_nodenet, position=(5, 5))
    assert world.agents[test_nodenet].position == (5, 5)
    assert world.data['agents'][test_nodenet]['position'] == (5, 5)


"""
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