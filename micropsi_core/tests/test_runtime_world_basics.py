#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""

"""
import os
import mock
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
    assert "Island" == wp["world_type"]
    assert test_world == wp["uid"]


def test_get_worldadapters(test_world):
    wa = micropsi.get_worldadapters(test_world)
    assert 'engine_l' in wa['Braitenberg']['datatargets']
    assert 'engine_r' in wa['Braitenberg']['datatargets']
    assert 'brightness_l' in wa['Braitenberg']['datasources']
    assert 'brightness_r' in wa['Braitenberg']['datasources']


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
    count = len(world.objects)
    runtime.add_worldobject(test_world, "Default", (10, 10), name='bazbaz', parameters={})
    assert count + 1 == len(world.objects)
    assert count + 1 == len(world.data['objects'])


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
    runtime.load_nodenet(test_nodenet)
    nodenet.world = world
    runtime.set_nodenet_properties(nodenet.uid, worldadapter='Braitenberg', world_uid=world.uid)
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
    runtime.set_nodenet_properties(test_nodenet, worldadapter='Braitenberg', world_uid=test_world)
    runtime.set_worldagent_properties(test_world, test_nodenet, position=(5, 5))
    assert world.agents[test_nodenet].position == (5, 5)
    assert world.data['agents'][test_nodenet]['position'] == (5, 5)


def test_agent_dying_unregisters_agent(test_world, test_nodenet):
    world = runtime.worlds[test_world]
    nodenet = runtime.get_nodenet(test_nodenet)
    runtime.load_nodenet(test_nodenet)
    nodenet.world = world
    runtime.set_nodenet_properties(nodenet.uid, worldadapter='Braitenberg', world_uid=world.uid)
    assert nodenet.uid in world.data['agents']
    assert nodenet.uid in world.agents
    mockdead = mock.Mock(return_value=False)
    world.agents[nodenet.uid].is_alive = mockdead
    world.step()
    assert nodenet.uid not in world.data['agents']
    assert nodenet.uid not in world.agents


def test_world_does_not_spawn_deleted_agents(test_world, resourcepath):
    from micropsi_core.world.world import World
    filename = os.path.join(resourcepath, 'worlds', 'foobar.json')
    data = """{
    "filename": "%s",
    "name": "foobar",
    "owner": "Pytest User",
    "uid": "foobar",
    "version":1,
    "world_type": "Island",
    "agents": {
        "dummy": {
            "name": "Dummy",
            "position": [17, 17],
            "type": "Braitenberg",
            "uid": "dummy"
        }
    }
    }"""
    with open(filename, 'w') as fp:
        fp.write(data)
    world = World(filename, world_type='Island', name='foobar', owner='Pytest User', uid='foobar')
    assert 'dummy' not in world.agents
    # assert 'dummy' not in world.data['agents']


def test_reset_datatargets(test_world, test_nodenet):
    world = runtime.worlds[test_world]
    nodenet = runtime.get_nodenet(test_nodenet)
    runtime.load_nodenet(test_nodenet)
    nodenet.world = world
    runtime.set_nodenet_properties(nodenet.uid, worldadapter='Braitenberg', world_uid=world.uid)
    world.agents[test_nodenet].datatargets['engine_r'] = 0.7
    world.agents[test_nodenet].datatargets['engine_l'] = 0.2
    world.agents[test_nodenet].reset_datatargets()
    assert world.agents[test_nodenet].datatargets['engine_l'] == 0
    assert world.agents[test_nodenet].datatargets['engine_r'] == 0


def test_actuators_do_not_reset_each_others_datatarget(test_world, test_nodenet):
    world = runtime.worlds[test_world]
    nodenet = runtime.get_nodenet(test_nodenet)
    runtime.load_nodenet(test_nodenet)
    nodenet.world = world
    runtime.set_runner_properties(200, 1)
    runtime.set_nodenet_properties(nodenet.uid, worldadapter='Braitenberg', world_uid=world.uid)
    actor1 = nodenet.netapi.create_node("Actor", None)
    actor2 = nodenet.netapi.create_node("Actor", None)
    actor1.set_parameter('datatarget', 'engine_r')
    actor2.set_parameter('datatarget', 'engine_r')
    reg1 = nodenet.netapi.create_node("Register", None)
    reg2 = nodenet.netapi.create_node("Register", None)
    nodenet.netapi.link(reg1, 'gen', actor1, 'gen')
    nodenet.netapi.link(reg2, 'gen', actor2, 'gen')
    reg1.activation = 0.7
    reg2.activation = 0.3
    mock_reset = mock.Mock(return_value=None)
    world.agents[test_nodenet].reset_datatargets = mock_reset
    runtime.step_nodenet(test_nodenet)
    assert world.agents[test_nodenet].datatargets['engine_r'] == 1


def test_worldadapter_update_calls_reset_datatargets(test_world, test_nodenet):
    world = runtime.worlds[test_world]
    nodenet = runtime.get_nodenet(test_nodenet)
    runtime.load_nodenet(test_nodenet)
    nodenet.world = world
    runtime.set_nodenet_properties(nodenet.uid, worldadapter='Braitenberg', world_uid=world.uid)
    world.agents[test_nodenet].reset_datatargets = mock.MagicMock(name='reset')
    runtime.step_nodenet(test_nodenet)
    world.agents[test_nodenet].reset_datatargets.assert_called_once()

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