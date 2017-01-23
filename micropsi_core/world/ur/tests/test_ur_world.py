
import pytest
import mock


pytest.importorskip('numpy')

import numpy as np


@mock.patch("micropsi_core.world.ur.optoforce_mixin.optoforce")
@mock.patch("micropsi_core.world.ur.ur_world.URConnection")
def test_urworld_basic(urmock, optomock, runtime):
    success, world_uid = runtime.new_world("URWorld", "URWorld", owner="tester", config={'ur_ip': '127.0.0.1'})
    assert success
    world = runtime.load_world(world_uid)
    assert world.__class__.__name__ == 'URWorld'

    optomock.get_ft_np = mock.Mock(return_value=np.zeros(6))
    world.connection_daemon.joint_pos = np.zeros(6)
    world.connection_daemon.joint_speeds = np.zeros(6)
    world.connection_daemon.tool_pos_6D = np.zeros(6)
    world.connection_daemon.tool_frc_6D = np.zeros(6)

    success, nodenet_uid = runtime.new_nodenet('ur', 'theano_engine', worldadapter='UR', world_uid=world_uid, use_modulators=False)
    net = runtime.get_nodenet(nodenet_uid)
    assert net.worldadapter_instance.__class__.__name__ == "UR"
    assert runtime.step_nodenet(nodenet_uid) == 1

    success, nodenet_uid = runtime.new_nodenet('urspeedJ', 'theano_engine', worldadapter='URSpeedJControlled', world_uid=world_uid, use_modulators=False)
    net = runtime.get_nodenet(nodenet_uid)
    assert net.worldadapter_instance.__class__.__name__ == "URSpeedJControlled"
    assert runtime.step_nodenet(nodenet_uid) == 1

    success, nodenet_uid = runtime.new_nodenet('uroptoforce', 'theano_engine', worldadapter='UROptoForce6D', world_uid=world_uid, use_modulators=False)
    net = runtime.get_nodenet(nodenet_uid)
    assert net.worldadapter_instance.__class__.__name__ == "UROptoForce6D"
    assert runtime.step_nodenet(nodenet_uid) == 1

    success, nodenet_uid = runtime.new_nodenet('urmovej', 'theano_engine', worldadapter='URMoveJControlled', world_uid=world_uid, use_modulators=False)
    net = runtime.get_nodenet(nodenet_uid)
    neuron = net.netapi.create_node('Neuron', None, "src")
    neuron.activation = 1
    actuator = net.netapi.create_node('Actuator', None, "exec")
    actuator.set_parameter('datatarget', 'execute')
    net.netapi.link(neuron, 'gen', actuator, 'gen')
    assert net.worldadapter_instance.__class__.__name__ == "URMoveJControlled"
    assert runtime.step_nodenet(nodenet_uid) == 1
