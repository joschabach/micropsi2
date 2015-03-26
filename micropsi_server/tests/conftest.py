
import os
import pytest
import logging
from webtest import TestApp


import configuration
configuration.RESOURCE_PATH = '/tmp/micropsi_tests'
configuration.SERVER_SETTINGS_PATH = '/tmp/micropsi_tests'

from micropsi_core import runtime as micropsi

try:
    os.makedirs('/tmp/micropsi_tests/worlds')
except OSError:
    pass
try:
    os.makedirs('/tmp/micropsi_tests/nodenets')
except OSError:
    pass

# create testuser:
from micropsi_server.micropsi_app import usermanager
usermanager.create_user('Pytest User', 'test', 'Administrator', uid='Pytest User')
user_token = usermanager.start_session('Pytest User', 'test', True)

world_uid = 'WorldOfPain'
nn_uid = 'Testnet'

logging.getLogger('system').setLevel(logging.WARNING)
logging.getLogger('world').setLevel(logging.WARNING)
logging.getLogger('nodenet').setLevel(logging.WARNING)


@pytest.fixture
def nodetype_def():
    return os.path.join(configuration.RESOURCE_PATH, 'nodetypes.json')


@pytest.fixture
def nodefunc_def():
    return os.path.join(configuration.RESOURCE_PATH, 'nodefunctions.py')


@pytest.fixture
def recipes_def():
    return os.path.join(configuration.RESOURCE_PATH, 'recipes.py')


def set_logging_levels():
    logging.getLogger('system').setLevel(logging.WARNING)
    logging.getLogger('world').setLevel(logging.WARNING)
    logging.getLogger('nodenet').setLevel(logging.WARNING)


class MicropsiTestApp(TestApp):
    auth = None

    def set_auth(self):
        self.auth = user_token

    def unset_auth(self):
        self.auth = None
        self.reset()

    def get_json(self, *args, **kwargs):
        headers = kwargs.setdefault("headers", {})
        if self.auth is not None:
            self.set_cookie('token', self.auth)
        headers["X-Requested-With"] = 'XMLHttpRequest'
        headers["Accept"] = "application/json"
        return super(MicropsiTestApp, self).get(*args, **kwargs)

    def post_json(self, *args, **kwargs):
        headers = kwargs.setdefault("headers", {})
        if self.auth is not None:
            self.set_cookie('token', self.auth)
        headers["X-Requested-With"] = 'XMLHttpRequest'
        headers["Accept"] = "application/json"
        return super(MicropsiTestApp, self).post_json(*args, **kwargs)


from micropsi_server.micropsi_app import micropsi_app
testapp = MicropsiTestApp(micropsi_app)


@pytest.fixture(scope="session")
def resourcepath():
    return configuration.RESOURCE_PATH


@pytest.fixture()
def app(test_world):
    return testapp


@pytest.fixture()
def test_world(request):
    global world_uid
    worlds = micropsi.get_available_worlds("Pytest User")
    if world_uid not in worlds:
        success, world_uid = micropsi.new_world("World of Pain", "Island", "Pytest User", uid=world_uid)

    def fin():
        try:
            micropsi.revert_world(world_uid)
        except KeyError:
            pass  # world was deleted in test
    request.addfinalizer(fin)
    return world_uid


@pytest.fixture()
def test_nodenet(request):
    global nn_uid
    nodenets = micropsi.get_available_nodenets("Pytest User") or {}
    if nn_uid not in nodenets:
        success, nn_uid = micropsi.new_nodenet("Testnet", worldadapter="Default", owner="Pytest User", world_uid=world_uid, uid='Testnet')
        micropsi.add_node(nn_uid, 'Concept', [10, 10], uid='N1', name='N1')
        micropsi.add_link(nn_uid, 'N1', 'gen', 'N1', 'gen')
        micropsi.save_nodenet(nn_uid)

    def fin():
            micropsi.revert_nodenet(nn_uid)
    request.addfinalizer(fin)
    return nn_uid


def pytest_runtest_call(item):
    if 'fixed_test_nodenet' in micropsi.nodenets:
        micropsi.revert_nodenet("fixed_test_nodenet")
    micropsi.logger.clear_logs()
    set_logging_levels()


def pytest_runtest_teardown(item, nextitem):
    if nextitem is None:
        print("DELETING ALL STUFF")
        import shutil
        shutil.rmtree(configuration.RESOURCE_PATH)

