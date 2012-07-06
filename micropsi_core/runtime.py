#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MicroPsi runtime component;
maintains a set of users, worlds (up to one per user), and agents, and provides an interface to external clients
"""

__author__ = 'joscha'
__date__ = '10.05.12'

# import nodenet
import world
import os
import tools

RESOURCE_PATH = os.path.join(os.path.dirname(__file__),"..","resources")

class MicroPsiRuntime(object):
    """The central component of the MicroPsi installation.

    The runtime instantiates a user manager, an agent manager and a world manager and coordinates the interaction
    between them. It must be a singleton, otherwise competing instances might conflict over the resource files.
    """

    def __init__(self):
        pass


AGENT_DIRECTORY = "agents"

class AgentManager(object):
    """Holds a number of agents (which are representated by node nets) and manages their persistency and execution"""

    def __init__(self, resource_path = RESOURCE_PATH):
        """Scans for existing node nets below the agent directory"""
        self.agent_path = os.path.join(resource_path, AGENT_DIRECTORY)
        tools.mkdir(self.agent_path)
        agent_file_list = []
        self.agents = {}

        for user_directory_name, user_directory_names, agent_file_names in os.walk(self.agent_path):
            for agent_file_name in agent_file_names:
                agent = Nodenet(agent_file_name)
                if agent:
                    self.agents[agent.name]= agent



def main():
    run = MicroPsiRuntime()

if __name__ == '__main__':
    main()
