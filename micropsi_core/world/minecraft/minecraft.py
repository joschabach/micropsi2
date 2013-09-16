import math
import os
from micropsi_core.world.world import World
from micropsi_core.world.worldadapter import WorldAdapter
from micropsi_core.world.worldobject import WorldObject
from micropsi_core.world.minecraft.MinecraftClient.spock.net.client import MinecraftClient
from micropsi_core.world.minecraft.MinecraftVisualisation.main import MinecraftVisualisation
from micropsi_core.world.minecraft.MinecraftClient.plugins import DebugPlugin, ReConnect, EchoPacket, Gravity, AntiAFK, ChatMessage, ChunkSaver
from micropsi_core.world.minecraft.MinecraftClient.spock.mcp.mcpacket import Packet

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
        self.the_image = None

    def step(self):
        if self.first_step: #TODO probably not too smart
            # launch minecraft bot
            plugins = [DebugPlugin.DebugPlugin, ChatMessage.ChatMessagePlugin, ChunkSaver.ChunkSaverPlugin, EchoPacket.EchoPacketPlugin] #TODO not all plugins - if any - are needed
            self.minecraftClient = MinecraftClient(plugins=plugins)
            self.minecraftClient.start()
            self.minecraftVisualisation = MinecraftVisualisation(self.minecraftClient)
            self.minecraftVisualisation.commence_vis()
            self.first_step = False

        self.chat_ping_counter += 1
        if self.chat_ping_counter % 10 == 0: #TODO find other way to send "keepalive"
            self.minecraftClient.push(Packet(ident = 0x03, data = {
						'text': "I'm alive! ping %s" % (self.chat_ping_counter) }))
        World.step(self)
        self.minecraftClient.advanceClient()
        self.the_image = self.minecraftVisualisation.advanceVisualisation()


class Braitencraft(WorldAdapter):

    datasources = {'diamond_offset_x': 0, 'diamond_offset_z': 0, 'diamond_offset_x_': 0, 'diamond_offset_z_': 0}
    datatargets = {'move_x': 0, 'move_z': 0, 'move_x_': 0, 'move_z_': 0}

    def update(self):
        """called on every world simulation step to advance the life of the agent"""
        x_coord = self.world.minecraftClient.position['x'] * -1

        #find diamond

        x_chunk = self.world.minecraftClient.position['x'] // 16
        z_chunk = self.world.minecraftClient.position['z'] // 16
        bot_block = (self.world.minecraftClient.position['x'], self.world.minecraftClient.position['y'], self.world.minecraftClient.position['z'])
        current_column = self.world.minecraftClient.world.columns[(x_chunk, z_chunk)]

        self.datasources['diamond_offset_x'] = 0
        self.datasources['diamond_offset_z'] = 0
        self.datasources['diamond_offset_x_'] = 0
        self.datasources['diamond_offset_z_'] = 0

        for y in range(0, 16):
            current_section = current_column.chunks[int((bot_block[1] + y - 10 // 2) // 16)] #TODO explain formula
            if current_section != None:
                for x in range(0, 16):
                    for z in range(0, 16):
                        current_block = current_section['block_data'].get(x, int((bot_block[1] + y - 10 // 2) % 16), z) #TODO explain formula
                        if current_block == 56:
                            diamond_coords = (x + x_chunk * 16,y,z + z_chunk * 16)
                            self.datasources['diamond_offset_x'] = bot_block[0] - diamond_coords[0] - 2
                            self.datasources['diamond_offset_z'] = bot_block[2] - diamond_coords[2] - 2
                            self.datasources['diamond_offset_x_'] = self.datasources['diamond_offset_x'] * -1
                            self.datasources['diamond_offset_z_'] = self.datasources['diamond_offset_z'] * -1

        print("self.datasources['diamond_offset_x_'] is ", self.datasources['diamond_offset_x_'])


        self.world.minecraftClient.move_x = self.datatargets['move_x']
        self.world.minecraftClient.move_z = self.datatargets['move_z']
        self.world.minecraftClient.move_x_ = self.datatargets['move_x_']
        self.world.minecraftClient.move_z_ = self.datatargets['move_z_']

        self.datatargets['move_x'] = 0
        self.datatargets['move_z'] = 0
        self.datatargets['move_x_'] = 0
        self.datatargets['move_z_'] = 0

        self.world.minecraftClient.psi_dispatcher.dispatchPsiCommands()