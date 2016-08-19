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
import mock
from datetime import datetime
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
    assert len(worldadapter.datasource_values) == 9
    world.step()
    worldadapter.set_datatarget_value('execute', 1)
    world.step()


def test_vrep_iiwa_ik_worldadapter():
    robotmock = VREPMock(objects=["LBR_iiwa_7_R800"], joints=["joint%d" % (i + 1) for i in range(6)])
    domock(robotmock)
    success, world_uid = runtime.new_world("vrep", "VREPWorld", owner="tester", config=worldconfig)

    world = runtime.worlds[world_uid]

    waconfig = {
        'robot_name': 'LBR_iiwa_7_R800',
        'control_type': 'ik',
        'randomize_arm': 'False'
    }

    result, worldadapter = world.register_nodenet('Robot', 'test', nodenet_name='test', config=waconfig)

    assert len(worldadapter.datasource_values) == 17
    assert worldadapter.robot_handle > 0
    world.step()
    worldadapter.set_datatarget_value('execute', 1)
    world.step()



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






