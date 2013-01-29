"""
Central initialization of fixtures for Runtime etc.
"""
import os
import pytest
from micropsi_core import runtime as micropsi

DELETE_TEST_FILES_ON_EXIT = False

world_uid = None
nn_uid = None


@pytest.fixture(scope="session")
def resourcepath():
    return os.path.join(os.path.dirname(__file__), "..", "..", micropsi.DATA_PATH)


@pytest.fixture(scope="session")
def test_world():
    global world_uid
    worlds = micropsi.get_available_worlds("Pytest User")
    if worlds:
        world_uid = worlds.keys()[0]
    else:
        success, world_uid = micropsi.new_world("World of Pain", "World", "Pytest User")

    def fin():
        if DELETE_TEST_FILES_ON_EXIT:
            micropsi.delete_world(world_uid)
    return world_uid


@pytest.fixture(scope="session")
def test_nodenet():
    global nn_uid
    nodenets = micropsi.get_available_nodenets("Pytest User") or {}
    for uid, nn in nodenets.items():
        if(nn.name == 'Testnet'):
            nn_uid = nodenets.keys()[0]
    else:
        success, nn_uid = micropsi.new_nodenet("Testnet", "Default", owner="Pytest User", world_uid=world_uid, uid='Testnet')

    def fin():
        if DELETE_TEST_FILES_ON_EXIT:
            micropsi.delete_nodenet(nn_uid)
    return nn_uid


@pytest.fixture(scope="function")
def fixed_nodenet(test_world):
    from micropsi_core.tests.nodenet_data import fixed_nodenet_data
    success, uid = micropsi.new_nodenet("Fixednet", "Default", owner="Pytest User", world_uid=test_world, uid='fixed_test_nodenet')
    micropsi.get_nodenet(uid)
    micropsi.merge_nodenet(uid, fixed_nodenet_data)

    def fin():
        if DELETE_TEST_FILES_ON_EXIT:
            micropsi.delete_nodenet(uid)
    return uid

#test_nodenet(micropsi())
