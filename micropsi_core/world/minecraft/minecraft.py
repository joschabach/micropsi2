import math
import os
from micropsi_core.world.world import World
from micropsi_core.world.worldadapter import WorldAdapter
from micropsi_core.world.worldobject import WorldObject
from micropsi_core.world.minecraft.spock.spock.net.client import Client as Spock
import micropsi_core.world.minecraft.vis.main as vis
from micropsi_core.world.minecraft.spock.plugins import DebugPlugin, ReConnect, EchoPacket, Gravity, AntiAFK, ChatMessage, ChunkSaver
from micropsi_core.world.minecraft.spock.spock.mcp.mcpacket import Packet

class Minecraft(World):
    """ mandatory: list of world adapters that are supported"""
    supported_worldadapters = ['Braitencraft']

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
            self.client = Spock(plugins=plugins)
            self.client.start()
            vis.commence_vis(self.client)
            self.first_step = False

        self.chat_ping_counter += 1
        if self.chat_ping_counter % 20 == 0: #TODO find other way to send "keepalive"
            self.client.push(Packet(ident = 0x03, data = {
						'text': "I'm alive! ping %s" % (self.chat_ping_counter) }))
            self.client.push(Packet(ident = 0x0B, data = {
                    'x': (self.client.position['x'])  // 1,
                    'y': self.client.position['y'] // 1,
                    'z': self.client.position['z'] + 1 // 1,
                    'on_ground': False,
                    'stance': self.client.position['y'] + 0.11
                    }))
        World.step(self)
        self.client.step()
        vis.step_vis()


class Braitencraft(WorldAdapter):
    """A simple Braitenberg vehicle chassis, with two light sensitive sensors and two engines"""

    datasources = {'diamond_offset_x': 0, 'diamond_offset_z': 0}
    datatargets = {'move_x': 0, 'move_z': 0}

    def update(self):
        """called on every world simulation step to advance the life of the agent"""
        x_coord = self.world.client.position['x'] * -1

        #find diamond

        x_chunk = self.world.client.position['x'] // 16
        z_chunk = self.world.client.position['z'] // 16
        bot_block = [self.world.client.position['x'], self.world.client.position['y'], self.world.client.position['z']]
        current_column = self.world.client.world.columns[(x_chunk, z_chunk)]

        diamond_coords = (0,0,0)
        for y in range(0, 16):
            current_section = current_column.chunks[int((bot_block[1] + y - 10 // 2) // 16)] #TODO explain formula
            if current_section != None:
                for x in range(0, 16):
                    for z in range(0, 16):
                        current_block = current_section['block_data'].get(x, int((bot_block[1] + y - 10 // 2) % 16), z) #TODO explain formula
                        if current_block == 56:
                            diamond_coords = (x + x_chunk * 16,y,z + z_chunk * 16)

        self.datasources['diamond_offset_x'] = self.world.client.position['x'] - diamond_coords[0] - 2
        self.datasources['diamond_offset_z'] = self.world.client.position['z'] - diamond_coords[2] - 2

        self.world.client.move_x = self.datatargets['move_x']
        self.world.client.move_z = self.datatargets['move_z']