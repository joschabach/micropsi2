
import os
import pytest
from webtest import TestApp

nn_uid = 'Testnet'

from configuration import config
from micropsi_server import usermanagement
from micropsi_server.micropsi_app import usermanager

user_token = list(usermanager.users['Pytest User']['sessions'].keys())[0]
test_path = os.path.join(config['paths']['persistency_directory'], 'user-test-db.json')


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
def app(default_world):
    return testapp


@pytest.fixture(scope="function")
def user_def():
    return test_path


@pytest.fixture(scope="function")
def user_mgr(user_def):
    return usermanagement.UserManager(user_def)


@pytest.fixture(scope="function")
def eliza(user_mgr):
    """ creates a user eliza, and a session. returns eliza's session token """
    user_mgr.create_user("eliza", "qwerty", "Full")
    token = user_mgr.start_session("eliza")
    return token
