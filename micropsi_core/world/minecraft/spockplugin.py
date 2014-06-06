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
        self.event = ploader.requires('Event')
        self.worldplugin = ploader.requires('World')

        #MicroPsi Datatargets
        self.psi_dispatcher = PsiDispatcher(self)
        self.move_x = 0
        self.move_z = 0
        self.move_x_ = 0
        self.move_z_ = 0

        #Game State variables
        #Plugins should read these (but generally not write)
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

        self.worldset = False

    def move(self, position=None):
        if not (self.net.connected and self.net.proto_state == mcdata.PLAY_STATE):
            return
        if position is None:
            position = self.client_info.position
        self.net.push(mcpacket.Packet(
            ident='PLAY>Player Position and Look',
            data=position
        ))