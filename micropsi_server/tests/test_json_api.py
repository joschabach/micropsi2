
import pytest
import json
import re


def test_generate_uid(app):
    response = app.get_json('/rpc/generate_uid()')
    assert 'status' in response.json_body
    assert re.match('[a-f0-9]+', response.json_body['data']) is not None


def test_get_available_nodenets(app):
    response = app.get_json('/rpc/get_available_nodenets(user_id="Pytest User")')
    assert 'status' in response.json_body
    import pdb; pdb.set_trace()
