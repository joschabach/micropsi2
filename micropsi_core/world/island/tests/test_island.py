#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""

"""
from micropsi_core import runtime
from micropsi_core import runtime as micropsi

__author__ = 'joscha'
__date__ = '29.10.12'


def test_island(resourcepath):
    success, world_uid = micropsi.new_world("Misland", "Island", owner="tester")
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
