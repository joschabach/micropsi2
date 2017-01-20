
import pytest

pytest.importorskip("numpy")
pytest.importorskip("gym")


def test_gymworld_basic(runtime):
    success, world_uid = runtime.new_world("OAIGym", "OAIGym", owner="tester", config={'render': 'False'})
    assert success
    world = runtime.load_world(world_uid)
    assert world.__class__.__name__ == 'OAIGym'
    success, nodenet_uid = runtime.new_nodenet('testagent', 'theano_engine', worldadapter='OAIGymAdapter', world_uid=world_uid, use_modulators=False)
    net = runtime.get_nodenet(nodenet_uid)
    assert net.worldadapter_instance.__class__.__name__ == "OAIGymAdapter"
    assert runtime.step_nodenet(nodenet_uid) == 1
