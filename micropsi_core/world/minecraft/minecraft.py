import math
import os
from micropsi_core.world.world import World
from micropsi_core.world.worldadapter import WorldAdapter
from micropsi_core.world.worldobject import WorldObject
from micropsi_core.world.minecraft.spock.riker.rkclient import RikerClient
import micropsi_core.world.minecraft.vis.main as vis
from micropsi_core.world.minecraft.spock.plugins import DebugPlugin, ReConnect, EchoPacket, Gravity, AntiAFK, ChatMessage, ChunkSaver
from micropsi_core.world.minecraft.spock.spock.mcp.mcpacket import Packet

class Minecraft(World):
    """ mandatory: list of world adapters that are supported"""
    supported_worldadapters = ['Braitenberg']

    assets = {
    'js': "minecraft/minecraft.js",
    'x': 2048,
    'y': 2048,
    }

    def __init__(self, filename, world_type="Minecraft", name="", owner="", uid=None, version=1):
        World.__init__(self, filename, world_type=world_type, name=name, owner=owner, uid=uid, version=version)
        self.current_step = 0
        self.data['assets'] = self.assets
        self.first_step = True
        self.chat_ping_counter = 0

    def step(self):
        if self.first_step: #TODO probably not too smart
            # launch minecraft bot
            plugins = [DebugPlugin.DebugPlugin, ChatMessage.ChatMessagePlugin, ChunkSaver.ChunkSaverPlugin] #TODO not all plugins - if any - are needed
            self.client = RikerClient(plugins=plugins) #TODO Riker is not needed either and not in development anymore
            self.client.start()
            vis.commence_vis(self.client)
            self.first_step = False

        self.chat_ping_counter += 1
        if self.chat_ping_counter % 100 == 0: #TODO find other way to send "keepalive"
            self.client.push(Packet(ident = 0x03, data = {
						'text': "I'm alive! ping %s" % (self.chat_ping_counter) }))
        World.step(self)
        self.client.step()
        vis.step_vis()


class Braitenberg(WorldAdapter):
    """A simple Braitenberg vehicle chassis, with two light sensitive sensors and two engines"""

    datasources = {'x_coord': 0.7}
    datatargets = {'psi_look_value': 0} #TODO this does not do anything yet

    def update(self):
        """called on every world simulation step to advance the life of the agent"""
        x_coord = self.world.client.position['x']
        self.world.client.psi_look_value = self.datatargets['psi_look_value']
        self.datasources['x_coord'] = x_coord