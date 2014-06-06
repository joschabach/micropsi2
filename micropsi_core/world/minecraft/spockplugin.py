import logging
from spock.mcp import mcdata, mcpacket
from spock.mcmap import smpmap
from micropsi_core.world.minecraft.psidispatcher import PsiDispatcher
from spock.utils import pl_announce

@pl_announce('Micropsi')
class MicropsiPlugin(object):

    def __init__(self, ploader, settings):

        self.worldadapter = settings['worldadapter']
        self.worldadapter.spockplugin = self

        self.net = ploader.requires('Net')
        ploader.reg_event_handler(
            mcdata.packet_idents['PLAY<Keep Alive'],
            self.handle_keepalive
        )

        self.event = ploader.requires('Event')
        self.event.reg_event_handler(
            'cl_position_update',
            self.handle_position_update
        )

        self.worldplugin = ploader.requires('World')
        self.event.reg_event_handler(
            'w_block_update',
            self.handle_block_update
        )

        #MicroPsi Datatargets
        self.psi_dispatcher = PsiDispatcher(self)
        self.move_x = 0
        self.move_z = 0
        self.move_x_ = 0
        self.move_z_ = 0

        #Game State variables
        #Plugins should read these (but generally not write)
        self.world = smpmap.World()
        self.world_time = {
            'world_age': 0,
            'time_of_day': 0,
        }
        self.position = {
            'x': 0,
            'y': 0,
            'z': 0,
            'stance': 0,
            'yaw': 0,
            'pitch': 0,
            'on_ground': False,
        }
        self.health = {
            'health': 20,
            'food': 20,
            'food_saturation': 5,
        }
        self.playerlist = {}
        self.entitylist = {}
        self.spawn_position = {
            'x': 0,
            'y': 0,
            'z': 0,
        }

    def handle_keepalive(self, name, packet):
        logging.getLogger("world").debug("Keep alive!")

    def handle_position_update(self, name, data):
        self.position = data

    def handle_block_update(self, name, data):
        if self.worldplugin:
            self.world = self.worldplugin.world.map