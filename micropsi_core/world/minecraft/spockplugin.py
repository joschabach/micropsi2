import logging
from spock.mcmap import smpmap
from spock.mcp import mcdata, mcpacket
from spock.mcp.mcpacket import Packet
from spock.utils import pl_announce
from micropsi_core.world.minecraft.psidispatcher import PsiDispatcher, STANCE_ADDITION
from micropsi_core.world.minecraft.psidispatcher import PsiDispatcher, STANCE_ADDITION
from micropsi_core.world.minecraft.psidispatcher import PsiDispatcher, STANCE_ADDITION

@pl_announce('Micropsi')
class MicropsiPlugin(object):

    def __init__(self, ploader, settings):

        # register required plugins
        self.net        = ploader.requires('Net')
        self.event      = ploader.requires('Event')
        self.world      = ploader.requires('World')
        self.clientinfo = ploader.requires('ClientInfo')
        self.threadpool = ploader.requires('ThreadPool')
        
        # 
        self.event.reg_event_handler(
            'cl_position_update',
            self.subtract_stance
        )

        self.psi_dispatcher = PsiDispatcher(self)

        # make references between micropsi world and MicropsiPlugin
        self.micropsi_world = settings['micropsi_world']
        self.micropsi_world.spockplugin = self

    def move(self, position=None):

        if not (self.net.connected and self.net.proto_state == mcdata.PLAY_STATE):
            return
        # writes new data to clientinfo which is pulled and pushed to Minecraft by ClientInfoPlugin
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
