#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MicroPsi runtime component;
maintains a set of users, worlds (up to one per user), and nodenets, and provides an interface to external clients
"""

__author__ = 'joscha'
__date__ = '10.05.12'

import micropsi_core
from micropsi_core.nodenet.nodenet import Nodenet, Node, Link, Nodespace, Nodetype, Monitor, STANDARD_NODETYPES
from micropsi_core.nodenet import node_alignment
from micropsi_core.world import world
from micropsi_core import config
import os
import tools
import json
import warnings
from threading import Thread
from datetime import datetime, timedelta
import time


RESOURCE_PATH = os.path.join(os.path.dirname(__file__), "..", "resources")
NODENET_DIRECTORY = "nodenets"
WORLD_DIRECTORY = "worlds"

AVAILABLE_WORLD_TYPES = ['World', 'berlin', 'island']  # TODO

configs = config.ConfigurationManager(os.path.join(RESOURCE_PATH, "server-config.json"))


class Bunch(dict):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        for i in kwargs:
            self[i] = kwargs[i]


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
    def __init__(self, resource_path):
        """Set up the MicroPsi runtime

        Arguments:
            resource_path: the path to the directory in which nodenet and world directories reside
        """

        self.nodenet_data = crawl_definition_files(path=os.path.join(resource_path, NODENET_DIRECTORY), type="nodenet")
        self.world_data = crawl_definition_files(path=os.path.join(resource_path, WORLD_DIRECTORY), type="world")
        if not self.world_data:
            # create a default world for convenience.
            uid = 'default'
            filename = os.path.join(RESOURCE_PATH, WORLD_DIRECTORY, uid)
            self.world_data[uid] = Bunch(uid=uid, name="default", filename=filename, version=1)
            with open(os.path.join(RESOURCE_PATH, WORLD_DIRECTORY, uid), 'w+') as fp:
                fp.write(json.dumps(self.world_data[uid], sort_keys=True, indent=4))
            fp.close()

        for uid in self.world_data:
            if "world_type" in self.world_data[uid]:
                try:
                    self.worlds[uid] = self._get_world_class(self.world_data[uid].world_type)(self, **self.world_data[uid])
                except AttributeError, err:
                    warnings.warn("Unknown world_type: %s (%s)" % (self.world_data[uid].world_type, err.message))
            else:
                self.worlds[uid] = world.World(self, **self.world_data[uid])
        self.init_runners()

    def init_runners(self):
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
            mod = __import__("micropsi_core.world.%s.%s" % (world_type, world_type), fromlist=['micropsi_core.world.%s' % world_type])
            return getattr(mod, world_type.capitalize())

    # MicroPsi API

    # Nodenet
    def get_available_nodenets(self, owner=None):
        """Returns a dict of uids: Nodenet of available (running and stored) nodenets.

        Arguments:
            owner (optional): when submitted, the list is filtered by this owner
        """
        if owner:
            return dict((uid, self.nodenet_data[uid]) for uid in self.nodenet_data if self.nodenet_data[uid].owner == owner)
        else:
            return self.nodenet_data

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
                for uid in self.nodenets:
                    if self.nodenets[uid].owner == data.owner:
                        self.unload_nodenet(uid)
                        break
                if data.get('world'):
                    world = self.worlds[data.world] or None
                    worldadapter = data.get('worldadapter')
                self.nodenets[nodenet_uid] = Nodenet(self, data.filename, name=data.name, worldadapter=worldadapter, world=world, owner=data.owner, uid=data.uid)
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
        if self.nodenets[nodenet_uid].world is not None:
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

    def new_nodenet(self, nodenet_name, worldadapter, template=None,  owner="", world_uid=None):
        """Creates a new node net manager and registers it.

        Arguments:
            worldadapter: the type of the world adapter supported by this nodenet. Also used to determine the set of
                gate types supported for directional activation spreading of this nodenet, and the initial node types
            owner (optional): the creator of this nodenet
            world_uid (optional): if submitted, attempts to bind the nodenet to this world

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
        data.update(dict(
            uid=tools.generate_uid(),
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
        if world_uid is not None or worldadapter is not None:
            if world_uid is None:
                world_uid = nodenet.world
            if worldadapter is None:
                worldadapter = nodenet.worldadapter
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
        assert nodenet_data['world'] in self.worlds
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
        from micropsi_core.world import worldadapter
        data = self.worlds[world_uid].data
        data['worldadapters'] = {}
        for name in self.worlds[world_uid].supported_worldadapters:
            data['worldadapters'][name] = {
                'datasources': getattr(worldadapter, name).datasources.keys(),
                'datatargets': getattr(worldadapter, name).datatargets.keys()
            }
        return data

    def get_worldadapters(self, world_uid):
        """Returns the world adapters available in the given world"""
        from micropsi_core.world import worldadapter
        data = {}
        for name in self.worlds[world_uid].supported_worldadapters:
            data[name] = {
                'datasources': getattr(worldadapter, name).datasources.keys(),
                'datatargets': getattr(worldadapter, name).datatargets.keys()
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
        self.world_data[uid] = Bunch(uid=uid, name=world_name, world_type=world_type, filename=filename, version=1, owner=owner)
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
        self.worlds[data['uid']] = self._get_world_class(self.world_data[data['uid']].world_type)(self, **self.world_data[data['uid']])
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

    def add_node(self, nodenet_uid, type, pos, nodespace, state=None, uid=None, name="", parameters={}):
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
        nodenet = self.nodenets[nodenet_uid]
        if type == "Nodespace":
            nodespace = Nodespace(nodenet, nodespace, pos, name=name, entitytype='nodespaces', uid=uid)
            uid = nodespace.uid
            nodenet.nodespaces[uid] = nodespace
        else:
            node = Node(nodenet, nodespace, pos, name=name, type=type, uid=uid, parameters=parameters)
            uid = node.uid
            nodenet.nodes[uid] = node
            nodenet.nodes[uid].activation = 0  # TODO: shoudl this be persisted?
            if state:
                nodenet.nodes[uid].state = state
        return True, uid

    def set_node_position(self, nodenet_uid, node_uid, pos):
        """Positions the specified node at the given coordinates."""
        nodenet = self.nodenets[nodenet_uid]
        if node_uid in nodenet.nodes:
            nodenet.nodes[node_uid].position = pos
        elif node_uid in nodenet.nodespaces:
            nodenet.nodespaces[node_uid].position = pos
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
            link_uids = []
            for key, gate in nodenet.nodes[node_uid].gates.items():
                link_uids.extend(gate.outgoing.keys())
            for key, slot in nodenet.nodes[node_uid].slots.items():
                link_uids.extend(slot.incoming.keys())
            parent_nodespace = nodenet.nodespaces.get(nodenet.nodes[node_uid].parent_nodespace)
            parent_nodespace.netentities["nodes"].remove(node_uid)
            del nodenet.nodes[node_uid]
            del nodenet.state['nodes'][node_uid]
            for uid in link_uids:
                nodenet.links[uid].remove()
                del nodenet.links[uid]
                del nodenet.state['links'][uid]
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
        nodenet.nodetypes[node_type] = Nodetype(node_type, nodenet, slots, gates, [], parameters, nodefunction_definition=node_function)
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
        return self.nodenets[nodenet_uid].state['nodespaces'][nodespace]['gatefunctions'].get(node_type, {}).get(gate_type)

    def set_gate_function(self, nodenet_uid, nodespace, node_type, gate_type, gate_function=None, parameters=None):
        """Sets the gate function of the given node and gate within the current nodespace.
        Gate functions are defined per nodespace, and handed the parameters dictionary. They must return an activation.
        The default function is a threshold with parameter t=0.
        None reverts the custom gate function of the given node and gate within the current nodespace to the default.
        Parameters is a list of keys for values of the gate function.
        """
        self.nodenets[nodenet_uid].nodespaces[nodespace].set_gate_function(node_type, gate_type, gate_function, parameters)
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

    def add_link(self, nodenet_uid, source_node_uid, gate_type, target_node_uid, slot_type, weight, certainty=1, uid=None):
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
        link = Link(
            nodenet.nodes[source_node_uid],
            gate_type,
            nodenet.nodes[target_node_uid],
            slot_type,
            weight=weight,
            certainty=certainty,
            uid=uid)
        # TODO: let the link itself do the next step.
        nodenet.state['links'][link.uid] = dict(
            source_node=source_node_uid,
            source_gate_name=gate_type,
            target_node=target_node_uid,
            target_slot_name=slot_type,
            weight=weight,
            certainty=certainty,
            uid=link.uid
        )
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
        return node_alignment.align(self.nodenets[nodenet_uid], nodespace)


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
