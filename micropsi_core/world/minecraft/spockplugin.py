import logging
from spock.mcp import mcdata, mcpacket
from spock.mcmap import smpmap
from micropsi_core.world.minecraft.psidispatcher import PsiDispatcher, STANCE_ADDITION
from spock.mcp.mcpacket import Packet
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
        self.threadpool = ploader.requires('ThreadPool')
        self.event.reg_event_handler(
            'cl_position_update',
            self.subtract_stance
        )

        self.psi_dispatcher = PsiDispatcher(self)

    def move(self, position=None):
        if not (self.net.connected and self.net.proto_state == mcdata.PLAY_STATE):
            return
        self.clientinfo.position = position

    def chat(self, message):
        self.net.push(Packet(ident='PLAY>Chat Message', data={'message': message}))

    def subtract_stance(self, name, packet):
        # this is to correctly calculate a y value -- the server seems to deliver the value with stance addition,
        # but for movements it will have to be sent without (the "foot" value).
        # Movements sent with stance addition (eye values sent as foot values) will be silently discarded
        # by the server as impossible, which is undesirable.
        self.clientinfo.position['stance'] = self.clientinfo.position['y']
        self.clientinfo.position['y'] = self.clientinfo.position['y'] - STANCE_ADDITION
