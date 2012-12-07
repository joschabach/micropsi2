#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MicroPsi runtime component;
maintains a set of users, worlds (up to one per user), and nodenets, and provides an interface to external clients
"""
import difflib
import operator

__author__ = 'joscha'
__date__ = '10.05.12'

from micropsi_core.nodenet.nodenet import Nodenet, Node, Link, Nodespace, Nodetype, Monitor, \
    STANDARD_NODETYPES, get_link_uid
from micropsi_core.nodenet import node_alignment
from micropsi_core.world import world
from micropsi_core import config
from micropsi_core.tools import Bunch
import os
import tools
import json
import warnings
from threading import Thread
from datetime import datetime, timedelta
import time
from configuration import RESOURCE_PATH

NODENET_DIRECTORY = "nodenets"
WORLD_DIRECTORY = "worlds"

AVAILABLE_WORLD_TYPES = ['World', 'berlin', 'island']  # TODO

configs = config.ConfigurationManager(os.path.join(RESOURCE_PATH, "server-config.json"))


class MicroPsiRuntime(object):
    worlds = {}
    nodenets = {}
    runner = {
        'nodenet': {'timestep': 1000, 'runner': None},
        'world': {'timestep': 5000, 'runner': None}
    }

    """The central component of the MicroPsi installation.

    The runtime instantiates nodenets and worlds and coordinates the interaction
    between them. It should be a singleton, otherwise competing instances might conflict over the resource files.
    """

    def __init__(self, resource_path = RESOURCE_PATH):
        """Set up the MicroPsi runtime

        Arguments:
            resource_path: the path to the directory in which nodenet and world directories reside
        """

        self.nodenet_data = crawl_definition_files(path=os.path.join(resource_path, NODENET_DIRECTORY), type="nodenet")
        self.world_data = crawl_definition_files(path=os.path.join(resource_path, WORLD_DIRECTORY), type="world")
        if not self.world_data:
            # create a default world for convenience.
            uid = tools.generate_uid()
            filename = os.path.join(RESOURCE_PATH, WORLD_DIRECTORY, uid)
            self.world_data[uid] = Bunch(uid=uid, name="default", filename=filename, version=1)
            with open(os.path.join(RESOURCE_PATH, WORLD_DIRECTORY, uid), 'w+') as fp:
                fp.write(json.dumps(self.world_data[uid], sort_keys=True, indent=4))
            fp.close()

        for uid in self.world_data:
            if "world_type" in self.world_data[uid]:
                try:
                    self.worlds[uid] = self._get_world_class(self.world_data[uid].world_type)(self,
                        **self.world_data[uid])
                except AttributeError, err:
                    warnings.warn("Unknown world_type: %s (%s)" % (self.world_data[uid].world_type, err.message))
            else:
                self.worlds[uid] = world.World(self, **self.world_data[uid])
        self.init_runners()

    def init_runners(self):
        """Initialize the threads for the continuous simulation of nodenets and worlds"""
        if 'worldrunner_timestep' not in configs:
            configs['worldrunner_timestep'] = 5000
            configs['nodenetrunner_timestep'] = 1000
            configs.save_configs()
        self.runner['world']['runner'] = Thread(target=self.worldrunner)
        self.runner['world']['runner'].daemon = True
        self.runner['nodenet']['runner'] = Thread(target=self.nodenetrunner)
        self.runner['nodenet']['runner'].daemon = True
        self.runner['world']['runner'].start()
        self.runner['nodenet']['runner'].start()

    def nodenetrunner(self):
        """Looping thread to simulate node nets continously"""
        while True:
            step = timedelta(milliseconds=configs['nodenetrunner_timestep'])
            start = datetime.now()
            for uid in self.nodenets:
                if self.nodenets[uid].is_active:
                    print "%s stepping nodenet %s" % (str(start), self.nodenets[uid].name)
                    self.nodenets[uid].step()
            left = step - (datetime.now() - start)
            time.sleep(float(str(left)[5:]))  # cut hours, minutes, convert to float.

    def worldrunner(self):
        """Looping thread to simulate worlds continously"""
        while True:
            if configs['worldrunner_timestep'] > 1000:
                step = timedelta(seconds=configs['worldrunner_timestep'] / 1000)
            else:
                step = timedelta(milliseconds=configs['worldrunner_timestep'])
            start = datetime.now()
            for uid in self.worlds:
                if self.worlds[uid].is_active:
                    print "%s stepping world %s" % (str(start), self.worlds[uid].name)
                    self.worlds[uid].step()
            left = step - (datetime.now() - start)
            if left.total_seconds() > 0:
                time.sleep(left.total_seconds())

    def _get_world_uid_for_nodenet_uid(self, nodenet_uid):
        """ Temporary method to get the world uid to a given nodenet uid.
            TODO: I guess this should be handled a bit differently?
        """
        if nodenet_uid in self.nodenet_data:
            return self.nodenet_data[nodenet_uid].world
        return None

    def _get_world_class(self, world_type):
        try:
            return getattr(world, world_type)
        except AttributeError:
            # here be dragons
            __import__("micropsi_core.world.%s" % world_type, fromlist=['micropsi_core.world'])
            mod = __import__("micropsi_core.world.%s.%s" % (world_type, world_type),
                fromlist=['micropsi_core.world.%s' % world_type])
            return getattr(mod, world_type.capitalize())

    # MicroPsi API

    # Nodenet
    def get_available_nodenets(self, owner=None):
        """Returns a dict of uids: Nodenet of available (running and stored) nodenets.

        Arguments:
            owner (optional): when submitted, the list is filtered by this owner
        """
        if owner:
            return dict(
                (uid, self.nodenet_data[uid]) for uid in self.nodenet_data if self.nodenet_data[uid].owner == owner)
        else:
            return self.nodenet_data

    def get_nodenet(self, nodenet_uid):
        """Returns the nodenet with the given uid, and loads into memory if necessary.
        Returns None if nodenet does not exist"""

        if nodenet_uid not in self.nodenets:
            if nodenet_uid in self.get_available_nodenets():
                self.load_nodenet(nodenet_uid)
            else:
                return None
        return self.nodenets[nodenet_uid]

    def load_nodenet(self, nodenet_uid):
        """ Load the nodenet with the given uid into memeory
            TODO: how do we know in which world we want to load the nodenet?
            I've added the world uid to the nodenet serialized data for the moment

            Arguments:
                nodenet_uid
            Returns:
                 True, nodenet_uid on success
                 False, errormessage on failure

        """
        if nodenet_uid in self.nodenet_data:
            world = worldadapter = None
            if nodenet_uid not in self.nodenets:
                data = self.nodenet_data[nodenet_uid]
                # for uid in self.nodenets: # TODO @Doik why are the nodenets unloaded here?
                #    if self.nodenets[uid].owner == data.owner:
                #        self.unload_nodenet(uid)
                #        break
                if data.get('world'):
                    world = self.worlds[data.world] or None
                    worldadapter = data.get('worldadapter')
                self.nodenets[nodenet_uid] = Nodenet(self, data.filename, name=data.name, worldadapter=worldadapter,
                    world=world, owner=data.owner, uid=data.uid)
            else:
                world = self.nodenets[nodenet_uid].world or None
                worldadapter = self.nodenets[nodenet_uid].worldadapter
            if world:
                world.register_nodenet(worldadapter, nodenet_uid)
            return True, nodenet_uid
        return False, "no such nodenet"

    def unload_nodenet(self, nodenet_uid):
        """ Unload the nodenet.
            Deletes the instance of this nodenet without deleting it from the storage

            Arguments:
                nodenet_uid
        """
        if not nodenet_uid in self.nodenets: return False
        if self.nodenets[nodenet_uid].world:
            self.nodenets[nodenet_uid].world.unregister_nodenet(nodenet_uid)
        del self.nodenets[nodenet_uid]
        return True


    def get_nodenet_area(self, nodenet_uid, nodespace="Root", x1=0, x2=-1, y1=0, y2=-1):
        """ return all nodes and links within the given area of the nodenet
            for representation in the UI
            TODO
        """
        if x2 < 0 or y2 < 0:
            data = {}
            for key in self.nodenets[nodenet_uid].state:
                if key in ['uid', 'links', 'nodespaces', 'monitors']:
                    data[key] = self.nodenets[nodenet_uid].state[key]
                elif key == "nodes":
                    i = 0
                    data[key] = {}
                    for id in self.nodenets[nodenet_uid].state[key]:
                        i += 1
                        data[key][id] = self.nodenets[nodenet_uid].state[key][id]
                        if i > 500:
                            break
            return data
        else:
            return self.nodenets[nodenet_uid].get_nodespace_area(nodespace, x1, x2, y1, y2)

    def new_nodenet(self, nodenet_name, worldadapter, template=None, owner="", world_uid=None, uid=None):
        """Creates a new node net manager and registers it.

        Arguments:
            worldadapter: the type of the world adapter supported by this nodenet. Also used to determine the set of
                gate types supported for directional activation spreading of this nodenet, and the initial node types
            owner (optional): the creator of this nodenet
            world_uid (optional): if submitted, attempts to bind the nodenet to this world
            uid (optional): if submitted, this is used as the UID for the nodenet (normally, this is generated)

        Returns
            nodenet_uid if successful,
            None if failure
        """
        if template is not None and template in self.nodenet_data:
            if template in self.nodenets:
                data = self.nodenets[template].state.copy()
            else:
                data = self.nodenet_data[template].copy()
        else:
            data = dict(
                nodes=dict(),
                links=dict(),
                step=0,
                version=1
            )
        if not uid: uid = tools.generate_uid()
        data.update(dict(
            uid=uid,
            name=nodenet_name,
            worldadapter=worldadapter,
            owner=owner,
            world=world_uid
        ))
        data['filename'] = os.path.join(RESOURCE_PATH, NODENET_DIRECTORY, data['uid'])
        self.nodenet_data[data['uid']] = Bunch(**data)
        with open(data['filename'], 'w+') as fp:
            fp.write(json.dumps(data, sort_keys=True, indent=4))
        fp.close()
        #self.load_nodenet(data['uid'])
        return True, data['uid']

    def clear_nodenet(self, nodenet_uid):
        """Deletes all contents of a nodenet"""

        nodenet = self.get_nodenet(nodenet_uid)
        nodenet.nodes = {}
        nodenet.links = {}
        nodenet.active_nodes = {}
        nodenet.privileged_active_nodes = {}
        nodenet.monitors = {}

        nodenet.nodes_by_coords = {}
        nodenet.max_coords = {'x': 0, 'y': 0}

        nodenet.nodespaces = {}
        Nodespace(nodenet, None, (0,0), "Root", "Root")

    def delete_nodenet(self, nodenet_uid):
        """Unloads the given nodenet from memory and deletes it from the storage.

        Simple unloading is maintained automatically when a nodenet is suspended and another one is accessed.
        """
        self.unload_nodenet(nodenet_uid)
        os.remove(self.nodenet_data[nodenet_uid].filename)
        del self.nodenet_data[nodenet_uid]
        return True

    def set_nodenet_properties(self, nodenet_uid, nodenet_name=None, worldadapter=None, world_uid=None, owner=None):
        """Sets the supplied parameters (and only those) for the nodenet with the given uid."""
        nodenet = self.nodenets[nodenet_uid]
        if world_uid is None:
            world_uid = nodenet.world
        if worldadapter is None:
            worldadapter = nodenet.worldadapter
        if world_uid is not None and worldadapter is not None:
            assert worldadapter in self.worlds[world_uid].supported_worldadapters
            nodenet.world = self.worlds[world_uid]
            nodenet.worldadapter = worldadapter
            self.worlds[world_uid].register_nodenet(nodenet_uid, worldadapter)
        if nodenet_name:
            nodenet.name = nodenet_name
        if owner:
            nodenet.owner = owner
        self.nodenet_data[nodenet_uid] = Bunch(**nodenet.state)
        return True

    def start_nodenetrunner(self, nodenet_uid):
        """Starts a thread that regularly advances the given nodenet by one step."""
        self.nodenets[nodenet_uid].is_active = True
        return True

    def set_nodenetrunner_timestep(self, timestep):
        """Sets the speed of the nodenet simulation in ms.

        Argument:
            timestep: sets the simulation speed.
        """
        configs['nodenetrunner_timestep'] = timestep
        self.runner['nodenet']['timestep'] = timestep
        return True

    def get_nodenetrunner_timestep(self):
        """Returns the speed that has been configured for the nodenet runner (in ms)."""
        return configs['nodenetrunner_timestep']

    def get_is_nodenet_running(self, nodenet_uid):
        """Returns True if a nodenet runner is active for the given nodenet, False otherwise."""
        return self.nodenets[nodenet_uid].is_active

    def stop_nodenetrunner(self, nodenet_uid):
        """Stops the thread for the given nodenet."""
        self.nodenets[nodenet_uid].is_active = False
        return True

    def step_nodenet(self, nodenet_uid, nodespace=None):
        """Advances the given nodenet by one simulation step.

        Arguments:
            nodenet_uid: The uid of the nodenet
            nodespace (optional): when supplied, returns the contents of the nodespace after the simulation step
        """
        self.nodenets[nodenet_uid].step()
        return self.nodenets[nodenet_uid].state['step']

    def revert_nodenet(self, nodenet_uid):
        """Returns the nodenet to the last saved state."""
        self.unload_nodenet(nodenet_uid)
        self.load_nodenet(nodenet_uid)
        return True

    def save_nodenet(self, nodenet_uid):
        """Stores the nodenet on the server (but keeps it open)."""
        nodenet = self.nodenets[nodenet_uid]
        with open(os.path.join(RESOURCE_PATH, NODENET_DIRECTORY, nodenet.filename), 'w+') as fp:
            fp.write(json.dumps(nodenet.state, sort_keys=True, indent=4))
        fp.close()
        return True

    def export_nodenet(self, nodenet_uid):
        """Exports the nodenet state to the user, so it can be viewed and exchanged.

        Returns a string that contains the nodenet state in JSON format.
        """
        return json.dumps(self.nodenets[nodenet_uid].state, sort_keys=True, indent=4)

    def import_nodenet(self, string, owner=None):
        """Imports the nodenet state, instantiates the nodenet.

        Arguments:
            nodenet_uid: the uid of the nodenet (may overwrite existing nodenet)
            string: a string that contains the nodenet state in JSON format.
        """
        nodenet_data = json.loads(string)
        if 'uid' not in nodenet_data:
            nodenet_data['uid'] = tools.generate_uid()
        if 'owner':
            nodenet_data['owner'] = owner
        # assert nodenet_data['world'] in self.worlds
        filename = os.path.join(RESOURCE_PATH, NODENET_DIRECTORY, nodenet_data['uid'])
        nodenet_data['filename'] = filename
        with open(filename, 'w+') as fp:
            fp.write(json.dumps(nodenet_data))
        fp.close()
        self.nodenet_data[nodenet_data['uid']] = parse_definition(nodenet_data, filename)
        return True

    def merge_nodenet(self, nodenet_uid, string):
        """Merges the nodenet data with an existing nodenet, instantiates the nodenet.

        Arguments:
            nodenet_uid: the uid of the existing nodenet (may overwrite existing nodenet)
            string: a string that contains the nodenet data that is to be merged in JSON format.
        """
        nodenet = self.nodenets[nodenet_uid]
        data = json.loads(string)
        # these values shouldn't be overwritten:
        for key in ['uid', 'filename', 'world']:
            data.pop(key, None)
        nodenet.state.update(data)
        self.save_nodenet(nodenet_uid)
        self.unload_nodenet(nodenet_uid)
        self.load_nodenet(nodenet_uid)
        return True

    def copy_nodes(self, node_uids, source_nodenet_uid, target_nodenet_uid, target_nodespace_uid="Root",
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
        source_nodenet = self.nodenets[source_nodenet_uid]
        target_nodenet = self.nodenets[target_nodenet_uid]
        nodes = {}
        nodespaces = {}
        for node_uid in node_uids:
            if node_uid in source_nodenet.nodes:
                nodes[node_uid] = source_nodenet.nodes[node_uid]
            elif node_uid in source_nodenet.nodespaces:
                nodespaces[node_uid] = source_nodenet.nodespaces[node_uid]
        target_nodenet.copy_nodes(nodes, nodespaces, target_nodespace_uid, copy_associated_links)
        return True

    # World
    def get_available_worlds(self, owner=None):
        """Returns a dict of uids: World of (running and stored) worlds.

        Arguments:
            owner (optional): when submitted, the list is filtered by this owner
        """
        if owner:
            return dict((uid, self.worlds[uid]) for uid in self.worlds if self.worlds[uid].owner == owner)
        else:
            return self.worlds

    def get_world_properties(self, world_uid):
        """ Returns some information about the current world for the client:
        * Available worldadapters
        * Datasources and -targets offered by the world / worldadapter
        * Available Nodetypes

        Arguments:
            world_uid: the uid of the worldad

        Returns:
            dictionary containing the information
        """

        data = self.worlds[world_uid].data
        data['worldadapters'] = self.get_worldadapters(world_uid)
        return data

    def get_worldadapters(self, world_uid):
        """Returns the world adapters available in the given world"""

        data = {}
        for name, worldadapter in self.worlds[world_uid].supported_worldadapters.items():
            data[name] = {
                'datasources': worldadapter.datasources.keys(),
                'datatargets': worldadapter.datatargets.keys()
            }
        return data

    def get_world_objects(self, world_uid, type=None):
        if world_uid in self.worlds:
            return self.worlds[world_uid].get_world_objects(type)
        return False

    def new_world(self, world_name, world_type, owner=""):
        """Creates a new world manager and registers it.

        Arguments:
            world_name: the name of the world
            world_type: the type of the world
            owner (optional): the creator of this world

        Returns
            world_uid if successful,
            None if failure
        """
        uid = tools.generate_uid()
        filename = os.path.join(RESOURCE_PATH, WORLD_DIRECTORY, uid)
        self.world_data[uid] = Bunch(uid=uid, name=world_name, world_type=world_type, filename=filename, version=1,
            owner=owner)
        with open(filename, 'w+') as fp:
            fp.write(json.dumps(self.world_data[uid], sort_keys=True, indent=4))
        fp.close()
        try:
            self.worlds[uid] = self._get_world_class(world_type)(self, **self.world_data[uid])
        except AttributeError:
            return False, "World type unknown"
        return True, uid

    def delete_world(self, world_uid):
        """Removes the world with the given uid from the server (and unloads it from memory if it is running.)"""
        for uid in self.nodenets:
            if self.nodenets[uid].world and self.nodenets[uid].world.uid == world_uid:
                self.nodenets[uid].world = None
        del self.worlds[world_uid]
        os.remove(self.world_data[world_uid].filename)
        del self.world_data[world_uid]
        return True

    def get_world_view(self, world_uid, step):
        """Returns the current state of the world for UI purposes, if current step is newer than the supplied one."""
        if step < self.worlds[world_uid].current_step:
            return self.worlds[world_uid].get_world_view(step)
        return {}

    def set_world_properties(self, world_uid, world_name=None, world_type=None, owner=None):
        """Sets the supplied parameters (and only those) for the world with the given uid."""
        pass

    def start_worldrunner(self, world_uid):
        """Starts a thread that regularly advances the world simulation."""
        self.worlds[world_uid].is_active = True
        return True

    def get_worldrunner_timestep(self):
        """Returns the speed that has been configured for the world runner (in ms)."""
        return configs['worldrunner_timestep']

    def get_is_world_running(self, world_uid):
        """Returns True if an worldrunner is active for the given world, False otherwise."""
        return self.worlds[world_uid].is_active

    def set_worldrunner_timestep(self, timestep):
        """Sets the interval of the simulation steps for the world runner (in ms)."""
        configs['worldrunner_timestep'] = timestep
        return True

    def stop_worldrunner(self, world_uid):
        """Ends the thread of the continuous world simulation."""
        self.worlds[world_uid].is_active = False
        return True

    def step_world(self, world_uid, return_world_view=False):
        """Advances the world simulation by one step.

        Arguments:
            world_uid: the uid of the simulation world
            return_world_view: if True, return the current world state for UI purposes
        """
        self.worlds[world_uid].step()
        if return_world_view:
            return self.get_world_view(world_uid)
        return True

    def revert_world(self, world_uid):
        """Reverts the world to the last saved state."""
        data = self.world_data[world_uid]
        self.worlds[world_uid] = self._get_world_class(data.world_type)(self, **data)
        return True

    def save_world(self, world_uid):
        """Stores the world state on the server."""
        with open(os.path.join(RESOURCE_PATH, WORLD_DIRECTORY, world_uid), 'w+') as fp:
            fp.write(json.dumps(self.worlds[world_uid].data, sort_keys=True, indent=4))
        fp.close()
        return True

    def export_world(self, world_uid):
        """Returns a JSON string with the current state of the world."""
        return json.dumps(self.worlds[world_uid].data, sort_keys=True, indent=4)

    def import_world(self, worlddata, owner=None):
        """Imports a JSON string with world data. May overwrite an existing world."""
        data = json.loads(worlddata)
        if not 'uid' in data:
            data['uid'] = tools.generate_uid()
        if owner is not None:
            data['owner'] = owner
        filename = os.path.join(RESOURCE_PATH, WORLD_DIRECTORY, data['uid'])
        data['filename'] = filename
        with open(filename, 'w+') as fp:
            fp.write(json.dumps(data))
        fp.close()
        self.world_data[data['uid']] = parse_definition(data, filename)
        self.worlds[data['uid']] = self._get_world_class(self.world_data[data['uid']].world_type)(self,
            **self.world_data[data['uid']])
        return data['uid']

    # Monitor

    def add_gate_monitor(self, nodenet_uid, node_uid, gate):
        """Adds a continuous monitor to the activation of a gate. The monitor will collect the activation
        value in every simulation step."""
        nodenet = self.nodenets[nodenet_uid]
        monitor = Monitor(nodenet, node_uid, 'gate', gate)
        nodenet.monitors[monitor.uid] = monitor
        return monitor.data

    def add_slot_monitor(self, nodenet_uid, node_uid, slot):
        """Adds a continuous monitor to the activation of a slot. The monitor will collect the activation
        value in every simulation step."""
        nodenet = self.nodenets[nodenet_uid]
        monitor = Monitor(nodenet, node_uid, 'slot', slot)
        nodenet.monitors[monitor.uid] = monitor
        return monitor.data

    def remove_monitor(self, nodenet_uid, monitor_uid):
        """Deletes an activation monitor."""
        del self.nodenets[nodenet_uid].data['monitors'][monitor_uid]
        del self.nodenets[nodenet_uid].monitors[monitor_uid]
        return True

    def clear_monitor(self, nodenet_uid, monitor_uid):
        """Leaves the monitor intact, but deletes the current list of stored values."""
        self.nodenets[nodenet_uid].monitors(monitor_uid).clear()
        return True

    def export_monitor_data(self, nodenet_uid, monitor_uid=None):
        """Returns a string with all currently stored monitor data for the given nodenet."""
        if monitor_uid is not None:
            return self.nodenets[nodenet_uid].state['monitors'][monitor_uid]
        else:
            return self.nodenets[nodenet_uid].state.get('monitors', {})

    def get_monitor_data(self, nodenet_uid, step):
        """Returns a dictionary of monitor_uid: [node_name/node_uid, slot_type/gate_type, activation_value] for
        the current step, it the current step is newer than the supplied simulation step."""
        pass

    # Node operations

    def get_nodespace(self, nodenet_uid, nodespace, step, **coordinates):
        """Returns the current state of the nodespace for UI purposes, if current step is newer than supplied one."""
        data = {}
        if step < self.nodenets[nodenet_uid].current_step:
            data = self.get_nodenet_area(nodenet_uid, nodespace, **coordinates)
            data.update({'current_step': self.nodenets[nodenet_uid].current_step})
        return data

    def get_node(self, nodenet_uid, node_uid):
        """Returns a dictionary with all node parameters, if node exists, or None if it does not. The dict is
        structured as follows:
            {
                uid: unique identifier,
                name (optional): display name,
                type: node type,
                parent: parent nodespace,
                x (optional): x position,
                y (optional): y position,
                activation: activation value,
                symbol (optional): a short string for compact display purposes,
                slots (optional): a list of lists [slot_type, {activation: activation_value,
                                                               links (optional): [link_uids]} (optional)]
                gates (optional): a list of lists [gate_type, {activation: activation_value,
                                                               function: gate_function (optional),
                                                               params: {gate_parameters} (optional),
                                                               links (optional): [link_uids]} (optional)]
                parameters (optional): a dict of arbitrary parameters that can make nodes stateful
            }
         """
        return self.nodenets[nodenet_uid].nodes[node_uid]

    def add_node(self, nodenet_uid, type, pos, nodespace="Root", state=None, uid=None, name="", parameters=None):
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
        nodenet = self.get_nodenet(nodenet_uid)
        if type == "Nodespace":
            nodespace = Nodespace(nodenet, nodespace, pos, name=name, uid=uid)
            uid = nodespace.uid
        else:
            node = Node(nodenet, nodespace, pos, name=name, type=type, uid=uid, parameters=parameters)
            uid = node.uid
            nodenet.update_node_positions()
        return True, uid

    def set_node_position(self, nodenet_uid, node_uid, pos):
        """Positions the specified node at the given coordinates."""
        nodenet = self.nodenets[nodenet_uid]
        if node_uid in nodenet.nodes:
            nodenet.nodes[node_uid].position = pos
        elif node_uid in nodenet.nodespaces:
            nodenet.nodespaces[node_uid].position = pos
        nodenet.update_node_positions()
        return True

    def set_node_name(self, nodenet_uid, node_uid, name):
        """Sets the display name of the node"""
        nodenet = self.nodenets[nodenet_uid]
        if node_uid in nodenet.nodes:
            nodenet.nodes[node_uid].name = name
        elif node_uid in nodenet.nodespaces:
            nodenet.nodespaces[node_uid].name = name
        return True

    def set_node_state(self, nodenet_uid, node_uid, state):
        """ Sets the state of the given node to the given state,
            provided, the nodetype allows the given state """
        node = self.nodenets[nodenet_uid].nodes[node_uid]
        if state and state in node.nodetype.states:
            node.state = state
            return True
        return False

    def set_node_activation(self, nodenet_uid, node_uid, activation):
        self.nodenets[nodenet_uid].nodes[node_uid].activation = activation
        return True

    def delete_node(self, nodenet_uid, node_uid):
        """Removes the node"""
        nodenet = self.nodenets[nodenet_uid]
        if node_uid in nodenet.nodespaces:
            for uid, node in nodenet.nodes.items():
                if node.parent_nodespace == node_uid:
                    self.delete_node(nodenet_uid, uid)
            parent_nodespace = nodenet.nodespaces.get(nodenet.nodespaces[node_uid].parent_nodespace)
            if parent_nodespace:
                parent_nodespace.netentities["nodespaces"].remove(node_uid)
            del nodenet.nodespaces[node_uid]
            del nodenet.state['nodespaces'][node_uid]
        else:
            nodenet.delete_node(node_uid)
        return True

    def get_available_node_types(self, nodenet_uid=None):
        """Returns a list of available node types. (Including native modules.)"""
        data = STANDARD_NODETYPES.copy()
        if nodenet_uid:
            data.update(self.nodenets[nodenet_uid].state.get('nodetypes', {}))
        return data

    def get_available_native_module_types(self, nodenet_uid):
        """Returns a list of native modules.
        If an nodenet uid is supplied, filter for node types defined within this nodenet."""
        return self.nodenets[nodenet_uid].state['nodetypes']

    def get_nodefunction(self, nodenet_uid, node_type):
        """Returns the current node function for this node type"""
        return self.nodenets[nodenet_uid].nodetypes[node_type].nodefunction_definition

    def set_nodefunction(self, nodenet_uid, node_type, nodefunction=None):
        """Sets a new node function for this node type. This amounts to a program that is executed every time the
        node becomes active. Parameters of the function are the node itself (and thus, its slots, gates and
        parent nodespace), the nodenet, and the parameter dict of this node).
        Setting the node_function to None will return it to its default state (passing the slot activations to
        all gate functions).
        """
        self.nodenets[nodenet_uid].nodetypes[node_type].nodefunction_definition = nodefunction
        return True

    def set_node_parameters(self, nodenet_uid, node_uid, parameters):
        """Sets a dict of arbitrary values to make the node stateful."""
        self.nodenets[nodenet_uid].nodes[node_uid].parameters = parameters
        return True

    def add_node_type(self, nodenet_uid, node_type, slots=[], gates=[], node_function=None, parameters=[]):
        """Adds or modifies a native module.

        Arguments:
            nodenet_uid: the nodenet into which the native module will be saved
            node_type: the identifier of the native module. If it already exists for another user, the new definition
                will hide the old one from view.
            node_function (optional): the program code of the native module. The native module is defined as a
                python function that takes the current node, the nodenet manager and the node parameters as arguments.
                The default node function takes the slot activations and calls all gatefunctions with
                it as an argument.
            slots (optional): the list of slot types for this node type
            gates (optional): the list of gate types for this node type
            parameters (optional): a dict of arbitrary parameters that can be used by the nodefunction to store states
        """
        nodenet = self.nodenets[nodenet_uid]
        nodenet.nodetypes[node_type] = Nodetype(node_type, nodenet, slots, gates, [], parameters,
            nodefunction_definition=node_function)
        return True

    def delete_node_type(self, nodenet_uid, node_type):
        """Remove the node type from the current nodenet definition, if it is part of it."""
        try:
            del self.nodenets[nodenet_uid].state['nodetypes'][node_type]
            return True
        except KeyError:
            return False

    def get_slot_types(self, nodenet_uid, node_type):
        """Returns the list of slot types for the given node type."""
        return self.nodenets[nodenet_uid].nodetypes[node_type].slottypes

    def get_gate_types(self, nodenet_uid, node_type):
        """Returns the list of gate types for the given node type."""
        return self.nodenets[nodenet_uid].nodetypes[node_type].gatetypes

    def get_gate_function(self, nodenet_uid, nodespace, node_type, gate_type):
        """Returns a string with the gate function of the given node and gate within the current nodespace.
        Gate functions are defined per nodespace, and handed the parameters dictionary. They must return an activation.
        """
        return self.nodenets[nodenet_uid].state['nodespaces'][nodespace]['gatefunctions'].get(node_type, {}).get(
            gate_type)

    def set_gate_function(self, nodenet_uid, nodespace, node_type, gate_type, gate_function=None, parameters=None):
        """Sets the gate function of the given node and gate within the current nodespace.
        Gate functions are defined per nodespace, and handed the parameters dictionary. They must return an activation.
        The default function is a threshold with parameter t=0.
        None reverts the custom gate function of the given node and gate within the current nodespace to the default.
        Parameters is a list of keys for values of the gate function.
        """
        self.nodenets[nodenet_uid].nodespaces[nodespace].set_gate_function(node_type, gate_type, gate_function,
            parameters)
        return True

    def set_gate_parameters(self, nodenet_uid, node_uid, gate_type, parameters=None):
        """Sets the gate parameters of the given gate of the given node to the supplied dictionary."""
        self.nodenets[nodenet_uid].nodes[node_uid].set_gate_parameters(gate_type, parameters)
        return True

    def get_available_datasources(self, nodenet_uid):
        """Returns a list of available datasource types for the given nodenet."""
        return self.worlds[self._get_world_uid_for_nodenet_uid(nodenet_uid)].get_available_datasources(nodenet_uid)

    def get_available_datatargets(self, nodenet_uid):
        """Returns a list of available datatarget types for the given nodenet."""
        return self.worlds[self._get_world_uid_for_nodenet_uid(nodenet_uid)].get_available_datatargets(nodenet_uid)

    def bind_datasource_to_sensor(self, nodenet_uid, sensor_uid, datasource):
        """Associates the datasource type to the sensor node with the given uid."""
        node = self.nodenets[nodenet_uid].nodes[sensor_uid]
        if node.type == "Sensor":
            node.parameters.update({'datasource': datasource})
            return True
        return False

    def bind_datatarget_to_actor(self, nodenet_uid, actor_uid, datatarget):
        """Associates the datatarget type to the actor node with the given uid."""
        node = self.nodenets[nodenet_uid].nodes[actor_uid]
        if node.type == "Actor":
            node.parameters.update({'datatarget': datatarget})
            return True
        return False

    def add_link(self, nodenet_uid, source_node_uid, gate_type, target_node_uid, slot_type, weight=1, certainty=1,
                 uid=None):
        """Creates a new link.

        Arguments.
            source_node_uid: uid of the origin node
            gate_type: type of the origin gate (usually defines the link type)
            target_node_uid: uid of the target node
            slot_type: type of the target slot
            weight: the weight of the link (a float)
            certainty (optional): a probabilistic parameter for the link
            uid (option): if none is supplied, a uid will be generated

        Returns:
            link_uid if successful,
            None if failure
        """
        nodenet = self.nodenets[nodenet_uid]

        # check if link already exists
        existing_uid = get_link_uid(
            nodenet.nodes[source_node_uid], gate_type,
            nodenet.nodes[target_node_uid], slot_type)
        if existing_uid:
            link = nodenet.links[existing_uid]
            link.weight = weight
            link.certainty = certainty
        else:
            link = Link(
                nodenet.nodes[source_node_uid],
                gate_type,
                nodenet.nodes[target_node_uid],
                slot_type,
                weight=weight,
                certainty=certainty,
                uid=uid)
            nodenet.links[link.uid] = link
        return True, link.uid

    def set_link_weight(self, nodenet_uid, link_uid, weight, certainty=1):
        """Set weight of the given link."""
        nodenet = self.nodenets[nodenet_uid]
        nodenet.state['links'][link_uid]['weight'] = weight
        nodenet.state['links'][link_uid]['certainty'] = certainty
        nodenet.links[link_uid].weight = weight
        nodenet.links[link_uid].certainty = certainty
        return True

    def get_link(self, nodenet_uid, link_uid):
        """Returns a dictionary of the parameters of the given link, or None if it does not exist. It is
        structured as follows:

            {
                uid: unique identifier,
                source_node_uid: uid of source node,
                gate_type: type of source gate (amounts to link type),
                target_node_uid: uid of target node,
                gate_type: type of target gate,
                weight: weight of the link (float value),
                certainty: probabilistic weight of the link (float value),
            }
        """
        return self.nodenets[nodenet_uid].links[link_uid]

    def delete_link(self, nodenet_uid, link_uid):
        """Delete the given link."""
        nodenet = self.nodenets[nodenet_uid]
        nodenet.links[link_uid].remove()
        del nodenet.links[link_uid]
        del nodenet.state['links'][link_uid]
        return True

    def align_nodes(self, nodenet_uid, nodespace):
        """Perform auto-alignment of nodes in the current nodespace"""
        result = node_alignment.align(self.nodenets[nodenet_uid], nodespace)
        if result:
            self.nodenets[nodenet_uid].update_node_positions()
        return result

    def add_label(self, nodenet_uid, label_text, node_uid, language="en", weight=1, certainty=1):
        """Adds a label to a node within a given nodenet"""

        nodenet = self.nodenets[nodenet_uid]
        if not isinstance(language, basestring) or not language:
            raise ValueError, "Illegal language code supplied"

        node = nodenet.nodes[node_uid]

        # test if nodespace with the given language already exists
        nodespace = nodenet.nodespaces.get(language)
        if nodespace is None:
            nodespace = Nodespace(nodenet, "Root", (100, 100), name="Labels " + language, uid=language)

        # test if label already exists
        label_uid = language + " " + label_text
        labelnode = nodenet.nodes.get(label_uid)
        if labelnode is None:
            index = len(nodespace.netentities.get("nodes",[]))
            labelnode = Node(nodenet, nodespace.uid,
                type="Label",
                position=node_alignment.calculate_grid_position(index),
                name=label_text,
                uid=label_uid
            )

        # check if link already exists
        candidate = get_link_uid(labelnode, "ref", node, "gen")
        if candidate:
            weight = max(weight, nodenet.links[candidate].weight)
            certainty = max(weight, nodenet.links[candidate].certainty)

        # create/update links
        self.add_link(nodenet_uid, labelnode.uid, "ref", node.uid, "gen", weight, certainty)
        self.add_link(nodenet_uid, node.uid, "sym", labelnode.uid, "gen", weight, certainty)
        return True

    def delete_label(self, nodenet_uid, label_text, node_uid=None, language="en"):
        """Removes a label, either completely or from an individual node"""

        nodenet = self.nodenets[nodenet_uid]
        label_uid = language + " " + label_text
        labelnode = nodenet.nodes[label_uid]
        if node_uid:
            node = nodenet.nodes[node_uid]
            for sym_link in labelnode.slots["gen"].incoming:
                if nodenet.links[sym_link].source_node.uid == node.uid:
                    self.delete_link(nodenet_uid, sym_link)
                    break
            for ref_link in labelnode.gates["ref"].outgoing:
                if nodenet.links[ref_link].target_node.uid == node.uid:
                    self.delete_link(nodenet_uid, ref_link)
                    break
        else:
            self.delete_node(nodenet_uid, labelnode.uid)
        return True

    def get_available_labels(self, nodenet_uid, language="en"):
        """Returns a list of all available labels for a given nodenet"""

        nodenet = self.nodenets[nodenet_uid]
        labels = None
        if language in nodenet.nodespaces:
            nodespace = nodenet.nodespaces.get(language)
            label_nodes = nodespace.netentities.get("nodes",{})
            labels = sorted([nodenet.nodes[uid].name for uid in label_nodes])
        return labels or []

    def get_nodes_from_labels(self, nodenet_uid, label_text_list, language="en", max_nodes=10, fuzzy_search=True):
        """Returns a dictionary of node uids, together with the weight of their connections to the labels

        Arguments:
            nodenet_uid: the nodenet in which we operate
            label_text_list: a list of strings where each is treated as a textual label
            language: the locale (default is 'en')
            max_nodes: the number of associated nodes that are maximally returned
        """

        # TODO make this work with spreading activation instead of link weight comparison

        MAX_NUMBER_OF_CHECKED_NODES = 10000 # make sure that memory demands are not excessive

        nodenet = self.get_nodenet(nodenet_uid)
        if fuzzy_search:
            vocabulary = self.get_available_labels(nodenet_uid, language)

        labels = {}
        for i in label_text_list:
            label_uid = language +" "+ i
            if label_uid in nodenet.nodes:
                labels[i] = { "uid": label_uid, "weight" : 1.0 }
            if fuzzy_search:
                more_labels = difflib.get_close_matches(i, vocabulary)
                for j in more_labels:
                    label_uid = language + " " + j
                    if label_uid in nodenet.nodes:
                        weight = difflib.SequenceMatcher(None, i, j).ratio()
                        if j not in labels or labels[j]["weight"] < weight:
                            labels[j] = { "uid": label_uid, "weight" : weight }

        linked_nodes = {}
        for k in labels.values():
            for ref_link in nodenet.nodes[k["uid"]].gates["ref"].outgoing.values():
                linked_nodes[ref_link.target_node] = max(linked_nodes.get(ref_link.target_node, 0),
                    ref_link.weight*k["weight"])
                if len(linked_nodes) > MAX_NUMBER_OF_CHECKED_NODES: break
            if len(linked_nodes) > MAX_NUMBER_OF_CHECKED_NODES: break

        result_list = sorted(linked_nodes.iteritems(), key=operator.itemgetter(1))[:max_nodes]

        return {k: v for k, v in result_list}

    def get_blueprint_from_node(self, nodenet_uid, node_uid, depth=4):
        """Returns a nodenet fragment made up of nodes, and links of the types por, ret, sub, sur,
            starting from the given node and extending sub-ward from there"""

        nodenet = self.nodenets[nodenet_uid]
        nodes = {}
        links = {}

        def _get_blueprint_from_node(node_uid, nodes, links, depth):
            node = nodenet.nodes[node_uid]
            nodes[node.uid] = node
            if "por" in node.gates:
                outgoing = node.gates["por"].outgoing
                for l, link in outgoing.items():
                    links[l] = link
                    connected_node = outgoing[l].target_node
                    # try to add the inverse link
                    if "ret" in connected_node.gates:
                        for r, i_link in connected_node.gates["ret"].outgoing.items():
                            if i_link.target_node == nodenet.nodes[node_uid]:
                                links[r] = i_link
                                break
                    if not connected_node.uid in nodes:
                        _get_blueprint_from_node(connected_node.uid, nodes, links, depth)
                        # perhaps only choose the strongest link

            if "sub" in node.gates and depth > 0:
                outgoing = node.gates["sub"].outgoing
                for l, link in outgoing.items():
                    links[l] = link
                    connected_node = outgoing[l].target_node
                    # try to add the inverse link
                    if "sur" in connected_node.gates:
                        for r, i_link in connected_node.gates["sur"].outgoing.items():
                            if i_link.target_node == nodenet.nodes[node_uid]:
                                links[r] = i_link
                                break
                    if not connected_node.uid in nodes:
                        _get_blueprint_from_node(connected_node.uid, nodes, links, depth - 1)

        _get_blueprint_from_node(node_uid, nodes, links, depth)
        return {
            "nodes": { uid: nodenet.state["nodes"][uid] for uid in nodes },
            "links": { l_uid: nodenet.state["links"][l_uid] for l_uid in links }}


    def get_stencils(self, label_list, language = "en", master_nodenet_uid="default_domain", max_stencils=5):
        """Ad hoc method for delivering suggestions from master nodenet

        Arguments:
            label_list: a list of strings that are used as search terms for retrieval
            master_nodenet_uid: the uid of the nodenet containing the stencils
        """
        if master_nodenet_uid not in self.nodenets:
            if master_nodenet_uid in self.get_available_nodenets():
                self.load_nodenet(master_nodenet_uid)

        if master_nodenet_uid not in self.nodenets: # we do not have suggestions for this domain
            return None



        labels = [ label.lower().strip() for label in label_list ]

        headnodes = self.get_nodes_from_labels(master_nodenet_uid, labels, language, max_nodes = max_stencils)
        return [self.get_blueprint_from_node(master_nodenet_uid, headnode.uid) for headnode in headnodes]


    def add_stencil(self, nodes, links, labels=None, language="en", master_nodenet_uid="default_domain", user=None):
        """Store a blueprint as a stencil in the master nodenet, and associate it with labels.
        Labels are extracted from the names of nodes, or used directly from the supplied list.

        Arguments:
            nodes: a dict of nodes, with types and names,
            links: a dict of links connecting these nodes (por/ret and sub/sur)
            labels: (optional) a list of strings that act as search terms later on
            language: (optional) the locale of the label(s)
            master_nodenet_uid: (optional) the uid of the nodenet of the domain
        """

        # check if master nodenet exists
        if not self.get_nodenet(master_nodenet_uid):
            self.new_nodenet(master_nodenet_uid, "Default", uid=master_nodenet_uid)
            self.load_nodenet(master_nodenet_uid)
        nodenet = self.nodenets[master_nodenet_uid]

        # check consistency before we drop this into the master nodenet
        for l_uid, l in links.items():
            source_node_uid = l.get("source_node_uid", l.get("source_node"))  # fixme
            target_node_uid = l.get("target_node_uid", l.get("target_node"))  # fixme
            if (not source_node_uid in nodes and not source_node_uid in nodenet.nodes) or (
                not target_node_uid in nodes and not target_node_uid in nodenet.nodes):
                raise KeyError, "node_uid referenced in link %s not found in nodes" % l_uid

        headnode_uid = self._find_headnode(nodes, links)
        if not headnode_uid:
            raise KeyError, "No head node found in stencil"

        headnode = nodes[headnode_uid]

        primary_labels = labels or []
        secondary_labels = []
        for uid, node in nodes.items():
            if uid != headnode_uid:
                if node.get("name"):
                    secondary_labels.append(node["name"])

        # add stencil to domain nodenet
        for uid, node in nodes.items():
            if not uid in self.nodenets[master_nodenet_uid].nodes:
                self.add_node(master_nodenet_uid,
                    node.get("type", "Concept"),
                    node.get("pos", (0,0)),
                    "Root",
                    uid = uid,
                    name = node.get("name", ""))
        for l_uid, link in links.items():
            source_node_uid = link.get("source_node_uid", link.get("source_node"))  # fixme
            target_node_uid = link.get("target_node_uid", link.get("target_node"))  # fixme
            self.add_link(master_nodenet_uid,
                source_node_uid,
                link["source_gate_name"],
                target_node_uid,
                link["target_slot_name"],
                weight = link.get("weight", 1.0),
                certainty = link.get("certainty", 1.0)
            )
        for label in primary_labels:
            self.add_label(master_nodenet_uid, label.lower(), headnode_uid, language, weight=1)
        if headnode.get("name"):
            self.add_label(master_nodenet_uid, headnode["name"].lower(), headnode_uid, language, weight = 0.5)

        for label in secondary_labels:
            self.add_label(master_nodenet_uid, label.lower(), headnode_uid, language, weight=0.1)

        if user:
            self.add_label(master_nodenet_uid, user, headnode_uid, "users")

        return headnode_uid

    def _find_headnode(self, node_dict, link_dict):
        """Helper function to identify a possible head node for a stencil, based on the supplied dictionaries of
        nodes and links.
        Returns the uid of the headnode, or raises a KeyError if none is found"""

        nodetable = {}
        for l_uid, l in link_dict.items():
            if not l.get('source_node_uid', l.get("source_node")) in nodetable:  # fixme
                nodetable[l["source_node_uid"]] = {}
            nodetable[l["source_node_uid"]][l_uid] = l

        # find headnode
        headnode = None
        headnode_uid = None
        for uid, ls in nodetable.items():
            headnode_uid = uid
            for l_uid, link in ls.items():
                if link["source_gate_name"] in ("sur", "ret", "por"):
                    headnode_uid = None
                    break
            if headnode_uid:
                return headnode_uid

        if not headnode:
            if len(node_dict) == 1:
                headnode_uid = node_dict.keys()[0]
                return headnode_uid
            else:
                return None

    def delete_stencil_by_headnode(self, headnode_uid, master_nodenet_uid="default_domain"):
        """Deletes a stencil from an existing nodenet, by identifying the nodes below the headnode and
        removing them."""

        nodenet = self.get_nodenet(master_nodenet_uid)
        if headnode_uid not in nodenet.nodes:
            return False

        nodes = set()

        def _retrieve_stencil_nodes(node_uid, nodes):
            if not node_uid in nodes:
                nodes.add(node_uid)
                por_gates = nodenet.nodes[node_uid].gates.get("por")
                sub_gates = nodenet.nodes[node_uid].gates.get("sub")

                if por_gates:
                    for link in por_gates.outgoing.values():
                        _retrieve_stencil_nodes(link.target_node.uid, nodes)
                if sub_gates:
                    for link in sub_gates.outgoing.values():
                        _retrieve_stencil_nodes(link.target_node.uid, nodes)

        _retrieve_stencil_nodes(headnode_uid, nodes)
        for node_uid in nodes:
            self.delete_node(master_nodenet_uid, node_uid)

        return True

    def delete_all_stencils_of_user(self, user, master_nodenet_uid="default_domain"):
        """Deletes all stencils associated with a given user"""

        headnodes = self.get_nodes_from_labels(master_nodenet_uid, [user], "users", max_nodes = 9999999999)
        for node in headnodes:
            self.delete_stencil_by_headnode(node.uid, master_nodenet_uid)
        try:
            self.delete_label(master_nodenet_uid, user, language = "users")
        except KeyError:
            # user has no stencils. never mind.
            pass
        return True


    def turn_nodenet_into_stencil(self, nodenet_uid, language="en", master_nodenet_uid="default_domain", user = None):
        """Helper method to import existing blueprints into stencils, which are held in a master nodenet.
        It is recommended to create a master nodenet for every language and knowledge domain."""

        nodenet = self.get_nodenet(nodenet_uid)
        result = self.add_stencil(nodenet.state["nodes"], nodenet.state["links"], [nodenet.name],
            language, master_nodenet_uid, user)
        if result:
            self.save_nodenet(master_nodenet_uid)
        return result


    def delete_stencil_by_nodenet(self, nodenet_uid, master_nodenet_uid="default_domain"):
        """Helper method to delete stencils from blueprints, based on a nodenet that was used to create it"""

        nodenet = self.get_nodenet(nodenet_uid)
        headnode_uid = self._find_headnode(nodenet.state["nodes"], nodenet.state["links"])

        result = self.delete_stencil_by_headnode(headnode_uid, master_nodenet_uid)
        if result:
            self.save_nodenet(master_nodenet_uid)
        return result



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
            owner=json.get("owner")
        )
        if "worldadapter" in json:
            result['worldadapter'] = json["worldadapter"]
            result['world'] = json["world"]
        if "world_type" in json:
            result['world_type'] = json['world_type']
        return Bunch(**result)


def main():
    MicroPsiRuntime(RESOURCE_PATH)

    if __name__ == '__main__':
        main()
