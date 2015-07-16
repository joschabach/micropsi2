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
import warnings
import threading
from datetime import datetime, timedelta
import time
import signal

import logging

from .micropsi_logger import MicropsiLogger

NODENET_DIRECTORY = "nodenets"
WORLD_DIRECTORY = "worlds"
RESOURCE_PATH = cfg['paths']['resource_path']

configs = config.ConfigurationManager(cfg['paths']['server_settings_path'])

worlds = {}
nodenets = {}
native_modules = {}
custom_recipes = {}

runner = {'timestep': 1000, 'runner': None, 'factor': 1}

signal_handler_registry = []

logger = MicropsiLogger({
    'system': cfg['logging']['level_system'],
    'world': cfg['logging']['level_world'],
    'nodenet': cfg['logging']['level_nodenet']
}, cfg['logging'].get('logfile'))

nodenet_lock = threading.Lock()

if cfg['micropsi2'].get('profile_runner'):
    import cProfile
    import pstats
    import io


def add_signal_handler(handler):
    signal_handler_registry.append(handler)


def signal_handler(signal, frame):
    logging.getLogger('system').info("Shutting down")
    for handler in signal_handler_registry:
        handler(signal, frame)
    sys.exit(0)


class MicropsiRunner(threading.Thread):

    sum_of_durations = 0
    number_of_samples = 0
    total_steps = 0
    granularity = 10
    conditions = {}

    def __init__(self):
        threading.Thread.__init__(self)
        if cfg['micropsi2'].get('profile_runner'):
            self.profiler = cProfile.Profile()
        else:
            self.profiler = None
        self.daemon = True
        self.paused = True
        self.state = threading.Condition()
        self.start()

    def check_conditions(self, nodenet_uid):
        if nodenet_uid in MicropsiRunner.conditions:
            conditions = MicropsiRunner.conditions[nodenet_uid]
            net = nodenets[nodenet_uid]
            if 'step' in conditions and net.current_step >= conditions['step']:
                if 'step_amount' in conditions:
                    conditions['step'] = net.current_step + conditions['step_amount']
                return False
            if 'monitor' in conditions and net.current_step > 0:
                monitor = net.get_monitor(conditions['monitor']['uid'])
                if net.current_step in monitor.values and round(monitor.values[net.current_step], 4) == round(conditions['monitor']['value'], 4):
                    return False
        return True

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
            uids = list(nodenets.keys())
            for uid in uids:
                if uid in nodenets:
                    nodenet = nodenets[uid]
                    if nodenet.is_active:
                        if not self.check_conditions(uid):
                            nodenet.is_active = False
                            continue
                        log = True
                        try:
                            if self.profiler:
                                self.profiler.enable()
                            nodenet.step()
                            if self.profiler:
                                self.profiler.disable()
                            nodenet.update_monitors()
                        except:
                            if self.profiler:
                                self.profiler.disable()
                            nodenet.is_active = False
                            logging.getLogger("nodenet").error("Exception in NodenetRunner:", exc_info=1)
                            MicropsiRunner.last_nodenet_exception[uid] = sys.exc_info()
                        if nodenet.world and nodenet.current_step % runner['factor'] == 0:
                            try:
                                nodenet.world.step()
                            except:
                                nodenet.is_active = False
                                logging.getLogger("world").error("Exception in WorldRunner:", exc_info=1)
                                MicropsiRunner.last_world_exception[nodenets[uid].world.uid] = sys.exc_info()

            elapsed = datetime.now() - start
            if log:
                ms = elapsed.seconds + ((elapsed.microseconds // 1000) / 1000)
                self.sum_of_durations += ms
                self.number_of_samples += 1
                self.total_steps += 1
                average_duration = self.sum_of_durations / self.number_of_samples
                if self.total_steps % self.granularity == 0:
                    if self.profiler:
                        s = io.StringIO()
                        sortby = 'cumtime'
                        ps = pstats.Stats(self.profiler, stream=s).sort_stats(sortby)
                        ps.print_stats('nodenet')
                        logging.getLogger("nodenet").debug(s.getvalue())

                    logging.getLogger("nodenet").debug("Step %d: Avg. %.8f sec" % (self.total_steps, average_duration))
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

    def resume(self):
        with self.state:
            self.paused = False
            self.state.notify()

    def pause(self):
        with self.state:
            self.paused = True


MicropsiRunner.last_world_exception = {}
MicropsiRunner.last_nodenet_exception = {}


def kill_runners(signal, frame):
    runner['runner'].resume()
    runner['running'] = False
    runner['runner'].join()


def _get_world_uid_for_nodenet_uid(nodenet_uid):
    """ get the world uid to a given nodenet uid."""
    if nodenet_uid in nodenet_data:
        return nodenet_data[nodenet_uid].world
    return None


# MicroPsi API


# loggers
def set_logging_levels(system=None, world=None, nodenet=None):
    if system is not None and system in logger.logging_levels:
        logger.set_logging_level('system', system)
    if world is not None and world in logger.logging_levels:
        logger.set_logging_level('world', world)
    if nodenet is not None and nodenet in logger.logging_levels:
        logger.set_logging_level('nodenet', nodenet)
    return True


def get_logger_messages(loggers=[], after=0):
    """ Returns messages for the specified loggers.
        If given, limits the messages to those that occured after the given timestamp"""
    if not isinstance(loggers, list):
        loggers = [loggers]
    return logger.get_logs(loggers, after)


def get_monitoring_info(nodenet_uid, logger=[], after=0):
    """ Returns log-messages and monitor-data for the given nodenet."""
    data = get_monitor_data(nodenet_uid, 0)
    data['logs'] = get_logger_messages(logger, after)
    return data


def get_logging_levels():
    inverse_map = {
        50: 'CRITICAL',
        40: 'ERROR',
        30: 'WARNING',
        20: 'INFO',
        10: 'DEBUG',
        0: 'NOTSET'
    }
    levels = {
        'system': inverse_map[logging.getLogger('system').getEffectiveLevel()],
        'world': inverse_map[logging.getLogger('world').getEffectiveLevel()],
        'nodenet': inverse_map[logging.getLogger('nodenet').getEffectiveLevel()],
    }
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
            return None
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
        world = worldadapter = None

        nodenet_lock.acquire()
        if nodenet_uid not in nodenets:
            data = nodenet_data[nodenet_uid]

            if data.world:
                if data.world in worlds:
                    world = worlds.get(data.world)
                    worldadapter = data.get('worldadapter')

            engine = data.get('engine', 'dict_engine')

            if engine == 'dict_engine':
                from micropsi_core.nodenet.dict_engine.dict_nodenet import DictNodenet
                nodenets[nodenet_uid] = DictNodenet(
                    name=data.name, worldadapter=worldadapter,
                    world=world, owner=data.owner, uid=data.uid,
                    native_modules=filter_native_modules(engine))
            elif engine == 'theano_engine':
                from micropsi_core.nodenet.theano_engine.theano_nodenet import TheanoNodenet
                nodenets[nodenet_uid] = TheanoNodenet(
                    name=data.name, worldadapter=worldadapter,
                    world=world, owner=data.owner, uid=data.uid,
                    native_modules=filter_native_modules(engine))
            # Add additional engine types here
            else:
                nodenet_lock.release()
                return False, "Nodenet %s requires unknown engine %s" % (nodenet_uid, engine)

            nodenets[nodenet_uid].load(os.path.join(RESOURCE_PATH, NODENET_DIRECTORY, nodenet_uid + ".json"))

            if "settings" in data:
                nodenets[nodenet_uid].settings = data["settings"].copy()
            else:
                nodenets[nodenet_uid].settings = {}
        else:
            world = nodenets[nodenet_uid].world or None
            worldadapter = nodenets[nodenet_uid].worldadapter
        if world:
            world.register_nodenet(worldadapter, nodenets[nodenet_uid])

        nodenet_lock.release()
        return True, nodenet_uid
    return False, "Nodenet %s not found in %s" % (nodenet_uid, RESOURCE_PATH)


def get_nodenet_data(nodenet_uid, nodespace, step=0, include_links=True):
    """ returns the current state of the nodenet """
    nodenet = get_nodenet(nodenet_uid)
    data = nodenet.metadata
    if step > nodenet.current_step:
        return data
    with nodenet.netlock:
        if not nodenets[nodenet_uid].is_nodespace(nodespace):
            nodespace = nodenets[nodenet_uid].get_nodespace(None).uid
        data.update(nodenets[nodenet_uid].get_nodespace_data(nodespace, include_links))
        data['nodespace'] = nodespace
        data.update({
            'nodetypes': nodenet.get_standard_nodetype_definitions(),
            'native_modules': filter_native_modules(nodenet.engine),
            'monitors': nodenet.construct_monitors_dict()
        })
    return data


def unload_nodenet(nodenet_uid):
    """ Unload the nodenet.
        Deletes the instance of this nodenet without deleting it from the storage

        Arguments:
            nodenet_uid
    """
    if not nodenet_uid in nodenets:
        return False
    if nodenets[nodenet_uid].world:
        nodenets[nodenet_uid].world.unregister_nodenet(nodenet_uid)
    del nodenets[nodenet_uid]
    return True


def new_nodenet(nodenet_name, engine="dict_engine", worldadapter=None, template=None, owner="", world_uid=None, uid=None):
    """Creates a new node net manager and registers it.

    Arguments:
        worldadapter(optional): the type of the world adapter supported by this nodenet. Also used to determine the set of
            gate types supported for directional activation spreading of this nodenet, and the initial node types
        owner (optional): the creator of this nodenet
        world_uid (optional): if submitted, attempts to bind the nodenet to this world
        uid (optional): if submitted, this is used as the UID for the nodenet (normally, this is generated)

    Returns
        nodenet_uid if successful,
        None if failure
    """
    if not uid:
        uid = tools.generate_uid()

    data = dict(
        version=1,
        step=0,
        uid=uid,
        name=nodenet_name,
        worldadapter=worldadapter,
        owner=owner,
        world=world_uid,
        settings={},
        engine=engine)

    filename = os.path.join(RESOURCE_PATH, NODENET_DIRECTORY, data['uid'] + ".json")
    nodenet_data[data['uid']] = Bunch(**data)
    load_nodenet(data['uid'])

    if template is not None and template in nodenet_data:
        load_nodenet(template)
        data_to_merge = nodenets[template].data
        data_to_merge.update(data)
        nodenets[uid].merge_data(data_to_merge)

    nodenets[uid].save(filename)
    return True, data['uid']


def delete_nodenet(nodenet_uid):
    """Unloads the given nodenet from memory and deletes it from the storage.

    Simple unloading is maintained automatically when a nodenet is suspended and another one is accessed.
    """
    filename = os.path.join(RESOURCE_PATH, NODENET_DIRECTORY, nodenet_uid + '.json')
    nodenet = get_nodenet(nodenet_uid)
    nodenet.remove(filename)
    unload_nodenet(nodenet_uid)
    del nodenet_data[nodenet_uid]
    return True


def set_nodenet_properties(nodenet_uid, nodenet_name=None, worldadapter=None, world_uid=None, owner=None):
    """Sets the supplied parameters (and only those) for the nodenet with the given uid."""

    nodenet = nodenets[nodenet_uid]
    if nodenet.world and nodenet.world.uid != world_uid:
        nodenet.world.unregister_nodenet(nodenet_uid)
        nodenet.world = None
    if worldadapter is None:
        worldadapter = nodenet.worldadapter
    if world_uid is not None and worldadapter is not None:
        assert worldadapter in worlds[world_uid].supported_worldadapters
        nodenet.world = worlds[world_uid]
        nodenet.worldadapter = worldadapter
        worlds[world_uid].register_nodenet(worldadapter, nodenet)
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
    """Sets the speed of the nodenet simulation in ms.

    Argument:
        timestep: sets the simulation speed.
    """
    configs['runner_timestep'] = timestep
    runner['timestep'] = timestep
    configs['runner_factor'] = int(factor)
    runner['factor'] = int(factor)
    return True


def set_runner_condition(nodenet_uid, monitor=None, steps=None):
    """ registers a condition that stops the runner if it is fulfilled"""
    MicropsiRunner.conditions[nodenet_uid] = {}
    if monitor is not None:
        MicropsiRunner.conditions[nodenet_uid]['monitor'] = monitor
    if steps is not None:
        MicropsiRunner.conditions[nodenet_uid]['step'] = nodenets[nodenet_uid].current_step + steps
        MicropsiRunner.conditions[nodenet_uid]['step_amount'] = steps
    return True, MicropsiRunner.conditions[nodenet_uid]


def remove_runner_condition(nodenet_uid):
    MicropsiRunner.conditions[nodenet_uid] = {}
    return True


def get_runner_properties():
    """Returns the speed that has been configured for the nodenet runner (in ms)."""
    return {
        'timestep': configs['runner_timestep'],
        'factor': configs['runner_factor']
    }


def get_is_nodenet_running(nodenet_uid):
    """Returns True if a nodenet runner is active for the given nodenet, False otherwise."""
    return nodenets[nodenet_uid].is_active


def stop_nodenetrunner(nodenet_uid):
    """Stops the thread for the given nodenet."""
    nodenets[nodenet_uid].is_active = False
    test = {nodenets[uid].is_active for uid in nodenets}
    if True not in test:
        test = {worlds[uid].is_active for uid in worlds}
        if True not in test:
            runner['runner'].pause()

    return True


def step_nodenet(nodenet_uid):
    """Advances the given nodenet by one simulation step.

    Arguments:
        nodenet_uid: The uid of the nodenet
    """
    nodenets[nodenet_uid].step()
    nodenets[nodenet_uid].update_monitors()
    if nodenets[nodenet_uid].world and nodenets[nodenet_uid].current_step % configs['runner_factor'] == 0:
        nodenets[nodenet_uid].world.step()
    return nodenets[nodenet_uid].current_step


def revert_nodenet(nodenet_uid):
    """Returns the nodenet to the last saved state."""
    unload_nodenet(nodenet_uid)
    load_nodenet(nodenet_uid)
    return True


def save_nodenet(nodenet_uid):
    """Stores the nodenet on the server (but keeps it open)."""
    nodenet = nodenets[nodenet_uid]
    nodenet.save(os.path.join(RESOURCE_PATH, NODENET_DIRECTORY, nodenet_uid + '.json'))
    nodenet_data[nodenet_uid] = Bunch(**nodenet.metadata)
    return True


def export_nodenet(nodenet_uid):
    """Exports the nodenet state to the user, so it can be viewed and exchanged.

    Returns a string that contains the nodenet state in JSON format.
    """
    return json.dumps(nodenets[nodenet_uid].data, sort_keys=True, indent=4)


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
    # assert import_data['world'] in worlds
    filename = os.path.join(RESOURCE_PATH, NODENET_DIRECTORY, import_data['uid'] + '.json')
    with open(filename, 'w+') as fp:
        fp.write(json.dumps(import_data))
    nodenet_data[import_data['uid']] = parse_definition(import_data, filename)
    load_nodenet(import_data['uid'])
    return import_data['uid']


def merge_nodenet(nodenet_uid, string, keep_uids=False):
    """Merges the nodenet data with an existing nodenet, instantiates the nodenet.

    Arguments:
        nodenet_uid: the uid of the existing nodenet (may overwrite existing nodenet)
        string: a string that contains the nodenet data that is to be merged in JSON format.
        keep_uids: if true, no uid replacement will be performed. Dangerous.
    """
    nodenet = nodenets[nodenet_uid]
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
    nodenet = nodenets[nodenet_uid]
    data = {}
    for uid in nodenet.get_nodespace_uids():
        nodespace = nodenet.get_nodespace(uid)
        data[uid] = {
            'uid': uid,
            'name': nodespace.name,
            'parent': nodespace.parent_nodespace,
            'nodes': {},
        }
        for nid in nodespace.get_known_ids('nodes'):
            data[uid]['nodes'][nid] = {
                'uid': nid,
                'name': nodenet.get_node(nid).name,
                'type': nodenet.get_node(nid).type
            }
    return data


def get_node(nodenet_uid, node_uid):
    """Returns a dictionary with all node parameters, if node exists, or None if it does not. The dict is
    structured as follows:

    {
        "index" (int): index for auto-alignment,
        "uid" (str): unique identifier,
        "state" (dict): a dictionary of node states and their values,
        "type" (string): the type of this node,
        "parameters" (dict): a dictionary of the node parameters
        "activation" (float): the activation of this node,
        "gate_parameters" (dict): a dictionary containing dicts of parameters for each gate of this node
        "name" (str): display name
        "gate_activations" (dict): a dictionary containing dicts of activations for each gate of this node
        "gate_functions"(dict): a dictionary containing the name of the gatefunction for each gate of this node
        "position" (list): the x, y coordinates of this node, as a list
        "sheaves" (dict): a dict of sheaf-activations for this node
        "parent_nodespace" (str): the uid of the nodespace this node lives in
    }
    """
    return nodenets[nodenet_uid].get_node(node_uid).data


def add_node(nodenet_uid, type, pos, nodespace=None, state=None, uid=None, name="", parameters=None):
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
    uid = nodenet.create_node(type, nodespace, pos, name, uid=uid, parameters=parameters)
    return True, uid

def add_nodespace(nodenet_uid, pos, nodespace=None, uid=None, name="", options=None):
    """Creates a new nodespace
    Arguments:
        nodenet_uid: uid of the nodespace manager
        position: position of the node in the current nodespace
        nodespace: uid of the parent nodespace
        uid (optional): if not supplied, a uid will be generated
        name (optional): if not supplied, the uid will be used instead of a display name
        options (optional): a dict of options. TBD
    """
    nodenet = get_nodenet(nodenet_uid)
    uid = nodenet.create_nodespace(nodespace, pos, name=name, uid=uid, options=options)
    return True, uid


def clone_nodes(nodenet_uid, node_uids, clonemode, nodespace=None, offset=[50, 50]):
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

    nodenet = get_nodenet(nodenet_uid)
    result = {'nodes': [], 'links': []}
    copynodes = {uid: nodenet.get_node(uid) for uid in node_uids}
    copylinks = {}
    uidmap = {}
    if clonemode != 'none':
        for _, n in copynodes.items():
            for g in n.get_gate_types():
                for link in n.get_gate(g).get_links():
                    if clonemode == 'all' or link.target_node.uid in copynodes:
                        copylinks[link.uid] = link
            if clonemode == 'all':
                for s in n.get_slot_types():
                    for link in n.get_slot(s).get_links():
                        copylinks[link.uid] = link

    for _, n in copynodes.items():
        target_nodespace = nodespace if nodespace is not None else n.parent_nodespace
        uid = nodenet.create_node(n.type, target_nodespace, (n.position[0] + offset[0], n.position[1] + offset[1]), name=n.name + '_copy', uid=None, parameters=n.clone_parameters().copy(), gate_parameters=n.get_gate_parameters())
        if uid:
            uidmap[n.uid] = uid
            result['nodes'].append(nodenet.get_node(uid).data)
        else:
            logger.warning('Could not clone node: ' + uid)

    for uid, l in copylinks.items():
        source_uid = uidmap.get(l.source_node.uid, l.source_node.uid)
        target_uid = uidmap.get(l.target_node.uid, l.target_node.uid)
        success = nodenet.create_link(
            source_uid,
            l.source_gate.type,
            target_uid,
            l.target_slot.type,
            l.weight,
            l.certainty)
        if success:
            links = nodenet.get_node(source_uid).get_gate(l.source_gate.type).get_links()
            link = None
            for candidate in links:
                if candidate.target_slot.type == l.target_slot.type and candidate.target_node.uid == target_uid:
                    link = candidate
                    break
            result['links'].append(link.data)
        else:
            logger.warning('Could not duplicate link: ' + uid)

    if len(result['nodes']) or len(nodes) == 0:
        return True, result
    else:
        return False, "Could not clone nodes. See log for details."


def __pythonify(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name).lower()
    return re.sub('([\s+\W])', '_', s1)


def generate_netapi_fragment(nodenet_uid, node_uids):
    lines = []
    idmap = {}
    nodenet = get_nodenet(nodenet_uid)
    nodes = []
    nodespaces = []
    for node_uid in node_uids:
        if not nodenet.is_nodespace(node_uid):
            nodes.append(nodenet.get_node(node_uid))
        else:
            nodespaces.append(nodenet.get_nodespace(node_uid))

    xpos = []
    ypos = []
    nodes = sorted(nodes, key=lambda node: node.position[1] * 1000 + node.position[0])
    nodespaces = sorted(nodespaces, key=lambda node: node.position[1] * 1000 + node.position[0])

    # nodespaces
    for i, nodespace in enumerate(nodespaces):
        name = nodespace.name.strip() if nodespace.name != nodespace.uid else None
        varname = "nodespace%i" % i
        if name:
            pythonname = __pythonify(name)
            if pythonname not in idmap.values():
                varname = pythonname
            lines.append("%s = netapi.create_nodespace(None, \"%s\")" % (varname, name))
        else:
            lines.append("%s = netapi.create_nodespace(None)" % (varname))
        idmap[nodespace.uid] = varname
        xpos.append(node.position[0])
        ypos.append(node.position[1])

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

        ndgps = node.clone_non_default_gate_parameters()
        for gatetype in ndgps.keys():
            for parameter, value in ndgps[gatetype].items():
                lines.append("%s.set_gate_parameter('%s', \"%s\", %.2f)" % (varname, gatetype, parameter, value))

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
    origin = (100, 100)
    factor = (int(min(xpos)), int(min(ypos)))
    lines.append("origin_pos = (%d, %d)" % origin)
    for node in nodes + nodespaces:
        x = int(node.position[0] - factor[0])
        y = int(node.position[1] - factor[1])
        lines.append("%s.position = (origin_pos[0] + %i, origin_pos[1] + %i)" % (idmap[node.uid], x, y))

    return "\n".join(lines)


def set_node_position(nodenet_uid, node_uid, pos):
    """Positions the specified node at the given coordinates."""
    nodenet = nodenets[nodenet_uid]
    if nodenet.is_node(node_uid):
        nodenet.get_node(node_uid).position = pos
    elif nodenet.is_nodespace(node_uid):
        nodenet.get_nodespace(node_uid).position = pos
    return True


def set_node_name(nodenet_uid, node_uid, name):
    """Sets the display name of the node"""
    nodenet = nodenets[nodenet_uid]
    if nodenet.is_node(node_uid):
        nodenet.get_node(node_uid).name = name
    elif nodenet.is_nodespace(node_uid):
        nodenet.get_nodespace(node_uid).name = name
    return True


def set_node_state(nodenet_uid, node_uid, state):
    """ Sets the state of the given node to the given state"""
    node = nodenets[nodenet_uid].get_node(node_uid)
    for key in state:
        node.set_state(key, state[key])
    return True


def set_node_activation(nodenet_uid, node_uid, activation):
    nodenets[nodenet_uid].get_node(node_uid).activation = activation
    return True


def delete_node(nodenet_uid, node_uid):
    """Removes the node or node space"""
    nodenet = nodenets[nodenet_uid]
    with nodenet.netlock:
        if nodenet.is_node(node_uid):
            nodenets[nodenet_uid].delete_node(node_uid)
            return True
        return False


def delete_nodespace(nodenet_uid, nodespace_uid):
    """ Removes the given node space and all its contents"""
    nodenet = nodenets[nodenet_uid]
    with nodenet.netlock:
        if nodenet.is_nodespace(nodespace_uid):
            nodenet.delete_nodespace(nodespace_uid)
            return True
        return False


def get_available_node_types(nodenet_uid):
    """Returns a list of available node types. (Including native modules.)"""
    nodenet = nodenets[nodenet_uid]
    all_nodetypes = filter_native_modules(nodenet.engine)
    all_nodetypes.update(nodenet.get_standard_nodetype_definitions())
    return all_nodetypes


def get_available_native_module_types(nodenet_uid):
    """Returns a list of native modules.
    If an nodenet uid is supplied, filter for node types defined within this nodenet."""
    return filter_native_modules(nodenets[nodenet_uid].engine)


def set_node_parameters(nodenet_uid, node_uid, parameters):
    """Sets a dict of arbitrary values to make the node stateful."""
    for key, value in parameters.items():
        nodenets[nodenet_uid].get_node(node_uid).set_parameter(key, value)
    return True


def get_gatefunction(nodenet_uid, node_uid, gate_type):
    """
    Returns the name of the gate function configured for that given node and gate
    """
    return nodenets[nodenet_uid].get_node(node_uid).get_gatefunction_name(gate_type)


def set_gatefunction(nodenet_uid, node_uid, gate_type, gatefunction=None):
    """
    Sets the gate function of the given node and gate.
    """
    nodenets[nodenet_uid].get_node(node_uid).set_gatefunction_name(gate_type, gatefunction)
    return True


def get_available_gatefunctions(nodenet_uid):
    """
    Returns a list of names of the available gatefunctions
    """
    return nodenets[nodenet_uid].get_available_gatefunctions()


def set_gate_parameters(nodenet_uid, node_uid, gate_type, parameters):
    """Sets the gate parameters of the given gate of the given node to the supplied dictionary."""
    for key, value in parameters.items():
        nodenets[nodenet_uid].get_node(node_uid).set_gate_parameter(gate_type, key, value)
    return True


def get_available_datasources(nodenet_uid):
    """Returns a list of available datasource types for the given nodenet."""
    world_uid = nodenets[nodenet_uid].world.uid
    return worlds[world_uid].get_available_datasources(nodenet_uid)


def get_available_datatargets(nodenet_uid):
    """Returns a list of available datatarget types for the given nodenet."""
    world_uid = nodenets[nodenet_uid].world.uid
    return worlds[world_uid].get_available_datatargets(nodenet_uid)


def bind_datasource_to_sensor(nodenet_uid, sensor_uid, datasource):
    """Associates the datasource type to the sensor node with the given uid."""
    node = nodenets[nodenet_uid].get_node(sensor_uid)
    if node.type == "Sensor":
        node.set_parameter('datasource', datasource)
        return True
    return False


def bind_datatarget_to_actor(nodenet_uid, actor_uid, datatarget):
    """Associates the datatarget type to the actor node with the given uid."""
    node = nodenets[nodenet_uid].get_node(actor_uid)
    if node.type == "Actor":
        node.set_parameter('datatarget', datatarget)
        return True
    return False


def add_link(nodenet_uid, source_node_uid, gate_type, target_node_uid, slot_type, weight=1, certainty=1):
    """Creates a new link.

    Arguments.
        source_node_uid: uid of the origin node
        gate_type: type of the origin gate (usually defines the link type)
        target_node_uid: uid of the target node
        slot_type: type of the target slot
        weight: the weight of the link (a float)
        certainty (optional): a probabilistic parameter for the link
    """
    nodenet = nodenets[nodenet_uid]
    with nodenet.netlock:
        success = nodenet.create_link(source_node_uid, gate_type, target_node_uid, slot_type, weight, certainty)
    uid = None
    if success:                                                       # todo: check whether clients need these uids
        uid = source_node_uid+":"+gate_type+":"+slot_type+":"+target_node_uid
    return success, uid


def set_link_weight(nodenet_uid, source_node_uid, gate_type, target_node_uid, slot_type, weight=1, certainty=1):
    """Set weight of the given link."""
    nodenet = nodenets[nodenet_uid]
    return nodenet.set_link_weight(source_node_uid, gate_type, target_node_uid, slot_type, weight, certainty)


def get_links_for_nodes(nodenet_uid, node_uids):
    """ Returns a dict of links connected to the given nodes """
    nodenet = nodenets[nodenet_uid]
    source_nodes = [nodenet.get_node(uid) for uid in node_uids]
    links = {}
    nodes = {}
    for node in source_nodes:
        nodelinks = node.get_associated_links()
        for l in nodelinks:
            links[l.uid] = l.data
            if l.source_node.parent_nodespace != node.parent_nodespace:
                nodes[l.source_node.uid] = l.source_node.data
            if l.target_node.parent_nodespace != node.parent_nodespace:
                nodes[l.target_node.uid] = l.target_node.data
    return {'links': links, 'nodes': nodes}



def delete_link(nodenet_uid, source_node_uid, gate_type, target_node_uid, slot_type):
    """Delete the given link."""
    nodenet = nodenets[nodenet_uid]
    return nodenet.delete_link(source_node_uid, gate_type, target_node_uid, slot_type)


def align_nodes(nodenet_uid, nodespace):
    """Perform auto-alignment of nodes in the current nodespace"""
    result = node_alignment.align(nodenets[nodenet_uid], nodespace)
    return result


def user_prompt_response(nodenet_uid, node_uid, values, resume_nodenet):
    for key, value in values.items():
        nodenets[nodenet_uid].get_node(node_uid).set_parameter(key, value)
    nodenets[nodenet_uid].is_active = resume_nodenet


def get_available_recipes():
    """ Returns a dict of the available user-recipes """
    recipes = {}
    for name, data in custom_recipes.items():
        if not name.startswith('_'):
            recipes[name] = {
                'name': name,
                'parameters': data['parameters']
            }
    return recipes


def run_recipe(nodenet_uid, name, parameters):
    """ Calls the given recipe with the provided parameters, and returns the output, if any """
    netapi = nodenets[nodenet_uid].netapi
    params = {}
    for key in parameters:
        if parameters[key] != '':
            params[key] = parameters[key]
    if name in custom_recipes:
        func = custom_recipes[name]['function']
        if cfg['micropsi2'].get('profile_runner'):
            profiler = cProfile.Profile()
            profiler.enable()
        result = func(netapi, **params)
        if cfg['micropsi2'].get('profile_runner'):
            profiler.disable()
            s = io.StringIO()
            sortby = 'cumtime'
            ps = pstats.Stats(profiler, stream=s).sort_stats(sortby)
            ps.print_stats('nodenet')
            logging.getLogger("nodenet").debug(s.getvalue())
        return True, result
    else:
        return False, "Script not found"


# --- end of API

def filter_native_modules(engine=None):
    data = {}
    for key in native_modules:
        if native_modules[key].get('engine') is None or engine is None or engine == native_modules[key]['engine']:
            data[key] = native_modules[key].copy()
    return data


def crawl_definition_files(path, type="definition"):
    """Traverse the directories below the given path for JSON definitions of nodenets and worlds,
    and return a dictionary with the signatures of these nodenets or worlds.
    """

    result = {}
    tools.mkdir(path)

    for user_directory_name, user_directory_names, file_names in os.walk(path):
        for definition_file_name in file_names:
            if definition_file_name.endswith(".json"):
                try:
                    filename = os.path.join(user_directory_name, definition_file_name)
                    with open(filename) as file:
                        data = parse_definition(json.load(file), filename)
                        result[data.uid] = data
                except ValueError:
                    warnings.warn("Invalid %s data in file '%s'" % (type, definition_file_name))
                except IOError:
                    warnings.warn("Could not open %s data file '%s'" % (type, definition_file_name))
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
        if "world_type" in json:
            result['world_type'] = json['world_type']
        if "settings" in json:
            result['settings'] = json['settings']
        return Bunch(**result)


# Set up the MicroPsi runtime
def load_definitions():
    global nodenet_data, world_data
    nodenet_data = crawl_definition_files(path=os.path.join(RESOURCE_PATH, NODENET_DIRECTORY), type="nodenet")
    world_data = crawl_definition_files(path=os.path.join(RESOURCE_PATH, WORLD_DIRECTORY), type="world")
    if not world_data:
        # create a default world for convenience.
        uid = tools.generate_uid()
        filename = os.path.join(RESOURCE_PATH, WORLD_DIRECTORY, uid + '.json')
        world_data[uid] = Bunch(uid=uid, name="default", version=1, filename=filename)
        with open(filename, 'w+') as fp:
            fp.write(json.dumps(world_data[uid], sort_keys=True, indent=4))
    return nodenet_data, world_data


# set up all worlds referred to in the world_data:
def init_worlds(world_data):
    global worlds
    for uid in world_data:
        if "world_type" in world_data[uid]:
            try:
                worlds[uid] = get_world_class_from_name(world_data[uid].world_type)(**world_data[uid])
            except TypeError:
                worlds[uid] = world.World(**world_data[uid])
            except AttributeError as err:
                warnings.warn("Unknown world_type: %s (%s)" % (world_data[uid].world_type, str(err)))
            except:
                warnings.warn("Can not instantiate World \"%s\": %s" % (world_data[uid].name, str(sys.exc_info()[1])))
        else:
            worlds[uid] = world.World(**world_data[uid])
    return worlds


def load_user_files(do_reload=False):
    # see if we have additional nodetypes defined by the user.
    import sys
    global native_modules
    native_modules = {}
    custom_nodetype_file = os.path.join(RESOURCE_PATH, 'nodetypes.json')
    if os.path.isfile(custom_nodetype_file):
        try:
            with open(custom_nodetype_file) as fp:
                native_modules = json.load(fp)
        except ValueError:
            warnings.warn("Nodetype data in %s not well-formed." % custom_nodetype_file)

    sys.path.append(RESOURCE_PATH)
    parse_recipe_file()
    return native_modules


def parse_recipe_file():
    custom_recipe_file = os.path.join(RESOURCE_PATH, 'recipes.py')
    if not os.path.isfile(custom_recipe_file):
        return

    import importlib.machinery
    import inspect
    global custom_recipes

    loader = importlib.machinery.SourceFileLoader("recipes", custom_recipe_file)
    recipes = loader.load_module()
    # import recipes
    custom_recipes = {}
    all_functions = inspect.getmembers(recipes, inspect.isfunction)
    for name, func in all_functions:
        argspec = inspect.getargspec(func)
        arguments = argspec.args[1:]
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
        custom_recipes[name] = {
            'name': name,
            'parameters': params,
            'function': func
        }


def reload_native_modules():
    # stop nodenets, save state
    runners = {}
    for uid in nodenets:
        if nodenets[uid].is_active:
            runners[uid] = True
            nodenets[uid].is_active = False
    load_user_files(True)
    import importlib
    custom_nodefunctions_file = os.path.join(RESOURCE_PATH, 'nodefunctions.py')
    if os.path.isfile(custom_nodefunctions_file):
        loader = importlib.machinery.SourceFileLoader("nodefunctions", custom_nodefunctions_file)
        loader.load_module()
    for nodenet_uid in nodenets:
        nodenets[nodenet_uid].reload_native_modules(filter_native_modules(nodenets[nodenet_uid].engine))
    # restart previously active nodenets
    for uid in runners:
        nodenets[uid].is_active = True
    return True


load_definitions()
init_worlds(world_data)
load_user_files()

# initialize runners
# Initialize the threads for the continuous simulation of nodenets and worlds
if 'runner_timestep' not in configs:
    configs['runner_timestep'] = 200
    configs.save_configs()
if 'runner_factor' not in configs:
    configs['runner_factor'] = 2
    configs.save_configs()

set_runner_properties(configs['runner_timestep'], configs['runner_factor'])

runner['running'] = True
runner['runner'] = MicropsiRunner()

add_signal_handler(kill_runners)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
