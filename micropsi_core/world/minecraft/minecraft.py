import math
import os
from micropsi_core.world.world import World
from micropsi_core.world.worldadapter import WorldAdapter
from micropsi_core.world.worldobject import WorldObject
from micropsi_core.world.minecraft import png
from micropsi_core.world.minecraft.spock.riker.rkclient import RikerClient
from micropsi_core.world.minecraft.spock.plugins import DebugPlugin, ReConnect, EchoPacket, Gravity, AntiAFK, ChatMessage, ChunkSaver


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
            plugins = [DebugPlugin.DebugPlugin, ChatMessage.ChatMessagePlugin, ChunkSaver.ChunkSaverPlugin]
            self.client = RikerClient(plugins=plugins)
            self.client.start()
            self.first_step = False
        World.step(self)
        self.client.step()


class Braitenberg(WorldAdapter):
    """A simple Braitenberg vehicle chassis, with two light sensitive sensors and two engines"""

    datasources = {'brightness_l': 1.7, 'brightness_r': 1.7}
    datatargets = {'engine_l': 0, 'engine_r': 0}

    # positions of sensors, relative to origin of agent center
    brightness_l_offset = (-0.25, 0.25)
    brightness_r_offset = (0.25, 0.25)

    # positions of engines, relative to origin of agent center
    engine_l_offset = (-0.3, 0)
    engine_r_offset = (0.3, 0)

    # agent diameter
    diameter = 0.6

    # maximum speed
    speed_limit = 1.5

    def initialize_worldobject(self, data):
        if not "position" in data:
            self.position = self.world.groundmap['start_position']


    def update(self):
        """called on every world simulation step to advance the life of the agent"""
        pass