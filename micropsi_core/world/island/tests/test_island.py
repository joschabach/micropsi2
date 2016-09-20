#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""

"""

__author__ = 'joscha'
__date__ = '29.10.12'


def test_island(runtime, resourcepath):
    success, world_uid = runtime.new_world("Misland", "Island", owner="tester")
    assert success
    world = runtime.worlds[world_uid]
    assert world.__class__.__name__ == 'Island'
    runtime.add_worldobject(world_uid, "Lightsource", (10, 10), uid='foobar', name='foobar', parameters={})
    runtime.save_world(world_uid)
    runtime.revert_world(world_uid)
    world = runtime.worlds[world_uid]
    assert world.objects["foobar"].__class__.__name__ == 'Lightsource'
    assert world.objects["foobar"].position == [10, 10]
    assert world.data['objects']['foobar']['position'] == [10, 10]
    assert world.__class__.__name__ == 'Island'
    runtime.set_worldobject_properties(world_uid, "foobar", position=(5, 5))
    assert world.objects["foobar"].position == (5, 5)
    assert world.data['objects']['foobar']['position'] == (5, 5)
    assert runtime.get_world_view(world_uid, -1)['objects']['foobar']['position'] == (5, 5)
    runtime.delete_world(world_uid)


def test_island_braitenberg(runtime, resourcepath, default_nodenet):
    ok, world_uid = runtime.new_world("Misland", "Island", owner="tester")
    world = runtime.worlds[world_uid]

    runtime.add_worldobject(world_uid, "Lightsource", (500, 300), uid='lightsource', name="light")

    nodenet = runtime.nodenets[default_nodenet]
    runtime.set_nodenet_properties(default_nodenet, worldadapter="Braitenberg", world_uid=world_uid)

    assert default_nodenet in world.agents

    # create a tiny braiti
    netapi = nodenet.netapi
    sensors = netapi.import_sensors(None)
    actors = netapi.import_actors(None)
    for s in sensors:
        for a in actors:
            if s.get_parameter('datasource') == 'brightness_l' and a.get_parameter('datatarget') == 'engine_r':
                netapi.link(s, 'gen', a, 'gen')
            if s.get_parameter('datasource') == 'brightness_r' and a.get_parameter('datatarget') == 'engine_l':
                netapi.link(a, 'gen', a, 'gen')

    runtime.set_worldagent_properties(world_uid, default_nodenet, position=(600, 500), orientation=0)

    for i in range(10):
        runtime.step_nodenet(default_nodenet)

    # assert it moved towards the lightsource
    assert world.agents[default_nodenet].position[0] < 600
    assert world.agents[default_nodenet].position[1] < 500


def test_island_survivor(runtime, resourcepath, default_nodenet):
    ok, world_uid = runtime.new_world("Misland", "Island", owner="tester")
    world = runtime.worlds[world_uid]

    # add some objects:
    # north: juniper
    runtime.add_worldobject(world_uid, "Juniper", (700, 300), uid='juniper', name="juniper")
    # west: champi
    runtime.add_worldobject(world_uid, "Champignon", (600, 400), uid='champignon', name="champignon")
    # east: mehir
    runtime.add_worldobject(world_uid, "Menhir", (800, 400), uid='menhir', name="menhir")
    # bottom: waterhole
    runtime.add_worldobject(world_uid, "Waterhole", (700, 500), uid='waterhole', name="waterhole")

    runtime.set_nodenet_properties(default_nodenet, worldadapter="Survivor", world_uid=world_uid)
    runtime.set_worldagent_properties(world_uid, default_nodenet, position=(700, 400), orientation=0)
    nodenet = runtime.nodenets[default_nodenet]
    worldadapter = nodenet.worldadapter_instance

    # go north:
    worldadapter.datatargets['loco_north'] = 1
    world.step()

    # hack action cooloff
    worldadapter.action_cooloff = 0

    # eat the juniper
    old_energy = worldadapter.datasources['body-energy']
    worldadapter.datatargets['action_eat'] = 1
    world.step()
    assert worldadapter.datasources['body-energy'] > old_energy

    # go to waterhole
    worldadapter.datatargets['loco_south'] = 1
    world.step()
    worldadapter.datatargets['loco_south'] = 1
    world.step()

    # hack action cooloff
    worldadapter.action_cooloff = 0

    # eat waterhole
    old_energy = worldadapter.datasources['body-energy']
    old_water = worldadapter.datasources['body-water']
    worldadapter.datatargets['action_eat'] = 1
    world.step()
    assert worldadapter.datasources['body-energy'] < old_energy
    assert worldadapter.datasources['body-water'] < old_water

    # drink waterhole
    old_energy = worldadapter.datasources['body-energy']
    old_water = worldadapter.datasources['body-water']
    worldadapter.datatargets['action_drink'] = 1
    world.step()
    assert worldadapter.datasources['body-energy'] < old_energy
    assert worldadapter.datasources['body-water'] > old_water

    worldadapter.energy = 0
    world.step()
    assert worldadapter.is_dead  # fin


def test_island_structured_objects(runtime, default_nodenet):
    ok, world_uid = runtime.new_world("Misland", "Island", owner="tester")
    world = runtime.worlds[world_uid]

    runtime.set_nodenet_properties(default_nodenet, worldadapter="StructuredObjects", world_uid=world_uid)
    runtime.set_worldagent_properties(world_uid, default_nodenet, position=(700, 400), orientation=0)
    nodenet = runtime.nodenets[default_nodenet]
    worldadapter = nodenet.worldadapter_instance

    runtime.add_worldobject(world_uid, "FlyAgaric", (700, 450), uid='flyagaric', name="flyagaric")

    runtime.step_nodenet(default_nodenet)
    view = world.get_world_view(1)['agents'][default_nodenet]

    grid = view['scene']['shape_grid']
    assert grid[0] == [None] * 5
    assert grid[1] == [None] * 5
    assert grid[2] == [None] * 5
    assert grid[3] == [None] * 5
    assert grid[4] == [None, None, {'type': 'cir', 'color': 'red'}, None, None]
    assert view['scene']['shape_name'] == 'FlyAgaric'

    # this thing can't move! needs fixing!
    runtime.delete_worldobject(world_uid, 'flyagaric')
    runtime.add_worldobject(world_uid, "Stone", (700, 450), uid='menhir', name="menhir")

    runtime.step_nodenet(default_nodenet)
    view = world.get_world_view(1)['agents'][default_nodenet]
    assert view['scene']['shape_grid'] != grid
    assert view['scene']['shape_name'] == 'Stone'
    assert worldadapter.datasources['major-newscene'] == 1

    worldadapter.datatargets['fov_x'] = 1
    worldadapter.datatargets['fov_y'] = 2

    # assert newscene info prevails until seen
    runtime.step_nodenet(default_nodenet)
    assert worldadapter.get_datasource_value('major-newscene') == 1
    assert worldadapter.datasources['presence-charcoal'] == 1
    assert worldadapter.datasources['presence-com'] == 1
    for key in worldadapter.datasources:
        if key.startswith('presence') and key != 'presence-com' and key != 'presence-charcoal':
            assert worldadapter.datasources[key] == 0

    worldadapter.datatargets['fov_reset'] = 1
    runtime.step_nodenet(default_nodenet)
    assert worldadapter.get_datasource_value('major-newscene') == 0
    assert worldadapter.datasources['fov-x'] == 0
    assert worldadapter.datasources['fov-y'] == 0


def test_island_worldobjects(runtime, default_nodenet):
    """ just for the nice coverage """
    from micropsi_core.world.island import island as isl
    ok, world_uid = runtime.new_world("Misland", "Island", owner="tester")
    world = runtime.worlds[world_uid]
    objs = ["Lightsource", "PalmTree", "Maple", "Braintree", "Wirselkraut", "Thornbush", "Juniper", "Champignon", "FlyAgaric", "Stone", "Boulder", "Menhir", "Waterhole"]
    edible = ["Lightsource", "Wirselkraut", "Thornbush", "Juniper", "Champignon", "FlyAgaric"]
    drinkable = ["Waterhole"]
    for obj in objs:
        inst = getattr(isl, obj)(world)
        res, energy, water, integrity = inst.action_eat()
        assert res == (obj in edible)
        res, energy, water, integrity = inst.action_drink()
        assert res == (obj in drinkable)
