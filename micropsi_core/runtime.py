#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MicroPsi runtime module;
maintains a set of users, worlds (up to one per user), and nodenets, and provides an interface to external clients
"""

from micropsi_core._runtime_api_world import *
from micropsi_core._runtime_api_monitors import *

__author__ = 'joscha'
__date__ = '10.05.12'

from configuration import RESOURCE_PATH, SERVER_SETTINGS_PATH, LOGGING

from micropsi_core.nodenet.node import Node, Nodetype
from micropsi_core.nodenet.nodenet import Nodenet
from micropsi_core.nodenet.nodespace import Nodespace

from copy import deepcopy

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

configs = config.ConfigurationManager(SERVER_SETTINGS_PATH)

worlds = {}
nodenets = {}
native_modules = {}
custom_recipes = {}

runner = {'timestep': 1000, 'runner': None, 'factor': 1}

signal_handler_registry = []

logger = MicropsiLogger({
    'system': LOGGING['level_system'],
    'world': LOGGING['level_world'],
    'nodenet': LOGGING['level_nodenet']
})

nodenet_lock = threading.Lock()


def add_signal_handler(handler):
    signal_handler_registry.append(handler)


def signal_handler(signal, frame):
    logging.getLogger('system').info("Shutting down")
    for handler in signal_handler_registry:
        handler(signal, frame)
    sys.exit(0)


stats = []


class MicropsiRunner(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
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
            for uid in nodenets:
                if nodenets[uid].is_active:
                    log = True
                    try:
                        nodenets[uid].step()
                        nodenets[uid].update_monitors()
                    except:
                        nodenets[uid].is_active = False
                        logging.getLogger("nodenet").error("Exception in NodenetRunner:", exc_info=1)
                        MicropsiRunner.last_nodenet_exception[uid] = sys.exc_info()
                    if nodenets[uid].world and nodenets[uid].current_step % runner['factor'] == 0:
                        try:
                            nodenets[uid].world.step()
                        except:
                            nodenets[uid].is_active = False
                            logging.getLogger("world").error("Exception in WorldRunner:", exc_info=1)
                            MicropsiRunner.last_world_exception[nodenets[uid].world.uid] = sys.exc_info()

            elapsed = datetime.now() - start
            if log:
                ms = elapsed.seconds + ((elapsed.microseconds // 1000) / 1000)
                stats.append(ms)
                if len(stats) % 100 == 0 and len(stats) > 0:
                    logging.getLogger("nodenet").debug("AFTER %d RUNS: AVG. %s sec" % (len(stats), str(sum(stats) / len(stats))))
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

            #engine = "theano_engine"

            if engine == 'dict_engine':
                from micropsi_core.nodenet.dict_engine.dict_nodenet import DictNodenet
                nodenets[nodenet_uid] = DictNodenet(
                    os.path.join(RESOURCE_PATH, NODENET_DIRECTORY, nodenet_uid + '.json'),
                    name=data.name, worldadapter=worldadapter,
                    world=world, owner=data.owner, uid=data.uid,
                    native_modules=native_modules)
            elif engine == 'theano_engine':
                from micropsi_core.nodenet.theano_engine.theano_nodenet import TheanoNodenet
                nodenets[nodenet_uid] = TheanoNodenet(
                    os.path.join(RESOURCE_PATH, NODENET_DIRECTORY, nodenet_uid + '.json'),
                    name=data.name, worldadapter=worldadapter,
                    world=world, owner=data.owner, uid=data.uid,
                    native_modules=native_modules)
            # Add additional engine types here
            else:
                nodenet_lock.release()
                return False, "Nodenet %s requires unknown engine %s" % (nodenet_uid, engine)

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


def get_nodenet_data(nodenet_uid, nodespace, coordinates):
    """ returns the current state of the nodenet """
    nodenet = get_nodenet(nodenet_uid)
    with nodenet.netlock:
        data = nodenet.data
    data.update(get_nodenet_area(nodenet_uid, nodespace, **coordinates))
    data.update({
        'nodetypes': nodenet.get_standard_nodetype_definitions(),
        'native_modules': native_modules
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


def get_nodenet_area(nodenet_uid, nodespace="Root", x1=0, x2=-1, y1=0, y2=-1):
    """ returns part of the nodespace for representation in the UI
    Either you specify an area to be retrieved, or the retrieval is limited to 500 nodes currently
    """
    if not nodenets[nodenet_uid].is_nodespace(nodespace):
        nodespace = "Root"
    with nodenets[nodenet_uid].netlock:
        if x2 < 0 or y2 < 0:
            data = nodenets[nodenet_uid].get_nodespace_data(nodespace, 500)
        else:
            data = nodenets[nodenet_uid].get_nodespace_area_data(nodespace, x1, x2, y1, y2)
        data['nodespace'] = nodespace
        return data


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
    if template is not None and template in nodenet_data:
        if template in nodenets:
            data = nodenets[template].data
        else:
            data = nodenet_data[template]
    else:
        data = dict(
            nodes=dict(),
            links=dict(),
            step=0,
            version=1
        )

    if not uid:
        uid = tools.generate_uid()
    data.update(dict(
        uid=uid,
        name=nodenet_name,
        worldadapter=worldadapter,
        owner=owner,
        world=world_uid,
        settings={},
        engine=engine
    ))
    filename = os.path.join(RESOURCE_PATH, NODENET_DIRECTORY, data['uid'] + ".json")
    nodenet_data[data['uid']] = Bunch(**data)
    with open(filename, 'w+') as fp:
        fp.write(json.dumps(data, sort_keys=True, indent=4))
    fp.close()
    load_nodenet(data['uid'])
    return True, data['uid']


def delete_nodenet(nodenet_uid):
    """Unloads the given nodenet from memory and deletes it from the storage.

    Simple unloading is maintained automatically when a nodenet is suspended and another one is accessed.
    """
    unload_nodenet(nodenet_uid)
    filename = os.path.join(RESOURCE_PATH, NODENET_DIRECTORY, nodenet_uid + '.json')
    os.remove(filename)
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
    with open(os.path.join(RESOURCE_PATH, NODENET_DIRECTORY, nodenet_uid + '.json'), 'w+') as fp:
        fp.write(json.dumps(nodenet.data, sort_keys=True, indent=4))
    fp.close()
    nodenet_data[nodenet_uid] = Bunch(**nodenet.data)
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
    fp.close()
    nodenet_data[import_data['uid']] = parse_definition(import_data, filename)
    load_nodenet(import_data['uid'])
    return import_data['uid']


def merge_nodenet(nodenet_uid, string):
    """Merges the nodenet data with an existing nodenet, instantiates the nodenet.

    Arguments:
        nodenet_uid: the uid of the existing nodenet (may overwrite existing nodenet)
        string: a string that contains the nodenet data that is to be merged in JSON format.
    """
    nodenet = nodenets[nodenet_uid]
    data = json.loads(string)
    nodenet.merge_data(data)
    save_nodenet(nodenet_uid)
    unload_nodenet(nodenet_uid)
    load_nodenet(nodenet_uid)
    return True


def copy_nodes(node_uids, source_nodenet_uid, target_nodenet_uid, target_nodespace_uid="Root",
               copy_associated_links=True):
    """Copies a set of netentities, either between nodenets or within a nodenet. If a target nodespace
    is supplied, all nodes will be inserted below that target nodespace, otherwise below "Root".
    If parent nodespaces are included in the set of node_uids, the contained nodes will remain in
    these parent nodespaces.
    Only explicitly listed nodes and nodespaces will be copied.
    UIDs will be kept if possible, but renamed in case of conflicts.

    Arguments:
        node_uids: a list of uids of nodes and nodespaces
        source_nodenet_uid
        target_nodenet_uid
        target_nodespace_uid: the uid of the nodespace into which the nodes will be copied
        copy_associated_links: if True, links to not-copied nodes will be copied, too (of course, this works
            only within the same nodenet)
    """
    source_nodenet = nodenets[source_nodenet_uid]
    target_nodenet = nodenets[target_nodenet_uid]
    nodes = {}
    nodespaces = {}
    for node_uid in node_uids:
        if source_nodenet.is_node(node_uid):
            nodes[node_uid] = source_nodenet.get_node(node_uid)
        elif source_nodenet.is_nodespace(node_uid):
            nodespaces[node_uid] = source_nodenet.get_nodespace(node_uid)

    _perform_copy_nodes(target_nodenet, nodes, nodespaces, target_nodespace_uid, copy_associated_links)
    return True


def _perform_copy_nodes(nodenet, nodes, nodespaces, target_nodespace=None, copy_associated_links=True):
    """takes a dictionary of nodes and merges them into the current nodenet.
    Links between these nodes will be copied, too.
    If the source nodes are within the current nodenet, it is also possible to retain the associated links.
    If the source nodes originate within a different nodespace (either because they come from a different
    nodenet, or because they are copied into a different nodespace), the associated links (i.e. those that
    link the copied nodes to elements that are themselves not being copied), can be retained, too.
    Nodes and links may need to receive new UIDs to avoid conflicts.

    Arguments:
        nodes: a dictionary of node_uids with nodes
        target_nodespace: if none is given, we copy into the same nodespace of the originating nodes
        copy_associated_links: if True, also copy connections to not copied nodes
    """
    rename_nodes = {}
    rename_nodespaces = {}
    if not target_nodespace:
        target_nodespace = "Root"
        # first, check for nodespace naming conflicts
    for nodespace_uid in nodespaces:
        if nodespace_uid in nodenet.get_nodespace_uids():
            rename_nodespaces[nodespace_uid] = micropsi_core.tools.generate_uid()
        # create the nodespaces
    for nodespace_uid in nodespaces:
        original = nodespaces[nodespace_uid]
        uid = rename_nodespaces.get(nodespace_uid, nodespace_uid)

        nodenet.create_nodespace(
            target_nodespace,
            original.position,
            original.name,
            uid)

    # set the parents (needs to happen in seperate loop to ensure nodespaces are already created
    for nodespace_uid in nodespaces:
        if nodespaces[nodespace_uid].parent_nodespace in nodespaces:
            uid = rename_nodespaces.get(nodespace_uid, nodespace_uid)
            target_nodespace = rename_nodespaces.get(nodespaces[nodespace_uid].parent_nodespace)
            nodenet.get_nodespace(uid).parent_nodespace = target_nodespace

    # copy the nodes
    for node_uid in nodes:
        if nodenet.is_node(node_uid):
            rename_nodes[node_uid] = micropsi_core.tools.generate_uid()
            uid = rename_nodes[node_uid]
        else:
            uid = node_uid

        original = nodes[node_uid]
        target = original.parent_nodespace if original.parent_nodespace in nodespaces else target_nodespace
        target = rename_nodespaces.get(target, target)

        gate_parameters = original.clone_non_default_gate_parameters()

        nodenet.create_node(
            original.type,
            target,
            original.position,
            original.name,
            uid,
            deepcopy(original.clone_parameters()),
            gate_parameters)

    # copy the links
    links_to_copy = set()
    for node_uid in nodes:
        node = nodes[node_uid]
        for slot in node.get_slot_types():
            for link in node.get_slot(slot).get_links():
                if link.source_node.uid in nodes or (copy_associated_links and nodenet.is_node(link.source_node.uid)):
                    links_to_copy.add(link)
        for gate in node.get_gate_types():
            for link in node.get_gate(gate).get_links():
                if link.target_node.uid in nodes or (copy_associated_links and nodenet.is_node(link.target_node.uid)):
                    links_to_copy.add(link)
    for link in links_to_copy:
        source_node = nodenet.get_node(rename_nodes.get(link.source_node.uid, link.source_node.uid))
        nodenet.create_link(
            source_node.uid,
            link.source_gate.type,
            link.target_node.uid,
            link.target_slot.type,
            link.weight,
            link.certainty)


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


def get_nodespace(nodenet_uid, nodespace, step=0, coordinates={}):
    """Returns the current state of the nodespace for UI purposes, if current step is newer than supplied one."""
    data = {}
    if nodenet_uid in MicropsiRunner.last_nodenet_exception:
        e = MicropsiRunner.last_nodenet_exception[nodenet_uid]
        del MicropsiRunner.last_nodenet_exception[nodenet_uid]
        raise Exception("Error during stepping nodenet").with_traceback(e[2]) from e[1]
    if step < nodenets[nodenet_uid].current_step:
        data = get_nodenet_area(nodenet_uid, nodespace, **coordinates)
        data.update({'current_step': nodenets[nodenet_uid].current_step, 'is_active': nodenets[nodenet_uid].is_active})
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


def add_node(nodenet_uid, type, pos, nodespace="Root", state=None, uid=None, name="", parameters=None):
    """Creates a new node. (Including nodespace, native module.)

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
    if type == "Nodespace":
        uid = nodenet.create_nodespace(nodespace, pos, name=name, uid=uid)
    else:
        uid = nodenet.create_node(type, nodespace, pos, name, uid=uid, parameters=parameters)
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
        success, link = nodenet.create_link(
            source_uid,
            l.source_gate.type,
            target_uid,
            l.target_slot.type,
            l.weight,
            l.certainty)
        if success:
            result['links'].append(link.data)
        else:
            logger.warning('Could not duplicate link: ' + uid)

    if len(result['nodes']) or len(nodes) == 0:
        return True, result
    else:
        return False, "Could not clone nodes. See log for details."


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

    # todo: There should be a separate JSON API method for deleting node spaces -- they're entities, but NOT nodes!

    nodenet = nodenets[nodenet_uid]
    if nodenet.is_nodespace(node_uid):
        nodenet.delete_nodespace(node_uid)
        return True
    elif nodenet.is_node(node_uid):
        nodenets[nodenet_uid].delete_node(node_uid)
        return True
    return False


def get_available_node_types(nodenet_uid):
    """Returns a list of available node types. (Including native modules.)"""
    nodenet = nodenets[nodenet_uid]
    all_nodetypes = native_modules.copy()
    all_nodetypes.update(nodenet.get_standard_nodetype_definitions())
    return all_nodetypes


def get_available_native_module_types(nodenet_uid):
    """Returns a list of native modules.
    If an nodenet uid is supplied, filter for node types defined within this nodenet."""
    return native_modules


def set_node_parameters(nodenet_uid, node_uid, parameters):
    """Sets a dict of arbitrary values to make the node stateful."""
    for key, value in parameters.items():
        if value == '':
            value = None
        nodenets[nodenet_uid].get_node(node_uid).set_parameter(key, value)
    return True


def get_gatefunction(nodenet_uid, node_uid, gate_type):
    """
    Returns the name of the gate function configured for that given node and gate
    """
    return nodenets[nodenet_uid].get_node(node_uid).get_gatefunction(gate_type)


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
    return worlds[_get_world_uid_for_nodenet_uid(nodenet_uid)].get_available_datasources(nodenet_uid)


def get_available_datatargets(nodenet_uid):
    """Returns a list of available datatarget types for the given nodenet."""
    return worlds[_get_world_uid_for_nodenet_uid(nodenet_uid)].get_available_datatargets(nodenet_uid)


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
        success, link = nodenet.create_link(source_node_uid, gate_type, target_node_uid, slot_type, weight, certainty)
    return success, link.uid


def set_link_weight(nodenet_uid, source_node_uid, gate_type, target_node_uid, slot_type, weight=1, certainty=1):
    """Set weight of the given link."""
    nodenet = nodenets[nodenet_uid]
    return nodenet.set_link_weight(source_node_uid, gate_type, target_node_uid, slot_type, weight, certainty)


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
        recipes[name] = {
            'name': name,
            'parameters': data['parameters']
        }
    return recipes


def run_recipe(nodenet_uid, name, parameters):
    """ Calls the given recipe with the provided parameters, and returns the output, if any """
    from functools import partial
    netapi = nodenets[nodenet_uid].netapi
    params = {}
    for key in parameters:
        if parameters[key] != '':
            params[key] = parameters[key]
    if name in custom_recipes:
        func = custom_recipes[name]['function']
        return True, func(netapi, **params)
    else:
        return False, "Script not found"


# --- end of API

def crawl_definition_files(path, type="definition"):
    """Traverse the directories below the given path for JSON definitions of nodenets and worlds,
    and return a dictionary with the signatures of these nodenets or worlds.
    """

    result = {}
    tools.mkdir(path)

    for user_directory_name, user_directory_names, file_names in os.walk(path):
        for definition_file_name in file_names:
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
        fp.close()
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
        else:
            worlds[uid] = world.World(**world_data[uid])
    return worlds


def load_user_files(do_reload=False):
    # see if we have additional nodetypes defined by the user.
    import sys
    global native_modules
    old_native_modules = native_modules.copy()
    native_modules = {}
    custom_nodetype_file = os.path.join(RESOURCE_PATH, 'nodetypes.json')
    custom_recipe_file = os.path.join(RESOURCE_PATH, 'recipes.py')
    custom_nodefunctions_file = os.path.join(RESOURCE_PATH, 'nodefunctions.py')
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
        defaults = argspec.defaults
        params = []
        for i, arg in enumerate(arguments):
            params.append({
                'name': arg,
                'default': defaults[i]
            })
        custom_recipes[name] = {
            'name': name,
            'parameters': params,
            'function': func
        }


def reload_native_modules(nodenet_uid=None):
    load_user_files(True)
    if nodenet_uid:
        nodenets[nodenet_uid].reload_native_modules(native_modules)
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
