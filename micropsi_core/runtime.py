#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MicroPsi runtime module;
maintains a set of users, worlds (up to one per user), and nodenets, and provides an interface to external clients
"""

from micropsi_core._runtime_api_world import *
from micropsi_core._runtime_api_monitors import *
import re

__author__ = 'joscha'
__date__ = '10.05.12'

from configuration import config as cfg

from micropsi_core.nodenet import node_alignment
from micropsi_core import config
from micropsi_core.tools import Bunch

import os
import sys
from micropsi_core import tools
import json
import threading
from datetime import datetime, timedelta
import time
import signal

import logging

from .micropsi_logger import MicropsiLogger


NODENET_DIRECTORY = "nodenets"
WORLD_DIRECTORY = "worlds"

runner = {'timestep': 1000, 'runner': None, 'factor': 1}

nodenet_lock = threading.Lock()

# global variables set by intialize()
RESOURCE_PATH = None
PERSISTENCY_PATH = None

configs = None
logger = None

worlds = {}
nodenets = {}
native_modules = {}
custom_recipes = {}
custom_operations = {}

netapi_consoles = {}

initialized = False

from code import InteractiveConsole


class FileCacher():
    "Cache the stdout text so we can analyze it before returning it"
    def __init__(self):
        self.reset()

    def reset(self):
        self.out = []

    def write(self,line):
        self.out.append(line)

    def flush(self):
        output = '\n'.join(self.out)
        self.reset()
        return output


class NetapiShell(InteractiveConsole):
    "Wrapper around Python that can filter input/output to the shell"
    def __init__(self, netapi):
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        self.outcache = FileCacher()
        self.errcache = FileCacher()
        InteractiveConsole.__init__(self, locals={'netapi': netapi})
        return

    def get_output(self):
        sys.stdout = self.outcache
        sys.stderr = self.errcache

    def return_output(self):
        sys.stdout = self.stdout
        sys.stderr = self.stderr

    def push(self,line):
        self.get_output()
        incomplete = InteractiveConsole.push(self,line)
        if incomplete:
            InteractiveConsole.push(self,'\n')
        self.return_output()
        err = self.errcache.flush()
        if err and err.startswith('Traceback'):
            parts = err.strip().split('\n')
            return False, "%s: %s" % (parts[-3], parts[-1])
        out = self.outcache.flush()
        return True, out.strip()


def signal_handler(signal, frame):
    logging.getLogger('system').info("Shutting down")
    kill_runners()
    for uid in worlds:
        worlds[uid].signal_handler(signal, frame)
    sys.exit(0)


class MicropsiRunner(threading.Thread):

    sum_of_durations = 0
    number_of_samples = 0
    total_steps = 0
    granularity = 10

    def __init__(self):
        threading.Thread.__init__(self)
        if cfg['micropsi2'].get('profile_runner'):
            import cProfile
            self.profiler = cProfile.Profile()
        else:
            self.profiler = None
        self.daemon = True
        self.paused = True
        self.state = threading.Condition()
        self.start()

    def run(self):
        while runner['running']:
            with self.state:
                if self.paused:
                    self.state.wait()

            if configs['runner_timestep'] > 1000:
                step = timedelta(seconds=configs['runner_timestep'] / 1000)
            else:
                step = timedelta(milliseconds=configs['runner_timestep'])

            start = datetime.now()
            log = False
            uids = [uid for uid in nodenets if nodenets[uid].is_active]
            for uid in uids:
                if uid in nodenets:
                    nodenet = nodenets[uid]
                    if nodenet.is_active:
                        if nodenet.check_stop_runner_condition():
                            nodenet.is_active = False
                            continue
                        log = True
                        if self.profiler:
                            self.profiler.enable()
                        try:
                            nodenet.timed_step()
                            nodenet.update_monitors_and_recorders()
                        except:
                            nodenet.is_active = False
                            logging.getLogger("agent.%s" % uid).error("Exception in NodenetRunner:", exc_info=1)
                            MicropsiRunner.last_nodenet_exception[uid] = sys.exc_info()
                        if nodenet.world and nodenet.current_step % runner['factor'] == 0:
                            try:
                                worlds[nodenet.world].step()
                            except:
                                nodenet.is_active = False
                                logging.getLogger("world").error("Exception in WorldRunner:", exc_info=1)
                                MicropsiRunner.last_world_exception[nodenets[uid].world] = sys.exc_info()
                        if self.profiler:
                            self.profiler.disable()

            elapsed = datetime.now() - start
            if log:
                ms = elapsed.seconds + ((elapsed.microseconds // 1000) / 1000)
                self.sum_of_durations += ms
                self.number_of_samples += 1
                self.total_steps += 1
                average_duration = self.sum_of_durations / self.number_of_samples
                if self.total_steps % self.granularity == 0:
                    if self.profiler:
                        import pstats
                        import io
                        s = io.StringIO()
                        sortby = 'cumtime'
                        ps = pstats.Stats(self.profiler, stream=s).sort_stats(sortby)
                        ps.print_stats('micropsi_')
                        logging.getLogger("system").debug(s.getvalue())

                    logging.getLogger("system").debug("Step %d: Avg. %.8f sec" % (self.total_steps, average_duration))
                    self.sum_of_durations = 0
                    self.number_of_samples = 0
                    if average_duration < 0.0001:
                        self.granularity = 10000
                    elif average_duration < 0.001:
                        self.granularity = 1000
                    else:
                        self.granularity = 100
            left = step - elapsed
            if left.total_seconds() > 0:
                time.sleep(left.total_seconds())
            if len(uids) == 0:
                self.pause()

    def resume(self):
        with self.state:
            self.paused = False
            self.state.notify()

    def pause(self):
        with self.state:
            self.paused = True


MicropsiRunner.last_world_exception = {}
MicropsiRunner.last_nodenet_exception = {}


def kill_runners(signal=None, frame=None):
    for uid in nodenets:
        if nodenets[uid].is_active:
            nodenets[uid].is_active = False
    runner['runner'].resume()
    runner['running'] = False
    runner['runner'].join()


# MicroPsi API


# loggers
def set_logging_levels(logging_levels):
    for key in logging_levels:
        if key == 'agent':
            cfg['logging']['level_agent'] = logging_levels[key]
        else:
            logger.set_logging_level(key, logging_levels[key])
    return True


def get_logger_messages(loggers=[], after=0):
    """ Returns messages for the specified loggers.
        If given, limits the messages to those that occured after the given timestamp"""
    if not isinstance(loggers, list):
        loggers = [loggers]
    return logger.get_logs(loggers, after)


def get_monitoring_info(nodenet_uid, logger=[], after=0, monitor_from=0, monitor_count=-1, with_recorders=False):
    """ Returns log-messages and monitor-data for the given nodenet."""
    data = get_monitor_data(nodenet_uid, 0, monitor_from, monitor_count, with_recorders=with_recorders)
    data['logs'] = get_logger_messages(logger, after)
    return data


def get_logging_levels(nodenet_uid=None):
    levels = {}
    for key in logging.Logger.manager.loggerDict:
        levels[key] = logging.getLevelName(logging.getLogger(key).getEffectiveLevel())
    levels['agent'] = cfg['logging']['level_agent']
    return levels


# Nodenet
def get_available_nodenets(owner=None):
    """Returns a dict of uids: Nodenet of available (running and stored) nodenets.

    Arguments:
        owner (optional): when submitted, the list is filtered by this owner
    """
    if owner:
        return dict(
            (uid, nodenet_data[uid]) for uid in nodenet_data if nodenet_data[uid].owner == owner)
    else:
        return nodenet_data


def get_nodenet(nodenet_uid):
    """Returns the nodenet with the given uid, and loads into memory if necessary.
    Returns None if nodenet does not exist"""

    if nodenet_uid not in nodenets:
        if nodenet_uid in get_available_nodenets():
            load_nodenet(nodenet_uid)
        else:
            raise KeyError("Unknown nodenet")
    return nodenets[nodenet_uid]


def load_nodenet(nodenet_uid):
    """ Load the nodenet with the given uid into memeory
        Arguments:
            nodenet_uid
        Returns:
             True, nodenet_uid on success
             False, errormessage on failure

    """
    if nodenet_uid in nodenet_data:
        world_uid = worldadapter = None

        with nodenet_lock:

            if cfg['micropsi2'].get('single_agent_mode'):
                # unload all other nodenets if single_agent_mode is selected
                for uid in list(nodenets.keys()):
                    if uid != nodenet_uid:
                        unload_nodenet(uid)

            if nodenet_uid not in nodenets:
                data = nodenet_data[nodenet_uid]

                worldadapter_instance = None
                if hasattr(data, 'world') and data.world:
                    load_world(data.world)
                    if data.world in worlds:
                        world_uid = data.world
                        worldadapter = data.get('worldadapter')
                    else:
                        logging.getLogger("system").warning("World %s for nodenet %s not found" % (data.world, data.uid))

                if world_uid:
                    result, worldadapter_instance = worlds[world_uid].register_nodenet(worldadapter, nodenet_uid, nodenet_name=data['name'], config=data.get('worldadapter_config', {}))
                    if not result:
                        logging.getLogger('system').warning(worldadapter_instance)
                        worldadapter_instance = None
                        worldadapter = None
                        world_uid = None

                engine = data.get('engine') or 'dict_engine'

                logger.register_logger("agent.%s" % nodenet_uid, cfg['logging']['level_agent'])

                params = {
                    'name': data.name,
                    'worldadapter': worldadapter,
                    'worldadapter_instance': worldadapter_instance,
                    'world': world_uid,
                    'owner': data.owner,
                    'uid': data.uid,
                    'native_modules': native_modules,
                    'use_modulators': data.get('use_modulators', True)  # getter for compatibility
                }
                if hasattr(data, 'version'):
                    params['version'] = data.version
                if engine == 'dict_engine':
                    from micropsi_core.nodenet.dict_engine.dict_nodenet import DictNodenet
                    nodenets[nodenet_uid] = DictNodenet(**params)
                elif engine == 'theano_engine':
                    from micropsi_core.nodenet.theano_engine.theano_nodenet import TheanoNodenet
                    nodenets[nodenet_uid] = TheanoNodenet(**params)
                # Add additional engine types here
                else:
                    return False, "Nodenet %s requires unknown engine %s" % (nodenet_uid, engine)

                nodenets[nodenet_uid].load()

                netapi_consoles[nodenet_uid] = NetapiShell(nodenets[nodenet_uid].netapi)

                if "settings" in data:
                    nodenets[nodenet_uid].settings = data["settings"].copy()
                else:
                    nodenets[nodenet_uid].settings = {}
            else:
                world_uid = nodenets[nodenet_uid].world or None
                worldadapter = nodenets[nodenet_uid].worldadapter

        return True, nodenet_uid
    return False, "Nodenet %s not found in %s" % (nodenet_uid, PERSISTENCY_PATH)


def load_world(world_uid):
    global worlds
    if world_uid not in worlds:
        if world_uid in world_data:
            if "world_type" in world_data[world_uid]:
                try:
                    worlds[world_uid] = get_world_class_from_name(world_data[world_uid].world_type)(**world_data[world_uid])
                except TypeError:
                    worlds[world_uid] = world.World(**world_data[world_uid])
                # except AttributeError as err:
                #     logging.getLogger('system').warning("Unknown world_type: %s (%s)" % (world_data[world_uid].world_type, str(err)))
                # except:
                #     logging.getLogger('system').warning("Can not instantiate World \"%s\": %s" % (world_data[world_uid].name, str(sys.exc_info()[1])))
            else:
                worlds[world_uid] = world.World(**world_data[world_uid])
    return worlds.get(world_uid)


def get_nodenet_metadata(nodenet_uid):
    """ returns the given nodenet's metadata"""
    nodenet = get_nodenet(nodenet_uid)
    data = nodenet.metadata
    data.update({
        'nodetypes': nodenet.get_standard_nodetype_definitions(),
        'nodespaces': nodenet.construct_nodespaces_dict(None, transitive=True),
        'native_modules': nodenet.get_native_module_definitions(),
        'monitors': nodenet.construct_monitors_dict(),
        'rootnodespace': nodenet.get_nodespace(None).uid,
        'resource_path': RESOURCE_PATH
    })
    return data


def get_nodenet_activation_data(nodenet_uid, nodespaces=[], last_call_step=-1):
    nodenet = get_nodenet(nodenet_uid)
    with nodenet.netlock:
        data = {
            'activations': nodenet.get_activation_data(nodespaces, rounded=1),
            'has_changes': nodenet.has_nodespace_changes(nodespaces, last_call_step)
        }
    return data


def get_nodes(nodenet_uid, nodespaces=[], include_links=True, links_to_nodespaces=[]):
    """Return data for the given nodespaces"""
    nodenet = get_nodenet(nodenet_uid)
    return nodenet.get_nodes(nodespaces, include_links, links_to_nodespaces=links_to_nodespaces)


def get_calculation_state(nodenet_uid, nodenet=None, nodenet_diff=None, world=None, monitors=None, dashboard=None, recorders=None):
    """ returns the current state of the calculation
    """
    data = {}
    nodenet_obj = get_nodenet(nodenet_uid)
    if nodenet_obj is not None:
        condition = nodenet_obj.get_runner_condition()
        if condition:
            data['calculation_condition'] = condition
            if 'monitor' in condition:
                monitor = nodenet_obj.get_monitor(condition['monitor']['uid'])
                if monitor:
                    data['calculation_condition']['monitor']['color'] = monitor.color
                else:
                    del data['calculation_condition']['monitor']
        data['calculation_running'] = nodenet_obj.is_active
        data['current_nodenet_step'] = nodenet_obj.current_step
        data['current_world_step'] = worlds[nodenet_obj.world].current_step if nodenet_obj.world else 0
        if nodenet is not None:
            if not type(nodenet) == dict:
                nodenet = {}
            data['nodenet'] = get_nodes(nodenet_uid, nodespaces=nodenet.get('nodespaces', []), include_links=nodenet.get('include_links', True), links_to_nodespaces=nodenet.get('links_to_nodespaces', []))
        if nodenet_diff is not None:
            activations = get_nodenet_activation_data(nodenet_uid, last_call_step=nodenet_diff['step'], nodespaces=nodenet_diff.get('nodespaces', []))
            data['nodenet_diff'] = {
                'activations': activations['activations'],
                'modulators': nodenet_obj.construct_modulators_dict()
            }
            if activations['has_changes']:
                data['nodenet_diff']['changes'] = nodenet_obj.get_nodespace_changes(nodenet_diff.get('nodespaces', []), nodenet_diff['step'], include_links=nodenet_diff.get('include_links', True))
        if nodenet_obj.user_prompt:
            data['user_prompt'] = nodenet_obj.user_prompt
            nodenet_obj.user_prompt = None
        if world is not None and nodenet_obj.world:
            if not type(world) == dict:
                world = {}
            data['world'] = get_world_view(world_uid=nodenet_obj.world, **world)
        if monitors is not None:
            if not type(monitors) == dict:
                monitors = {}
            data['monitors'] = get_monitoring_info(nodenet_uid=nodenet_uid, **monitors)
        if dashboard is not None:
            data['dashboard'] = get_agent_dashboard(nodenet_uid)
        if recorders is not None:
            data['recorders'] = nodenet_obj.construct_recorders_dict()
        return True, data
    else:
        return False, "No such nodenet"


def unload_nodenet(nodenet_uid):
    """ Unload the nodenet.
        Deletes the instance of this nodenet without deleting it from the storage

        Arguments:
            nodenet_uid
    """
    if nodenet_uid not in nodenets:
        return False
    if nodenet_uid in netapi_consoles:
        del netapi_consoles[nodenet_uid]
    nodenet = nodenets[nodenet_uid]
    if nodenet.world:
        worlds[nodenet.world].unregister_nodenet(nodenet.uid)
    del nodenets[nodenet_uid]
    logger.unregister_logger('agent.%s' % nodenet_uid)
    return True


def new_nodenet(nodenet_name, engine="dict_engine", worldadapter=None, template=None, owner="", world_uid=None, use_modulators=True, worldadapter_config={}):
    """Creates a new node net manager and registers it.

    Arguments:
        worldadapter(optional): the type of the world adapter supported by this nodenet. Also used to determine the set of
            gate types supported for directional activation spreading of this nodenet, and the initial node types
        owner (optional): the creator of this nodenet
        world_uid (optional): if submitted, attempts to bind the nodenet to this world

    Returns
        nodenet_uid if successful,
        None if failure
    """
    uid = tools.generate_uid()

    data = dict(
        step=0,
        uid=uid,
        name=nodenet_name,
        worldadapter=worldadapter,
        owner=owner,
        world=world_uid,
        settings={},
        engine=engine,
        use_modulators=use_modulators,
        worldadapter_config=worldadapter_config)

    nodenet_data[data['uid']] = Bunch(**data)
    load_nodenet(data['uid'])
    if template is not None and template in nodenet_data:
        load_nodenet(template)
        data_to_merge = get_nodenet(template).export_json()
        data_to_merge.update(data)
        load_nodenet(uid)
        nodenets[uid].merge_data(data_to_merge)

    nodenets[uid].save()
    return True, data['uid']


def delete_nodenet(nodenet_uid):
    """Unloads the given nodenet from memory and deletes it from the storage.

    Simple unloading is maintained automatically when a nodenet is suspended and another one is accessed.
    """
    import shutil
    if nodenet_uid in nodenets:
        unload_nodenet(nodenet_uid)
    del nodenet_data[nodenet_uid]
    nodenet_directory = os.path.join(RESOURCE_PATH, NODENET_DIRECTORY, nodenet_uid)
    shutil.rmtree(nodenet_directory)
    return True


def set_nodenet_properties(nodenet_uid, nodenet_name=None, worldadapter=None, world_uid=None, owner=None, worldadapter_config={}):
    """Sets the supplied parameters (and only those) for the nodenet with the given uid."""

    nodenet = get_nodenet(nodenet_uid)
    if nodenet.world and (nodenet.world != world_uid or nodenet.worldadapter != worldadapter):
        worlds[nodenet.world].unregister_nodenet(nodenet.uid)
        nodenet.world = None
    if worldadapter is None:
        worldadapter = nodenet.worldadapter
    if world_uid is not None and worldadapter is not None:
        world_obj = load_world(world_uid)
        assert worldadapter in world_obj.supported_worldadapters
        nodenet.world = world_uid
        nodenet.worldadapter = worldadapter
        result, wa_instance = world_obj.register_nodenet(worldadapter, nodenet.uid, nodenet_name=nodenet.name, config=worldadapter_config)
        if result:
            nodenet.worldadapter_instance = wa_instance
    if nodenet_name:
        nodenet.name = nodenet_name
    if owner:
        nodenet.owner = owner
    return True


def start_nodenetrunner(nodenet_uid):
    """Starts a thread that regularly advances the given nodenet by one step."""

    nodenets[nodenet_uid].is_active = True
    if runner['runner'].paused:
        runner['runner'].resume()
    return True


def set_runner_properties(timestep, factor):
    """Sets the speed of the nodenet calculation in ms.

    Argument:
        timestep: sets the calculation speed.
    """
    configs['runner_timestep'] = timestep
    runner['timestep'] = timestep
    configs['runner_factor'] = int(factor)
    runner['factor'] = int(factor)
    return True


def set_runner_condition(nodenet_uid, monitor=None, steps=None):
    """ registers a condition that stops the runner if it is fulfilled"""
    nodenet = get_nodenet(nodenet_uid)
    condition = {}
    if monitor:
        if type(monitor) == dict and 'uid' in monitor and 'value' in monitor:
            condition['monitor'] = monitor
        else:
            return False, "Monitor condition expects a dict with keys 'uid' and 'value'"
    if steps:
        steps = int(steps)
        condition['step'] = nodenet.current_step + steps
        condition['step_amount'] = steps
    if condition:
        nodenet.set_runner_condition(condition)
    return True, condition


def remove_runner_condition(nodenet_uid):
    get_nodenet(nodenet_uid).unset_runner_condition()
    return True


def get_runner_properties():
    """Returns the speed that has been configured for the nodenet runner (in ms)."""
    return {
        'timestep': configs['runner_timestep'],
        'factor': configs['runner_factor']
    }


def get_is_nodenet_running(nodenet_uid):
    """Returns True if a nodenet runner is active for the given nodenet, False otherwise."""
    return get_nodenet(nodenet_uid).is_active


def stop_nodenetrunner(nodenet_uid):
    """Stops the thread for the given nodenet."""
    nodenet = get_nodenet(nodenet_uid)
    nodenet.is_active = False
    test = {nodenets[uid].is_active for uid in nodenets}
    if True not in test:
        runner['runner'].pause()
    return True


def step_nodenet(nodenet_uid):
    """Advances the given nodenet by one calculation step.

    Arguments:
        nodenet_uid: The uid of the nodenet
    """
    nodenet = get_nodenet(nodenet_uid)

    if cfg['micropsi2'].get('profile_runner'):
        import cProfile
        profiler = cProfile.Profile()
        profiler.enable()

    nodenet.timed_step()

    if cfg['micropsi2'].get('profile_runner'):
        profiler.disable()
        import pstats
        import io
        s = io.StringIO()
        sortby = 'cumtime'
        ps = pstats.Stats(profiler, stream=s).sort_stats(sortby)
        ps.print_stats('micropsi_')
        logging.getLogger("agent.%s" % nodenet_uid).debug(s.getvalue())

    nodenet.update_monitors_and_recorders()
    if nodenet.world and nodenet.current_step % configs['runner_factor'] == 0:
        worlds[nodenet.world].step()
    return nodenet.current_step


def step_nodenets_in_world(world_uid, nodenet_uid=None, steps=1):
    """ Advances all nodenets registered in the given world
    (or, only the given nodenet) by the given number of steps"""
    nodenet = None
    if nodenet_uid is not None:
        nodenet = get_nodenet(nodenet_uid)
    if nodenet and nodenet.world == world_uid:
        for i in range(steps):
            nodenet.timed_step()
            nodenet.update_monitors_and_recorders()
    else:
        for i in range(steps):
            for uid in worlds[world_uid].agents:
                nodenet = get_nodenet(uid)
                nodenet.timed_step()
                nodenet.update_monitors_and_recorders()
    return True


def revert_nodenet(nodenet_uid, also_revert_world=False):
    """Returns the nodenet to the last saved state."""
    nodenet = get_nodenet(nodenet_uid)
    if also_revert_world and nodenet_uid in nodenets and nodenet.world:
        revert_world(nodenet.world)
    unload_nodenet(nodenet_uid)
    load_nodenet(nodenet_uid)
    return True


def save_nodenet(nodenet_uid):
    """Stores the nodenet on the server (but keeps it open)."""
    nodenet = get_nodenet(nodenet_uid)
    nodenet.save()
    nodenet_data[nodenet_uid] = Bunch(**nodenet.metadata)
    return True


def export_nodenet(nodenet_uid):
    """Exports the nodenet state to the user, so it can be viewed and exchanged.

    Returns a string that contains the nodenet state in JSON format.
    """
    return json.dumps(get_nodenet(nodenet_uid).export_json(), sort_keys=True, indent=4)


def import_nodenet(string, owner=None):
    """Imports the nodenet state, instantiates the nodenet.

    Arguments:
        nodenet_uid: the uid of the nodenet (may overwrite existing nodenet)
        string: a string that contains the nodenet state in JSON format.
    """
    global nodenet_data
    import_data = json.loads(string)
    if 'uid' not in import_data:
        import_data['uid'] = tools.generate_uid()
    else:
        if import_data['uid'] in nodenets:
            raise RuntimeError("A nodenet with this ID already exists.")
    if 'owner':
        import_data['owner'] = owner
    nodenet_uid = import_data['uid']
    filename = os.path.join(PERSISTENCY_PATH, NODENET_DIRECTORY, import_data['uid'] + '.json')
    meta = parse_definition(import_data, filename)
    nodenet_data[nodenet_uid] = meta
    # assert import_data['world'] in worlds
    with open(filename, 'w+', encoding="utf-8") as fp:
        fp.write(json.dumps(meta))
    load_nodenet(nodenet_uid)
    merge_nodenet(nodenet_uid, string, keep_uids=True)
    save_nodenet(nodenet_uid)
    return nodenet_uid


def merge_nodenet(nodenet_uid, string, keep_uids=False):
    """Merges the nodenet data with an existing nodenet, instantiates the nodenet.

    Arguments:
        nodenet_uid: the uid of the existing nodenet (may overwrite existing nodenet)
        string: a string that contains the nodenet data that is to be merged in JSON format.
        keep_uids: if true, no uid replacement will be performed. Dangerous.
    """
    nodenet = get_nodenet(nodenet_uid)
    data = json.loads(string)
    nodenet.merge_data(data, keep_uids)
    return True


# Node operations

def get_nodespace_list(nodenet_uid):
    """ returns a list of nodespaces in the given nodenet. information includes:
     - nodespace name,
     - nodespace parent
     - a list of nodes (uid, name, and type) residing in that nodespace
    """
    nodenet = get_nodenet(nodenet_uid)
    data = {}
    for uid in nodenet.get_nodespace_uids():
        nodespace = nodenet.get_nodespace(uid)
        data[uid] = {
            'uid': uid,
            'name': nodespace.name,
            'parent': nodespace.parent_nodespace,
            'nodes': {},
            'properties': nodenet.get_nodespace_properties(uid)
        }
        for nid in nodespace.get_known_ids('nodes'):
            data[uid]['nodes'][nid] = {
                'uid': nid,
                'name': nodenet.get_node(nid).name,
                'type': nodenet.get_node(nid).type
            }
    return data


def get_node(nodenet_uid, node_uid, include_links=True):
    """Returns a dictionary with all node parameters, if node exists, or None if it does not. The dict is
    structured as follows:

    {
        "uid" (str): unique identifier,
        "state" (dict): a dictionary of node states and their values,
        "type" (string): the type of this node,
        "parameters" (dict): a dictionary of the node parameters
        "activation" (float): the activation of this node,
        "name" (str): display name
        "gate_activations" (dict): a dictionary containing dicts of activations for each gate of this node
        "gate_configuration"(dict): a dictionary containing the name of the gatefunction and its parameters for each gate
        "position" (list): the x, y, z coordinates of this node, as a list
        "parent_nodespace" (str): the uid of the nodespace this node lives in
    }
    """
    nodenet = get_nodenet(nodenet_uid)
    if nodenet.is_node(node_uid):
        return True, nodenet.get_node(node_uid).get_data(include_links=include_links)
    elif nodenet.is_nodespace(node_uid):
        data = nodenet.get_nodespace(node_uid).get_data()
        data['type'] = 'Nodespace'
        return True, data
    else:
        return False, "Unknown UID"


def add_node(nodenet_uid, type, pos, nodespace=None, state=None, name="", parameters=None):
    """Creates a new node. (Including native module.)

    Arguments:
        nodenet_uid: uid of the nodespace manager
        type: type of the node
        position: position of the node in the current nodespace
        nodespace: uid of the nodespace
        uid (optional): if not supplied, a uid will be generated
        name (optional): if not supplied, the uid will be used instead of a display name
        parameters (optional): a dict of arbitrary parameters that can make nodes stateful

    Returns:
        node_uid if successful,
        None if failure.
    """
    nodenet = get_nodenet(nodenet_uid)
    uid = nodenet.create_node(type, nodespace, pos, name, parameters=parameters)
    return True, uid


def add_nodespace(nodenet_uid, nodespace=None, name="", options=None):
    """Creates a new nodespace
    Arguments:
        nodenet_uid: uid of the nodespace manager
        nodespace: uid of the parent nodespace
        name (optional): if not supplied, the uid will be used instead of a display name
        options (optional): a dict of options. TBD
    """
    nodenet = get_nodenet(nodenet_uid)
    uid = nodenet.create_nodespace(nodespace, name=name, options=options)
    return True, uid


def clone_nodes(nodenet_uid, node_uids, clonemode, nodespace=None, offset=[50, 50, 50]):
    """
    Clones a bunch of nodes. The nodes will get new unique node ids,
    a "copy" suffix to their name, and a slight positional offset.
    To specify whether the links should be copied too, you can give the following clone-modes:
    * "all" to clone all links
    * "internal" to only clone links within the clone set of nodes
    * "none" to not clone links at all.

    Per default, a clone of a node will appear in the same nodespace, slightly below the original node.

    If you however specify a nodespace, all clones will be copied to the given nodespace.
    """

    offset = (offset + [0] * 3)[:3]
    nodenet = get_nodenet(nodenet_uid)
    result = {}
    copynodes = {uid: nodenet.get_node(uid) for uid in node_uids}
    copylinks = {}
    followupnodes = []
    uidmap = {}
    if clonemode != 'none':
        for _, n in copynodes.items():
            for g in n.get_gate_types():
                for link in n.get_gate(g).get_links():
                    if clonemode == 'all' or link.target_node.uid in copynodes:
                        copylinks[link.signature] = link
            if clonemode == 'all':
                for s in n.get_slot_types():
                    for link in n.get_slot(s).get_links():
                        copylinks[link.signature] = link
                        if link.source_node.uid not in copynodes:
                            followupnodes.append(link.source_node.uid)

    for _, n in copynodes.items():
        target_nodespace = nodespace if nodespace is not None else n.parent_nodespace
        uid = nodenet.create_node(n.type, target_nodespace, [n.position[0] + offset[0], n.position[1] + offset[1], n.position[2] + offset[2]], name=n.name, uid=None, parameters=n.clone_parameters().copy(), gate_configuration=n.get_gate_configuration())
        if uid:
            uidmap[n.uid] = uid
        else:
            logger.warning('Could not clone node: ' + uid)

    for uid, l in copylinks.items():
        source_uid = uidmap.get(l.source_node.uid, l.source_node.uid)
        target_uid = uidmap.get(l.target_node.uid, l.target_node.uid)
        nodenet.create_link(
            source_uid,
            l.source_gate.type,
            target_uid,
            l.target_slot.type,
            l.weight)

    for uid in uidmap.values():
        result[uid] = nodenet.get_node(uid).get_data(include_links=True)

    for uid in followupnodes:
        result[uid] = nodenet.get_node(uid).get_data(include_links=True)

    if len(result.keys()) or len(nodes) == 0:
        return True, result
    else:
        return False, "Could not clone nodes. See log for details."


def get_nodespace_changes(nodenet_uid, nodespaces, since_step):
    """ Returns a dict of changes that happened in the nodenet in the given nodespace since the given step.
    Contains uids of deleted nodes and nodespaces and the datadicts for changed or added nodes and nodespaces
    """
    return get_nodenet(nodenet_uid).get_nodespace_changes(nodespaces, since_step)


def get_nodespace_properties(nodenet_uid, nodespace_uid=None):
    """ retrieve the ui properties for the given nodespace"""
    return get_nodenet(nodenet_uid).get_nodespace_properties(nodespace_uid)


def set_nodespace_properties(nodenet_uid, nodespace_uid, properties):
    """ sets the ui properties for the given nodespace"""
    return get_nodenet(nodenet_uid).set_nodespace_properties(nodespace_uid, properties)


def __pythonify(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name).lower()
    return re.sub('([\s+\W])', '_', s1)


def generate_netapi_fragment(nodenet_uid, node_uids):
    lines = []
    idmap = {}
    nodenet = get_nodenet(nodenet_uid)
    nodes = []
    #nodespaces = []
    #for node_uid in node_uids:
    #    if not nodenet.is_nodespace(node_uid):
    #        nodes.append(nodenet.get_node(node_uid))
    #    else:
    #        nodespaces.append(nodenet.get_nodespace(node_uid))

    for node_uid in node_uids:
        nodes.append(nodenet.get_node(node_uid))

    xpos = []
    ypos = []
    zpos = []
    nodes = sorted(nodes, key=lambda node: node.position[1] * 1000 + node.position[0])
    #nodespaces = sorted(nodespaces, key=lambda node: node.position[1] * 1000 + node.position[0])

    # nodespaces
    #for i, nodespace in enumerate(nodespaces):
    #    name = nodespace.name.strip() if nodespace.name != nodespace.uid else None
    #    varname = "nodespace%i" % i
    #    if name:
    #        pythonname = __pythonify(name)
    #        if pythonname not in idmap.values():
    #            varname = pythonname
    #        lines.append("%s = netapi.create_nodespace(None, \"%s\")" % (varname, name))
    #    else:
    #        lines.append("%s = netapi.create_nodespace(None)" % (varname))
    #    idmap[nodespace.uid] = varname
    #    xpos.append(nodespace.position[0])
    #    ypos.append(nodespace.position[1])
    #    zpos.append(nodespace.position[2])

    # nodes and gates
    for i, node in enumerate(nodes):
        name = node.name.strip() if node.name != node.uid else None
        varname = "node%i" % i
        if name:
            pythonname = __pythonify(name)
            if pythonname not in idmap.values():
                varname = pythonname
            lines.append("%s = netapi.create_node('%s', None, \"%s\")" % (varname, node.type, name))
        else:
            lines.append("%s = netapi.create_node('%s', None)" % (varname, node.type))

        gate_config = node.get_gate_configuration()
        for gatetype, gconfig in gate_config.items():
            lines.append("%s.set_gate_configuration('%s', \"%s\", %.2f)" % (varname, gatetype, gconfig['gatefunction'], gconfig.get('gatefunction_parameters', {})))

        nps = node.clone_parameters()
        for parameter, value in nps.items():
            if value is None:
                continue

            if parameter not in node.nodetype.parameter_defaults or node.nodetype.parameter_defaults[parameter] != value:
                if isinstance(value, str):
                    lines.append("%s.set_parameter(\"%s\", \"%s\")" % (varname, parameter, value))
                else:
                    lines.append("%s.set_parameter(\"%s\", %.2f)" % (varname, parameter, value))

        idmap[node.uid] = varname
        xpos.append(node.position[0])
        ypos.append(node.position[1])
        zpos.append(node.position[2])

    lines.append("")

    # links
    for node in nodes:
        for gatetype in node.get_gate_types():
            gate = node.get_gate(gatetype)
            for link in gate.get_links():
                if link.source_node.uid not in idmap or link.target_node.uid not in idmap:
                    continue

                source_id = idmap[link.source_node.uid]
                target_id = idmap[link.target_node.uid]

                reciprocal = False
                if link.source_gate.type == 'sub' and 'sur' in link.target_node.get_gate_types() and link.weight == 1:
                    surgate = link.target_node.get_gate('sur')
                    for rec_link in surgate.get_links():
                        if rec_link.target_node.uid == node.uid and rec_link.target_slot.type == 'sur' and rec_link.weight == 1:
                            reciprocal = True
                            lines.append("netapi.link_with_reciprocal(%s, %s, 'subsur')" % (source_id, target_id))

                if link.source_gate.type == 'sur' and 'sub' in link.target_node.get_gate_types() and link.weight == 1:
                    subgate = link.target_node.get_gate('sub')
                    for rec_link in subgate.get_links():
                        if rec_link.target_node.uid == node.uid and rec_link.target_slot.type == 'sub' and rec_link.weight == 1:
                            reciprocal = True

                if link.source_gate.type == 'por' and 'ret' in link.target_node.get_gate_types() and link.weight == 1:
                    surgate = link.target_node.get_gate('ret')
                    for rec_link in surgate.get_links():
                        if rec_link.target_node.uid == node.uid and rec_link.target_slot.type == 'ret' and rec_link.weight == 1:
                            reciprocal = True
                            lines.append("netapi.link_with_reciprocal(%s, %s, 'porret')" % (source_id, target_id))

                if link.source_gate.type == 'ret' and 'por' in link.target_node.get_gate_types() and link.weight == 1:
                    subgate = link.target_node.get_gate('por')
                    for rec_link in subgate.get_links():
                        if rec_link.target_node.uid == node.uid and rec_link.target_slot.type == 'por' and rec_link.weight == 1:
                            reciprocal = True

                if link.source_gate.type == 'cat' and 'exp' in link.target_node.get_gate_types() and link.weight == 1:
                    surgate = link.target_node.get_gate('exp')
                    for rec_link in surgate.get_links():
                        if rec_link.target_node.uid == node.uid and rec_link.target_slot.type == 'exp' and rec_link.weight == 1:
                            reciprocal = True
                            lines.append("netapi.link_with_reciprocal(%s, %s, 'catexp')" % (source_id, target_id))

                if link.source_gate.type == 'exp' and 'cat' in link.target_node.get_gate_types() and link.weight == 1:
                    subgate = link.target_node.get_gate('cat')
                    for rec_link in subgate.get_links():
                        if rec_link.target_node.uid == node.uid and rec_link.target_slot.type == 'cat' and rec_link.weight == 1:
                            reciprocal = True

                if not reciprocal:
                    weight = link.weight if link.weight != 1 else None
                    if weight is not None:
                        lines.append("netapi.link(%s, '%s', %s, '%s', %.8f)" % (source_id, gatetype, target_id, link.target_slot.type, weight))
                    else:
                        lines.append("netapi.link(%s, '%s', %s, '%s')" % (source_id, gatetype, target_id, link.target_slot.type))

    lines.append("")

    # positions
    origin = [100, 100, 0]
    factor = [int(min(xpos)), int(min(ypos)), int(min(zpos))]
    lines.append("origin_pos = (%d, %d, %d)" % (origin[0], origin[1], origin[2]))
    for node in nodes:
        x = int(node.position[0] - factor[0])
        y = int(node.position[1] - factor[1])
        z = int(node.position[2] - factor[2])
        lines.append("%s.position = (origin_pos[0] + %i, origin_pos[1] + %i, origin_pos[2] + %i)" % (idmap[node.uid], x, y, z))

    return "\n".join(lines)


def set_node_positions(nodenet_uid, positions):
    """ Takes a dict with node_uids as keys and new positions for the nodes as values """
    get_nodenet(nodenet_uid).set_node_positions(positions)
    return True


def set_node_name(nodenet_uid, node_uid, name):
    """Sets the display name of the node"""
    nodenet = get_nodenet(nodenet_uid)
    if nodenet.is_node(node_uid):
        nodenet.get_node(node_uid).name = name
    elif nodenet.is_nodespace(node_uid):
        nodenet.get_nodespace(node_uid).name = name
    return True


def set_node_state(nodenet_uid, node_uid, state):
    """ Sets the state of the given node to the given state"""
    node = get_nodenet(nodenet_uid).get_node(node_uid)
    for key in state:
        node.set_state(key, state[key])
    return True


def set_node_activation(nodenet_uid, node_uid, activation):
    get_nodenet(nodenet_uid).get_node(node_uid).activation = activation
    return True


def delete_nodes(nodenet_uid, node_uids):
    """Removes the nodes with the given uids"""
    nodenet = get_nodenet(nodenet_uid)
    with nodenet.netlock:
        for uid in node_uids:
            if nodenet.is_node(uid):
                nodenet.delete_node(uid)
    return True


def delete_nodespace(nodenet_uid, nodespace_uid):
    """ Removes the given node space and all its contents"""
    nodenet = get_nodenet(nodenet_uid)
    with nodenet.netlock:
        if nodenet.is_nodespace(nodespace_uid):
            nodenet.delete_nodespace(nodespace_uid)
            return True
        return False


def get_available_node_types(nodenet_uid):
    """Returns a list of available node types. (Including native modules.)"""
    nodenet = get_nodenet(nodenet_uid)
    return {
        'nodetypes': nodenet.get_standard_nodetype_definitions(),
        'native_modules': nodenet.get_native_module_definitions()
    }


def get_available_native_module_types(nodenet_uid):
    """Returns a list of native modules.
    If an nodenet uid is supplied, filter for node types defined within this nodenet."""
    return get_nodenet(nodenet_uid).get_native_module_definitions()


def set_node_parameters(nodenet_uid, node_uid, parameters):
    """Sets a dict of arbitrary values to make the node stateful."""
    nodenet = get_nodenet(nodenet_uid)
    for key, value in parameters.items():
        nodenet.get_node(node_uid).set_parameter(key, value)
    return True


def get_available_gatefunctions(nodenet_uid):
    """
    Returns a dict of the available gatefunctions and their parameters and parameter-defaults
    """
    return get_nodenet(nodenet_uid).get_available_gatefunctions()


def set_gate_configuration(nodenet_uid, node_uid, gate_type, gatefunction=None, gatefunction_parameters=None):
    """Sets the configuration of the given gate of the given node to the supplied gatefunction and -parameters."""
    nodenet = get_nodenet(nodenet_uid)
    nodenet.get_node(node_uid).set_gate_configuration(gate_type, gatefunction, gatefunction_parameters)
    return True


def get_available_datasources(nodenet_uid):
    """Returns a list of available datasource types for the given nodenet."""
    nodenet = get_nodenet(nodenet_uid)
    if nodenet.worldadapter_instance:
        return nodenet.worldadapter_instance.get_available_datasources()
    return []


def get_available_datatargets(nodenet_uid):
    """Returns a list of available datatarget types for the given nodenet."""
    nodenet = get_nodenet(nodenet_uid)
    if nodenet.worldadapter_instance:
        return nodenet.worldadapter_instance.get_available_datatargets()
    return []


def bind_datasource_to_sensor(nodenet_uid, sensor_uid, datasource):
    """Associates the datasource type to the sensor node with the given uid."""
    node = get_nodenet(nodenet_uid).get_node(sensor_uid)
    if node.type == "Sensor":
        node.set_parameter('datasource', datasource)
        return True
    return False


def bind_datatarget_to_actuator(nodenet_uid, actuator_uid, datatarget):
    """Associates the datatarget type to the actuator node with the given uid."""
    node = get_nodenet(nodenet_uid).get_node(actuator_uid)
    if node.type == "Actuator":
        node.set_parameter('datatarget', datatarget)
        return True
    return False


def add_link(nodenet_uid, source_node_uid, gate_type, target_node_uid, slot_type, weight=1):
    """Creates a new link.

    Arguments.
        source_node_uid: uid of the origin node
        gate_type: type of the origin gate (usually defines the link type)
        target_node_uid: uid of the target node
        slot_type: type of the target slot
        weight: the weight of the link (a float)
    """
    nodenet = get_nodenet(nodenet_uid)
    with nodenet.netlock:
        success = nodenet.create_link(source_node_uid, gate_type, target_node_uid, slot_type, weight)
    uid = None
    if success:                                                       # todo: check whether clients need these uids
        uid = "%s:%s:%s:%s" % (source_node_uid, gate_type, slot_type, target_node_uid)
    return success, uid


def set_link_weight(nodenet_uid, source_node_uid, gate_type, target_node_uid, slot_type, weight=1):
    """Set weight of the given link."""
    return get_nodenet(nodenet_uid).set_link_weight(source_node_uid, gate_type, target_node_uid, slot_type, weight)


def get_links_for_nodes(nodenet_uid, node_uids):
    """ Returns a list of links connected to the given nodes,
    and their connected nodes, if they are not in the same nodespace"""
    nodenet = get_nodenet(nodenet_uid)
    links, nodes = nodenet.get_links_for_nodes(node_uids)
    return {'links': links, 'nodes': nodes}


def delete_link(nodenet_uid, source_node_uid, gate_type, target_node_uid, slot_type):
    """Delete the given link."""
    return get_nodenet(nodenet_uid).delete_link(source_node_uid, gate_type, target_node_uid, slot_type)


def align_nodes(nodenet_uid, nodespace):
    """Perform auto-alignment of nodes in the current nodespace"""
    result = node_alignment.align(get_nodenet(nodenet_uid), nodespace)
    return result


def user_prompt_response(nodenet_uid, node_uid, values, resume_nodenet):
    nodenet = get_nodenet(nodenet_uid)
    for key, value in values.items():
        nodenet.get_node(node_uid).set_parameter(key, value)
    nodenet.is_active = resume_nodenet
    nodenet.user_prompt = None


def get_available_recipes():
    """ Returns a dict of the available user-recipes """
    recipes = {}
    for name, data in custom_recipes.items():
        if not name.startswith('_'):
            recipes[name] = {
                'name': name,
                'parameters': data['parameters'],
                'docstring': data['docstring'],
                'category': data['category']
            }
    return recipes


def get_available_operations():
    """ Returns a dict of available user-operations """
    operations = {}
    for name, data in custom_operations.items():
        if not name.startswith('_'):
            operations[name] = {
                'name': name,
                'parameters': data['parameters'],
                'docstring': data['docstring'],
                'category': data['category'],
                'selection': data['selectioninfo']
            }
    return operations


def run_recipe(nodenet_uid, name, parameters):
    """ Calls the given recipe with the provided parameters, and returns the output, if any """
    netapi = get_nodenet(nodenet_uid).netapi
    params = {}
    for key in parameters:
        if parameters[key] != '':
            params[key] = parameters[key]
    if name in custom_recipes:
        func = custom_recipes[name]['function']
        if cfg['micropsi2'].get('profile_runner'):
            import cProfile
            profiler = cProfile.Profile()
            profiler.enable()
        result = {'reload': True}
        ret = func(netapi, **params)
        if ret:
            result.update(ret)
        if cfg['micropsi2'].get('profile_runner'):
            profiler.disable()
            import pstats
            import io
            s = io.StringIO()
            sortby = 'cumtime'
            ps = pstats.Stats(profiler, stream=s).sort_stats(sortby)
            ps.print_stats('nodenet')
            logging.getLogger("agent.%s" % nodenet_uid).debug(s.getvalue())
        return True, result
    else:
        return False, "Script not found"


def run_operation(nodenet_uid, name, parameters, selection_uids):
    """ Calls the given operation on the selection"""
    netapi = get_nodenet(nodenet_uid).netapi
    params = {}
    for key in parameters:
        if parameters[key] != '':
            params[key] = parameters[key]
    if name in custom_operations:
        func = custom_operations[name]['function']
        result = {}
        ret = func(netapi, selection_uids, **params)
        if ret:
            result.update(ret)
        return True, result
    else:
        return False, "Operation not found"


def get_agent_dashboard(nodenet_uid):
    from .emoexpression import calc_emoexpression_parameters
    net = get_nodenet(nodenet_uid)
    with net.netlock:
        data = net.get_dashboard()
        data['face'] = calc_emoexpression_parameters(net)
        return data


def run_netapi_command(nodenet_uid, command):
    get_nodenet(nodenet_uid)
    shell = netapi_consoles[nodenet_uid]
    return shell.push(command)


def get_netapi_autocomplete_data(nodenet_uid, name=None):
    import inspect
    nodenet = get_nodenet(nodenet_uid)
    if nodenet is None or nodenet_uid not in netapi_consoles:
        return {}
    nodetypes = get_available_node_types(nodenet_uid)

    shell = netapi_consoles[nodenet_uid]
    res, locs = shell.push("[k for k in locals() if not k.startswith('_')]")
    locs = eval(locs)

    def parsemembers(members):
        data = {}
        for name, thing in members:
            if name.startswith('_'):
                continue
            if inspect.isroutine(thing):
                argspec = inspect.getargspec(thing)
                arguments = argspec.args[1:]
                defaults = argspec.defaults or []
                params = []
                diff = len(arguments) - len(defaults)
                for i, arg in enumerate(arguments):
                    if i >= diff:
                        params.append({
                            'name': arg,
                            'default': defaults[i - diff]
                        })
                    else:
                        params.append({'name': arg})

                data[name] = params
            else:
                data[name] = None
        return data

    data = {
        'types': {},
        'autocomplete_options': {}
    }

    for n in locs:
        if name is None or n == name:
            res, typedescript = shell.push(n)
            if 'netapi' in typedescript:
                data['types'][n] = 'netapi'
            else:
                # get type of thing.
                match = re.search('^<([A-Za-z]+) ', typedescript)
                if match:
                    typename = match.group(1)
                    if typename in ['Nodespace', 'Node', 'Gate', 'Slot']:
                        data['types'][n] = typename
                    elif typename in nodetypes['nodetypes'] or typename in nodetypes['native_modules']:
                        data['types'][n] = 'Node'

    for t in set(data['types'].values()):
        if t == 'netapi':
            netapi = nodenet.netapi
            methods = inspect.getmembers(netapi, inspect.ismethod)
            data['autocomplete_options']['netapi'] = parsemembers(methods)
        elif t == 'Nodespace':
            from micropsi_core.nodenet.nodespace import Nodespace
            data['autocomplete_options']['Nodespace'] = parsemembers(inspect.getmembers(Nodespace))
        elif t in ['Node', 'Gate', 'Slot']:
            from micropsi_core.nodenet import node
            cls = getattr(node, t)
            data['autocomplete_options'][t] = parsemembers(inspect.getmembers(cls))

    return data


# --- end of API


def crawl_definition_files(path, datatype="definition"):
    """Traverse the directories below the given path for JSON definitions of nodenets and worlds,
    and return a dictionary with the signatures of these nodenets or worlds.
    """
    from micropsi_core.world.world import WORLD_VERSION
    from micropsi_core.nodenet.nodenet import NODENET_VERSION
    result = {}
    os.makedirs(path, exist_ok=True)
    for user_directory_name, user_directory_names, file_names in os.walk(path):
        for definition_file_name in file_names:
            if definition_file_name.endswith(".json"):
                try:
                    filename = os.path.join(user_directory_name, definition_file_name)
                    with open(filename, encoding="utf-8") as file:
                        data = parse_definition(json.load(file), filename)
                        if datatype == 'world' and data.version != WORLD_VERSION:
                            logging.getLogger("system").warning("Wrong Version of world data in file %s" % definition_file_name)
                        elif datatype == 'nodenet' and data.version != NODENET_VERSION:
                            logging.getLogger("system").warning("Wrong Version of nodenet data in file %s" % definition_file_name)
                        else:
                            result[data.uid] = data
                except ValueError:
                    logging.getLogger('system').warning("Invalid %s data in file '%s'" % (datatype, definition_file_name))
                except IOError:
                    logging.getLogger('system').warning("Could not open %s data file '%s'" % (datatype, definition_file_name))
    return result


def parse_definition(json, filename=None):
    if "uid" in json:
        result = dict(
            uid=json["uid"],
            name=json.get("name", json["uid"]),
            filename=filename or json.get("filename"),
            owner=json.get("owner"),
            engine=json.get("engine"),
        )
        if "worldadapter" in json:
            result['worldadapter'] = json["worldadapter"]
            result['world'] = json["world"]
            result['worldadapter_config'] = json.get('worldadapter_config', {})
        if "world_type" in json:
            result['world_type'] = json['world_type']
        if "settings" in json:
            result['settings'] = json['settings']
        if "config" in json:
            result['config'] = json['config']
        if 'use_modulators' in json:
            result['use_modulators'] = json['use_modulators']
        if 'version' in json:
            result['version'] = json['version']
        return Bunch(**result)


# Set up the MicroPsi runtime
def load_definitions():
    global nodenet_data, world_data
    nodenet_data = crawl_definition_files(path=os.path.join(PERSISTENCY_PATH, NODENET_DIRECTORY), datatype="nodenet")
    world_data = crawl_definition_files(path=os.path.join(PERSISTENCY_PATH, WORLD_DIRECTORY), datatype="world")
    if not world_data:
        # create a default world for convenience.
        uid = tools.generate_uid()
        filename = os.path.join(PERSISTENCY_PATH, WORLD_DIRECTORY, uid + '.json')
        world_data[uid] = Bunch(uid=uid, name="default", version=1, filename=filename, owner="admin", world_type="DefaultWorld")
        with open(filename, 'w+', encoding="utf-8") as fp:
            fp.write(json.dumps(world_data[uid], sort_keys=True, indent=4))
    for uid in world_data:
        world_data[uid].supported_worldadapters = get_world_class_from_name(world_data[uid].get('world_type', "DefaultWorld")).get_supported_worldadapters()
    return nodenet_data, world_data


def load_user_files(path, reload_nodefunctions=False, errors=[]):
    global native_modules, custom_recipes
    for f in os.listdir(path):
        if not f.startswith('.') and f != '__pycache__':
            abspath = os.path.join(path, f)
            err = None
            if os.path.isdir(abspath):
                errors.extend(load_user_files(path=abspath, reload_nodefunctions=reload_nodefunctions, errors=[]))
            elif f == 'nodetypes.json':
                err = parse_native_module_file(abspath)
            elif f == 'recipes.py':
                err = parse_recipe_or_operations_file(abspath, reload_nodefunctions)
            elif f == 'nodefunctions.py' and reload_nodefunctions:
                err = reload_nodefunctions_file(abspath)
            elif f == 'operations.py':
                err = parse_recipe_or_operations_file(abspath, reload_nodefunctions)
            if err:
                errors.append(err)
    return errors


def parse_native_module_file(path):

    global native_modules
    with open(path, encoding="utf-8") as fp:
        category = os.path.relpath(os.path.dirname(path), start=RESOURCE_PATH)
        try:
            modules = json.load(fp)
        except ValueError as oi:
            print("oi: "+oi)
            return "Nodetype data in %s/nodetypes.json not well-formed. Boing." % category
        for key in modules:
            modules[key]['path'] = os.path.join(os.path.dirname(path), 'nodefunctions.py')
            modules[key]['category'] = category
            if key in native_modules:
                logging.getLogger("system").warning("Native module names must be unique. %s is not." % key)
            native_modules[key] = modules[key]


def parse_recipe_or_operations_file(path, reload=False, category_overwrite=False):
    global custom_recipes
    import importlib
    import inspect

    category = category_overwrite or os.path.relpath(os.path.dirname(path), start=RESOURCE_PATH)
    if category == '.':
        category == ''  # relapth in rootfolder
    relpath = os.path.relpath(path, start=RESOURCE_PATH)
    name = os.path.basename(path)[:-3]

    mode = 'recipes' if os.path.basename(path).startswith('recipes') else 'operations'

    try:
        loader = importlib.machinery.SourceFileLoader(name, path)
        recipes = loader.load_module()
        # recipes = __import__(pyname, fromlist=['recipes'])
        # importlib.reload(sys.modules[pyname])
    except SyntaxError as e:
        return "%s in %s file %s, line %d" % (e.__class__.__name__, mode, relpath, e.lineno)
    except ImportError as e:
        return "%s in %s file %s: %s" % (e.__class__.__name__, mode, relpath, e.msg)

    for name, module in inspect.getmembers(recipes, inspect.ismodule):
        if hasattr(module, '__file__') and module.__file__.startswith(RESOURCE_PATH):
            module = importlib.reload(module)

    all_functions = inspect.getmembers(recipes, inspect.isfunction)
    for name, func in all_functions:
        filename = os.path.realpath(func.__code__.co_filename)
        if filename != os.path.realpath(path) and os.path.basename(filename) == os.path.basename(path):
            # import from another file of the same mode. ignore, to avoid
            # false duplicate-function-name alerts
            continue
        argspec = inspect.getargspec(func)
        if mode == 'recipes':
            arguments = argspec.args[1:]
        elif mode == 'operations':
            arguments = argspec.args[2:]
        defaults = argspec.defaults or []
        params = []
        diff = len(arguments) - len(defaults)
        for i, arg in enumerate(arguments):
            if i >= diff:
                default = defaults[i - diff]
            else:
                default = None
            params.append({
                'name': arg,
                'default': default
            })
        if mode == 'recipes' and name in custom_recipes and id(func) != id(custom_recipes[name]['function']):
            logging.getLogger("system").warning("Recipe function names must be unique. %s is not." % name)
        elif mode == 'operations' and name in custom_operations and id(func) != id(custom_operations[name]['function']):
            logging.getLogger("system").warning("Operations function names must be unique. %s is not." % name)
        data = {
            'name': name,
            'parameters': params,
            'function': func,
            'docstring': inspect.getdoc(func),
            'category': category,
            'path': path
        }

        if mode == 'recipes':
            custom_recipes[name] = data
        elif mode == 'operations':
            if hasattr(func, 'selectioninfo'):
                data['selectioninfo'] = func.selectioninfo
                custom_operations[name] = data


def reload_nodefunctions_file(path):
    import importlib
    import inspect
    try:
        loader = importlib.machinery.SourceFileLoader("nodefunctions", path)
        nodefuncs = loader.load_module()
        for name, module in inspect.getmembers(nodefuncs, inspect.ismodule):
            if hasattr(module, '__file__') and module.__file__.startswith(RESOURCE_PATH):
                loader = importlib.machinery.SourceFileLoader(name, module.__file__)
                loader.load_module()
    except SyntaxError as e:
        relpath = os.path.relpath(path, start=RESOURCE_PATH)
        return "%s in nodefunction file %s, line %d" % (e.__class__.__name__, relpath, e.lineno)
    except ImportError as e:
        relpath = os.path.relpath(path, start=RESOURCE_PATH)
        return "%s in nodfunction file %s: %s" % (e.__class__.__name__, relpath, e.msg)


def reload_native_modules():
    # stop nodenets, save state
    global native_modules, custom_recipes, custom_operations
    native_modules = {}
    custom_recipes = {}
    custom_operations = {}
    runners = {}
    errors = []
    # load builtins:
    from micropsi_core.nodenet.native_modules import nodetypes
    native_modules.update(nodetypes)
    operationspath = os.path.dirname(os.path.realpath(__file__)) + '/nodenet/operations/'
    for file in os.listdir(operationspath):
        import micropsi_core.nodenet.operations
        if file != '__init__.py' and not file.startswith('.') and os.path.isfile(os.path.join(operationspath, file)):
            err = parse_recipe_or_operations_file(os.path.join(operationspath, file), category_overwrite=file[:-3])
            if err:
                errors.append(err)

    for uid in nodenets:
        if nodenets[uid].is_active:
            runners[uid] = True
            nodenets[uid].is_active = False
    errors.extend(load_user_files(RESOURCE_PATH, reload_nodefunctions=True, errors=[]))
    for nodenet_uid in nodenets:
        nodenets[nodenet_uid].reload_native_modules(native_modules)
    # restart previously active nodenets
    for uid in runners:
        nodenets[uid].is_active = True

    if len(errors) == 0:
        return True, []
    else:
        return False, errors


def initialize(persistency_path=None, resource_path=None):
    global PERSISTENCY_PATH, RESOURCE_PATH, configs, logger, runner, initialized

    if persistency_path is None:
        persistency_path = cfg['paths']['data_directory']

    if resource_path is None:
        resource_path = persistency_path

    PERSISTENCY_PATH = persistency_path
    RESOURCE_PATH = resource_path

    sys.path.append(resource_path)

    configs = config.ConfigurationManager(cfg['paths']['server_settings_path'])

    if logger is None:
        logger = MicropsiLogger({
            'system': cfg['logging']['level_system'],
            'world': cfg['logging']['level_world']
        }, cfg['logging'].get('logfile'))

    load_definitions()
    result, errors = reload_native_modules()
    for e in errors:
        logging.getLogger("system").error(e)

    # discover available worlds:
    import importlib
    basedir = os.path.join(os.path.dirname(__file__), 'world')
    dirs = os.listdir(basedir)
    #  look into each folder in world/
    for d in dirs:
        worlddir = os.path.join(basedir, d)
        if os.path.isdir(worlddir) and not d.startswith('__'):
            try:
                init = importlib.import_module(".%s" % d, package='micropsi_core.world')
                # import all modules defined in __init__.__all__
                if init and hasattr(init, '__all__'):
                    for world in init.__all__:
                        importlib.import_module(".%s" % world, package='micropsi_core.world.%s' % d)
                        logging.getLogger("system").debug("Found %s world" % world)
            except ImportError:
                logging.getLogger("system").debug("Error importing %s world" % world)

    # initialize runners
    # Initialize the threads for the continuous calculation of nodenets and worlds
    if 'runner_timestep' not in configs:
        configs['runner_timestep'] = 200
        configs.save_configs()
    if 'runner_factor' not in configs:
        configs['runner_factor'] = 2
        configs.save_configs()

    set_runner_properties(configs['runner_timestep'], configs['runner_factor'])

    runner['running'] = True
    if runner.get('runner') is None:
        runner['runner'] = MicropsiRunner()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGABRT, signal_handler)
    initialized = True
