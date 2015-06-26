"""
Central initialization of fixtures for Runtime etc.
"""
import pytest
from micropsi_core import runtime as micropsi

DELETE_TEST_FILES_ON_EXIT = True


nn_uid = 'Testnet'


@pytest.fixture(scope="function")
def fixed_nodenet(request, test_world, engine):
    from micropsi_core.tests.nodenet_data import fixed_nodenet_data
    if engine == "theano_engine":
        fixed_nodenet_data = fixed_nodenet_data.replace('Root', 's0001')
    success, uid = micropsi.new_nodenet("Fixednet", engine=engine, worldadapter="Braitenberg", owner="Pytest User", world_uid=test_world, uid='fixed_test_nodenet')
    micropsi.get_nodenet(uid)
    micropsi.merge_nodenet(uid, fixed_nodenet_data, keep_uids=True)
    micropsi.save_nodenet(uid)
    return uid
