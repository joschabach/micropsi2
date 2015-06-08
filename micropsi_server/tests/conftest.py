
import os
import pytest
from webtest import TestApp

nn_uid = 'Testnet'

from configuration import config
from conftest import user_token
from micropsi_server import usermanagement

test_path = os.path.join(config['paths']['resource_path'], 'user-test-db.json')


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


def pytest_runtest_teardown(item, nextitem):
    if nextitem is not None:
        if os.path.isfile(test_path):
            os.remove(test_path)


@pytest.fixture()
def app(test_world):
    return testapp


@pytest.fixture(scope="function")
def user_def():
    return test_path


@pytest.fixture(scope="function")
def user_mgr(user_def):
    return usermanagement.UserManager(user_def)


@pytest.fixture(scope="function")
def eliza(user_mgr):
    user_mgr.create_user("eliza", "qwerty", "Full")
    user_mgr.start_session("eliza")
    return "eliza"
