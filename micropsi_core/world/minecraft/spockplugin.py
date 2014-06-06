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
        self.world = ploader.requires('World')
        self.clientinfo = ploader.requires('ClientInfo')

        #MicroPsi Datatargets
        self.psi_dispatcher = PsiDispatcher(self)
        self.move_x = 0
        self.move_z = 0
        self.move_x_ = 0
        self.move_z_ = 0

    def move(self, position=None):
        if not (self.net.connected and self.net.proto_state == mcdata.PLAY_STATE):
            return
        if position is None:
            position = self.client_info.position
        self.net.push(mcpacket.Packet(
            ident='PLAY>Player Position and Look',
            data=position
        ))