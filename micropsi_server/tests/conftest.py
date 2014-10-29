
import os
import pytest
import logging
from webtest import TestApp
from base64 import b64encode

try:
    os.makedirs('/tmp/micropsi_tests/worlds')
except OSError:
    pass
try:
    os.makedirs('/tmp/micropsi_tests/nodenets')
except OSError:
    pass

import configuration
configuration.RESOURCE_PATH = '/tmp/micropsi_tests'

world_uid = None
nn_uid = None

logging.getLogger('system').setLevel(logging.WARNING)
logging.getLogger('world').setLevel(logging.WARNING)
logging.getLogger('nodenet').setLevel(logging.WARNING)


def set_logging_levels():
    logging.getLogger('system').setLevel(logging.WARNING)
    logging.getLogger('world').setLevel(logging.WARNING)
    logging.getLogger('nodenet').setLevel(logging.WARNING)


class MicropsiTestApp(TestApp):
    auth = None

    def set_auth(self, user, password):
        self.auth = (user, password)

    def _gen_request(self, method, url, **kw):
        if self.auth:
            headers = kw.get("headers")
            if not headers:
                headers = kw["headers"] = {}
            headers["X-Devpi-Auth"] = b64encode("%s:%s" % self.auth)
        return super(MicropsiTestApp, self)._gen_request(method, url, **kw)

    def get_json(self, *args, **kwargs):
        headers = kwargs.setdefault("headers", {})
        headers["X-Requested-With"] = 'XMLHttpRequest'
        headers["Accept"] = "application/json"
        return super(MicropsiTestApp, self).get(*args, **kwargs)

    def post_json(self, *args, **kwargs):
        headers = kwargs.setdefault("headers", {})
        headers["X-Requested-With"] = 'XMLHttpRequest'
        headers["Accept"] = "application/json"
        return super(MicropsiTestApp, self).post(*args, **kwargs)


from micropsi_server.micropsi_app import micropsi_app
testapp = MicropsiTestApp(micropsi_app)


@pytest.fixture(scope="session")
def resourcepath():
    return configuration.RESOURCE_PATH


@pytest.fixture(scope="session")
def app(test_world):
    return testapp


@pytest.fixture(scope="session")
def test_world(request):
    global world_uid
    worlds = micropsi.get_available_worlds("Pytest User")
    if worlds:
        world_uid = list(worlds.keys())[0]
    else:
        success, world_uid = micropsi.new_world("World of Pain", "Island", "Pytest User")

    def fin():
        micropsi.delete_world(world_uid)
    request.addfinalizer(fin)
    return world_uid


@pytest.fixture(scope="session")
def test_nodenet(request):
    global nn_uid
    nodenets = micropsi.get_available_nodenets("Pytest User") or {}
    for uid, nn in nodenets.items():
        if(nn.name == 'Testnet'):
            nn_uid = list(nodenets.keys())[0]
    else:
        success, nn_uid = micropsi.new_nodenet("Testnet", "Default", owner="Pytest User", world_uid=world_uid, uid='Testnet')

    def fin():
        micropsi.delete_nodenet(nn_uid)
    request.addfinalizer(fin)
    return nn_uid


def pytest_runtest_call(item):
    if 'fixed_test_nodenet' in micropsi.nodenets:
        micropsi.revert_nodenet("fixed_test_nodenet")
    micropsi.logger.clear_logs()
    set_logging_levels()

