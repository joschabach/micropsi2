#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MicroPsi runtime component;
maintains a set of users, worlds (up to one per user), and nodenets, and provides an interface to external clients
"""

__author__ = 'joscha'
__date__ = '10.05.12'

from micropsi_core.world.world import World
from micropsi_core.nodenet.nodenet import Nodenet, Node, Link, Gate, Slot, Nodespace
import os
import tools
import json
import warnings
from bunch import Bunch

RESOURCE_PATH = os.path.join(os.path.dirname(__file__),"..","resources")
NODENET_DIRECTORY = "nodenets"
WORLD_DIRECTORY = "worlds"


class MicroPsiRuntime(object):

    worlds = {}
    nodenets = {}

    """The central component of the MicroPsi installation.

    The runtime instantiates nodenets and worlds and coordinates the interaction
    between them. It should be a singleton, otherwise competing instances might conflict over the resource files.
    """
    def __init__(self, resource_path):
        """Set up the MicroPsi runtime

        Arguments:
            resource_path: the path to the directory in which nodenet and world directories reside
        """

        self.nodenet_data = crawl_definition_files(path = os.path.join(resource_path, NODENET_DIRECTORY), type = "nodenet")
        self.world_data = crawl_definition_files(path = os.path.join(resource_path, WORLD_DIRECTORY), type = "world")
        for uid in self.world_data:
            self.worlds[uid] = World(self, **self.world_data[uid])


    def _get_world_uid_for_nodenet_uid(self, nodenet_uid):
        """ Temporary method to get the world uid to a given nodenet uid.
            TODO: I guess this should be handled a bit differently?
        """
        if nodenet_uid in self.nodenet_data:
            return self.nodenet_data[nodenet_uid].world
        return None


    def _get_nodenet(self, nodenet_uid):
        """ get the nodenet instance to the given nodenet_uid.
            this will lookup the world this nodenet lives in from the nodenet_data,
            and then fetch the nodenet instance from the respective world instance.
            TODO: please review: should we leave it like that or rather add a hash of
                  nodenets in addition to the hash of worlds?
        """
        return self.worlds[self._get_world_uid_for_nodenet_uid(nodenet_uid)].agents[nodenet_uid]

    # MicroPsi API

    # Nodenet

    def get_available_nodenets(self, owner = None):
        """Returns a dict of uids: Nodenet of available (running and stored) nodenets.

        Arguments:
            owner (optional): when submitted, the list is filtered by this owner
        """
        if owner:
            return { uid: self.nodenet_data[uid] for uid in self.nodenet_data if self.nodenet_data[uid].owner == owner }
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
        world_uid = self._get_world_uid_for_nodenet_uid(nodenet_uid)
        if world_uid:
            return self.worlds[world_uid].register_nodenet(self.nodenet_data[nodenet_uid].worldadapter, nodenet_uid)
        return False, "no such nodenet"

    def get_nodenet_area(self, nodenet_uid, x1=0, x2=-1, y1=0, y2=-1):
        """ return all nodes and links within the given area of the nodenet
            for representation in the UI
            TODO
        """
        return self._get_nodenet(nodenet_uid).state

    def new_nodenet(self, nodenet_name, worldadapter, owner = "", world_uid = None):
        """Creates a new node net manager and registers it.

        Arguments:
            worldadapter: the type of the world adapter supported by this nodenet. Also used to determine the set of
                gate types supported for directional activation spreading of this nodenet, and the initial node types
            owner (optional): the creator of this nodenet
            world_uid (optional): if submitted, attempts to bind the nodenet to this world

        Returns
            world_uid if successful,
            None if failure

        TODO: I'd suggest, that this should rather return the nodenet UID?
        """
        data = dict(
            uid=tools.generate_uid(),
            name=nodenet_name,
            worldadapter=worldadapter,
            owner=owner,
            world=world_uid,
            nodes=dict(),
            links=dict(),
            version=1
        )
        data['filename'] = os.path.join(RESOURCE_PATH, NODENET_DIRECTORY, data['uid'])
        self.nodenet_data[data['uid']] = Bunch(**data)
        with open(data['filename'], 'w+') as fp:
            fp.write(json.dumps(data, sort_keys=True, indent=4))
        fp.close
        #self.load_nodenet(data['uid'])
        return True, data['uid']

    def delete_nodenet(self, nodenet_uid):
        """Unloads the given nodenet from memory and deletes it from the storage.

        Simple unloading is maintained automatically when a nodenet is suspended and another one is accessed.
        """
        data = self.nodenet_data[nodenet_uid]
        self.worlds[data.world].unregister_nodenet(nodenet_uid)
        os.remove(data.filename)
        del self.nodenet_data[nodenet_uid]
        return True

    def set_nodenet_properties(self, nodenet_uid, nodenet_name = None, worldadapter = None, world_uid = None, owner = None):
        """Sets the supplied parameters (and only those) for the nodenet with the given uid."""
        pass

    def start_nodenetrunner(self, nodenet_uid):
        """Starts a thread that regularly advances the given nodenet by one step."""
        pass

    def set_nodenetrunner_timestep(self, timestep):
        """Sets the speed of the nodenet simulation in ms.

        Argument:
            timestep: sets the simulation speed.
        """
        pass

    def get_nodenetrunner_timestep(self):
        """Returns the speed that has been configured for the nodenet runner (in ms)."""
        pass

    def get_is_nodenet_running(self, nodenet_uid):
        """Returns True if a nodenet runner is active for the given nodenet, False otherwise."""
        pass

    def stop_nodenetrunner(self, nodenet_uid):
        """Stops the thread for the given nodenet."""
        pass

    def step_nodenet(self, nodenet_uid, nodespace = None):
        """Advances the given nodenet by one simulation step.

        Arguments:
            nodenet_uid: The uid of the nodenet
            nodespace (optional): when supplied, returns the contents of the nodespace after the simulation step
        """
        nodenet = self._get_nodenet(nodenet_uid)
        nodenet.step()
        return nodenet.state['step']

    def revert_nodenet(self, nodenet_uid):
        """Returns the nodenet to the last saved state."""
        world = self.worlds[self._get_world_uid_for_nodenet_uid(nodenet_uid)]
        world.unregister_nodenet(nodenet_uid)
        return world.register_nodenet(self.nodenet_data[nodenet_uid].worldadapter, nodenet_uid)

    def save_nodenet(self, nodenet_uid):
        """Stores the nodenet on the server (but keeps it open)."""
        nodenet = self._get_nodenet(nodenet_uid)
        with open(os.path.join(RESOURCE_PATH, NODENET_DIRECTORY, nodenet.filename), 'w+') as fp:
            fp.write(json.dumps(nodenet.state, sort_keys=True, indent=4))
        fp.close
        return True

    def export_nodenet(self, nodenet_uid):
        """Exports the nodenet state to the user, so it can be viewed and exchanged.

        Returns a string that contains the nodenet state in JSON format.
        """
        pass

    def import_nodenet(self, anodenet_uid, string):
        """Imports the nodenet state, instantiates the nodenet.

        Arguments:
            nodenet_uid: the uid of the nodenet (may overwrite existing nodenet)
            string: a string that contains the nodenet state in JSON format.
        """
        pass

    def merge_nodenet(self, nodenet_uid, string):
        """Merges the nodenet data with an existing nodenet, instantiates the nodenet.

        Arguments:
            nodenet_uid: the uid of the existing nodenet (may overwrite existing nodenet)
            string: a string that contains the nodenet data that is to be merged in JSON format.
        """
        pass

    # World

    def get_available_worlds(self, owner = None):
        """Returns a dict of uids: World of (running and stored) worlds.

        Arguments:
            owner (optional): when submitted, the list is filtered by this owner
        """
        if owner:
            return { uid: self.worlds[uid] for uid in self.worlds if self.worlds[uid].owner == owner }
        else:
            return self.worlds

    def get_worldadapters(self, world_uid):
        """Returns the world adapters available in the given world"""
        if world_uid in self.worlds:
            return self.worlds[world_uid].worldadapters
        return None

    def new_world(self, world_name, world_type, owner = ""):
        """Creates a new world manager and registers it.

        Arguments:
            world_name: the name of the world
            world_type: the type of the world
            owner (optional): the creator of this world

        Returns
            world_uid if successful,
            None if failure
        """
        pass

    def delete_world(self, world_uid):
        """Removes the world with the given uid from the server (and unloads it from memory if it is running.)"""
        pass

    def get_world_view(self, world_uid, step):
        """Returns the current state of the world for UI purposes, if current step is newer than the supplied one."""
        pass

    def set_world_properties(self, world_uid, world_name = None, world_type = None, owner = None):
        """Sets the supplied parameters (and only those) for the world with the given uid."""
        pass

    def start_worldrunner(self, world_uid):
        """Starts a thread that regularly advances the world simulation."""
        pass

    def get_worldrunner_timestep(self):
        """Returns the speed that has been configured for the world runner (in ms)."""
        pass

    def get_is_world_running(self, world_uid):
        """Returns True if an worldrunner is active for the given world, False otherwise."""
        pass

    def set_worldrunner_timestep(self):
        """Sets the interval of the simulation steps for the world runner (in ms)."""
        pass

    def stop_worldrunner(self, world_uid):
        """Ends the thread of the continuous world simulation."""
        pass

    def step_world(self, world_uid, return_world_view = False):
        """Advances the world simulation by one step.

        Arguments:
            world_uid: the uid of the simulation world
            return_world_view: if True, return the current world state for UI purposes
        """
        pass

    def revert_world(self, world_uid):
        """Reverts the world to the last saved state."""
        pass

    def save_world(self, world_uid):
        """Stores the world state on the server."""
        pass

    def export_world(self, world_uid):
        """Returns a JSON string with the current state of the world."""
        pass

    def import_world(self, world_uid, worlddata):
        """Imports a JSON string with world data. May overwrite an existing world."""
        pass

    # Monitor

    def add_gate_monitor(self, nodenet_uid, node_uid, gate_index):
        """Adds a continuous monitor to the activation of a gate. The monitor will collect the activation
        value in every simulation step."""
        pass

    def add_slot_monitor(self, nodenet_uid, node_uid, slot_index):
        """Adds a continuous monitor to the activation of a slot. The monitor will collect the activation
        value in every simulation step."""
        pass

    def remove_monitor(self, monitor_uid):
        """Deletes an activation monitor."""
        pass

    def clear_monitor(self, monitor_uid):
        """Leaves the monitor intact, but deletes the current list of stored values."""
        pass

    def export_monitor_data(self, nodenet_uid):
        """Returns a string with all currently stored monitor data for the given nodenet."""
        pass

    def get_monitor_data(self, nodenet_uid, step):
        """Returns a dictionary of monitor_uid: [node_name/node_uid, slot_type/gate_type, activation_value] for
        the current step, it the current step is newer than the supplied simulation step."""
        pass

    # Node operations

    def get_nodespace(self, nodenet_uid, nodespace, step):
        """Returns the current state of the nodespace for UI purposes, if current step is newer than supplied one."""
    pass

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
        pass

    def add_node(self, nodenet_uid, type, x, y, nodespace, uid = None, name = ""):
        """Creates a new node. (Including nodespace, native module.)

        Arguments:
            nodenet_uid: uid of the nodespace manager
            type: type of the node
            x, y (optional): position of the node in the current nodespace
            nodespace: uid of the nodespace
            uid (optional): if not supplied, a uid will be generated
            name (optional): if not supplied, the uid will be used instead of a display name
            parameters (optional): a dict of arbitrary parameters that can make nodes stateful

        Returns:
            node_uid if successful,
            None if failure.
        """
        nodenet = self._get_nodenet(nodenet_uid)
        nodenet.state['nodes'][uid] = dict(
            name=name,
            uid=uid,
            nodespace=nodespace,
            x=x,
            y=y,
            type=type,
            activation=0
        )
        nodenet.nodes[uid] = Node(nodenet, nodespace, (x,y), name=name, type=type, uid=uid)
        return True, nodenet_uid


    def set_node_position(self, nodenet_uid, node_uid, x, y):
        """Positions the specified node at the given coordinates."""
        pass

    def set_node_name(self, nodenet_uid, node_uid, name):
        """Sets the display name of the node"""
        pass

    def delete_node(self, nodenet_uid, node_uid):
        """Removes the node"""
        nodenet = self._get_nodenet(nodenet_uid)
        link_uids = []
        for key, gate in nodenet.nodes[node_uid].gates.items():
            link_uids.extend(gate.outgoing.keys())
        for key, slot in nodenet.nodes[node_uid].slots.items():
            link_uids.extend(slot.incoming.keys())
        del nodenet.nodes[node_uid]
        del nodenet.state['nodes'][node_uid]
        for uid in link_uids:
            del nodenet.links[uid]
            del nodenet.state['links'][uid]
        return True

    def get_available_node_types(self, nodenet_uid):
        """Returns a list of available node types. (Including native modules.)"""
        pass

    def get_available_native_module_types(self, nodenet_uid = None):
        """Returns a list of native modules.
        If an nodenet uid is supplied, filter for node types defined within this nodenet."""
        pass

    def get_node_function(self, nodenet_uid, node_type):
        """Returns the current node function for this node type"""
        pass

    def set_node_function(self, nodenet_uid, node_type, node_function = None):
        """Sets a new node fuction for this node type. This amounts to a program that is executed every time the
        node becomes active. Parameters of the function are the node itself (and thus, its slots, gates and
        parent nodespace), the nodenet, and the parameter dict of this node).
        Setting the node_function to None will return it to its default state (passing the slot activations to
        all gate functions).
        """
        pass

    def set_node_parameters(self, nodenet_uid, node_uid, **parameters):
        """Sets a dict of arbitrary values to make the node stateful."""
        nodenet = self._get_nodenet(nodenet_uid)
        state = nodenet.state['nodes'][node_uid]
        node = nodenet.nodes[node_uid]
        for key,value in parameters.items():
            if key in state: state[key] = value

    def add_node_type(self, nodenet_uid, node_type, slots = None, gates = None, node_function = None, parameters = None):
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
        pass

    def delete_node_type(self, nodenet_uid, node_type):
        """Remove the node type from the current nodenet definition, if it is part of it."""
        pass

    def get_slot_types(self, nodenet_uid, node_type):
        """Returns the list of slot types for the given node type."""
        pass

    def get_gate_types(self, nodenet_uid, node_type):
        """Returns the list of gate types for the given node type."""
        pass

    def get_gate_function(self, nodenet_uid, nodespace, node_type, gate_type):
        """Returns a string with the gate function of the given node and gate within the current nodespace.
        Gate functions are defined per nodespace, and handed the parameters dictionary. They must return an activation.
        """
        pass

    def set_gate_function(self, nodenet_uid, nodespace, node_type, gate_type, gate_function = None, parameters = None):
        """Sets the gate function of the given node and gate within the current nodespace.
        Gate functions are defined per nodespace, and handed the parameters dictionary. They must return an activation.
        The default function is a threshold with parameter t=0.
        None reverts the custom gate function of the given node and gate within the current nodespace to the default.
        Parameters is a list of keys for values of the gate function.
        """
        pass

    def set_gate_parameters(self, nodenet_uid, node_uid, gate_type, parameters = None):
        """Sets the gate parameters of the given gate of the given node to the supplied dictionary."""
        pass

    def get_available_datasources(self, nodenet_uid):
        """Returns a list of available datasource types for the given nodenet."""
        return self._get_nodenet(nodenet_uid).worldadapter.get_available_datasources()

    def get_available_datatargets(self, nodenet_uid):
        """Returns a list of available datatarget types for the given nodenet."""
        pass

    def bind_datasource_to_sensor(self, nodenet_uid, sensor_uid, datasource):
        """Associates the datasource type to the sensor node with the given uid."""
        node = self._get_nodenet(nodenet_uid).nodes[sensor_uid]
        if node.type == "Sensor":
            node.nodenet.state['nodes'][sensor_uid]['datasource'] = datasource
            node.data['datasource'] = datasource
            return True
        return False

    def bind_datatarget_to_actor(self, nodenet_uid, actor_uid, datatarget):
        """Associates the datatarget type to the actor node with the given uid."""
        pass

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
        nodenet = self._get_nodenet(nodenet_uid)
        link = Link(
            nodenet.nodes[source_node_uid],
            gate_type,
            nodenet.nodes[target_node_uid],
            slot_type,
            weight=weight,
            certainty=certainty,
            uid=uid)
        nodenet.state['links'][link.uid] = dict(
            sourceNode=source_node_uid,
            sourceGate=gate_type,
            targetNode=target_node_uid,
            targetSlot=slot_type,
            weight=weight,
            certainty=certainty,
            uid=link.uid
        )
        nodenet.links[link.uid] = link
        return True, link.uid



    def set_link_weight(self, nodenet_uid, link_uid, weight, certainty = 1):
        """Set weight of the given link."""
        nodenet = self._get_nodenet(nodenet_uid)
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
        pass

    def delete_link(self, nodenet_uid, link_uid):
        """Delete the given link."""
        nodenet = self._get_nodenet(nodenet_uid)
        nodenet.links[link_uid].remove()
        del nodenet.links[link_uid]
        del nodenet.state['links'][link_uid]
        return True


def crawl_definition_files(path, type = "definition"):
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
                    data = json.load(file)
                    if "uid" in data:
                        result[data["uid"]] = Bunch(
                            uid = data["uid"],
                            name = data.get("name", data["uid"]),
                            filename = filename,
                            owner = data.get("owner")
                        )
                        if "worldadapter" in data:
                            result[data["uid"]].worldadapter = data["worldadapter"]
                            result[data["uid"]].world = data["world"]
            except ValueError:
                warnings.warn("Invalid %s data in file '%s'" %(type, definition_file_name))
            except IOError:
                warnings.warn("Could not open %s data file '%s'" %(type, definition_file_name))
    return result

def main():
    run = MicroPsiRuntime(RESOURCE_PATH)

if __name__ == '__main__':
    main()
