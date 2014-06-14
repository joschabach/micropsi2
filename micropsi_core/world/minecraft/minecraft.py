import warnings
from threading import Thread
import configparser
from micropsi_core.world.world import World
from micropsi_core.world.worldadapter import WorldAdapter
from spock.plugins import DefaultPlugins
from spock.client import Client
from micropsi_core.world.minecraft import spockplugin
from spock.plugins.helpers.clientinfo import ClientInfoPlugin
from spock.plugins.helpers.move import MovementPlugin
from spock.plugins.helpers.world import WorldPlugin
from spock.plugins.core.event import EventPlugin


class Minecraft(World):
    """ mandatory: list of world adapters that are supported"""
    supported_worldadapters = ['MinecraftWorldadapter']

    assets = {
    'x': 2048,
    'y': 2048,
    }



    def __init__(self, filename, world_type="Minecraft", name="", owner="", uid=None, version=1):
        from micropsi_core.runtime import add_signal_handler
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
		    'plugins': plugins,
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
        add_signal_handler(self.kill_minecraft_thread)

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
        self.minecraft_communication_thread.join()
        self.spockplugin.threadpool.shutdown(False)


class MinecraftWorldadapter(WorldAdapter):

    datasources = {'diamond_offset_x': 0,
                   'diamond_offset_z': 0,
                   'grd_stone': 0,
                   'grd_dirt': 0,
                   'grd_wood': 0,
                   'grd_coal': 0,
                   'obstcl_x+': 0,
                   'obstcl_x-': 0,
                   'obstcl_z+': 0,
                   'obstcl_z-': 0}
    datatargets = {'move_x': 0,
                   'move_z': 0}


    def update(self):
        """called on every world simulation step to advance the life of the agent"""
        #find diamond
        bot_x = self.world.spockplugin.clientinfo.position['x']
        bot_y = self.world.spockplugin.clientinfo.position['y']
        bot_z = self.world.spockplugin.clientinfo.position['z']
        bot_coords = (bot_x, bot_y, bot_z)
        x_chunk = bot_x // 16
        z_chunk = bot_z // 16
        current_column = self.world.spockplugin.world.map.columns[(x_chunk, z_chunk)]
        current_section = current_column.chunks[int((bot_y - 1) // 16)]

        self.detect_groundtypes(bot_coords, current_section)
        self.detect_diamond(current_column, bot_coords, x_chunk, z_chunk)
        self.detect_obstacles(bot_coords, current_section)

        move_x = self.datatargets['move_x']
        move_z = self.datatargets['move_z']

        self.world.spockplugin.psi_dispatcher.dispatchPsiCommands(bot_coords, current_section, move_x, move_z)


    def detect_diamond(self, current_column, bot_coords, x_chunk, z_chunk):
        for y in range(0, 16):
            current_section = current_column.chunks[int((bot_coords[1] + y - 10 // 2) // 16)] #TODO explain formula
            if current_section != None:
                for x in range(0, 16):
                    for z in range(0, 16):
                        current_block = current_section.get(x, int((bot_coords[1] + y - 10 // 2) % 16), z).id #TODO explain formula
                        if current_block == 56:
                            diamond_coords = (x + x_chunk * 16,y,z + z_chunk * 16)
                            self.datasources['diamond_offset_x'] = bot_coords[0] - diamond_coords[0]
                            self.datasources['diamond_offset_z'] = bot_coords[2] - diamond_coords[2]


    def detect_groundtypes(self, bot_coords, current_section):
        block_below = current_section.get(int(bot_coords[0]) % 16, int((bot_coords[1] - 1) % 16), int(bot_coords[2]) % 16).id
        self.datasources['grd_dirt'] = 1 if (block_below == 2) else 0
        self.datasources['grd_stone'] = 1 if (block_below == 1) else 0
        self.datasources['grd_wood'] = 1 if (block_below == 17) else 0
        self.datasources['grd_coal'] = 1 if (block_below == 173) else 0


    def detect_obstacles(self, bot_coords, current_section):
        self.datasources['obstcl_x+'] = 1 if current_section.get(int(bot_coords[0] + 1) % 16, int((bot_coords[1] + 1) % 16), int(bot_coords[2]) % 16).id != 0 else 0
        self.datasources['obstcl_x-'] = 1 if current_section.get(int(bot_coords[0] - 1) % 16, int((bot_coords[1] + 1) % 16), int(bot_coords[2]) % 16).id != 0 else 0
        self.datasources['obstcl_z+'] = 1 if current_section.get(int(bot_coords[0]) % 16, int((bot_coords[1] + 1) % 16), int(bot_coords[2] + 1) % 16).id != 0 else 0
        self.datasources['obstcl_z-'] = 1 if current_section.get(int(bot_coords[0]) % 16, int((bot_coords[1] + 1) % 16), int(bot_coords[2] - 1) % 16).id != 0 else 0