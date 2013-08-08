import math
import os
from micropsi_core.world.world import World
from micropsi_core.world.worldadapter import WorldAdapter
from micropsi_core.world.worldobject import WorldObject
from micropsi_core.world.minecraft import png
from micropsi_core.world.minecraft.spock.riker.rkclient import RikerClient
import micropsi_core.world.minecraft.vis.main as vis
from micropsi_core.world.minecraft.spock.plugins import DebugPlugin, ReConnect, EchoPacket, Gravity, AntiAFK, ChatMessage, ChunkSaver
import micropsi_core.world.minecraft.vis.main

class Minecraft(World):
    """ mandatory: list of world adapters that are supported"""
    supported_worldadapters = ['Braitenberg']

    assets = {
    'background': "island/psi_1.png",
    'js': "island/island.js",
    'x': 2048,
    'y': 2048,
    'icons': {
    'Braitenberg': 'island/braitenberg.png'
    }
    }

    def __init__(self, filename, world_type="Minecraft", name="", owner="", uid=None, version=1):
        World.__init__(self, filename, world_type=world_type, name=name, owner=owner, uid=uid, version=version)
        self.current_step = 0
        self.data['assets'] = self.assets
        self.first_step = True

    def step(self):
        if self.first_step:
            # launch minecraft bot
            username = "ownspock"
            password = ""
            micropsi_core.world.minecraft.vis.main.commence_vis()
            micropsi_core.world.minecraft.vis.main.step_vis()
            plugins = [DebugPlugin.DebugPlugin, ChatMessage.ChatMessagePlugin, ChunkSaver.ChunkSaverPlugin]
            self.client = RikerClient(plugins=plugins)
            self.client.start()
            self.first_step = False
        World.step(self)
        self.client.step()
        micropsi_core.world.minecraft.vis.main.step_vis()


class Braitenberg(WorldAdapter):
    """A simple Braitenberg vehicle chassis, with two light sensitive sensors and two engines"""

    datasources = {'x_coord': 0.7}
    datatargets = {'psi_look_value': 0}

    def initialize_worldobject(self, data):
        if not "position" in data:
            self.position = self.world.groundmap['start_position']


    def update(self):
        """called on every world simulation step to advance the life of the agent"""
        x_coord = self.world.client.position['x']
        self.world.client.psi_look_value = self.datatargets['psi_look_value']
        self.datasources['x_coord'] = x_coord