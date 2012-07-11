#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MicroPsi runtime component;
maintains a set of users, worlds (up to one per user), and agents, and provides an interface to external clients
"""

__author__ = 'joscha'
__date__ = '10.05.12'

import environment
import nodenet
import os
import tools

AGENT_DIRECTORY = "agents"
WORLD_DIRECTORY = "worlds"


class MicroPsiRuntime(object):
    """The central component of the MicroPsi installation.

    The runtime instantiates agents and worlds and coordinates the interaction
    between them. It should be a singleton, otherwise competing instances might conflict over the resource files.
    """
    def __init__(self, resource_path):
        """Scan for existing node nets below the agent directory and set up a list of available agents.

        Arguments:
            resource_path: the path to the directory in which agent and world directories reside
        """
        self.agent_path = os.path.join(resource_path, AGENT_DIRECTORY)
        tools.mkdir(self.agent_path)
        self.agents = {}

        for user_directory_name, user_directory_names, agent_file_names in os.walk(self.agent_path):
            for agent_file_name in agent_file_names:
                agent = nodenet.NodenetManager(agent_file_name)
                if agent.name: self.agents[agent.name] = None

        self.world_path = os.path.join(resource_path, AGENT_DIRECTORY)
        tools.mkdir(self.world_path)
        self.worlds = {}

        for user_directory_name, user_directory_names, world_file_names in os.walk(self.world_path):
            for world_file_name in world_file_names:
                world = environment.WorldManager(world_file_name)
                if world.name: self.worlds[world.name] = None

    # MicroPsi API

    # Agent

    def get_available_agents(self, owner = None):
        """Returns a dict of uids: names of available (running and stored) agents.

        Arguments:
            owner (optional): when submitted, the list is filtered by this owner
        """
        pass

    def new_agent(self, agent_name, agent_type, owner = "", world_uid = None):
        """Creates a new node net manager and registers it.

        Arguments:
            agent_type: the type of the world adapter supported by this agent. Also used to determine the set of
                gate types supported for directional activation spreading of this agent, and the initial node types
            owner (optional): the creator of this agent
            world_id (optional): if submitted, attempts to bind the agent to this world

        Returns
            True, agent_uid if successful,
            False, error_message if failure
        """
        pass

    def delete_agent(self, agent_uid):
        """Unloads the given agent from memory and deletes it from the storage.

        Simple unloading is maintained automatically when an agent is suspended and another one is accessed.
        """
        pass

    def set_agent_data(self, agent_uid, agent_name = None, agent_type = None, world_uid = None, owner = None):
        """Sets the supplied parameters (and only those) for the agent with the given uid."""
        pass

    def start_agentrunner(self, agent_uid):
        """Starts a thread that regularly advances the given agent by one step."""
        pass

    def set_agentrunner_timestep(self, timestep):
        """Sets the speed of the agent simulation in ms.

        Argument:
            timestep: sets the simulation speed.
        """
        pass

    def get_agentrunner_timestep(self):
        """Returns the speed that has been configured for the agent runner (in ms)."""
        pass

    def get_is_agent_running(self, agent_uid):
        """Returns True if an agentrunner is active for the given agent, False otherwise."""
        pass

    def stop_agentrunner(self, agent_uid):
        """Stops the thread for the given agent."""
        pass

    def step_agent(self, agent_uid, nodespace = None):
        """Advances the given agent by one simulation step.

        Arguments:
            agent_uid: The uid of the agent
            nodespace (optional): when supplied, returns the contents of the nodespace after the simulation step
        """
        pass

    def revert_agent(self, agent_uid):
        """Returns the agent to the last saved state."""
        pass

    def save_agent(self, agent_uid):
        """Stores the agent on the server (but keeps it open)."""
        pass

    def export_agent(self, agent_uid):
        """Exports the nodenet data to the user, so it can be viewed and exchanged.

        Returns a string that contains the nodenet in JSON format.
        """
        pass

    def import_agent(self, agent_uid, nodenet):
        """Imports the nodenet data, instantiates the agent.

        Arguments:
            agent_uid: the uid of the agent (may overwrite existing agent)
            nodenet: a string that contains the nodenet in JSON format.
        """
        pass

    def merge_agent(self, agent_uid, nodenet):
        """Merges the nodenet data with an existing agent, instantiates the agent.

        Arguments:
            agent_uid: the uid of the agent (may overwrite existing agent)
            nodenet: a string that contains the nodenet in JSON format.
        """
        pass

    # World

    def get_available_worlds(self, owner = None):
        """Returns a dict of uids: names of available (running and stored) worlds.

        Arguments:
            owner (optional): when submitted, the list is filtered by this owner
        """

    def new_world(self, world_name, world_type, owner = ""):
        """Creates a new world manager and registers it.

        Arguments:
            world_name: the name of the world
            world_type: the type of the world
            owner (optional): the creator of this world

        Returns
            True, agent_uid if successful,
            False, error_message if failure
        """
        pass

    def delete_world(self, world_uid):
        """Removes the world with the given uid from the server (and unloads it from memory if it is running.)"""
        pass

    def get_world_view(self, world_uid, step):
        """Returns the current state of the world for UI purposes, if current step is newer than the supplied one."""
        pass

    def set_world_data(self, world_uid, world_name = None, world_type = None, owner = None):
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
        """Stores the world data on the server."""
        pass

    def export_world(self, world_uid):
        """Returns a JSON string with the current state of the world."""
        pass

    def import_world(self, world_uid, worlddata):
        """Imports a JSON string with world data. May overwrite an existing world."""
        pass

    # Monitor

    def add_gate_monitor(self, agent_uid, node_uid, gate_index):
        """Adds a continuous monitor to the activation of a gate. The monitor will collect the activation
        value in every simulation step."""
        pass

    def add_slot_monitor(self, agent_uid, node_uid, slot_index):
        """Adds a continuous monitor to the activation of a slot. The monitor will collect the activation
        value in every simulation step."""
        pass

    def remove_monitor(self, monitor_uid):
        """Deletes an activation monitor."""
        pass

    def clear_monitor(self, monitor_uid):
        """Leaves the monitor intact, but deletes the current list of stored values."""
        pass

    def export_monitor_data(self, agent_uid):
        """Returns a string with all currently stored monitor data for the given agent."""
        pass

    def get_monitor_data(self, agent_uid, step):
        """Returns a dictionary of monitor_uid: [node_name/node_uid, slot_type/gate_type, activation_value] for
        the current step, it the current step is newer than the supplied simulation step."""
        pass

    # Nodenet

    def get_nodespace(self, agent_uid, nodespace, step):
        """Returns the current state of the nodespace for UI purposes, if current step is newer than supplied one."""
    pass

    def get_node(self, agent_uid, node_uid):
        """Returns a dictionary with all node parameters, if node exists, or None if it does not.
        """
        pass

    def add_node(self, agent_uid, type, x, y, nodespace, uid = None, name = ""):
        """Creates a new node. (Including nodespace, native module.)

        Arguments:
            agent_uid: uid of the nodespace manager
            type: type of the node
            x, y: position of the node in the current nodespace
            nodespace: uid of the nodespace
            uid (optional): if not supplied, a uid will be generated
            name (optional): if not supplied, the uid will be used instead of a display name

        Returns:
            True, node_uid if successful,
            False, error_message if failure.
        """
        pass

    def set_node_position(self, agent_uid, node_uid, x, y):
        """Positions the specified node at the given coordinates."""
        pass

    def set_node_name(self, agent_uid, node_uid, name):
        """Sets the display name of the node"""
        pass

    def delete_node(self, agent_uid, node_uid):
        """Removes the node"""
        pass

    def get_available_node_types(self, agent_uid = None):
        """Returns an ordered list of node types available. (Including native modules.)
        If an agent uid is supplied, filter for node types defined within this agent."""
        pass

    def get_available_native_module_types(self, agent_uid = None):
        """Returns a list of native modules.
        If an agent uid is supplied, filter for node types defined within this agent."""
        pass

    def get_node_function(self, agent_uid, node_type):
        """Returns the current node function for this node type"""
        pass

    def add_node_type(self, agent_uid, node_type, node_function, slots, gates):
        """Adds or modifies a native module.

        Arguments:
            agent_uid: the agent into which the native module will be saved
            node_type: the identifier of the native module. If it already exists for another user, the new definition
                will hide the old one from view.
            node_function: the program code of the native module. The native module is defined as a python function
                that takes the current node and the current nodenet manager as arguments.
            slots: the list of slot types for this node type
            gates: the list of gate types for this node type
        """
        pass

    def delete_node_type(self, agent_uid, node_type):
        """Remove the node type from the current agent definition, if it is part of it."""
        pass

    def get_slots(self, agent_uid, node_type):
        """Returns the list of slot types for the current node type."""
        pass

    def get_gates(self, agent_uid, node_type):
        pass

    def get_gate_function(self, agent_uid, nodespace, node_type, gatetype):
        pass

    def set_gate_function(self, agent_uid, nodespace, node_type, gatetype):
        pass

    def set_gate_parameters(self, agent_uid, node_uid, gate):
        pass

    def get_available_datasources(self, agent_uid):
        pass

    def get_available_datatargets(self, agent_uid):
        pass

    def bind_datasource_to_sensor(self, agent_uid, sensor_id, datasource):
        pass

    def bind_datatarget_to_actor(self, agent_uid, actor_id, datatarget):
        pass

    def add_link(self, source_node_uid, source_gate_index, target_node_uid, target_node_index, weight, uid = None):
        pass

    def set_link_weight(self, link_id, weight):
        pass

    def delete_link(self, link_id):
        pass




def main():
    run = MicroPsiRuntime()

if __name__ == '__main__':
    main()
