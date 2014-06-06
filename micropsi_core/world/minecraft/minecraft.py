import math
import os
import warnings
import signal
from threading import Thread
import configparser
from micropsi_core.world.world import World
from micropsi_core.world.worldadapter import WorldAdapter
from micropsi_core.world.worldobject import WorldObject
from spock.plugins import DefaultPlugins
from spock.client import Client
from spock.client import PluginLoader
#from micropsi_core.world.minecraft.visualisation.main import MinecraftVisualisation
from micropsi_core.world.minecraft import spockplugin
from spock.plugins.helpers import start
from spock.plugins.core import timers
from spock.plugins.helpers.clientinfo import ClientInfoPlugin
from spock.plugins.helpers.move import MovementPlugin
from spock.plugins.helpers.world import WorldPlugin
from spock.plugins.core.event import EventPlugin


class Minecraft(World):
    """ mandatory: list of world adapters that are supported"""
    supported_worldadapters = ['MinecraftWorldadapter']

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

        plugins = DefaultPlugins
        plugins.append(ClientInfoPlugin)
        plugins.append(MovementPlugin)
        plugins.append(WorldPlugin)
        plugins.append(spockplugin.MicropsiPlugin)

        settings = {
            'username': 'bot',          #minecraft.net username or name for unauthenticated servers
		    'password': '',             #Password for account, ignored if not authenticated
		    'authenticated': False,     #Authenticate with authserver.mojang.com
		    'bufsize': 4096,            #Size of socket buffer
		    'sock_quit': True,          #Stop bot on socket error or hangup
		    'sess_quit': True,          #Stop bot on failed session login
		    'thread_workers': 5,        #Number of workers in the thread pool
		    'plugins': DefaultPlugins,
		    'plugin_settings': {
            spockplugin.MicropsiPlugin: {"worldadapter": self},
            EventPlugin: {"killsignals": False}
            },                          #Extra settings for plugins
            'packet_trace': False,
            'mc_username': "sepp",
            "mc_password": "hugo"
        }
        self.spock = Client(plugins=plugins, settings=settings)
        # the MicropsiPlugin will create self.spockplugin here on instantiation

        server_parameters = self.read_server_parameters()
        self.minecraft_communication_thread = Thread(target=self.spock.start, args=server_parameters)
        self.minecraft_communication_thread.start()
        signal.signal(signal.SIGINT, self.kill_minecraft_thread)
        signal.signal(signal.SIGTERM, self.kill_minecraft_thread)

    def step(self):
        World.step(self)

    def read_server_parameters(self):
        server = 'localhost'
        port = 25565

        try:
            config = configparser.ConfigParser()
            config.read_file(open('config.ini'))
            if 'minecraft_server' in config.keys():
                server = config['minecraft_server']
            if 'minecraft_port' in config.keys():
                port = config['minecraft_port']
        except OSError:
            warnings.warn('Could not read config.ini, falling back to defaults for minecraft server configuration.')

        return server, port

    def kill_minecraft_thread(self, *args):
        self.spockplugin.event.kill()


class MinecraftWorldadapter(WorldAdapter):

    #datasources = {'diamond_offset_x': 0, 'diamond_offset_z': 0, 'diamond_offset_x_': 0, 'diamond_offset_z_': 0}
    datasources = {'diamond_offset_x': 0, 'diamond_offset_z': 0, 'diamond_offset_x_': 0, 'diamond_offset_z_': 0, }
    datatargets = {'move_x': 0, 'move_z': 0, 'move_x_': 0, 'move_z_': 0}

    def update(self):
        """called on every world simulation step to advance the life of the agent"""
        x_coord = self.world.spockplugin.position['x'] * -1

        #find diamond

        x_chunk = self.world.spockplugin.position['x'] // 16
        z_chunk = self.world.spockplugin.position['z'] // 16
        bot_block = (self.world.spockplugin.position['x'], self.world.spockplugin.position['y'], self.world.spockplugin.position['z'])
        current_column = self.world.spockplugin.worldplugin.map.columns[(x_chunk, z_chunk)]

        self.datasources['diamond_offset_x'] = 0
        self.datasources['diamond_offset_z'] = 0
        self.datasources['diamond_offset_x_'] = 0
        self.datasources['diamond_offset_z_'] = 0

        for y in range(0, 16):
            current_section = current_column.chunks[int((self.world.spockplugin.position['y'] + y - 10 // 2) // 16)] #TODO explain formula
            if current_section != None:
                for x in range(0, 16):
                    for z in range(0, 16):
                        current_block = current_section.get(x, int((self.world.spockplugin.position['y'] + y - 10 // 2) % 16), z).id #TODO explain formula
                        if current_block == 56:
                            diamond_coords = (x + x_chunk * 16,y,z + z_chunk * 16)
                            self.datasources['diamond_offset_x'] = bot_block[0] - diamond_coords[0] - 2
                            self.datasources['diamond_offset_z'] = bot_block[2] - diamond_coords[2] - 2
                            self.datasources['diamond_offset_x_'] = self.datasources['diamond_offset_x'] * -1
                            self.datasources['diamond_offset_z_'] = self.datasources['diamond_offset_z'] * -1

        print("self.datasources['diamond_offset_x_'] is ", self.datasources['diamond_offset_x_'])


        self.world.spockplugin.move_x = self.datatargets['move_x']
        self.world.spockplugin.move_z = self.datatargets['move_z']
        self.world.spockplugin.move_x_ = self.datatargets['move_x_']
        self.world.spockplugin.move_z_ = self.datatargets['move_z_']

        self.datatargets['move_x'] = 0
        self.datatargets['move_z'] = 0
        self.datatargets['move_x_'] = 0
        self.datatargets['move_z_'] = 0

#        self.world.spockplugin.psi_dispatcher.dispatchPsiCommands()
