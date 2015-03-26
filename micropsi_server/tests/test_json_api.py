
import pytest
import json
import re


def assert_success(response):
    assert response.json_body['status'] == 'success'
    assert 'data' in response.json_body


def assert_failure(response):
    assert response.json_body['status'] == 'error'
    assert 'data' in response.json_body


def test_generate_uid(app):
    response = app.get_json('/rpc/generate_uid()')
    assert_success(response)
    assert re.match('[a-f0-9]+', response.json_body['data']) is not None


def test_select_nodenet(app, test_nodenet):
    app.set_auth()
    response = app.get_json('/rpc/select_nodenet(nodenet_uid="%s")' % test_nodenet)
    assert_success(response)
    data = response.json_body['data']
    assert data == test_nodenet


def test_load_nodenet(app, test_nodenet):
    response = app.get_json('/rpc/load_nodenet(nodenet_uid="%s",coordinates={"x1":0,"x2":100,"y1":0,"y2":100})' % test_nodenet)
    assert_success(response)
    data = response.json_body['data']
    assert 'nodetypes' in data
    assert 'nodes' in data
    assert 'links' in data
    assert data['uid'] == test_nodenet


def test_new_nodenet(app):
    app.set_auth()
    response = app.post_json('/rpc/new_nodenet', params={
        'name': 'FooBarTestNet'
    })
    assert_success(response)
    uid = response.json_body['data']
    assert uid is not None
    response = app.get_json('/rpc/load_nodenet(nodenet_uid="%s",coordinates={"x1":0,"x2":100,"y1":0,"y2":100})' % uid)
    assert_success(response)
    assert response.json_body['data']['name'] == 'FooBarTestNet'
    assert response.json_body['data']['nodes'] == {}


def test_get_available_nodenets(app, test_nodenet):
    response = app.get_json('/rpc/get_available_nodenets(user_id="Pytest User")')
    assert_success(response)
    assert test_nodenet in response.json_body['data']


def test_delete_nodenet(app, test_nodenet):
    response = app.get_json('/rpc/delete_nodenet(nodenet_uid="%s")' % test_nodenet)
    assert_success(response)
    response = app.get_json('/rpc/get_available_nodenets(user_id="Pytest User")')
    assert test_nodenet not in response.json_body['data']


def test_set_nodenet_properties(app, test_nodenet, test_world):
    app.set_auth()
    response = app.post_json('/rpc/set_nodenet_properties', params=dict(nodenet_uid=test_nodenet, nodenet_name="new_name", worldadapter="Braitenberg", world_uid=test_world, settings={'foo': 'bar'}))
    assert_success(response)
    response = app.get_json('/rpc/load_nodenet(nodenet_uid="%s",coordinates={"x1":0,"x2":100,"y1":0,"y2":100})' % test_nodenet)
    data = response.json_body['data']
    assert data['name'] == 'new_name'
    assert data['worldadapter'] == 'Braitenberg'
    assert data['settings']['foo'] == 'bar'


def test_set_node_state(app, test_nodenet):
    response = app.post_json('/rpc/set_node_state', params={
        'nodenet_uid': test_nodenet,
        'node_uid': 'N1',
        'state': {'foo': 'bar'}
    })
    assert_success(response)
    response = app.get_json('/rpc/load_nodenet(nodenet_uid="%s",coordinates={"x1":0,"x2":100,"y1":0,"y2":100})' % test_nodenet)
    assert response.json_body['data']['nodes']['N1']['state'] == {'foo': 'bar'}


def test_set_node_activation(app, test_nodenet):
    response = app.post_json('/rpc/set_node_activation', params={
        'nodenet_uid': test_nodenet,
        'node_uid': 'N1',
        'activation': '0.734'
    })
    assert_success(response)
    response = app.get_json('/rpc/load_nodenet(nodenet_uid="%s",coordinates={"x1":0,"x2":100,"y1":0,"y2":100})' % test_nodenet)
    sheaves = response.json_body['data']['nodes']['N1']['sheaves']
    assert sheaves['default']['activation'] == 0.734


def test_start_simulation(app, test_nodenet):
    app.set_auth()
    response = app.get_json('/rpc/load_nodenet(nodenet_uid="%s",coordinates={"x1":0,"x2":100,"y1":0,"y2":100})' % test_nodenet)
    response = app.post_json('/rpc/start_simulation', params=dict(nodenet_uid=test_nodenet))
    assert_success(response)
    response = app.get_json('/rpc/load_nodenet(nodenet_uid="%s",coordinates={"x1":0,"x2":100,"y1":0,"y2":100})' % test_nodenet)
    assert response.json_body['data']['is_active']


def test_get_runner_properties(app):
    app.set_auth()
    response = app.get_json('/rpc/get_runner_properties()')
    assert_success(response)
    assert 'timestep' in response.json_body['data']
    assert 'factor' in response.json_body['data']


def test_set_runner_properties(app):
    app.set_auth()
    response = app.post_json('/rpc/set_runner_properties', params=dict(timestep=123, factor=1))
    assert_success(response)
    response = app.get_json('/rpc/get_runner_properties()')
    assert_success(response)
    assert response.json_body['data']['timestep'] == 123
    assert response.json_body['data']['factor'] == 1


def test_get_is_simulation_running(app, test_nodenet):
    response = app.get_json('/rpc/get_is_simulation_running(nodenet_uid="%s")' % test_nodenet)
    assert_success(response)
    assert not response.json_body['data']


def test_stop_simulation(app, test_nodenet):
    app.set_auth()
    response = app.post_json('/rpc/start_simulation', params=dict(nodenet_uid=test_nodenet))
    assert_success(response)
    response = app.get_json('/rpc/get_is_simulation_running(nodenet_uid="%s")' % test_nodenet)
    assert_success(response)
    assert response.json_body['data']
    response = app.post_json('/rpc/stop_simulation', params=dict(nodenet_uid=test_nodenet))
    assert_success(response)
    response = app.get_json('/rpc/get_is_simulation_running(nodenet_uid="%s")' % test_nodenet)
    assert_success(response)
    assert not response.json_body['data']


def test_step_simulation(app, test_nodenet):
    app.set_auth()
    response = app.get_json('/rpc/load_nodenet(nodenet_uid="%s",coordinates={"x1":0,"x2":100,"y1":0,"y2":100})' % test_nodenet)
    assert response.json_body['data']['current_step'] == 0
    response = app.get_json('/rpc/step_simulation(nodenet_uid="%s")' % test_nodenet)
    assert_success(response)
    assert response.json_body['data'] == 1
    response = app.get_json('/rpc/load_nodenet(nodenet_uid="%s",coordinates={"x1":0,"x2":100,"y1":0,"y2":100})' % test_nodenet)
    assert response.json_body['data']['current_step'] == 1


def test_get_current_state(app, test_nodenet, test_world):
    from time import sleep
    app.set_auth()
    response = app.get_json('/rpc/load_nodenet(nodenet_uid="%s",coordinates={"x1":0,"x2":100,"y1":0,"y2":100})' % test_nodenet)
    assert response.json_body['data']['current_step'] == 0
    response = app.post_json('/rpc/set_nodenet_properties', params=dict(nodenet_uid=test_nodenet, nodenet_name="new_name", worldadapter="Braitenberg", world_uid=test_world, settings={'foo': 'bar'}))

    response = app.post_json('/rpc/add_gate_monitor', params={
        'nodenet_uid': test_nodenet,
        'node_uid': 'N1',
        'gate': 'sub',
    })
    monitor_uid = response.json_body['data']
    response = app.get_json('/rpc/start_simulation(nodenet_uid="%s")' % test_nodenet)
    sleep(0.4)
    response = app.post_json('/rpc/get_current_state', params={
        'nodenet_uid': test_nodenet,
        'nodenet': {
            'nodespace': 'Root',
            'step': -1,
        },
        'monitors': {
            'logger': ['system', 'world', 'nodenet'],
            'after': 0
        },
        'world': {
            'step': -1
        }
    })

    data = response.json_body['data']

    assert data['current_nodenet_step'] > 0
    assert data['current_world_step'] > 0
    assert data['simulation_running']

    assert 'nodenet' in data
    assert data['nodenet']['current_step'] > 0
    assert data['nodenet']['is_active']

    assert 'servertime' in data['monitors']['logs']
    assert 'logs' in data['monitors']['logs']
    assert len(data['monitors']['monitors'][monitor_uid]['values']) == data['nodenet']['current_step']

    assert test_nodenet in data['world']['agents']
    assert data['world']['current_step'] > 0


def test_revert_nodenet(app, test_nodenet, test_world):
    app.set_auth()
    response = app.post_json('/rpc/set_nodenet_properties', params=dict(nodenet_uid=test_nodenet, nodenet_name="new_name", worldadapter="Braitenberg", world_uid=test_world, settings={'foo': 'bar'}))
    assert_success(response)
    response = app.get_json('/rpc/revert_nodenet(nodenet_uid="%s")' % test_nodenet)
    assert_success(response)
    response = app.get_json('/rpc/load_nodenet(nodenet_uid="%s",coordinates={"x1":0,"x2":100,"y1":0,"y2":100})' % test_nodenet)
    data = response.json_body['data']
    assert data['name'] == 'Testnet'
    assert data['worldadapter'] == 'Default'
    assert data['settings'] == {}


def test_save_nodenet(app, test_nodenet, test_world):
    app.set_auth()
    response = app.post_json('/rpc/set_nodenet_properties', params=dict(nodenet_uid=test_nodenet, nodenet_name="new_name", worldadapter="Braitenberg", world_uid=test_world, settings={'foo': 'bar'}))
    assert_success(response)
    response = app.get_json('/rpc/save_nodenet(nodenet_uid="%s")' % test_nodenet)
    assert_success(response)
    response = app.get_json('/rpc/revert_nodenet(nodenet_uid="%s")' % test_nodenet)
    assert_success(response)
    response = app.get_json('/rpc/load_nodenet(nodenet_uid="%s",coordinates={"x1":0,"x2":100,"y1":0,"y2":100})' % test_nodenet)
    data = response.json_body['data']
    assert data['name'] == 'new_name'
    assert data['worldadapter'] == 'Braitenberg'
    assert data['settings']['foo'] == 'bar'

    # now delete the nodenet, to get default state back.
    app.get_json('/rpc/delete_nodenet(nodenet_uid="%s")' % test_nodenet)


def test_export_nodenet(app, test_nodenet):
    response = app.get_json('/rpc/export_nodenet(nodenet_uid="%s")' % test_nodenet)
    assert_success(response)
    data = json.loads(response.json_body['data'])
    assert data['name'] == 'Testnet'
    assert data['nodes']['N1']['type'] == 'Concept'


def test_import_nodenet(app, test_nodenet):
    app.set_auth()
    response = app.get_json('/rpc/export_nodenet(nodenet_uid="%s")' % test_nodenet)
    data = json.loads(response.json_body['data'])
    del data['uid']
    response = app.post_json('/rpc/import_nodenet', params={
        'nodenet_data': json.dumps(data)
    })
    assert_success(response)
    uid = response.json_body['data']
    assert uid is not None
    response = app.get_json('/rpc/load_nodenet(nodenet_uid="%s",coordinates={"x1":0,"x2":100,"y1":0,"y2":100})' % uid)
    assert list(response.json_body['data']['nodes'].keys()) == ['N1']
    assert response.json_body['data']['name'] == 'Testnet'
    response = app.get_json('/rpc/delete_nodenet(nodenet_uid="%s")' % uid)


def test_merge_nodenet(app, test_nodenet):
    app.set_auth()
    response = app.get_json('/rpc/export_nodenet(nodenet_uid="%s")' % test_nodenet)
    data = json.loads(response.json_body['data'])
    response = app.post_json('/rpc/new_nodenet', params={
        'name': 'ImporterNet',
        'worldadapter': 'Braitenberg',
        'owner': 'Pytest User'
    })
    uid = response.json_body['data']

    data['uid'] = uid
    response = app.post_json('/rpc/merge_nodenet', params={
        'nodenet_uid': uid,
        'nodenet_data': json.dumps(data)
    })
    assert_success(response)
    response = app.get_json('/rpc/load_nodenet(nodenet_uid="%s",coordinates={"x1":0,"x2":100,"y1":0,"y2":100})' % uid)
    assert list(response.json_body['data']['nodes'].keys()) == ['N1']
    assert response.json_body['data']['name'] == 'Testnet'
    response = app.get_json('/rpc/delete_nodenet(nodenet_uid="%s")' % uid)


###################################################
##
##
##      WORLD
##
##
###################################################

def test_get_available_worlds(app, test_world):
    response = app.get_json('/rpc/get_available_worlds()')
    assert_success(response)
    assert test_world in response.json_body['data']


def test_get_available_worlds_for_user(app, test_world):
    response = app.get_json('/rpc/get_available_worlds(user_id="Pytest User")')
    assert_success(response)
    assert test_world in response.json_body['data']


# TODO: get_nodenet_properties is missing.
def test_get_world_properties(app, test_world):
    response = app.get_json('/rpc/get_world_properties(world_uid="%s")' % test_world)
    assert_success(response)
    data = response.json_body['data']
    assert data['uid'] == test_world
    assert data['name'] == "World of Pain"
    assert 'available_worldadapters' in data
    assert 'available_worldobjects' in data


def test_get_worldadapters(app, test_world):
    response = app.get_json('/rpc/get_worldadapters(world_uid="%s")' % test_world)
    assert_success(response)
    assert 'Braitenberg' in response.json_body['data']


def test_get_world_objects(app, test_world):
    response = app.get_json('/rpc/get_world_objects(world_uid="%s")' % test_world)
    assert_success(response)
    assert response.json_body['data'] == {}


def test_add_worldobject(app, test_world):
    response = app.post_json('/rpc/add_worldobject', params={
        'world_uid': test_world,
        'type': 'Braintree',
        'position': [10, 10],
        'name': 'Testtree'
    })
    assert_success(response)
    uid = response.json_body['data']
    assert uid is not None
    response = app.get_json('/rpc/get_world_objects(world_uid="%s")' % test_world)
    assert uid in response.json_body['data']


def test_delete_worldobject(app, test_world):
    response = app.post_json('/rpc/add_worldobject', params={
        'world_uid': test_world,
        'type': 'Braintree',
        'position': [10, 10],
        'name': 'Testtree'
    })
    uid = response.json_body['data']
    response = app.post_json('/rpc/delete_worldobject', params={
        'world_uid': test_world,
        'object_uid': uid
    })
    assert_success(response)
    response = app.get_json('/rpc/get_world_objects(world_uid="%s")' % test_world)
    assert uid not in response.json_body['data']


def test_set_worldobject_properties(app, test_world):
    response = app.post_json('/rpc/add_worldobject', params={
        'world_uid': test_world,
        'type': 'Braintree',
        'position': [10, 10],
        'name': 'Testtree'
    })
    uid = response.json_body['data']
    response = app.post_json('/rpc/set_worldobject_properties', params={
        'world_uid': test_world,
        'uid': uid,
        'position': [20, 20],
        'orientation': 27,
        'name': 'edited'
    })
    assert_success(response)
    response = app.get_json('/rpc/get_world_objects(world_uid="%s")' % test_world)
    data = response.json_body['data']
    assert data[uid]['position'] == [20, 20]
    assert data[uid]['orientation'] == 27
    assert data[uid]['name'] == 'edited'


def test_get_world_view(app, test_world):
    response = app.get_json('/rpc/get_world_view(world_uid="%s", step=0)' % test_world)
    assert_success(response)
    assert 'agents' in response.json_body['data']
    assert 'objects' in response.json_body['data']
    assert response.json_body['data']['current_step'] == 0
    assert 'step' not in response.json_body['data']


def test_set_worldagent_properties(app, test_world, test_nodenet):
    # create agent.
    app.set_auth()
    response = app.post_json('/rpc/set_nodenet_properties', params=dict(nodenet_uid=test_nodenet, worldadapter="Braitenberg", world_uid=test_world))
    response = app.post_json('/rpc/set_worldagent_properties', params={
        'world_uid': test_world,
        'uid': test_nodenet,
        'position': [23, 23],
        'orientation': 37,
        'name': 'Sepp'
    })
    assert_success(response)
    response = app.get_json('/rpc/get_world_view(world_uid="%s", step=0)' % test_world)
    data = response.json_body['data']['agents'][test_nodenet]
    assert data['position'] == [23, 23]
    assert data['orientation'] == 37
    assert data['name'] == 'Sepp'


def test_new_world(app):
    app.set_auth()
    response = app.post_json('/rpc/new_world', params={
        'world_name': 'FooBarTestWorld',
        'world_type': 'Island'
    })
    assert_success(response)
    uid = response.json_body['data']
    response = app.get_json('/rpc/get_available_worlds(user_id="Pytest User")')
    assert uid in response.json_body['data']


def test_get_available_world_types(app):
    response = app.get_json('/rpc/get_available_world_types()')
    assert_success(response)
    assert 'Island' in response.json_body['data']


def test_delete_world(app, test_world):
    # delete the world created in the test above
    response = app.get_json('/rpc/get_available_worlds(user_id="Pytest User")')
    world_uid = None
    for uid, data in response.json_body['data'].items():
        if data['name'] == "FooBarTestWorld" and uid != test_world:
            world_uid = uid
            break
    assert world_uid is not None
    response = app.get_json('/rpc/delete_world(world_uid="%s")' % world_uid)
    assert_success(response)
    response = app.get_json('/rpc/get_available_worlds(user_id="Pytest User")')
    assert world_uid not in response.json_body['data']


def test_set_world_properties(app, test_world):
    app.set_auth()
    response = app.post_json('/rpc/set_world_properties', params={
        'world_uid': test_world,
        'world_name': 'asdf',
        'owner': 'Pytest User'
    })
    assert_success(response)
    response = app.get_json('/rpc/get_world_properties(world_uid="%s")' % test_world)
    assert response.json_body['data']['name'] == "asdf"


def test_revert_world(app, test_world):
    app.set_auth()
    response = app.post_json('/rpc/add_worldobject', params={
        'world_uid': test_world,
        'type': 'Braintree',
        'position': [10, 10],
        'name': 'Testtree'
    })
    response = app.get_json('/rpc/revert_world(world_uid="%s")' % test_world)
    assert_success(response)
    response = app.get_json('/rpc/get_world_view(world_uid="%s",step=0)' % test_world)
    data = response.json_body['data']
    assert data['objects'] == {}


def test_save_world(app, test_world):
    app.set_auth()
    response = app.post_json('/rpc/add_worldobject', params={
        'world_uid': test_world,
        'type': 'Braintree',
        'position': [10, 10],
        'name': 'Testtree'
    })
    uid = response.json_body['data']
    response = app.get_json('/rpc/save_world(world_uid="%s")' % test_world)
    assert_success(response)
    response = app.get_json('/rpc/revert_world(world_uid="%s")' % test_world)
    response = app.get_json('/rpc/get_world_view(world_uid="%s",step=0)' % test_world)
    data = response.json_body['data']
    assert uid in data['objects']
    # delete the world, to get the default state back
    app.get_json('/rpc/delete_world(world_uid="%s")' % test_world)


def test_export_world(app, test_world):
    response = app.get_json('/rpc/export_world(world_uid="%s")' % test_world)
    assert_success(response)
    export_data = json.loads(response.json_body['data'])
    assert export_data['uid'] == test_world
    assert export_data['name'] == 'World of Pain'
    assert export_data['objects'] == {}
    assert export_data['agents'] == {}
    assert export_data['owner'] == 'Pytest User'
    assert export_data['current_step'] == 0
    assert export_data['world_type'] == 'Island'


def test_import_world(app, test_world):
    response = app.get_json('/rpc/export_world(world_uid="%s")' % test_world)
    data = json.loads(response.json_body['data'])
    del data['uid']
    data['name'] = 'Copied Pain'
    response = app.post_json('/rpc/import_world', params={
        'worlddata': json.dumps(data)
    })
    assert_success(response)
    uid = response.json_body['data']
    response = app.get_json('/rpc/export_world(world_uid="%s")' % uid)
    data = json.loads(response.json_body['data'])
    assert data['owner'] == 'Pytest User'
    assert data['name'] == 'Copied Pain'
    assert data['objects'] == {}
    assert data['agents'] == {}
    assert uid != test_world


###################################################
##
##
##      MONITORS
##
##
###################################################

def test_export_monitor_data_all(app, test_nodenet):
    response = app.get_json('/rpc/export_monitor_data(nodenet_uid="%s")' % test_nodenet)
    assert_success(response)
    assert response.json_body['data'] == {}


def test_add_gate_monitor(app, test_nodenet):
    response = app.post_json('/rpc/add_gate_monitor', params={
        'nodenet_uid': test_nodenet,
        'node_uid': 'N1',
        'gate': 'sub',
        'sheaf': 'default'
    })
    assert_success(response)
    uid = response.json_body['data']
    response = app.post_json('/rpc/export_monitor_data', params={
        'nodenet_uid': test_nodenet,
        'monitor_uid': uid
    })
    assert response.json_body['data']['node_uid'] == 'N1'
    assert response.json_body['data']['target'] == 'sub'
    assert response.json_body['data']['type'] == 'gate'
    assert response.json_body['data']['sheaf'] == 'default'
    assert response.json_body['data']['values'] == {}


def test_add_slot_monitor(app, test_nodenet):
    response = app.post_json('/rpc/add_slot_monitor', params={
        'nodenet_uid': test_nodenet,
        'node_uid': 'N1',
        'slot': 'gen',
        'name': 'Foobar'
    })
    assert_success(response)
    uid = response.json_body['data']
    response = app.post_json('/rpc/export_monitor_data', params={
        'nodenet_uid': test_nodenet,
        'monitor_uid': uid
    })
    assert response.json_body['data']['name'] == 'Foobar'
    assert response.json_body['data']['node_uid'] == 'N1'
    assert response.json_body['data']['target'] == 'gen'
    assert response.json_body['data']['type'] == 'slot'
    assert response.json_body['data']['sheaf'] == 'default'
    assert response.json_body['data']['values'] == {}


def test_add_link_monitor(app, test_nodenet):
    response = app.post_json('/rpc/add_link_monitor', params={
        'nodenet_uid': test_nodenet,
        'source_node_uid': 'N1',
        'gate_type': 'gen',
        'target_node_uid': 'N1',
        'slot_type': 'gen',
        'property': 'weight',
        'name': 'LinkWeight'
    })
    assert_success(response)
    uid = response.json_body['data']
    response = app.post_json('/rpc/export_monitor_data', params={
        'nodenet_uid': test_nodenet,
        'monitor_uid': uid
    })
    assert response.json_body['data']['name'] == 'LinkWeight'
    assert response.json_body['data']['source_node_uid'] == 'N1'
    assert response.json_body['data']['gate_type'] == 'gen'
    assert response.json_body['data']['target_node_uid'] == 'N1'
    assert response.json_body['data']['slot_type'] == 'gen'
    assert response.json_body['data']['property'] == 'weight'


def test_add_custom_monitor(app, test_nodenet):
    response = app.post_json('/rpc/add_custom_monitor', params={
        'nodenet_uid': test_nodenet,
        'function': 'return len(netapi.get_nodes())',
        'name': 'nodecount'
    })
    assert_success(response)
    uid = response.json_body['data']
    response = app.post_json('/rpc/export_monitor_data', params={
        'nodenet_uid': test_nodenet,
        'monitor_uid': uid
    })
    assert response.json_body['data']['name'] == 'nodecount'


def test_remove_monitor(app, test_nodenet):
    response = app.post_json('/rpc/add_slot_monitor', params={
        'nodenet_uid': test_nodenet,
        'node_uid': 'N1',
        'slot': 'gen'
    })
    uid = response.json_body['data']
    response = app.post_json('/rpc/remove_monitor', params={
        'nodenet_uid': test_nodenet,
        'monitor_uid': uid
    })
    assert_success(response)
    response = app.post_json('/rpc/export_monitor_data', params={
        'nodenet_uid': test_nodenet
    })
    assert uid not in response.json_body['data']


def test_clear_monitor(app, test_nodenet):
    response = app.post_json('/rpc/add_slot_monitor', params={
        'nodenet_uid': test_nodenet,
        'node_uid': 'N1',
        'slot': 'gen'
    })
    uid = response.json_body['data']
    response = app.post_json('/rpc/clear_monitor', params={
        'nodenet_uid': test_nodenet,
        'monitor_uid': uid
    })
    assert_success(response)


def test_get_monitor_data(app, test_nodenet):
    response = app.post_json('/rpc/add_gate_monitor', params={
        'nodenet_uid': test_nodenet,
        'node_uid': 'N1',
        'gate': 'sub'
    })
    uid = response.json_body['data']
    response = app.post_json('/rpc/get_monitor_data', params={
        'nodenet_uid': test_nodenet,
        'step': 0
    })
    assert_success(response)
    assert uid in response.json_body['data']['monitors']


###################################################
##
##
##      NODENET
##
##
###################################################

def test_get_nodespace_list(app, test_nodenet):
    response = app.get_json('/rpc/get_nodespace_list(nodenet_uid="%s")' % test_nodenet)
    assert_success(response)
    assert response.json_body['data']['Root']['name'] == 'Root'
    assert response.json_body['data']['Root']['parent'] is None
    assert 'N1' in response.json_body['data']['Root']['nodes']


def test_get_nodespace(app, test_nodenet):
    response = app.post_json('/rpc/get_nodespace', params={
        'nodenet_uid': test_nodenet,
        'nodespace': 'Root',
        'step': -1,
        'coordinates': {'x1': 0, 'x2': 100, 'y1': 0, 'y2': 100}
    })
    assert_success(response)
    assert 'N1' in response.json_body['data']['nodes']


def test_get_node(app, test_nodenet):
    response = app.get_json('/rpc/get_node(nodenet_uid="%s",node_uid="N1")' % test_nodenet)
    assert_success(response)
    assert response.json_body['data']['type'] == 'Concept'


def test_add_node(app, test_nodenet):
    app.set_auth()
    response = app.post_json('/rpc/add_node', params={
        'nodenet_uid': test_nodenet,
        'type': 'Register',
        'position': [23, 42],
        'nodespace': "Root",
        'uid': "N2",
        'name': 'N2'
    })
    assert_success(response)
    assert response.json_body['data'] == 'N2'


def test_clone_nodes(app, test_nodenet):
    app.set_auth()
    response = app.post_json('/rpc/clone_nodes', params={
        'nodenet_uid': test_nodenet,
        'node_uids': ['N1'],
        'clone_mode': 'all',
        'nodespace': 'Root',
        'offset': [23, 23]
    })
    assert_success(response)
    node = response.json_body['data']['nodes'][0]
    link = response.json_body['data']['links'][0]
    assert node['name'] == 'N1_copy'
    assert node['position'] == [33, 33]
    assert link['source_node_uid'] == node['uid']
    assert link['target_node_uid'] == node['uid']


def test_set_node_position(app, test_nodenet):
    app.set_auth()
    response = app.post_json('/rpc/set_node_position', params={
        'nodenet_uid': test_nodenet,
        'node_uid': 'N1',
        'position': [42, 23]
    })
    assert_success(response)
    response = app.get_json('/rpc/get_node(nodenet_uid="%s",node_uid="N1")' % test_nodenet)
    assert response.json_body['data']['position'] == [42, 23]


def test_set_node_name(app, test_nodenet):
    app.set_auth()
    response = app.post_json('/rpc/set_node_name', params={
        'nodenet_uid': test_nodenet,
        'node_uid': 'N1',
        'name': 'changed'
    })
    assert_success(response)
    response = app.get_json('/rpc/get_node(nodenet_uid="%s",node_uid="N1")' % test_nodenet)
    assert response.json_body['data']['name'] == 'changed'


def test_delete_node(app, test_nodenet):
    app.set_auth()
    response = app.post_json('/rpc/delete_node', params={
        'nodenet_uid': test_nodenet,
        'node_uid': 'N1'
    })
    assert_success(response)
    response = app.get_json('/rpc/load_nodenet(nodenet_uid="%s",coordinates={"x1":0,"x2":100,"y1":0,"y2":100})' % test_nodenet)
    assert response.json_body['data']['nodes'] == {}


def test_align_nodes(app, test_nodenet):
    # TODO: Why does autoalign only move a node if it has no links?
    response = app.post_json('/rpc/add_node', params={
        'nodenet_uid': test_nodenet,
        'type': 'Register',
        'position': [5, 5],
        'nodespace': "Root",
        'uid': "N2",
        'name': 'N2'
    })
    response = app.post_json('/rpc/align_nodes', params={
        'nodenet_uid': test_nodenet,
        'nodespace': 'Root'
    })
    assert_success(response)
    response = app.get_json('/rpc/get_node(nodenet_uid="%s",node_uid="N2")' % test_nodenet)
    assert response.json_body['data']['position'] != [5, 5]


def test_get_available_node_types(app, test_nodenet):
    response = app.get_json('/rpc/get_available_node_types(nodenet_uid="%s")' % test_nodenet)
    assert_success(response)
    assert 'Concept' in response.json_body['data']
    assert 'Register' in response.json_body['data']
    assert 'Sensor' in response.json_body['data']


def test_get_available_native_module_types(app, test_nodenet):
    response = app.get_json('/rpc/get_available_native_module_types(nodenet_uid="%s")' % test_nodenet)
    assert_success(response)
    assert response.json_body['data'] == {}


def test_set_node_parameters(app, test_nodenet):
    app.set_auth()
    # add activator
    response = app.post_json('/rpc/add_node', params={
        'nodenet_uid': test_nodenet,
        'type': 'Activator',
        'nodespace': 'Root',
        'position': [23, 42],
        'uid': "A"
    })
    response = app.post_json('/rpc/set_node_parameters', params={
        'nodenet_uid': test_nodenet,
        'node_uid': 'A',
        'parameters': {'type': 'sub'}
    })
    assert_success(response)
    response = app.get_json('/rpc/get_node(nodenet_uid="%s",node_uid="A")' % test_nodenet)
    assert response.json_body['data']['parameters']['type'] == 'sub'


def test_get_gate_function(app, test_nodenet):
    response = app.post_json('/rpc/get_gate_function', params={
        'nodenet_uid': test_nodenet,
        'nodespace': 'Root',
        'node_type': 'Concept',
        'gate_type': 'sub'
    })
    assert_success(response)
    assert response.json_body['data'] == ''


def test_set_gate_function(app, test_nodenet):
    app.set_auth()
    response = app.post_json('/rpc/set_gate_function', params={
        'nodenet_uid': test_nodenet,
        'nodespace': 'Root',
        'node_type': 'Concept',
        'gate_type': 'sub',
        'gate_function': 'return -0.5'
    })
    assert_success(response)
    response = app.post_json('/rpc/get_gate_function', params={
        'nodenet_uid': test_nodenet,
        'nodespace': 'Root',
        'node_type': 'Concept',
        'gate_type': 'sub'
    })
    assert response.json_body['data'] == 'return -0.5'


def test_set_gate_parameters(app, test_nodenet):
    app.set_auth()
    response = app.post_json('/rpc/set_gate_parameters', params={
        'nodenet_uid': test_nodenet,
        'node_uid': 'N1',
        'gate_type': 'gen',
        'parameters': {'minimum': -2}
    })
    assert_success(response)
    response = app.get_json('/rpc/get_node(nodenet_uid="%s",node_uid="N1")' % test_nodenet)
    assert response.json_body['data']['gate_parameters']['gen']['minimum'] == -2


def test_get_available_datasources(app, test_nodenet, test_world):
    app.set_auth()
    # set worldadapter
    response = app.post_json('/rpc/set_nodenet_properties', params=dict(nodenet_uid=test_nodenet, world_uid=test_world, worldadapter="Braitenberg"))
    response = app.get_json('/rpc/get_available_datasources(nodenet_uid="%s")' % test_nodenet)
    assert_success(response)
    assert 'brightness_l' in response.json_body['data']
    assert 'brightness_l' in response.json_body['data']


def test_get_available_datatargets(app, test_nodenet, test_world):
    app.set_auth()
    response = app.post_json('/rpc/set_nodenet_properties', params=dict(nodenet_uid=test_nodenet, world_uid=test_world, worldadapter="Braitenberg"))
    response = app.get_json('/rpc/get_available_datatargets(nodenet_uid="%s")' % test_nodenet)
    assert_success(response)
    assert 'engine_l' in response.json_body['data']
    assert 'engine_r' in response.json_body['data']


def test_bind_datasource_to_sensor(app, test_nodenet):
    app.set_auth()
    app.post_json('/rpc/add_node', params={
        'nodenet_uid': test_nodenet,
        'type': 'Sensor',
        'position': [23, 42],
        'nodespace': 'Root',
        'uid': 'S'
    })
    response = app.post_json('/rpc/bind_datasource_to_sensor', params={
        'nodenet_uid': test_nodenet,
        'sensor_uid': 'S',
        'datasource': 'brightness_l'
    })
    assert_success(response)
    response = app.get_json('/rpc/get_node(nodenet_uid="%s",node_uid="S")' % test_nodenet)
    assert response.json_body['data']['parameters']['datasource'] == 'brightness_l'


def test_bind_datatarget_to_actor(app, test_nodenet):
    app.set_auth()
    app.post_json('/rpc/add_node', params={
        'nodenet_uid': test_nodenet,
        'type': 'Actor',
        'position': [23, 42],
        'nodespace': 'Root',
        'uid': 'A'
    })
    response = app.post_json('/rpc/bind_datatarget_to_actor', params={
        'nodenet_uid': test_nodenet,
        'actor_uid': 'A',
        'datatarget': 'engine_l'
    })
    assert_success(response)
    response = app.get_json('/rpc/get_node(nodenet_uid="%s",node_uid="A")' % test_nodenet)
    assert response.json_body['data']['parameters']['datatarget'] == 'engine_l'


def test_add_link(app, test_nodenet):
    app.set_auth()
    response = app.post_json('/rpc/add_link', params={
        'nodenet_uid': test_nodenet,
        'source_node_uid': 'N1',
        'gate_type': 'sub',
        'target_node_uid': 'N1',
        'slot_type': 'gen',
        'weight': 0.7
    })
    assert_success(response)
    uid = response.json_body['data']
    assert uid is not None
    response = app.get_json('/rpc/export_nodenet(nodenet_uid="%s")' % test_nodenet)
    data = json.loads(response.json_body['data'])
    assert uid in data['links']


def test_set_link_weight(app, test_nodenet):
    app.set_auth()
    response = app.post_json('/rpc/set_link_weight', params={
        'nodenet_uid': test_nodenet,
        'source_node_uid': "N1",
        'gate_type': "gen",
        'target_node_uid': "N1",
        'slot_type': "gen",
        'weight': 0.345
    })
    assert_success(response)
    response = app.get_json('/rpc/export_nodenet(nodenet_uid="%s")' % test_nodenet)
    data = json.loads(response.json_body['data'])
    assert data['links']['N1:gen:gen:N1']['weight'] == 0.345


def test_delete_link(app, test_nodenet):
    app.set_auth()
    response = app.post_json('/rpc/delete_link', params={
        'nodenet_uid': test_nodenet,
        'source_node_uid': "N1",
        'gate_type': "gen",
        'target_node_uid': "N1",
        'slot_type': "gen"
    })
    assert_success(response)
    response = app.get_json('/rpc/export_nodenet(nodenet_uid="%s")' % test_nodenet)
    data = json.loads(response.json_body['data'])
    data['links'] == {}


def test_reload_native_modules(app, test_nodenet, nodetype_def, nodefunc_def):
    app.set_auth()
    # create a native module:
    with open(nodetype_def, 'w') as fp:
        fp.write('{"Testnode": {\
            "name": "Testnode",\
            "slottypes": ["gen", "foo", "bar"],\
            "nodefunction_name": "testnodefunc",\
            "gatetypes": ["gen", "foo", "bar"],\
            "symbol": "t"}}')
    with open(nodefunc_def, 'w') as fp:
        fp.write("def testnodefunc(netapi, node=None, **prams):\r\n    return 17")
    response = app.get_json('/rpc/reload_native_modules()')
    assert_success(response)
    response = app.get_json('/rpc/get_available_node_types(nodenet_uid="%s")' % test_nodenet)
    data = response.json_body['data']['Testnode']
    assert data['nodefunction_name'] == "testnodefunc"
    assert data['gatetypes'] == ['gen', 'foo', 'bar']
    assert data['slottypes'] == ['gen', 'foo', 'bar']
    assert data['name'] == 'Testnode'


def test_user_prompt_response(app, test_nodenet):
    response = app.post_json('/rpc/user_prompt_response', {
        'nodenet_uid': test_nodenet,
        'node_uid': 'N1',
        'values': {'foo': 'bar'},
        'resume_nodenet': True
    })
    assert_success(response)
    response = app.get_json('/rpc/export_nodenet(nodenet_uid="%s")' % test_nodenet)
    data = json.loads(response.json_body['data'])
    assert data['nodes']['N1']['parameters']['foo'] == 'bar'
    assert data['is_active']


def test_set_logging_levels(app):
    response = app.post_json('/rpc/set_logging_levels', params={
        'system': 'INFO',
        'world': 'DEBUG',
        'nodenet': 'CRITICAL'
    })
    assert_success(response)
    import logging
    assert logging.getLogger('nodenet').getEffectiveLevel() == 50
    assert logging.getLogger('world').getEffectiveLevel() == 10
    assert logging.getLogger('system').getEffectiveLevel() == 20


def test_get_logger_messages(app, test_nodenet):
    response = app.get_json('/rpc/get_logger_messages(logger=["system"])')
    assert_success(response)
    assert 'servertime' in response.json_body['data']
    assert response.json_body['data']['logs'] == []


def test_get_monitoring_info(app, test_nodenet):
    response = app.get_json('/rpc/get_monitoring_info(nodenet_uid="%s",logger=["system,world"])' % test_nodenet)
    assert_success(response)
    assert 'logs' in response.json_body['data']
    assert 'current_step' in response.json_body['data']
    assert response.json_body['data']['monitors'] == {}
    assert 'servertime' in response.json_body['data']['logs']
    assert response.json_body['data']['logs']['logs'] == []


def test_400(app):
    app.set_auth()
    response = app.get_json('/rpc/save_nodenet("foobar")', expect_errors=True)
    assert_failure(response)
    assert "Malformed arguments" in response.json_body['data']


def test_401(app, test_nodenet):
    app.unset_auth()
    response = app.get_json('/rpc/delete_nodenet(nodenet_uid="%s")' % test_nodenet, expect_errors=True)
    assert_failure(response)
    assert 'Insufficient permissions' in response.json_body['data']


def test_404(app):
    response = app.get_json('/rpc/notthere(foo="bar")', expect_errors=True)
    assert_failure(response)
    assert response.json_body['data'] == "Function not found"


def test_405(app, test_nodenet):
    response = app.get_json('/rpc/get_available_nodenets', params={'nodenet_uid': test_nodenet}, expect_errors=True)
    assert_failure(response)
    assert response.json_body['data'] == "Method not allowed"


def test_500(app):
    response = app.get_json('/rpc/generate_uid(foo="bar")', expect_errors=True)
    assert_failure(response)
    assert "unexpected keyword argument" in response.json_body['data']
    assert response.json_body['traceback'] is not None


def test_get_recipes(app, test_nodenet, recipes_def):
    app.set_auth()
    with open(recipes_def, 'w') as fp:
        fp.write("""
def foobar(netapi, quatsch=23):
    return quatsch
""")
    response = app.get_json('/rpc/reload_native_modules(nodenet_uid="%s")' % test_nodenet)
    response = app.get_json('/rpc/get_available_recipes()')
    data = response.json_body['data']
    assert 'foobar' in data
    assert len(data['foobar']['parameters']) == 1
    assert data['foobar']['parameters'][0]['name'] == 'quatsch'
    assert data['foobar']['parameters'][0]['default'] == 23


def test_run_recipes(app, test_nodenet, recipes_def):
    app.set_auth()
    with open(recipes_def, 'w') as fp:
        fp.write("""
def foobar(netapi, quatsch=23):
    return quatsch
""")
    response = app.get_json('/rpc/reload_native_modules(nodenet_uid="%s")' % test_nodenet)
    response = app.post_json('/rpc/run_recipe', {
        'nodenet_uid': test_nodenet,
        'name': 'foobar',
        'parameters': {
            'quatsch': ''
        }
    })
    data = response.json_body['data']
    assert data == 23


def test_nodenet_data_structure(app, test_nodenet, nodetype_def, nodefunc_def):
    app.set_auth()
    from micropsi_core.nodenet.node import Nodetype
    with open(nodetype_def, 'w') as fp:
        fp.write('{"Testnode": {\
            "name": "Testnode",\
            "slottypes": ["gen", "foo", "bar"],\
            "nodefunction_name": "testnodefunc",\
            "gatetypes": ["gen", "foo", "bar"],\
            "symbol": "t"}}')
    with open(nodefunc_def, 'w') as fp:
        fp.write("def testnodefunc(netapi, node=None, **prams):\r\n    return 17")
    response = app.get_json('/rpc/reload_native_modules(nodenet_uid="%s")' % test_nodenet)
    app.post_json('/rpc/add_node', params={
        'nodenet_uid': test_nodenet,
        'type': 'Nodespace',
        'position': [23, 23],
        'nodespace': 'Root',
        'uid': 'NS1',
        'name': 'Test-Node-Space'
    })
    app.post_json('/rpc/add_node', params={
        'nodenet_uid': test_nodenet,
        'type': 'Concept',
        'position': [42, 42],
        'nodespace': 'NS1',
        'uid': 'N2'
    })
    response = app.post_json('/rpc/add_gate_monitor', params={
        'nodenet_uid': test_nodenet,
        'node_uid': 'N1',
        'gate': 'gen',
        'name': 'Testmonitor'
    })
    monitor_uid = response.json_body['data']

    response_1 = app.get_json('/rpc/load_nodenet(nodenet_uid="%s",coordinates={"x1":0,"x2":100,"y1":0,"y2":100})' % test_nodenet)
    response = app.get_json('/rpc/save_nodenet(nodenet_uid="%s")' % test_nodenet)
    response = app.get_json('/rpc/revert_nodenet(nodenet_uid="%s")' % test_nodenet)
    response_2 = app.get_json('/rpc/load_nodenet(nodenet_uid="%s",coordinates={"x1":0,"x2":100,"y1":0,"y2":100})' % test_nodenet)

    assert response_1.json_body['data'] == response_2.json_body['data']

    data = response_2.json_body['data']

    # Monitors
    response = app.get_json('/rpc/export_monitor_data(nodenet_uid="%s", monitor_uid="%s")' % (test_nodenet, monitor_uid))
    monitor_data = response.json_body['data']

    assert data['monitors'][monitor_uid]['name'] == 'Testmonitor'
    assert data['monitors'][monitor_uid]['node_uid'] == 'N1'
    assert data['monitors'][monitor_uid]['target'] == 'gen'
    assert data['monitors'][monitor_uid]['type'] == 'gate'
    assert data['monitors'][monitor_uid]['uid'] == monitor_uid
    assert data['monitors'][monitor_uid]['values'] == {}
    assert data['monitors'][monitor_uid] == monitor_data

    # Nodes
    response = app.get_json('/rpc/get_node(nodenet_uid="%s", node_uid="N1")' % test_nodenet)
    node_data = response.json_body['data']

    assert 'N1' in data['nodes']
    assert 'N2' not in data['nodes']
    assert 'NS1' not in data['nodes']

    for key in ['gen', 'por', 'ret', 'sub', 'sur', 'cat', 'exp', 'sym', 'ref']:
        assert data['nodes']['N1']['gate_activations'][key]['default']['activation'] == 0
        assert data['nodes']['N1']['gate_parameters'][key] == Nodetype.GATE_DEFAULTS

    assert data['nodes']['N1']['name'] == 'N1'
    assert data['nodes']['N1']['parameters'] == {}
    assert data['nodes']['N1']['parent_nodespace'] == 'Root'
    assert data['nodes']['N1']['position'] == [10, 10]
    assert data['nodes']['N1']['type'] == "Concept"
    assert data['nodes']['N1'] == node_data

    # Links
    assert data['links']['N1:gen:gen:N1']['weight'] == 1
    assert data['links']['N1:gen:gen:N1']['certainty'] == 1
    assert data['links']['N1:gen:gen:N1']['source_node_uid'] == 'N1'
    assert data['links']['N1:gen:gen:N1']['target_node_uid'] == 'N1'
    assert data['links']['N1:gen:gen:N1']['source_gate_name'] == 'gen'
    assert data['links']['N1:gen:gen:N1']['target_slot_name'] == 'gen'
    #assert data['links']['N1:gen:gen:N1'] == link_data

    # Nodespaces
    #assert data['nodespaces']['NS1']['index'] == 3
    assert data['nodespaces']['NS1']['name'] == 'Test-Node-Space'
    assert data['nodespaces']['NS1']['gatefunctions'] == {}
    assert data['nodespaces']['NS1']['parent_nodespace'] == 'Root'
    assert data['nodespaces']['NS1']['position'] == [23, 23]

    # Nodetypes
    response = app.get_json('/rpc/get_available_node_types(nodenet_uid="%s")' % test_nodenet)
    node_type_data = response.json_body['data']

    for key in ['Comment', 'Nodespace']:
        assert 'gatetypes' not in data['nodetypes'][key]
        assert 'slottypes' not in data['nodetypes'][key]

    for key in ['Concept', 'Pipe', 'Register', 'Script', 'Actor']:
        assert 'gatetypes' in data['nodetypes'][key]
        assert 'slottypes' in data['nodetypes'][key]

    assert 'slottypes' in data['nodetypes']['Activator']
    assert 'gatetypes' not in data['nodetypes']['Activator']

    assert 'slottypes' not in data['nodetypes']['Sensor']
    assert 'gatetypes' in data['nodetypes']['Sensor']

    assert data['nodetypes'] == node_type_data

    # Native Modules
    response = app.get_json('/rpc/get_available_native_module_types(nodenet_uid="%s")' % test_nodenet)
    native_module_data = response.json_body['data']

    assert data['native_modules']['Testnode']['gatetypes'] == ['gen', 'foo', 'bar']
    assert data['native_modules']['Testnode']['name'] == 'Testnode'
    assert data['native_modules']['Testnode']['nodefunction_name'] == 'testnodefunc'
    assert data['native_modules']['Testnode']['slottypes'] == ['gen', 'foo', 'bar']
    assert data['native_modules']['Testnode']['symbol'] == 't'

    assert data['native_modules'] == native_module_data

    # Nodenet
    assert data['current_step'] == 0  # TODO:
    assert 'step' not in data  # current_step && step?
    assert data['version'] == 1
    assert data['world'] == 'WorldOfPain'
    assert data['worldadapter'] == 'Default'

