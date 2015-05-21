
import pytest
from webtest import TestApp

# create testuser:
from micropsi_server.micropsi_app import usermanager
usermanager.create_user('Pytest User', 'test', 'Administrator', uid='Pytest User')
user_token = usermanager.start_session('Pytest User', 'test', True)


nn_uid = 'Testnet'


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


@pytest.fixture()
def app(test_world):
    return testapp
