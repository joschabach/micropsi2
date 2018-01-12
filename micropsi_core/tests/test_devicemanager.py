
import pytest


def create_dummy_device(resourcepath, name="dummy", retval="[1,2,3,4,5]", connected="True", device_type="InputDevice"):
    dummy_device = """
from micropsi_core.device.device import %s

class %sDevice(%s):

    @classmethod
    def get_options(cls):
        opts = super().get_options()
        opts.append({
            'name': 'foobar',
            'default': 42
        })
        return opts

    def __init__(self, config):
        super().__init__(config)
        connected = %s
        self.calls = 0
        if not connected:
            raise RuntimeError("Failed to connect")
        self.init_foobar = config['foobar']

    def read_data(self):
        import numpy as np
        self.calls += 1
        return np.array(%s)

    def get_data_size(self):
        return 5

    def get_prefix(self):
        return "%s"
""" % (device_type, name.capitalize(), device_type, connected, retval, name)

    import os
    os.makedirs(os.path.join(resourcepath, 'devices', name), exist_ok=True)
    devicef = os.path.join(resourcepath, 'devices', name, "%s_device.py" % name)
    with open(devicef, 'w') as fp:
        fp.write(dummy_device)


@pytest.mark.engine("theano_engine")
@pytest.mark.engine("numpy_engine")
def test_devicemanager(runtime, test_nodenet, resourcepath):
    from micropsi_core.device import devicemanager
    create_dummy_device(resourcepath)

    res, errors = runtime.reload_code()
    assert res
    assert 'DummyDevice' in runtime.get_device_types()

    _, uid = runtime.add_device('DummyDevice', {'name': 'foo'})
    online_devices = runtime.get_devices()
    assert uid in online_devices
    assert online_devices[uid]['config']['name'] == 'foo'
    assert online_devices[uid]['config']['foobar'] == 42
    assert online_devices[uid]['type'] == 'DummyDevice'
    assert online_devices[uid]['nature'] == 'InputDevice'
    known_devices = devicemanager.get_known_devices()
    assert uid in known_devices
    assert known_devices[uid]['config']['name'] == 'foo'
    assert known_devices[uid]['config']['foobar'] == 42
    assert online_devices[uid]['type'] == 'DummyDevice'
    assert online_devices[uid]['nature'] == 'InputDevice'
    assert runtime.devicemanager.online_devices[uid].init_foobar == 42

    runtime.set_device_properties(uid, {'name': 'bar', 'foobar': 23})
    online_devices = runtime.get_devices()
    assert online_devices[uid]['config']['name'] == 'bar'
    assert online_devices[uid]['config']['foobar'] == 23
    known_devices = devicemanager.get_known_devices()
    assert known_devices[uid]['config']['name'] == 'bar'
    assert known_devices[uid]['config']['foobar'] == 23
    assert runtime.devicemanager.online_devices[uid].init_foobar == 23

    runtime.remove_device(uid)
    assert uid not in runtime.get_devices()
    assert uid not in devicemanager.get_known_devices()


@pytest.mark.engine("theano_engine")
@pytest.mark.engine("numpy_engine")
def test_devices_with_worldadapters(runtime, test_nodenet, resourcepath, default_world):
    import numpy as np
    create_dummy_device(resourcepath)

    res, errors = runtime.reload_code()
    _, uid = runtime.add_device('DummyDevice', {'name': 'foo'})

    runtime.set_nodenet_properties(
        test_nodenet, world_uid=default_world,
        worldadapter="ArrayWorldAdapter", device_map={uid: 'dummy'})
    wa = runtime.get_nodenet(test_nodenet).worldadapter_instance
    assert 'dummy' in wa.get_available_flow_datasources()
    runtime.step_nodenet(test_nodenet)
    assert np.all(wa.get_flow_datasource('dummy') == [1, 2, 3, 4, 5])
    runtime.remove_device(uid)


@pytest.mark.engine("theano_engine")
@pytest.mark.engine("numpy_engine")
def test_async_devices(runtime, test_nodenet, resourcepath, default_world):
    import numpy as np
    create_dummy_device(resourcepath, device_type="InputDeviceAsync")
    res, errors = runtime.reload_code()
    _, uid = runtime.add_device('DummyDevice', {'name': 'foo'})
    runtime.set_nodenet_properties(
        test_nodenet, world_uid=default_world,
        worldadapter="ArrayWorldAdapter", device_map={uid: 'dummy'})
    wa = runtime.get_nodenet(test_nodenet).worldadapter_instance
    assert 'dummy' in wa.get_available_flow_datasources()
    res, errs = runtime.reload_code()  # tests stopping unstarted threads.
    assert res
    runtime.step_nodenet(test_nodenet)
    wa = runtime.get_nodenet(test_nodenet).worldadapter_instance
    assert np.all(wa.get_flow_datasource('dummy') == [1, 2, 3, 4, 5])
    import time
    time.sleep(.2)
    assert runtime.devicemanager.online_devices[uid].calls > 2
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


@pytest.mark.engine("theano_engine")
@pytest.mark.engine("numpy_engine")
def test_changing_device_config(runtime, test_nodenet, resourcepath, default_world):
    create_dummy_device(resourcepath)
    create_dummy_device(resourcepath, name='anotherDummy')
    res, errors = runtime.reload_code()
    _, uid = runtime.add_device('DummyDevice', {'name': 'foo'})
    nodenet = runtime.nodenets[test_nodenet]
    netapi = nodenet.netapi

    runtime.set_nodenet_properties(test_nodenet, world_uid=default_world, worldadapter="ArrayWorldAdapter", device_map={uid: 'dummy'})
    assert {'dummy'} == set(runtime.get_nodenet(test_nodenet).worldadapter_instance.get_available_flow_datasources())
    assert netapi.get_nodes()[0].outputs == ['dummy']

    runtime.set_nodenet_properties(test_nodenet, world_uid=default_world, worldadapter="ArrayWorldAdapter", device_map={uid: 'anotherDummy'})
    assert {'anotherDummy'} == set(runtime.get_nodenet(test_nodenet).worldadapter_instance.get_available_flow_datasources())
    assert netapi.get_nodes()[0].outputs == ['anotherDummy']


@pytest.mark.engine("theano_engine")
@pytest.mark.engine("numpy_engine")
def test_unconnected_or_removed_devices(runtime, test_nodenet, resourcepath, default_world):
    import os
    import shutil
    import numpy as np
    create_dummy_device(resourcepath)
    res, errors = runtime.reload_code()

    _, uid = runtime.add_device('DummyDevice', {'name': 'foo'})
    nodenet = runtime.nodenets[test_nodenet]

    runtime.set_nodenet_properties(test_nodenet, world_uid=default_world, worldadapter="ArrayWorldAdapter", device_map={uid: 'dummy'})
    assert {'dummy'} == set(runtime.get_nodenet(test_nodenet).worldadapter_instance.get_available_flow_datasources())
    assert runtime.get_devices()[uid]['online']
    runtime.save_nodenet(test_nodenet)
    runtime.unload_nodenet(test_nodenet)

    # mock disconnected device by
    create_dummy_device(resourcepath, connected='False')
    res, errors = runtime.reload_code()

    nodenet = runtime.get_nodenet(test_nodenet)
    assert {'dummy'} == set(nodenet.worldadapter_instance.get_available_flow_datasources())
    assert not runtime.get_devices()[uid]['online']
    runtime.step_nodenet(test_nodenet)
    assert np.all(nodenet.worldadapter_instance.get_flow_datasource('dummy') == np.zeros(5))
    runtime.unload_nodenet(test_nodenet)

    # remove dummy device
    shutil.rmtree(os.path.join(resourcepath, 'devices'))
    res, errors = runtime.reload_code()

    nodenet = runtime.get_nodenet(test_nodenet)
    assert 'dummy' not in nodenet.worldadapter_instance.get_available_flow_datasources()
    assert not runtime.get_devices()[uid]['online']
