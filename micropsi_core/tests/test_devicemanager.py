
import pytest


def create_dummy_device(resourcepath, retval="[1,2,3,4,5]"):
    dummy_device = """
from micropsi_core.device.device import InputDevice

class DummyDevice(InputDevice):
    def __init__(self, config):
        super().__init__(config)

    def read_data(self):
        import numpy as np
        return np.array("""+retval+""")

    def get_data_size(self):
        return 5

    def get_prefix(self):
        return "dummy"
"""
    import os
    os.makedirs(os.path.join(resourcepath, 'devices', 'dummy'), exist_ok=True)

    devicef = os.path.join(resourcepath, 'devices', 'dummy', 'dummy_device.py')
    with open(devicef, 'w') as fp:
        fp.write(dummy_device)


@pytest.mark.engine("theano_engine")
@pytest.mark.engine("numpy_engine")
def test_devicemanager(runtime, test_nodenet, resourcepath):
    create_dummy_device(resourcepath)

    res, errors = runtime.reload_code()
    assert res
    assert 'DummyDevice' in runtime.get_device_types()

    _, uid = runtime.add_device('DummyDevice', {'name': 'foo'})
    assert uid in runtime.get_devices()

    runtime.set_device_properties(uid, {'name': 'bar'})
    assert runtime.get_devices()[uid]['config']['name'] == 'bar'

    runtime.remove_device(uid)
    assert uid not in runtime.get_devices()


@pytest.mark.engine("theano_engine")
@pytest.mark.engine("numpy_engine")
def test_devices_with_worldadapters(runtime, test_nodenet, resourcepath, default_world):
    create_dummy_device(resourcepath)

    res, errors = runtime.reload_code()
    _, uid = runtime.add_device('DummyDevice', {'name': 'foo'})

    runtime.set_nodenet_properties(test_nodenet, world_uid=default_world, worldadapter="ArrayWorldAdapter", device_map={uid: 'dummy'})

    assert 'dummy' in runtime.get_nodenet(test_nodenet).worldadapter_instance.get_available_flow_datasources()

    runtime.remove_device(uid)


@pytest.mark.engine("theano_engine")
@pytest.mark.engine("numpy_engine")
def test_device_reload(runtime, test_nodenet, resourcepath, default_world):
    import numpy as np
    create_dummy_device(resourcepath)
    res, errors = runtime.reload_code()

    _, uid = runtime.add_device('DummyDevice', {'name': 'foo'})
    runtime.set_nodenet_properties(test_nodenet, world_uid=default_world, worldadapter="ArrayWorldAdapter", device_map={uid: 'dummy'})

    assert 'dummy' in runtime.get_nodenet(test_nodenet).worldadapter_instance.get_available_flow_datasources()
    create_dummy_device(resourcepath, retval="[9,8,7,6,5]")
    res, errors = runtime.reload_code()

    # assert runtime.set_nodenet_properties(test_nodenet, world_uid=default_world, worldadapter="ArrayWorldAdapter", device_map={uid: 'new_device_name'})
    runtime.step_nodenet(test_nodenet)
    assert np.all(runtime.nodenets[test_nodenet].worldadapter_instance.get_flow_datasource("dummy") == np.asarray([9, 8, 7, 6, 5]))
