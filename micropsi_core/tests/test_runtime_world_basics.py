#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""

"""
import os
import mock

__author__ = 'joscha'
__date__ = '29.10.12'


def test_new_world(runtime, resourcepath, default_world):
    success, world_uid = runtime.new_world("Waterworld", "DefaultWorld", owner="tester")
    assert success
    assert world_uid != default_world
    world_properties = runtime.get_world_properties(world_uid)
    assert world_properties["name"] == "Waterworld"
    w_path = os.path.join(resourcepath, runtime.WORLD_DIRECTORY, world_uid + ".json")
    assert os.path.exists(w_path)

    # get_available_worlds
    worlds = runtime.get_available_worlds()
    myworlds = runtime.get_available_worlds("tester")
    assert default_world in worlds
    assert world_uid in worlds
    assert world_uid in myworlds
    assert default_world not in myworlds

    world = runtime.worlds[world_uid]
    assert world.name == "Waterworld"
    assert world.owner == "tester"
    assert world.__class__.get_config_options() == []
    assert world.get_available_worldadapters()['Default'].__name__ == "Default"
    assert world.config == {}

    # delete_world
    runtime.delete_world(world_uid)
    assert world_uid not in runtime.get_available_worlds()
    assert not os.path.exists(w_path)


def test_get_world_properties(runtime, default_world):
    wp = runtime.get_world_properties(default_world)
    assert wp["world_type"] == "DefaultWorld"
    assert default_world == wp["uid"]


def test_start_stop_simulation(runtime, default_world, default_nodenet):
    nodenet = runtime.get_nodenet(default_nodenet)
    world = runtime.load_world(default_world)
    runtime.set_nodenet_properties(default_nodenet, worldadapter="Default", world_uid=default_world)
    runtime.start_nodenetrunner(default_nodenet)
    assert world.is_active
    assert nodenet.is_active
    runtime.stop_nodenetrunner(default_nodenet)
    assert not world.is_active
    assert not nodenet.is_active


def test_get_worldadapters(runtime, default_world, default_nodenet):
    wa = runtime.get_worldadapters(default_world)
    assert 'Default' in wa
    assert 'description' in wa['Default']
    assert 'datasources' not in wa['Default']
    runtime.set_nodenet_properties(default_nodenet, worldadapter='Default', world_uid=default_world)
    wa = runtime.get_worldadapters(default_world, default_nodenet)
    assert wa['Default']['datatargets'] == ['echo']
    assert set(wa['Default']['datasources']) == set(['static_on', 'random', 'static_off'])


def test_add_worldobject(runtime, default_world):
    world = runtime.load_world(default_world)
    result, foobar_uid = runtime.add_worldobject(default_world, "TestObject", (10, 10), name='foobar', parameters={})
    assert foobar_uid in world.data['objects']
    assert foobar_uid in world.objects
    result, spam_uid = runtime.add_worldobject(default_world, "Spam", (10, 10))
    assert not result  # spam is not supported
    runtime.save_world(default_world)
    runtime.revert_world(default_world)
    assert foobar_uid in world.data['objects']
    assert foobar_uid in world.objects


def test_add_worldobject_without_id(runtime, default_world):
    world = runtime.load_world(default_world)
    count = len(world.objects)
    runtime.add_worldobject(default_world, "TestObject", (10, 10), name='bazbaz', parameters={})
    assert count + 1 == len(world.objects)
    assert count + 1 == len(world.data['objects'])


def test_get_worldobjects(runtime, default_world):
    runtime.load_world(default_world)
    reuslt, foobar_uid = runtime.add_worldobject(default_world, "TestObject", (10, 10), name='foobar', parameters={})
    objects = runtime.get_world_objects(default_world)
    assert foobar_uid in objects
    objects = runtime.get_world_objects(default_world, type="Spam")
    assert not objects
    objects = runtime.get_world_objects(default_world, type="TestObject")
    assert foobar_uid in objects


def test_register_agent(runtime, default_world, default_nodenet):
    world = runtime.load_world(default_world)
    nodenet = runtime.get_nodenet(default_nodenet)
    assert nodenet.uid not in world.data['agents']
    nodenet.world = default_world
    runtime.set_nodenet_properties(nodenet.uid, worldadapter='Default', world_uid=world.uid)
    assert nodenet.uid in world.data['agents']
    assert nodenet.uid in world.agents
    runtime.save_world(default_world)
    runtime.revert_world(default_world)
    assert nodenet.uid in world.data['agents']
    assert nodenet.uid in world.agents


def test_set_object_properties(runtime, default_world):
    world = runtime.load_world(default_world)
    result, foobar_uid = runtime.add_worldobject(default_world, "TestObject", (10, 10), name='foobar', parameters={"foo": "bar"})
    runtime.set_worldobject_properties(default_world, foobar_uid, name="foobaz", position=(5, 5), orientation=270, parameters={"foo": "baz"})
    assert world.objects[foobar_uid].position == (5, 5)
    assert world.data['objects'][foobar_uid]['position'] == (5, 5)
    assert world.objects[foobar_uid].parameters["foo"] == "baz"
    assert world.data['objects'][foobar_uid]['parameters']["foo"] == "baz"
    assert world.objects[foobar_uid].name == "foobaz"
    assert world.data['objects'][foobar_uid]['name'] == "foobaz"
    assert world.objects[foobar_uid].orientation == 270
    assert world.data['objects'][foobar_uid]['orientation'] == 270

    assert runtime.get_world_view(default_world, -1)['objects'][foobar_uid]['position'] == (5, 5)


def test_set_agent_properties(runtime, default_world, default_nodenet):
    world = runtime.load_world(default_world)
    runtime.set_nodenet_properties(default_nodenet, worldadapter='Default', world_uid=default_world)
    runtime.set_worldagent_properties(default_world, default_nodenet, position=(5, 5), orientation=180, parameters={'foo': 'bar'})
    assert world.agents[default_nodenet].position == (5, 5)
    assert world.data['agents'][default_nodenet]['position'] == (5, 5)
    assert world.agents[default_nodenet].orientation == 180
    assert world.data['agents'][default_nodenet]['orientation'] == 180
    assert world.agents[default_nodenet].parameters == {'foo': 'bar'}
    assert world.data['agents'][default_nodenet]['parameters'] == {'foo': 'bar'}


def test_agent_dying_unregisters_agent(runtime, default_world, default_nodenet):
    world = runtime.load_world(default_world)
    nodenet = runtime.get_nodenet(default_nodenet)
    nodenet.world = default_world
    runtime.set_nodenet_properties(nodenet.uid, worldadapter='Default', world_uid=world.uid)
    assert nodenet.uid in world.agents
    mockdead = mock.Mock(return_value=False)
    world.agents[nodenet.uid].is_alive = mockdead
    world.step()
    assert nodenet.uid not in world.agents


def test_world_does_not_spawn_deleted_agents(runtime, default_world, resourcepath):
    from micropsi_core.world.world import World
    filename = os.path.join(resourcepath, 'worlds', 'foobar.json')
    data = """{
    "filename": "%s",
    "name": "foobar",
    "owner": "Pytest User",
    "uid": "foobar",
    "version":1,
    "world_type": "DefaultWorld",
    "agents": {
        "dummy": {
            "name": "Dummy",
            "position": [17, 17],
            "type": "Default",
            "uid": "dummy"
        }
    }
    }"""
    with open(filename, 'w') as fp:
        fp.write(data)
    world = World(filename, world_type='DefaultWorld', name='foobar', owner='Pytest User', uid='foobar')
    assert 'dummy' not in world.agents
    # assert 'dummy' not in world.data['agents']


def test_reset_datatargets(runtime, default_world, default_nodenet):
    world = runtime.load_world(default_world)
    nodenet = runtime.get_nodenet(default_nodenet)
    nodenet.world = default_world
    runtime.set_nodenet_properties(nodenet.uid, worldadapter='Default', world_uid=world.uid)
    world.agents[default_nodenet].datatargets['echo'] = 0.7
    world.agents[default_nodenet].reset_datatargets()
    assert world.agents[default_nodenet].datatargets['echo'] == 0


def test_worldadapter_update_calls_reset_datatargets(runtime, default_world, default_nodenet):
    world = runtime.load_world(default_world)
    nodenet = runtime.get_nodenet(default_nodenet)
    nodenet.world = default_world
    runtime.set_nodenet_properties(nodenet.uid, worldadapter='Default', world_uid=world.uid)
    world.agents[default_nodenet].reset_datatargets = mock.MagicMock(name='reset')
    runtime.step_nodenet(default_nodenet)
    world.agents[default_nodenet].reset_datatargets.assert_called_once_with()


def test_worlds_are_configurable(runtime):
    res, uid = runtime.new_world('testworld', 'DefaultWorld', config={'foo': 'bar', '42': '23'})
    assert uid in runtime.worlds
    assert runtime.worlds[uid].data['config']['foo'] == 'bar'
    runtime.revert_world(uid)
    assert runtime.worlds[uid].data['config']['foo'] == 'bar'
    assert runtime.worlds[uid].data['config']['42'] == '23'


def test_set_world_properties(runtime, default_nodenet):
    res, world_uid = runtime.new_world('testworld', 'DefaultWorld', config={'foo': 'bar', '42': '23'})
    nodenet = runtime.get_nodenet(default_nodenet)
    nodenet.world = world_uid
    runtime.set_nodenet_properties(nodenet.uid, worldadapter='Default', world_uid=world_uid)
    assert default_nodenet in runtime.worlds[world_uid].agents
    assert runtime.nodenets[default_nodenet].worldadapter == "Default"
    old_wa = nodenet.worldadapter_instance
    runtime.set_world_properties(world_uid, world_name='renamedworld', config={'foo': 'dings', '42': '5'})
    assert runtime.worlds[world_uid].name == 'renamedworld'
    assert runtime.worlds[world_uid].data['config']['foo'] == 'dings'
    assert runtime.worlds[world_uid].data['config']['42'] == '5'
    assert default_nodenet in runtime.worlds[world_uid].agents
    assert nodenet.worldadapter_instance is not None and nodenet.worldadapter_instance is not old_wa


def test_get_world_uid_by_name(runtime, default_world):
    assert runtime.get_world_uid_by_name("World of Pain") == default_world
    assert runtime.get_world_uid_by_name("Netherworld") is None


def test_world_discovery(runtime, default_nodenet, resourcepath):
    import os
    with open(os.path.join(resourcepath, 'worlds.json'), 'w') as fp:
        fp.write("""
            {"worlds": ["custom_world.py"],
            "worldadapters": ["someadapter.py"]}""")
    with open(os.path.join(resourcepath, 'custom_world.py'), 'w') as fp:
        fp.write("""

from micropsi_core.world.world import World
from dependency import things

class MyWorld(World):
    supported_worldadapters = ['MyCustomWA']

    def __init__(self, filename, **kwargs):
        super().__init__(filename, **kwargs)
        for key in things:
            setattr(self, key, things[key])

""")
    os.mkdir(os.path.join(resourcepath, 'dependency'))
    with open(os.path.join(resourcepath, 'dependency', '__init__.py'), 'w') as fp:
        fp.write("""
things = {'foo': 'baz'}
""")

    with open(os.path.join(resourcepath, 'someadapter.py'), 'w') as fp:
        fp.write("""

from micropsi_core.world.worldadapter import WorldAdapter

class MyCustomWA(WorldAdapter):
    def __init__(self, world, uid=None, config={}, **data):
        super().__init__(world, uid=uid, config=config, **data)
        self.datasources = {'foo': 1}
        self.datatargets = {'bar': 0}
        self.datatarget_feedback = {'bar': 0}

    def update_data_sources_and_targets(self):
        self.datasources['foo'] = self.datatargets['bar'] * 2

""")

    runtime.reload_code()
    assert "MyWorld" in runtime.get_available_world_types()

    result, world_uid = runtime.new_world("test world", "MyWorld")

    assert runtime.worlds[world_uid].foo == 'baz'
    assert runtime.set_nodenet_properties(default_nodenet, world_uid=world_uid, worldadapter="MyCustomWA")
    assert runtime.nodenets[default_nodenet].worldadapter_instance.__class__.__name__ == 'MyCustomWA'


def test_realtime_world_stepping(runtime, default_nodenet, resourcepath):
    import os
    import time
    with open(os.path.join(resourcepath, 'worlds.json'), 'w') as fp:
        fp.write("""
            {"worlds": ["custom_world.py"],
            "worldadapters": ["custom_world.py"]}""")
    with open(os.path.join(resourcepath, 'custom_world.py'), 'w') as fp:
        fp.write("""

from micropsi_core.world.world import World
from micropsi_core.world.worldadapter import WorldAdapter

class MyWorld(World):
    is_realtime = True
    supported_worldadapters = ['MyCustomWA']

    def __init__(self, filename, **kwargs):
        super().__init__(filename, **kwargs)
        self.custom_state = None

    def simulation_started(self):
        super().simulation_started()
        self.custom_state = 'runner started'

    def simulation_stopped(self):
        super().simulation_stopped()
        self.custom_state = 'runner stopped'

class MyCustomWA(WorldAdapter):
    def __init__(self, world, uid=None, config={}, **data):
        super().__init__(world, uid=uid, config=config, **data)

    def update_data_sources_and_targets(self):
        pass
""")
    runtime.reload_code()
    result, world_uid = runtime.new_world("test world", "MyWorld")
    assert runtime.set_nodenet_properties(default_nodenet, world_uid=world_uid, worldadapter="MyCustomWA")
    runtime.single_step_nodenet_only(default_nodenet)
    assert not runtime.worlds[world_uid].is_active
    assert runtime.nodenets[default_nodenet].current_step == 1
    assert runtime.worlds[world_uid].current_step == 0
    assert runtime.worlds[world_uid].custom_state is None
    runtime.step_nodenet(default_nodenet)
    time.sleep(.2)
    assert not runtime.nodenets[default_nodenet].is_active
    assert runtime.nodenets[default_nodenet].current_step == 2
    assert runtime.worlds[world_uid].is_active
    assert runtime.worlds[world_uid].current_step > 3
    assert runtime.worlds[world_uid].custom_state == 'runner started'
    runtime.stop_nodenetrunner(default_nodenet)
    assert not runtime.worlds[world_uid].is_active
    assert runtime.worlds[world_uid].custom_state == 'runner stopped'
    runtime.start_nodenetrunner(default_nodenet)
    time.sleep(.2)
    runtime.step_nodenet(default_nodenet)
    laststep = runtime.nodenets[default_nodenet].current_step
    time.sleep(.2)
    assert laststep == runtime.nodenets[default_nodenet].current_step
    assert not runtime.nodenets[default_nodenet].is_active
    assert runtime.worlds[world_uid].is_active
