from threading import Thread

from spock.client import Client
from spock.plugins import DefaultPlugins
from spock.plugins.core.event import EventPlugin
from spock.plugins.helpers.clientinfo import ClientInfoPlugin
from spock.plugins.helpers.move import MovementPlugin
from spock.plugins.helpers.world import WorldPlugin
from spock.plugins.helpers.reconnect import ReConnectPlugin

from micropsi_core.world.world import World
from micropsi_core.world.worldadapter import WorldAdapter
from micropsi_core.world.minecraft.spockplugin import MicropsiPlugin
from micropsi_core.world.minecraft.minecraft_graph_locomotion import MinecraftGraphLocomotion
from micropsi_core.world.minecraft.minecraft_vision import MinecraftVision


class Minecraft(World):
    """
    mandatory: list of world adapters that are supported
    """
    supported_worldadapters = [
        'MinecraftWorldAdapter',
        'MinecraftBraitenberg',
        'MinecraftGraphLocomotion',
        "MinecraftVision"
    ]

    assets = {
        'template': 'minecraft/minecraft.tpl',
        'js': 'minecraft/minecraft.js',
        'x': 256,
        'y': 256,
    }

    # thread and spock only exist once
    instances = {
        'spock': None,
        'thread': None
    }

    def __init__(self, filename, world_type="Minecraft", name="", owner="", engine=None, uid=None, version=1):
        """
        Initializes spock client including MicropsiPlugin, starts minecraft communication thread.
        """
        from micropsi_core.runtime import add_signal_handler

        # do spock things first, then initialize micropsi world because the latter requires self.spockplugin

        # register all necessary spock plugins
        # DefaultPlugins contain EventPlugin, NetPlugin, TimerPlugin, AuthPlugin,
        # ThreadPoolPlugin, StartPlugin and KeepalivePlugin
        plugins = DefaultPlugins
        plugins.append(ClientInfoPlugin)
        plugins.append(MovementPlugin)
        plugins.append(WorldPlugin)
        plugins.append(MicropsiPlugin)
        plugins.append(ReConnectPlugin)

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

        # instantiate spock client if not yet done, which in turn instantiates its plugins
        # ( MicropsiPlugin sets self.spockplugin upon instantiation )
        if self.instances['spock'] is None:
            self.instances['spock'] = Client(plugins=plugins, settings=settings)

        if self.instances['thread'] is None:
            # start new thread for minecraft comm" which starts spock client
            thread = Thread(
                target=self.instances['spock'].start,
                args=(settings['server'], settings['port']))
            # Note: client.start() is attached in StartPlugin w/ setattr(self.client, 'start', self.start)
            thread.start()
            self.instances['thread'] = thread
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
            'username': cfg['minecraft']['username'],
            'password': cfg['minecraft']['password'],
            'authenticated': True if cfg['minecraft']['authenticated'] == 'True' else False,
            'bufsize': 4096,  # size of socket buffer
            'sock_quit': True,  # stop bot on socket error or hangup
            'sess_quit': True,  # stop bot on failed session login
            'thread_workers': 5,     # number of workers in the thread pool
            'packet_trace': False,
            'mc_username': "test",
            'mc_password': "test",
            'server': cfg['minecraft']['server'],
            'port': int(cfg['minecraft']['port'])
        }
        return settings

    def kill_minecraft_thread(self, *args):
        """
        """
        self.spockplugin.event.kill()
        self.instances['thread'].join()
        # self.spockplugin.threadpool.shutdown(False)


class Minecraft2D(Minecraft):
    """ mandatory: list of world adapters that are supported"""
    supported_worldadapters = [
        'MinecraftWorldAdapter',
        'MinecraftGraphLocomotion'
    ]

    assets = {
        'template': 'minecraft/minecraft.tpl',
        'js': 'minecraft/minecraft2d.js',
    }

    def step(self):
        """
        Is called on every world step to advance the simulation.
        """
        World.step(self)

        # a 2D perspective projection
        self.get_perspective_projection(self.spockplugin.clientinfo.position)

    def get_perspective_projection(self, agent_info):
        """
        """
        from math import sqrt
        from micropsi_core.world.minecraft import structs

        # specs
        focal_length = 1  # distance of image plane from projective point
        max_dist = 150    # maximum distance for raytracing
        resolution = 4    # camera resolution for a specific visual field
        im_width = 32     # width of projection /image plane
        im_height = 16    # height of projection /image plane
        cam_width = 1.    # width of viewport /camera coords
        cam_height = 1.   # height of viewport /camera coords

        # save parameters for frontend
        self.assets['width'] = im_width * resolution
        self.assets['height'] = im_height * resolution

        # get agent's position, yaw, and pitch
        position = (int(agent_info['x']), int(agent_info['y']), int(agent_info['z']))
        yaw = 360 - float(agent_info['yaw']) % 360    # given in degrees
        # check which yaw value is straight forward, potentially it's 90, ie. mc yaw + 90
        pitch = float(agent_info['pitch'])      # given in degrees

        # "Yaw is measured in degrees, and does not follow classical trigonometry rules. The unit circle of yaw on
        #  the XZ-plane starts at (0, 1) and turns counterclockwise, with 90 at (-1, 0), 180 at (0,-1) and 270 at
        #  (1, 0). Additionally, yaw is not clamped to between 0 and 360 degrees; any number is valid, including
        #  negative numbers and numbers greater than 360."

        # "Pitch is measured in degrees, where 0 is looking straight ahead,
        # -90 is looking straight up, and 90 is looking straight down. "

        # perspective of particular yaw values
        #   0 -
        #  90 -
        # 180 -
        # 270 -

        # perspective of particular pitch values
        #   0 - straight ahead
        #  90 - straight down
        # 180 - upside down straight backwards
        # 270 - straight up

        # span viewport
        tick_w = cam_width / im_width / resolution
        tick_h = cam_height / im_height / resolution
        # the horizontal plane is split half-half, the vertical plane is shifted upwards wrt the agent's position
        h_line = [i for i in self.frange(position[0] - 0.5 * cam_width, position[0] + 0.5 * cam_width, tick_w)]
        v_line = [i for i in self.frange(position[1] - 0.05 * cam_height, position[1] + 0.95 * cam_height, tick_h)]

        # compute pixel values of image plane
        projection = tuple()

        x0, y0, z0 = position   # agent's position aka projective point
        zi = z0 + focal_length

        for xi in reversed(h_line):
            for yi in reversed(v_line):

                distance = 0    # just a counter
                block_type = 0
                xb, yb, zb = xi, yi, zi

                # compute difference vector between projective point and image point
                diff = (xi - x0, yi - y0, zi - z0)

                # normalize difference vector
                magnitude = sqrt(diff[0] ** 2 + diff[1] ** 2 + diff[2] ** 2)
                if magnitude == 0.:
                    magnitude = 1.
                norm = (diff[0] / magnitude, diff[1] / magnitude, diff[2] / magnitude)

                # rotate norm vector
                norm = self.rotate_around_x_axis(norm, pitch)
                norm = self.rotate_around_y_axis(norm, yaw)

                # rotate diff vector
                diff = self.rotate_around_x_axis(diff, pitch)
                diff = self.rotate_around_y_axis(diff, yaw)

                # add diff to projection point aka agent's position
                xb, yb, zb = x0 + diff[0], y0 + diff[1], z0 + diff[2]

                while block_type <= 0:  # which is air

                    # check block type of next distance point along ray
                    # aka add normalized difference vector to image point
                    xb = xb + norm[0]
                    yb = yb + norm[1]
                    zb = zb + norm[2]

                    block_type = self.spockplugin.get_block_type(
                        int(xb),
                        int(yb),
                        int(zb),
                    )

                    distance += 1
                    if distance >= max_dist:
                        break

                # add block name, distance to projection plane
                # hm, if block_type unknown, expect an exception
                if structs.block_names.get(str(block_type)):
                    block_name = structs.block_names[str(block_type)]
                projection += (block_name, distance)

        self.data['projection'] = projection

    def rotate_around_x_axis(self, pos, angle):
        """ Rotate a 3D point around the x-axis given a specific angle. """
        from math import radians, cos, sin

        # convert angle in degrees to radians
        theta = radians(angle)

        # rotate vector
        x = pos[0]
        y = pos[1] * cos(theta) - pos[2] * sin(theta)
        z = pos[1] * sin(theta) + pos[2] * cos(theta)

        return (x, y, z)

    def rotate_around_y_axis(self, pos, angle):
        """ Rotate a 3D point around the y-axis given a specific angle. """
        from math import radians, cos, sin

        # convert angle in degrees to radians
        theta = radians(angle)

        # rotate vector
        x = pos[0] * cos(theta) + pos[2] * sin(theta)
        y = pos[1]
        z = - pos[0] * sin(theta) + pos[2] * cos(theta)

        return (x, y, z)

    def rotate_around_z_axis(self, pos, angle):
        """ Rotate a 3D point around the z-axis given a specific angle. """
        from math import radians, cos, sin

        # convert angle in degrees to radians
        theta = radians(angle)

        # rotate vector
        x = pos[0] * cos(theta) - pos[1] * sin(theta)
        y = pos[0] * sin(theta) + pos[1] * cos(theta)
        z = pos[2]

        return (x, y, z)

    def frange(self, start, end, step):
        """
        Range for floats.
        """
        while start < end:
            yield start
            start += step


class MinecraftWorldAdapter(WorldAdapter):
    """
    World adapter for a basic Minecraft agent that receives its xyz position and
    the ground type of the block it is standing on as sensory input, and randomly
    moves into one of the four cardinal directions ( until it dies ).
    """

    supported_datasources = ['x', 'y', 'z', 'yaw', 'pitch', 'groundtype']
    supported_datatargets = ['go_north', 'go_east', 'go_west', 'go_south', 'yaw', 'pitch']

    spawn_position = {
        'x': -105,
        'y': 63,
        'z': 59,
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

    def update_data_sources_and_targets(self):
        """ Advances the agent's life on every cycle of the world simulation. """
        import random

        # translate data targets
        self.position = (self.datasources['x'], self.datasources['y'], self.datasources['z'])

        movement = self.translate_datatargets_to_xz()

        # note: movement info is sent regardless of change
        self.world.spockplugin.dispatchMovement(movement[0], movement[1])

        position = self.world.spockplugin.clientinfo.position
        amp = random.choice([-4, -3, 2, 3, 4])
        position['yaw'] = (position['yaw'] + amp * self.datatargets['yaw']) % 360
        # not used yet but data target gets activation every once in a random while
        # position['pitch'] = (position['pitch'] + self.datatargets['pitch'])
        # position['pitch'] = 0
        self.world.spockplugin.move(position=position)

        # get new datasources
        self.datasources['x'] = self.world.spockplugin.clientinfo.position['x']
        self.datasources['y'] = self.world.spockplugin.clientinfo.position['y']
        self.datasources['z'] = self.world.spockplugin.clientinfo.position['z']
        self.datasources['yaw'] = self.world.spockplugin.clientinfo.position['yaw']
        self.datasources['pitch'] = self.world.spockplugin.clientinfo.position['pitch']
        self.datasources['groundtype'] = self.get_groundtype()

    def translate_datatargets_to_xz(self):
        """ Translates movements in cardinal directions to x,z coordinates. """

        # Reminder: x increases East, decreases West,
        #           z increases South, decreases North
        x, z = 0., 0.
        if self.datatargets['go_north'] > 0:
            z = -1.
        elif self.datatargets['go_east'] > 0:
            x = 1.
        elif self.datatargets['go_south'] > 0:
            z = 1.
        elif self.datatargets['go_west'] > 0:
            x = -1.
        return (x, z)

    def get_groundtype(self):
        """
        """
        try:
            groundtype = self.world.spockplugin.get_block_type(
                int(self.datasources['x']),
                int(self.datasources['y'] - 1),
                int(self.datasources['z']))

        except AttributeError:
            groundtype = None

        return groundtype


class MinecraftBraitenberg(WorldAdapter):

    supported_datasources = [
        'diamond_offset_x',
        'diamond_offset_z',
        'grd_stone',
        'grd_dirt',
        'grd_wood',
        'grd_coal',
        'obstcl_x+',
        'obstcl_x-',
        'obstcl_z+',
        'obstcl_z-'
    ]
    supported_datatargets = [
        'move_x',
        'move_z'
    ]

    def update_data_sources_and_targets(self):
        """called on every world simulation step to advance the life of the agent"""
        # find diamond
        bot_x = self.world.spockplugin.clientinfo.position['x']
        bot_y = self.world.spockplugin.clientinfo.position['y']
        bot_z = self.world.spockplugin.clientinfo.position['z']
        bot_coords = (bot_x, bot_y, bot_z)
        x_chunk = bot_x // 16
        z_chunk = bot_z // 16

        current_column = self.world.spockplugin.world.columns[(x_chunk, z_chunk)]
        current_section = current_column.chunks[int((bot_y - 1) // 16)]

        self.detect_groundtypes(bot_coords, current_section)
        self.detect_diamond(current_column, bot_coords, x_chunk, z_chunk)
        self.detect_obstacles(bot_coords, current_section)

        move_x = self.datatargets['move_x']
        move_z = self.datatargets['move_z']
        self.world.spockplugin.psi_dispatcher.dispatchPsiCommands(bot_coords, current_section, move_x, move_z)

    def detect_diamond(self, current_column, bot_coords, x_chunk, z_chunk):
        for y in range(0, 16):
            current_section = current_column.chunks[int((bot_coords[1] + y - 10 // 2) // 16)]  # TODO explain formula
            if current_section is not None:
                for x in range(0, 16):
                    for z in range(0, 16):
                        # TODO explain formula
                        current_block = current_section.get(x, int((bot_coords[1] + y - 10 // 2) % 16), z).id
                        if current_block == 56:
                            diamond_coords = (x + x_chunk * 16, y, z + z_chunk * 16)
                            self.datasources['diamond_offset_x'] = bot_coords[0] - diamond_coords[0]
                            self.datasources['diamond_offset_z'] = bot_coords[2] - diamond_coords[2]

    def detect_groundtypes(self, bot_coords, current_section):
        block_below = current_section.get(
            int(bot_coords[0]) % 16,
            int((bot_coords[1] - 1) % 16),
            int(bot_coords[2]) % 16).id
        self.datasources['grd_dirt'] = 1 if (block_below == 2) else 0
        self.datasources['grd_stone'] = 1 if (block_below == 1) else 0
        self.datasources['grd_wood'] = 1 if (block_below == 17) else 0
        self.datasources['grd_coal'] = 1 if (block_below == 173) else 0

    def detect_obstacles(self, bot_coords, current_section):
        self.datasources['obstcl_x+'] = \
            1 if current_section.get(
                int(bot_coords[0] + 1) % 16,
                int((bot_coords[1] + 1) % 16),
                int(bot_coords[2]) % 16).id != 0 \
            else 0
        self.datasources['obstcl_x-'] = \
            1 if current_section.get(
                int(bot_coords[0] - 1) % 16,
                int((bot_coords[1] + 1) % 16),
                int(bot_coords[2]) % 16).id != 0 \
            else 0
        self.datasources['obstcl_z+'] = \
            1 if current_section.get(
                int(bot_coords[0]) % 16,
                int((bot_coords[1] + 1) % 16),
                int(bot_coords[2] + 1) % 16).id != 0 \
            else 0
        self.datasources['obstcl_z-'] = \
            1 if current_section.get(
                int(bot_coords[0]) % 16,
                int((bot_coords[1] + 1) % 16),
                int(bot_coords[2] - 1) % 16).id != 0 \
            else 0
