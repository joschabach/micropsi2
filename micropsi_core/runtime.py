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




def main():
    run = MicroPsiRuntime()

if __name__ == '__main__':
    main()
