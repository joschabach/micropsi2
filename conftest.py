
import os
import shutil
import pytest
import logging
import tempfile

try:
    import theano
    engine_defaults = "dict_engine,theano_engine"
except:
    engine_defaults = "dict_engine"


directory = tempfile.TemporaryDirectory()
testpath = directory.name
print("test data directory:", testpath)

from micropsi_core import runtime as micropsi_runtime
from micropsi_core.runtime import cfg
original_ini_data_directory = cfg['paths']['data_directory']

cfg['paths']['data_directory'] = testpath
cfg['paths']['server_settings_path'] = os.path.join(testpath, 'server_cfg.json')
cfg['paths']['usermanager_path'] = os.path.join(testpath, 'user-db.json')
cfg['micropsi2']['single_agent_mode'] = ''
if 'theano' in cfg:
    cfg['theano']['initial_number_of_nodes'] = '50'
if 'on_exception' in cfg['micropsi2']:
    cfg['micropsi2']['on_exception'] = ''


world_uid = 'WorldOfPain'
nn_uid = 'Testnet'


def pytest_addoption(parser):
    """register argparse-style options and ini-style config values."""
    parser.addoption("--engine", action="store", default=engine_defaults,
        help="The engine that should be used for this testrun.")
    parser.addoption("--agents", action="store_true",
        help="Only test agents-code from the data_directory")


def pytest_cmdline_main(config):
    """ called for performing the main command line action. The default
    implementation will invoke the configure hooks and runtest_mainloop. """
    if config.getoption('agents'):
        config.args = [original_ini_data_directory]
        micropsi_runtime.initialize(persistency_path=testpath, resource_path=original_ini_data_directory)
    else:
        micropsi_runtime.initialize(persistency_path=testpath)
        from micropsi_server.micropsi_app import usermanager

        usermanager.create_user('Pytest User', 'test', 'Administrator', uid='Pytest User')
        usermanager.start_session('Pytest User', 'test', True)

    set_logging_levels()


def pytest_configure(config):
    # register an additional marker
    config.addinivalue_line("markers",
        "engine(name): mark test to run only on the specified engine")


def pytest_unconfigure(config):
    directory.cleanup()


def pytest_generate_tests(metafunc):
    if 'engine' in metafunc.fixturenames:
        engines = []
        for e in metafunc.config.option.engine.split(','):
            if e in ['theano_engine', 'dict_engine']:
                engines.append(e)
        if not engines:
            pytest.exit("Unknown engine.")
        metafunc.parametrize("engine", engines, scope="session")


def pytest_runtest_setup(item):
    engine_marker = item.get_marker("engine")
    if engine_marker is not None:
        engine_marker = engine_marker.args[0]
        if engine_marker != item.callspec.params['engine']:
            pytest.skip("test requires engine %s" % engine_marker)
    for item in os.listdir(testpath):
        if item != 'worlds' and item != 'nodenets':
            path = os.path.join(testpath, item)
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
    os.mkdir(os.path.join(testpath, 'Test'))
    open(os.path.join(testpath, 'Test', '__init__.py'), 'w').close()
    micropsi_runtime.reload_native_modules()
    micropsi_runtime.logger.clear_logs()
    micropsi_runtime.set_runner_properties(1, 1)
    set_logging_levels()


def pytest_internalerror(excrepr, excinfo):
    """ called for internal errors. """
    micropsi_runtime.kill_runners()
    directory.cleanup()


def pytest_keyboard_interrupt(excinfo):
    """ called for keyboard interrupt. """
    micropsi_runtime.kill_runners()
    directory.cleanup()


def set_logging_levels():
    """ sets the logging levels of the default loggers back to WARNING """
    logging.getLogger('system').setLevel(logging.WARNING)
    logging.getLogger('world').setLevel(logging.WARNING)
    micropsi_runtime.cfg['logging']['level_agent'] = 'WARNING'


@pytest.fixture(scope="session")
def resourcepath():
    """ Fixture: the resource path """
    return micropsi_runtime.RESOURCE_PATH


@pytest.fixture(scope="session")
def runtime():
    """ Fixture: The micropsi runtime """
    return micropsi_runtime


@pytest.yield_fixture(scope="function")
def test_world(request):
    """
    Fixture: A test world of type Island
    """
    global world_uid
    success, world_uid = micropsi_runtime.new_world("World of Pain", "Island", "Pytest User")
    yield world_uid
    try:
        micropsi_runtime.delete_world(world_uid)
    except:
        pass


@pytest.fixture(scope="function")
def default_world(request):
    """
    Fixture: A test world of type default
    """
    for uid in micropsi_runtime.world_data:
        if micropsi_runtime.world_data[uid].get('world_type', 'DefaultWorld') == 'DefaultWorld':
            micropsi_runtime.load_world(uid)
            return uid


@pytest.yield_fixture(scope="function")
def default_nodenet(request):
    """
    A nodenet with the default engine
    Use this for tests that are engine-agnostic
    """
    success, nn_uid = micropsi_runtime.new_nodenet("Defaultnet", owner="Pytest User")
    micropsi_runtime.save_nodenet(nn_uid)
    yield nn_uid
    try:
        micropsi_runtime.delete_nodenet(nn_uid)
    except:
        pass


@pytest.yield_fixture(scope="function")
def test_nodenet(request, test_world, engine):
    """
    An empty nodenet, with the currently tested engine.
    Use this for tests that should run in both engines
    """
    global nn_uid
    success, nn_uid = micropsi_runtime.new_nodenet("Testnet", engine=engine, owner="Pytest User")
    micropsi_runtime.save_nodenet(nn_uid)
    yield nn_uid
    try:
        micropsi_runtime.delete_nodenet(nn_uid)
    except:
        pass


@pytest.fixture(scope="function")
def node(request, test_nodenet):
    """
    Fixture: A Pipe node with a genloop
    """
    res, uid = micropsi_runtime.add_node(test_nodenet, 'Pipe', [10, 10, 10], name='N1')
    micropsi_runtime.add_link(test_nodenet, uid, 'gen', uid, 'gen')
    return uid
