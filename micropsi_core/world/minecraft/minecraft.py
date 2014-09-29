import warnings
from threading import Thread
import configparser

from spock.client import Client
from spock.plugins import DefaultPlugins
from spock.plugins.core.event import EventPlugin
from spock.plugins.helpers.clientinfo import ClientInfoPlugin
from spock.plugins.helpers.move import MovementPlugin
from spock.plugins.helpers.world import WorldPlugin

from micropsi_core.world.world import World
from micropsi_core.world.worldadapter import WorldAdapter
from micropsi_core.world.minecraft.spockplugin import MicropsiPlugin
from micropsi_core.world.minecraft.minecraftvision import MinecraftVision


class Minecraft(World):
    """    
    mandatory: list of world adapters that are supported
    """
    supported_worldadapters = ['MinecraftWorldAdapter', 'MinecraftBraitenberg', 'MinecraftVision']

    assets = {
        'template': 'minecraft/minecraft.tpl',
        'js': "minecraft/minecraft.js",
        'x': 256,
        'y': 256,
    }

    def __init__(self, filename, world_type="Minecraft", name="", owner="", uid=None, version=1):
        """
        Initializes spock client including MicropsiPlugin, starts minecraft communication thread.
        """
        from micropsi_core.runtime import add_signal_handler

        # do spock things first, then initialize micropsi world because the latter requires self.spockplugin
        
        # register all necessary spock plugins
        plugins = DefaultPlugins    # contains EventPlugin, NetPlugin, TimerPlugin, AuthPlugin
                                    # ThreadPoolPlugin, StartPlugin and KeepalivePlugin
        plugins.append(ClientInfoPlugin)
        plugins.append(MovementPlugin)
        plugins.append(WorldPlugin)
        plugins.append(MicropsiPlugin)

        # get spock configs
        settings = self.get_config()
        
        # add plugin-specific settings
        settings['plugins'] = plugins
        settings['plugin_settings'] = {
            MicropsiPlugin: {
                "micropsi_world": self
            },
            EventPlugin: {
                "killsignals": False
            }
        }
        
        # instantiate spock client, which in turn instantiates its plugins
        # ( MicropsiPlugin sets self.spockplugin upon instantiation )
        spock_client = Client(plugins=plugins, settings=settings)
        # start new thread for minecraft comm" which starts spock client
        self.minecraft_communication_thread = Thread(
            target=spock_client.start, 
            args=(settings['server'], settings['port']))
        # Note: client.start() is attached in StartPlugin w/ setattr(self.client, 'start', self.start)
        self.minecraft_communication_thread.start()
        # 
        add_signal_handler(self.kill_minecraft_thread)

        # once MicropsiPlugin is instantiated and running, initialize micropsi world
        World.__init__(self, filename, world_type=world_type, name=name, owner=owner, uid=uid, version=version)

        # make data accessible to frontend
        self.data['assets'] = self.assets

        # copied from jonas' code as is
        self.current_step = 0
        self.first_step = True
        self.chat_ping_counter = 0
        self.the_image = None

    def get_config(self):
        """
        Collect config settings required by spock /minecraft as specified in 
        config.ini.
        """
        from configuration import config as cfg

        settings = {
            'username':             cfg['minecraft']['username'],
            'password':             cfg['minecraft']['password'],
            'authenticated':        True if cfg['minecraft']['authenticated'] == 'True' else False,
            'bufsize':              4096, # size of socket buffer
            'sock_quit':            True, # stop bot on socket error or hangup
            'sess_quit':            True, # stop bot on failed session login
            'thread_workers':       5,    # number of workers in the thread pool
            'packet_trace':         False,
            'mc_username':          "test",
            "mc_password":          "test",
            'server':               cfg['minecraft']['server'],
            'port':                 int(cfg['minecraft']['port'])
        }
        return settings 

    def kill_minecraft_thread(self, *args):
        """
        """
        self.spockplugin.event.kill()
        self.minecraft_communication_thread.join()
        self.spockplugin.threadpool.shutdown(False)


class Minecraft2D(Minecraft):
    """ mandatory: list of world adapters that are supported"""
    supported_worldadapters = ['MinecraftWorldAdapter']

    assets = {
        'template': 'minecraft/minecraft.tpl',
        'js': "minecraft/minecraft2d.js",
        'x': 800,
        'y': 600,
        'height': 20
    }

    def step(self):
        """
        Is called on every world step to advance the simulation.
        """
        World.step(self)
        self.project_and_render(self.spockplugin.world.map.columns, self.spockplugin.clientinfo.position)

    def project_and_render(self, columns, agent_info):
        """ """
        import math
        from micropsi_core.world.minecraft import structs

        # "Yaw is measured in degrees, and does not follow classical trigonometry rules. The unit circle of yaw on 
        #  the XZ-plane starts at (0, 1) and turns counterclockwise, with 90 at (-1, 0), 180 at (0,-1) and 270 at 
        #  (1, 0). Additionally, yaw is not clamped to between 0 and 360 degrees; any number is valid, including 
        #  negative numbers and numbers greater than 360."

        # "Pitch is measured in degrees, where 0 is looking straight ahead, -90 is looking straight up, and 90 is 
        #  looking straight down. "

        side_relation   = self.assets['x'] / self.assets['y']
        height          = self.assets['height']
        width           = int(height * side_relation)
        
        self.data['misc'] = { 'side_relation': side_relation, 'height': height, 'width': width }

        x       = int(agent_info['x'])
        y       = int(agent_info['y'] + 2)  # +2 to move reference point to head ?
        z       = int(agent_info['z'])
        yaw     = agent_info['yaw']         # rotation on the x axis, in degrees 
        pitch   = agent_info['pitch']       # rotation on the y axis, in degrees

        projection = ()
        intersection = 0

        # orientation = self.datatargets['orientation'] # x_axis + 360 / orientation  degrees
        # currently: orientation = yaw #TOOD: fix this.

        # get agent's coordinates and orientation
        fpoint = (x,y,z)    # focal point

        # for every pixel in the image plane
        for x_pixel in range( -width//2, width//2 ):
            for y_pixel in range( height//2, -height//2, -1 ):

                # 
                x_angle = x_pixel * pitch // -height
                x_angle = x_angle / 360
                y_angle = y_pixel * pitch // -height

                # x_blocks_per_distance = math.tan(x_angle)
                y_blocks_per_distance = math.tan(y_angle)
                
                intersection = 0
                distance = 0
                
                # while the intersecting block is of type air, get next block
                while intersection == 0:
                
                    intersection = self.get_blocktype(
                        x + int( distance * math.cos(( yaw + x_angle ) * 2 * math.pi )), 
                        y + int( y_blocks_per_distance * distance ), 
                        z + int( distance * math.sin(( yaw + x_angle ) * 2 * math.pi )))
                
                    distance += 1
                
                projection = projection + (structs.block_names[str(intersection)],  distance)

        self.data['projection'] = projection

    def get_blocktype(self, x, y, z):
        """ """
        key = (x // 16, z // 16)
        columns = self.spockplugin.world.map.columns
        if key not in columns:
            return -1
        current_column = columns[key]
        if len(current_column.chunks) <= y // 16:
            return -1
        try:
            current_section = current_column.chunks[y // 16]
        except IndexError:
            return -1
        if current_section is None:
            return -1
        else:
            return current_section.get(x % 16, y % 16, z % 16).id


class MinecraftWorldAdapter(WorldAdapter):
    """
    World adapter for a basic Minecraft agent that receives its xyz position and 
    the ground type of the block it is standing on as sensory input, and randomly 
    moves into one of the four cardinal directions ( until it dies ).
    """

    datasources = {
        'x':            0.,  # increases East, decreases West
        'y':            0.,  # increases upwards, decreases downwards
        'z':            0.,  # increases South, decreases North
        'yaw':          0.,
        'pitch':        0.,
        'groundtype':   0,
    }
    datatargets = {
        'go_north':     0.,
        'go_east':      0.,
        'go_west':      0.,
        'go_south':     0.,
        'yaw':          0.,
        'pitch':        0.,
    }
    spawn_position = {
        'x':         -105,
        'y':           63,
        'z':           59,
    }

    def __init__(self, world, uid=None, **data):
        world.spockplugin.clientinfo.spawn_position = self.spawn_position
        WorldAdapter.__init__(self, world, uid=uid, **data)

    def initialize_worldobject(self, data):
        
        self.datasources['x'] = self.world.spockplugin.clientinfo.position['x']
        self.datasources['y'] = self.world.spockplugin.clientinfo.position['y']
        self.datasources['z'] = self.world.spockplugin.clientinfo.position['z']
        self.datasources['yaw'] = self.world.spockplugin.clientinfo.position['yaw']
        self.datasources['pitch'] = self.world.spockplugin.clientinfo.position['pitch']
        self.datasources['groundtype'] = self.get_groundtype()
        
    def update(self):
        """ Advances the agent's life on every cycle of the world simulation. """

        # translate data targets
        self.position = (self.datasources['x'], self.datasources['y'], self.datasources['z'])
        section = self.get_current_section()
        if section:
            movement = self.translate_datatargets_to_xz()
            # change the next line, don't use PsiDispatcher, use MicropsiPlugin instead
            self.world.spockplugin.psi_dispatcher.dispatchPsiCommands(self.position, section, movement[0], movement[1])

        position = self.world.spockplugin.clientinfo.position
        position['yaw'] = self.datatargets['yaw']
        position['pitch'] = self.datatargets['pitch']
        # to look around, change yaw; eg. position['yaw'] = (self.datatargets['yaw'] + 5) % 360
        # to look up and down, change pitch; 
        # eg. sign = lambda x: (1, -1)[x<0] or sign = lambda x: x and (1, -1)[x<0] and
        # position['pitch'] = (self.datatargets['pitch'] + 5) % 90 * sign(self.datatargets['pitch'])

        self.world.spockplugin.psi_dispatcher.micropsiplugin.move(position=position)

        # get new datasources
        self.datasources['x'] = self.world.spockplugin.clientinfo.position['x']
        self.datasources['y'] = self.world.spockplugin.clientinfo.position['y']
        self.datasources['z'] = self.world.spockplugin.clientinfo.position['z']
        self.datasources['yaw'] = self.world.spockplugin.clientinfo.position['yaw']
        self.datasources['pitch'] = self.world.spockplugin.clientinfo.position['pitch']
        self.datasources['groundtype'] = self.get_groundtype()

    def get_current_section(self):
        """ Given a yzx position returns the current section. """

        try:

            chunk_x = self.datasources['x'] // 16
            chunk_z = self.datasources['z'] // 16
            column  = self.world.spockplugin.world.map.columns[(chunk_x, chunk_z)]
            section = column.chunks[int((self.datasources['y'] - 1) // 16)]
        
        except KeyError:

            section = None

        return section

    def translate_datatargets_to_xz(self):
        """ Translates movements in cardinal directions to x,z coordinates. """
        
        # Reminder: x increases East, decreases West; z increases South, decreases North
        x, z = 0., 0.
        if self.datatargets['go_north'] > 0:
            z = -1.
        elif self.datatargets['go_east'] > 0:
            x =  1.
        elif self.datatargets['go_south'] > 0:
            z =  1.
        elif self.datatargets['go_west'] > 0:
            x = -1.
        return (x,z)

    def get_groundtype(self):
        """
        """
        try:

            section = self.get_current_section()
            groundtype = section.get(int(self.datasources['x']) % 16, \
                int((self.datasources['y'] - 1) % 16), int(self.datasources['z']) % 16).id

        except AttributeError:

            groundtype = None
        
        return groundtype


class MinecraftBraitenberg(WorldAdapter):

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
        self.datasources['obstcl_x+'] = \
            1 if current_section.get(int(bot_coords[0] + 1) % 16, int((bot_coords[1] + 1) % 16), int(bot_coords[2]) % 16).id != 0 \
            else 0
        self.datasources['obstcl_x-'] = \
            1 if current_section.get(int(bot_coords[0] - 1) % 16, int((bot_coords[1] + 1) % 16), int(bot_coords[2]) % 16).id != 0 \
            else 0
        self.datasources['obstcl_z+'] = \
            1 if current_section.get(int(bot_coords[0]) % 16, int((bot_coords[1] + 1) % 16), int(bot_coords[2] + 1) % 16).id != 0 \
            else 0
        self.datasources['obstcl_z-'] = \
            1 if current_section.get(int(bot_coords[0]) % 16, int((bot_coords[1] + 1) % 16), int(bot_coords[2] - 1) % 16).id != 0 \
            else 0

