"""
This plugin creates a convenient start() method and attaches it directly
to the client. More complex bots will likely want to create their own
initialization plugin, so StartPlugin stays out of the way unless you
call the start() method. However, the start() method is very convenient
for demos and tutorials, and illustrates the basic steps for initializing
a bot.
"""
from spock.mcp.mcpacket import Packet

from spock.mcp import mcpacket, mcdata

class StartPlugin:
    def __init__(self, ploader, settings):
        self.event = ploader.requires('Event')
        self.settings = ploader.requires('Settings')
        self.client = ploader.requires('Client')
        self.net = ploader.requires('Net')
        self.auth = ploader.requires('Auth')

        self.event.reg_event_handler(mcdata.packet_idents['PLAY<Spawn Position'], self.initial_spawn)

        setattr(self.client, 'start', self.start)

    def start(self, host = 'localhost', port = 25565):
        if 'error' not in self.auth.start_session(
            self.settings['mc_username'],
            self.settings['mc_password']
        ):
            self.net.connect(host, port)
            self.handshake()
            self.login_start()
            self.event.event_loop()

    def handshake(self):
        self.net.push(mcpacket.Packet(
            ident='HANDSHAKE>Handshake',
            data = {
                'protocol_version': mcdata.MC_PROTOCOL_VERSION,
                'host': self.net.host,
                'port': self.net.port,
                'next_state': mcdata.LOGIN_STATE
            }
        ))

    def login_start(self):
        self.net.push(mcpacket.Packet(
            ident='LOGIN>Login Start',
            data = {'name': self.auth.username},
        ))

    # Initial spawn only
    def initial_spawn(self, name, event):
        self.event.unreg_event_handler(mcdata.packet_idents['PLAY<Spawn Position'], self.initial_spawn)
        self.net.push(Packet(ident='PLAY>Client Settings', data={'locale': 'en_US',
                                                                 'view_distance': 12,
                                                                 'chat_flags': 0,
                                                                 'chat_colors': 1,
                                                                 'difficulty': 0,
                                                                 'show_cape': 1}))
        self.net.push(Packet(ident='PLAY>Client Status', data={'action': 0}))
