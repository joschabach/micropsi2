
import os
import shutil
import pytest
import logging


try:
    shutil.rmtree('/tmp/micropsi_tests/')
except OSError:
    pass

os.makedirs('/tmp/micropsi_tests/worlds')
os.makedirs('/tmp/micropsi_tests/nodenets')


# override config
import configuration
configuration.RESOURCE_PATH = '/tmp/micropsi_tests'
configuration.SERVER_SETTINGS_PATH = configuration.RESOURCE_PATH + '/server_config.json'
configuration.USERMANAGER_PATH = configuration.RESOURCE_PATH + '/user-db.json'

from micropsi_core import runtime as micropsi

# create testuser
from micropsi_server.micropsi_app import usermanager
usermanager.create_user('Pytest User', 'test', 'Administrator', uid='Pytest User')
user_token = usermanager.start_session('Pytest User', 'test', True)

# reset logging levels
logging.getLogger('system').setLevel(logging.WARNING)
logging.getLogger('world').setLevel(logging.WARNING)
logging.getLogger('nodenet').setLevel(logging.WARNING)

world_uid = 'WorldOfPain'
nn_uid = 'Testnet'

nodetype_file = os.path.join(configuration.RESOURCE_PATH, 'nodetypes.json')
nodefunc_file = os.path.join(configuration.RESOURCE_PATH, 'nodefunctions.py')
recipes_file = os.path.join(configuration.RESOURCE_PATH, 'recipes.py')


def set_logging_levels():
    logging.getLogger('system').setLevel(logging.WARNING)
    logging.getLogger('world').setLevel(logging.WARNING)
    logging.getLogger('nodenet').setLevel(logging.WARNING)


def pytest_addoption(parser):
    parser.addoption("--engine", action="store", default="dict_engine,theano_engine",
        help="The engine that should be used for this testrun.")


def pytest_generate_tests(metafunc):
    if 'engine' in metafunc.fixturenames:
        engines = []
        for e in metafunc.config.option.engine.split(','):
            if e in ['theano_engine', 'dict_engine']:
                engines.append(e)
        if not engines:
            pytest.exit("Unknown engine.")
        metafunc.parametrize("engine", engines, scope="session")


def pytest_configure(config):
    # register an additional marker
    config.addinivalue_line("markers",
        "engine(name): mark test to run only on the specified engine")


def pytest_runtest_setup(item):
    engine_marker = item.get_marker("engine")
    if engine_marker is not None:
        engine_marker = engine_marker.args[0]
        if engine_marker != item.callspec.params['engine']:
            pytest.skip("test requires engine %s" % engine_marker)


def pytest_runtest_teardown(item, nextitem):
    if nextitem is None:
        print("DELETING ALL STUFF")
        shutil.rmtree(configuration.RESOURCE_PATH)
    else:
        uids = list(micropsi.nodenets.keys())
        for uid in uids:
            micropsi.delete_nodenet(uid)
        if os.path.isfile(nodetype_file):
            os.remove(nodetype_file)
        if os.path.isfile(nodefunc_file):
            os.remove(nodefunc_file)
        if os.path.isfile(recipes_file):
            os.remove(recipes_file)
        micropsi.reload_native_modules()
        micropsi.logger.clear_logs()
        set_logging_levels()


@pytest.fixture(scope="session")
def resourcepath():
    return configuration.RESOURCE_PATH


@pytest.fixture()
def nodetype_def():
    return nodetype_file


@pytest.fixture
def nodefunc_def():
    return nodefunc_file


@pytest.fixture
def recipes_def():
    return recipes_file


@pytest.fixture(scope="function")
def test_world(request):
    global world_uid
    worlds = micropsi.get_available_worlds("Pytest User")
    if world_uid not in worlds:
        success, world_uid = micropsi.new_world("World of Pain", "Island", "Pytest User", uid=world_uid)

    def fin():
        try:
            micropsi.delete_world(world_uid)
        except:
            pass  # world was deleted in test
    request.addfinalizer(fin)
    return world_uid


@pytest.fixture(scope="function")
def test_nodenet(request, test_world, engine):
    global nn_uid
    nodenets = micropsi.get_available_nodenets("Pytest User") or {}
    if nn_uid not in nodenets:
        success, nn_uid = micropsi.new_nodenet("Testnet", engine=engine, owner="Pytest User", uid='Testnet')
        micropsi.save_nodenet(nn_uid)
    return nn_uid


@pytest.fixture(scope="function")
def node(request, test_nodenet):
    res, uid = micropsi.add_node(test_nodenet, 'Pipe', [10, 10], name='N1')
    micropsi.add_link(test_nodenet, uid, 'gen', uid, 'gen')
    return uid
