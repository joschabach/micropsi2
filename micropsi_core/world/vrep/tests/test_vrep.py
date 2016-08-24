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
from unittest import mock

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


def test_vrep_with_external_process(runtime):
    apimock = VREPMock()
    domock(apimock)
    success, world_uid = runtime.new_world("vrep", "VREPWorld", owner="tester", config=worldconfig)
    world = runtime.worlds[world_uid]
    assert apimock.initialized
    assert mock
    assert world.synchronous_mode is False
    assert world.vrep_watchdog is None
    assert world.connection_daemon.is_connected
    conf = world.get_config_options()
    for item in conf:
        assert item['name'] in worldconfig

    runtime.delete_world(world.uid)
    # assert vrep shutdown ran
    assert not apimock.initialized


def test_vrep_robot_worldadapter(runtime):
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
    assert set(worldadapter.datatarget_names) == {"joint_1", "joint_2", "restart", "execute"}
    assert set(worldadapter.datasource_names) == {"joint_angle_1", "joint_angle_2", "joint_force_1", "joint_force_2", "tip-x", "tip-y", "tip-z", }
    world.step()
    worldadapter.set_datatarget_value('execute', 1)
    world.step()
    data = world.get_world_view(1)
    assert 'test' in data['agents']


def test_vrep_iiwa_ik_worldadapter_synchmode(runtime):
    robotmock = VREPMock(objects=["LBR_iiwa_7_R800"], joints=["joint%d" % (i + 1) for i in range(7)])
    domock(robotmock)
    wconf = worldconfig.copy()
    wconf['simulation_speed'] = 3
    success, world_uid = runtime.new_world("vrep", "VREPWorld", owner="tester", config=wconf)

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


def test_vrep_oneballrobot(runtime):
    robotmock = VREPMock(objects=["MTB_Robot", "Ball"], vision=["Observer"], collision=['Collision'], joints=["joint%d" % (i + 1) for i in range(2)])
    domock(robotmock)
    wconf = worldconfig.copy()
    wconf['simulation_speed'] = 1
    success, world_uid = runtime.new_world("vrep", "VREPWorld", owner="tester", config=wconf)

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


def test_vrep_objects6d(runtime):
    robotmock = VREPMock(objects=["fork", "ghost-fork"], vision=["Observer"])
    domock(robotmock)
    wconf = worldconfig.copy()
    wconf['simulation_speed'] = 1
    success, world_uid = runtime.new_world("vrep", "VREPWorld", owner="tester", config=wconf)

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


def test_vrep_forcetorque(runtime):
    robotmock = VREPMock(objects=["MTB_Robot"], joints=["joint1", "joint2"])
    domock(robotmock)
    success, world_uid = runtime.new_world("vrep", "VREPWorld", owner="tester", config=worldconfig)

    world = runtime.worlds[world_uid]
    waconfig = {
        'robot_name': 'MTB_Robot',
        'control_type': 'force/torque',
        'randomize_arm': 'True'
    }

    result, worldadapter = world.register_nodenet('Robot', 'test', nodenet_name='test', config=waconfig)
    worldadapter.set_datatarget_value('execute', 1)
    worldadapter.set_datatarget_range('joint_1', [.3, .4])
    world.step()
    # what to assert?


def test_vrep_ikrobot(runtime):
    robotmock = VREPMock(objects=["LBR_iiwa_7_R800", "fork"], joints=["joint%d" % (i + 1) for i in range(7)])
    domock(robotmock)
    success, world_uid = runtime.new_world("vrep", "VREPWorld", owner="tester", config=worldconfig)

    world = runtime.worlds[world_uid]
    waconfig = {
        'robot_name': 'LBR_iiwa_7_R800',
        'control_type': 'ik',
        'randomize_arm': 'False',
        'objects': 'fork'
    }
    config_options = vrep_world.IKRobot.get_config_options()
    for item in config_options:
        assert item['name'] in waconfig

    result, worldadapter = world.register_nodenet('IKRobot', 'test', nodenet_name='test', config=waconfig)
    # 2 sources for 7 joints, 3 for tip, 6 for objects6d
    assert len(worldadapter.datasource_values) == 2 * 7 + 3 + 6
    # 2 default, 3 ik, 6 + execute for objects6d
    assert len(worldadapter.datatarget_values) == 2 + 3 + 7
    worldadapter.set_datatarget_value('execute', 1)
    worldadapter.set_datatarget_range('ik_x', [.3, .4, .5])
    world.step()
    # what to assert?


def test_vrep_ikrobotwithgrayscalevision(runtime):
    robotmock = VREPMock(objects=["LBR_iiwa_7_R800", "fork"], vision=["Observer"], joints=["joint%d" % (i + 1) for i in range(7)])
    domock(robotmock)
    success, world_uid = runtime.new_world("vrep", "VREPWorld", owner="tester", config=worldconfig)

    world = runtime.worlds[world_uid]
    waconfig = {
        'robot_name': 'LBR_iiwa_7_R800',
        'control_type': 'ik',
        'randomize_arm': 'False',
        'objects': 'fork'
    }
    config_options = vrep_world.IKRobotWithGreyscaleVision.get_config_options()
    for item in config_options:
        assert item['name'] in waconfig

    result, worldadapter = world.register_nodenet('IKRobotWithGreyscaleVision', 'test', nodenet_name='test', config=waconfig)
    # assert vision in datasources
    assert len(worldadapter.datasource_values) == 23 + (16 * 16)
    worldadapter.set_datatarget_value('execute', 1)
    worldadapter.set_datatarget_range('ik_x', [.3, .4, .5])
    world.step()
    # what to assert?


def test_vrep_with_internal_process(resourcepath, default_nodenet, runtime):
    import stat
    from time import sleep
    apimock = VREPMock(objects=["MTB_Robot"], joints=["joint1", "joint2"])
    domock(apimock)
    dummyexecutable = os.path.join(resourcepath, 'vrep_dummy')
    with open(dummyexecutable, 'w') as fp:
        fp.write("""#!/usr/bin/env python3
from time import sleep
while True:
    sleep(2)  # we are just idle waiting""")
    os.chmod(dummyexecutable, stat.S_IXUSR | stat.S_IWUSR | stat.S_IRUSR)

    wconf = worldconfig.copy()
    wconf['vrep_binary'] = dummyexecutable
    wconf['vrep_scene'] = 'doesntmatter.ttt'
    wconf['simulation_speed'] = 0

    waconfig = {
        'robot_name': 'MTB_Robot',
        'control_type': 'force/torque',
        'randomize_arm': 'True'
    }

    success, world_uid = runtime.new_world("vrep", "VREPWorld", owner="tester", config=wconf)
    world = runtime.worlds[world_uid]
    result, worldadapter = world.register_nodenet("Robot", default_nodenet, config=waconfig)

    assert not world.synchronous_mode
    assert world.vrep_watchdog is not None
    assert world.vrep_watchdog.process is not None
    assert world.connection_daemon.is_connected
    assert apimock.initialized

    world.vrep_watchdog.pause()
    world.vrep_watchdog.kill_vrep()
    assert world.vrep_watchdog.process is None
    world.vrep_watchdog.resume()

    with mock.patch.object(worldadapter, 'initialize') as initmock:
        sleep(2)  # give the watchdog and connection_daemon a moment
        assert world.vrep_watchdog.process is not None
        assert world.connection_daemon.is_connected
        initmock.assert_called_once()

    runtime.delete_world(world_uid)
    assert not apimock.initialized


def test_vrep_error_handling(runtime):
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

    def sideeffect(**_):
        worldadapter.initialized = True

    with mock.patch.object(worldadapter, 'initialize', side_effect=sideeffect) as initmock:
        # timeouts, and emtpy responses we can recover from:
        # one empty call is simpy repeated.
        robotmock.repeat_error_call = 1
        assert worldadapter.call_vrep(robotmock.mock_repeat_error_response, [1]) is True
        initmock.assert_not_called()

        # two empty calls lead to reconnect
        robotmock.repeat_error_call = 2
        assert worldadapter.call_vrep(robotmock.mock_repeat_error_response, [2]) is True
        initmock.assert_called_once()

        # this is the same as 1:
        robotmock.repeat_error_call = 1
        assert worldadapter.call_vrep(robotmock.mock_repeat_error_response, [3]) is True
        initmock.assert_not_called()

        # as is this
        robotmock.repeat_error_call = 1
        assert worldadapter.call_vrep(robotmock.mock_repeat_error_response, [16]) is True

        # we can not recover from these:
        assert worldadapter.call_vrep(robotmock.mock_error_response, [4]) is False
        assert worldadapter.call_vrep(robotmock.mock_error_response, [8]) is False
        assert worldadapter.call_vrep(robotmock.mock_error_response, [32]) is False
        assert worldadapter.call_vrep(robotmock.mock_error_response, [64]) is False
