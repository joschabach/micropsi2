"""
Central initialization of fixtures for Runtime etc.
"""
import os
import pytest
from micropsi_core import runtime

DELETE_TEST_FILES_ON_EXIT = False

world_uid = None
nn_uid = None

@pytest.fixture(scope="session")
def resourcepath():
    return os.path.join(os.path.dirname(__file__), "..", "..", "resources")

@pytest.fixture(scope="session")
def micropsi():
    return runtime.MicroPsiRuntime(resourcepath())

@pytest.fixture(scope="session")
def test_world(micropsi):
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
def test_nodenet(micropsi):
    global nn_uid
    nodenets = micropsi.get_available_nodenets("Pytest User")
    if nodenets:
        nn_uid = nodenets.keys()[0]
    else:
        success, nn_uid = micropsi.new_nodenet("Testnet", "Default", owner="Pytest User", world_uid=world_uid)
    def fin():
        if DELETE_TEST_FILES_ON_EXIT:
            micropsi.delete_nodenet(nn_uid)
    return nn_uid

test_nodenet(micropsi())