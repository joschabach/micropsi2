#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import pytest

# skip these tests if numpy is not installed
pytest.importorskip("numpy")
pytest.importorskip("vrep")
pytest.importorskip("matplotlib")
pytest.importorskip("scipy")
pytest.importorskip("PIL")

import os
import numpy as np
import time
from unittest import mock
from datetime import datetime
from operator import add 
from micropsi_core import runtime

from vrep_api_mock import VREPMock
from micropsi_core.world.vrep import vrep_world

worldconfig = {
    'vrep_host': '127.0.0.1',
    'vrep_port': '19999',
    'simulation_speed': 0,
    'vrep_binary': '',
    'vrep_scene': '',
    'run_headless': ''
}


def domock(mockding=None):
    if not mockding:
        mockding = VREPMock()
    vrep_world.vrep = mockding


def test_vrep_with_external_process():
    domock()
    success, world_uid = runtime.new_world("vrep", "VREPWorld", owner="tester", config=worldconfig)
    world = runtime.worlds[world_uid]
    assert world.synchronous_mode is False
    assert world.vrep_watchdog is None
    assert world.connection_daemon.is_connected
    conf = world.get_config_options()
    for item in conf:
        assert item['name'] in worldconfig


def test_vrep_robot_worldadapter():
    robotmock = VREPMock(objects=["MTB_Robot"], joints=["joint1", "joint2"])
    domock(robotmock)
    success, world_uid = runtime.new_world("vrep", "VREPWorld", owner="tester", config=worldconfig)

    world = runtime.worlds[world_uid]

    waconfig = {
        'robot_name': 'MTB_Robot',
        'control_type': 'movements',
        'randomize_arm': 'True'
    }

    result, worldadapter = world.register_nodenet('Robot', 'test', nodenet_name='test', config=waconfig)

    assert worldadapter.robot_handle > 0
    assert len(worldadapter.datasource_values) == 7
    world.step()
    worldadapter.set_datatarget_value('execute', 1)
    world.step()
    data = world.get_world_view(1)
    assert 'test' in data['agents']


def test_vrep_iiwa_ik_worldadapter_synchmode():
    robotmock = VREPMock(objects=["LBR_iiwa_7_R800"], joints=["joint%d" % (i + 1) for i in range(7)])
    domock(robotmock)
    worldconfig['simulation_speed'] = 3
    success, world_uid = runtime.new_world("vrep", "VREPWorld", owner="tester", config=worldconfig)

    world = runtime.worlds[world_uid]

    waconfig = {
        'robot_name': 'LBR_iiwa_7_R800',
        'control_type': 'ik',
        'randomize_arm': 'False'  # TODO: ik + randomize arm is broken.
    }

    assert world.synchronous_mode
    result, worldadapter = world.register_nodenet('Robot', 'test', nodenet_name='test', config=waconfig)

    assert len(worldadapter.datasource_values) == 17
    assert worldadapter.robot_handle > 0

    world.step()
    # values now:
    ok, ik_pos = robotmock.simxGetObjectPosition(1, worldadapter.ik_follower_handle, -1, robotmock.simx_opmode_oneshot)
    # datatargets
    worldadapter.set_datatarget_range('ik_x', [0.1, 0.2, 0.3])
    # expected settings after action
    expected = [round(val + (0.1 * (i + 1)), 4) for i, val in enumerate(ik_pos)]
    # start doing stuff.
    worldadapter.set_datatarget_value('execute', 1)
    world.step()
    ok, pos = robotmock.simxGetObjectPosition(1, worldadapter.ik_follower_handle, -1, robotmock.simx_opmode_oneshot)
    assert pos == ik_pos  # not called since simspeed == 3
    world.step()
    ok, pos = robotmock.simxGetObjectPosition(1, worldadapter.ik_follower_handle, -1, robotmock.simx_opmode_oneshot)
    assert pos == ik_pos  # not called since simspeed == 3
    world.step()
    ok, pos = robotmock.simxGetObjectPosition(1, worldadapter.ik_target_handle, -1, robotmock.simx_opmode_oneshot)
    pos = [round(val, 4) for val in pos]
    assert pos == expected


def test_vrep_OneBallRobot():
    robotmock = VREPMock(objects=["MTB_Robot", "Ball"], vision=["Observer"], collision=['Collision'], joints=["joint%d" % (i + 1) for i in range(2)])
    domock(robotmock)
    worldconfig['simulation_speed'] = 1
    success, world_uid = runtime.new_world("vrep", "VREPWorld", owner="tester", config=worldconfig)

    waconfig = {
        'robot_name': 'MTB_Robot',
        'control_type': 'angles',
        'randomize_arm': 'False',
        'collision_name': 'Collision',
        'randomize_ball': 'True'
    }

    config_options = vrep_world.OneBallRobot.get_config_options()
    for item in config_options:
        assert item['name'] in waconfig
    world = runtime.worlds[world_uid]
    result, worldadapter = world.register_nodenet('OneBallRobot', 'test', nodenet_name='test', config=waconfig)

    assert 'ball-distance' in worldadapter.datasource_names
    assert 'ball-x' in worldadapter.datasource_names
    assert 'ball-y' in worldadapter.datasource_names
    assert 'collision' in worldadapter.datasource_names

    worldadapter.set_datatarget_value("execute", 1)
    world.step()
    assert worldadapter.get_datasource_value('ball-distance') != 0
    ball_x = worldadapter.get_datasource_value('ball-x')
    assert ball_x != 0
    ball_y = worldadapter.get_datasource_value('ball-y')
    assert ball_y != 0
    assert worldadapter.get_datasource_value('collision') == 0

    # step 5 times, otherwise we can not reset
    world.step()
    world.step()
    world.step()
    world.step()
    world.step()

    # agent has vision. make sure it's delivered
    viewdata = world.get_world_view(1)
    assert 'plots' in viewdata

    # set restart flag
    worldadapter.set_datatarget_value('restart', 1)
    # mock collision state
    robotmock.mock_collision(worldadapter.collision_handle, True)

    world.step()

    # assert randomize ball was called.
    assert ball_x != worldadapter.get_datasource_value('ball-x')
    assert ball_y != worldadapter.get_datasource_value('ball-y')
    # assert collision state gets written to datasource
    assert worldadapter.get_datasource_value('collision') == 1


def test_vrep_Objects6D():
    robotmock = VREPMock(objects=["fork", "ghost-fork"], vision=["Observer"])
    domock(robotmock)
    worldconfig['simulation_speed'] = 1
    success, world_uid = runtime.new_world("vrep", "VREPWorld", owner="tester", config=worldconfig)

    waconfig = {
        "objects": "fork,ghost-fork"
    }

    config_options = vrep_world.Objects6D.get_config_options()
    for item in config_options:
        assert item['name'] in waconfig

    world = runtime.worlds[world_uid]
    result, worldadapter = world.register_nodenet('Objects6D', 'test', nodenet_name='test', config=waconfig)

    for t in ['x', 'y', 'z', 'alpha', 'beta', 'gamma']:
        assert "fork-%s" % t in worldadapter.datasource_names
        assert "fork-%s" % t in worldadapter.datatarget_names
        assert "ghost-fork-%s" % t in worldadapter.datasource_names
        assert "ghost-fork-%s" % t in worldadapter.datatarget_names

    worldadapter.set_datatarget_value("execute", 1)
    worldadapter.set_datatarget_value("execute-fork", 1)
    worldadapter.set_datatarget_value("execute-ghost-fork", 1)
    world.step()
    worldadapter.set_datatarget_range('fork-x', [.1, .3, .5])
    worldadapter.set_datatarget_range('ghost-fork-x', [.2, .4, .6])
    worldadapter.set_datatarget_range('fork-alpha', [.3, .6, .9])
    worldadapter.set_datatarget_range('ghost-fork-alpha', [.4, .7, 1.])
    world.step()
    assert np.all(worldadapter.get_datasource_range("fork-x", 3) == [.1, .3, .5])
    assert np.all(worldadapter.get_datasource_range("ghost-fork-x", 3) == [.2, .4, .6])
    assert np.all(worldadapter.get_datasource_range("fork-alpha", 3) == [.3, .6, .9])
    assert np.all(worldadapter.get_datasource_range("ghost-fork-alpha", 3) == [.4, .7, 1.])

    assert 'plots' in world.get_world_view(1)


# def test_vrewp_with_internal_process():
#     config = {
#         'vrep_host': '127.0.0.1',
#         'vrep_port': '19999',
#         'simulation_speed': 0,
#         'vrep_binary': '/tmp/vrep.app',
#         'vrep_scene': '/tmp/scene.ttt',
#         'run_headless': 'true'
#     }

#     from micropsi_core.world.vrep import vrep_world
#     with mock
#     success, world_uid = runtime.new_world("vrep", "VREPWorld", owner="tester", config=config)

#     world = runtime.worlds[world_uid]
#     assert world.synchronous_mode is False
#     assert world.vrep_watchdog is None
#     assert world.vrep_connection_daemon.is_connected






