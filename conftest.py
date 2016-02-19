
import os
import shutil
import pytest
import logging


testpath = os.path.join('.', 'test-data')

try:
    shutil.rmtree(testpath)
except OSError:
    pass

# override config
from configuration import config
config['paths']['resource_path'] = testpath
config['paths']['server_settings_path'] = os.path.join(config['paths']['resource_path'], 'server_config.json')
config['paths']['usermanager_path'] = os.path.join(config['paths']['resource_path'], 'user-db.json')
config['micropsi2']['single_agent_mode'] = ''
if 'theano' in config:
    config['theano']['initial_number_of_nodes'] = '50'

from micropsi_core import runtime as micropsi

# create testuser
from micropsi_server.micropsi_app import usermanager

usermanager.create_user('Pytest User', 'test', 'Administrator', uid='Pytest User')
user_token = usermanager.start_session('Pytest User', 'test', True)

# reset logging levels
logging.getLogger('system').setLevel(logging.WARNING)
logging.getLogger('world').setLevel(logging.WARNING)

world_uid = 'WorldOfPain'
nn_uid = 'Testnet'


try:
    import theano
    engine_defaults = "dict_engine,theano_engine"
except:
    engine_defaults = "dict_engine"


def set_logging_levels():
    logging.getLogger('system').setLevel(logging.WARNING)
    logging.getLogger('world').setLevel(logging.WARNING)
    micropsi.cfg['logging']['level_agent'] = 'WARNING'


def pytest_addoption(parser):
    parser.addoption("--engine", action="store", default=engine_defaults,
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
    for uid in list(micropsi.nodenets.keys()):
        micropsi.delete_nodenet(uid)
    for uid in list(micropsi.worlds.keys()):
        micropsi.delete_world(uid)
    shutil.rmtree(config['paths']['resource_path'])
    os.mkdir(config['paths']['resource_path'])
    os.mkdir(os.path.join(config['paths']['resource_path'], 'nodenets'))
    os.mkdir(os.path.join(config['paths']['resource_path'], 'worlds'))
    # default native module container
    os.mkdir(os.path.join(config['paths']['resource_path'], 'Test'))
    micropsi.reload_native_modules()
    micropsi.logger.clear_logs()
    set_logging_levels()


@pytest.fixture(scope="session")
def resourcepath():
    return config['paths']['resource_path']


@pytest.fixture(scope="function")
def test_world(request):
    """
    Fixture: A test world of type Island
    """
    global world_uid
    success, world_uid = micropsi.new_world("World of Pain", "Island", "Pytest User", uid=world_uid)
    return world_uid


@pytest.fixture(scope="function")
def test_nodenet(request, test_world, engine):
    """
    Fixture: A completely empty nodenet without a worldadapter
    """
    global nn_uid
    success, nn_uid = micropsi.new_nodenet("Testnet", engine=engine, owner="Pytest User", uid='Testnet')
    micropsi.save_nodenet(nn_uid)
    return nn_uid


@pytest.fixture(scope="function")
def node(request, test_nodenet):
    """
    Fixture: A Pipe node with a genloop
    """
    res, uid = micropsi.add_node(test_nodenet, 'Pipe', [10, 10, 10], name='N1')
    micropsi.add_link(test_nodenet, uid, 'gen', uid, 'gen')
    return uid


def pytest_internalerror(excrepr, excinfo):
    """ called for internal errors. """
    shutil.rmtree(config['paths']['resource_path'])


def pytest_keyboard_interrupt(excinfo):
    """ called for keyboard interrupt. """
    shutil.rmtree(config['paths']['resource_path'])
