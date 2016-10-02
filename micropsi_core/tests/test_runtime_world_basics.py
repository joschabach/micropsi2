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

    world = micropsi.worlds[world_uid]
    assert world.name == "Waterworld"
    assert world.owner == "tester"
    assert world.__class__.get_config_options() == []
    assert world.get_available_worldadapters()['Default'].__name__ == "Default"
    assert world.config == {}

    # delete_world
    micropsi.delete_world(world_uid)
    assert world_uid not in micropsi.get_available_worlds()
    assert not os.path.exists(w_path)


def test_get_world_properties(test_world):
    wp = micropsi.get_world_properties(test_world)
    assert "Island" == wp["world_type"]
    assert test_world == wp["uid"]


def test_get_worldadapters(test_world, default_nodenet):
    wa = micropsi.get_worldadapters(test_world)
    assert 'Braitenberg' in wa
    assert 'description' in wa['Braitenberg']
    assert 'datasources' not in wa['Braitenberg']
    runtime.set_nodenet_properties(default_nodenet, worldadapter='Braitenberg', world_uid=test_world)
    wa = micropsi.get_worldadapters(test_world, default_nodenet)
    assert wa['Braitenberg']['datatargets'] == ['engine_l', 'engine_r']
    assert wa['Braitenberg']['datasources'] == ['brightness_l', 'brightness_r']


def test_add_worldobject(test_world):
    world = runtime.load_world(test_world)
    result, foobar_uid = runtime.add_worldobject(test_world, "Default", (10, 10), name='foobar', parameters={})
    assert foobar_uid in world.data['objects']
    assert foobar_uid in world.objects
    result, spam_uid = runtime.add_worldobject(test_world, "Spam", (10, 10))
    assert not result  # spam is not supported
    runtime.save_world(test_world)
    runtime.revert_world(test_world)
    assert foobar_uid in world.data['objects']
    assert foobar_uid in world.objects


def test_add_worldobject_without_id(test_world):
    world = runtime.load_world(test_world)
    count = len(world.objects)
    runtime.add_worldobject(test_world, "Default", (10, 10), name='bazbaz', parameters={})
    assert count + 1 == len(world.objects)
    assert count + 1 == len(world.data['objects'])


def test_get_worldobjects(test_world):
    runtime.load_world(test_world)
    reuslt, foobar_uid = runtime.add_worldobject(test_world, "Default", (10, 10), name='foobar', parameters={})
    objects = runtime.get_world_objects(test_world)
    assert foobar_uid in objects
    objects = runtime.get_world_objects(test_world, type="Spam")
    assert not objects
    objects = runtime.get_world_objects(test_world, type="Default")
    assert foobar_uid in objects


def test_register_agent(test_world, default_nodenet):
    world = runtime.load_world(test_world)
    nodenet = runtime.get_nodenet(default_nodenet)
    assert nodenet.uid not in world.data['agents']
    nodenet.world = test_world
    runtime.set_nodenet_properties(nodenet.uid, worldadapter='Braitenberg', world_uid=world.uid)
    assert nodenet.uid in world.data['agents']
    assert nodenet.uid in world.agents
    runtime.save_world(test_world)
    runtime.revert_world(test_world)
    assert nodenet.uid in world.data['agents']
    assert nodenet.uid in world.agents


def test_set_object_properties(test_world):
    world = runtime.load_world(test_world)
    result, foobar_uid = runtime.add_worldobject(test_world, "Default", (10, 10), name='foobar', parameters={"foo": "bar"})
    runtime.set_worldobject_properties(test_world, foobar_uid, name="foobaz", position=(5, 5), orientation=270, parameters={"foo": "baz"})
    assert world.objects[foobar_uid].position == (5, 5)
    assert world.data['objects'][foobar_uid]['position'] == (5, 5)
    assert world.objects[foobar_uid].parameters["foo"] == "baz"
    assert world.data['objects'][foobar_uid]['parameters']["foo"] == "baz"
    assert world.objects[foobar_uid].name == "foobaz"
    assert world.data['objects'][foobar_uid]['name'] == "foobaz"
    assert world.objects[foobar_uid].orientation == 270
    assert world.data['objects'][foobar_uid]['orientation'] == 270

    assert runtime.get_world_view(test_world, -1)['objects'][foobar_uid]['position'] == (5, 5)


def test_set_agent_properties(test_world, default_nodenet):
    world = runtime.load_world(test_world)
    runtime.set_nodenet_properties(default_nodenet, worldadapter='Braitenberg', world_uid=test_world)
    runtime.set_worldagent_properties(test_world, default_nodenet, position=(5, 5), orientation=180, parameters={'foo': 'bar'})
    assert world.agents[default_nodenet].position == (5, 5)
    assert world.data['agents'][default_nodenet]['position'] == (5, 5)
    assert world.agents[default_nodenet].orientation == 180
    assert world.data['agents'][default_nodenet]['orientation'] == 180
    assert world.agents[default_nodenet].parameters == {'foo': 'bar'}
    assert world.data['agents'][default_nodenet]['parameters'] == {'foo': 'bar'}


def test_agent_dying_unregisters_agent(test_world, default_nodenet):
    world = runtime.load_world(test_world)
    nodenet = runtime.get_nodenet(default_nodenet)
    nodenet.world = test_world
    runtime.set_nodenet_properties(nodenet.uid, worldadapter='Braitenberg', world_uid=world.uid)
    assert nodenet.uid in world.agents
    mockdead = mock.Mock(return_value=False)
    world.agents[nodenet.uid].is_alive = mockdead
    world.step()
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


def test_reset_datatargets(test_world, default_nodenet):
    world = runtime.load_world(test_world)
    nodenet = runtime.get_nodenet(default_nodenet)
    nodenet.world = test_world
    runtime.set_nodenet_properties(nodenet.uid, worldadapter='Braitenberg', world_uid=world.uid)
    world.agents[default_nodenet].datatargets['engine_r'] = 0.7
    world.agents[default_nodenet].datatargets['engine_l'] = 0.2
    world.agents[default_nodenet].reset_datatargets()
    assert world.agents[default_nodenet].datatargets['engine_l'] == 0
    assert world.agents[default_nodenet].datatargets['engine_r'] == 0


def test_worldadapter_update_calls_reset_datatargets(test_world, default_nodenet):
    world = runtime.load_world(test_world)
    nodenet = runtime.get_nodenet(default_nodenet)
    nodenet.world = test_world
    runtime.set_nodenet_properties(nodenet.uid, worldadapter='Braitenberg', world_uid=world.uid)
    world.agents[default_nodenet].reset_datatargets = mock.MagicMock(name='reset')
    runtime.step_nodenet(default_nodenet)
    world.agents[default_nodenet].reset_datatargets.assert_called_once_with()


def test_worlds_are_configurable():
    res, uid = runtime.new_world('testworld', 'Island', config={'foo': 'bar', '42': '23'})
    assert uid in runtime.worlds
    assert runtime.worlds[uid].data['config']['foo'] == 'bar'
    runtime.revert_world(uid)
    assert runtime.worlds[uid].data['config']['foo'] == 'bar'
    assert runtime.worlds[uid].data['config']['42'] == '23'


def test_set_world_properties(default_nodenet):
    res, world_uid = runtime.new_world('testworld', 'Island', config={'foo': 'bar', '42': '23'})
    nodenet = runtime.get_nodenet(default_nodenet)
    nodenet.world = world_uid
    runtime.set_nodenet_properties(nodenet.uid, worldadapter='Braitenberg', world_uid=world_uid)
    assert default_nodenet in runtime.worlds[world_uid].agents
    assert runtime.nodenets[default_nodenet].worldadapter == "Braitenberg"
    old_wa = nodenet.worldadapter_instance
    runtime.set_world_properties(world_uid, world_name='renamedworld', config={'foo': 'dings', '42': '5'})
    assert runtime.worlds[world_uid].name == 'renamedworld'
    assert runtime.worlds[world_uid].data['config']['foo'] == 'dings'
    assert runtime.worlds[world_uid].data['config']['42'] == '5'
    assert default_nodenet in runtime.worlds[world_uid].agents
    assert nodenet.worldadapter_instance is not None and nodenet.worldadapter_instance is not old_wa


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