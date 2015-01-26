from spock.mcp import mcpacket, mcdata

MOVEMENT_TICK = 1

class MovementPlugin:
    def __init__(self, ploader, settings):
        self.client_info = ploader.requires('ClientInfo')
        self.net = ploader.requires('Net')
        self.world = ploader.requires('World')
        self.timer = ploader.requires('Timers')
        self.timer.reg_event_timer(MOVEMENT_TICK, self.send_update, -1)

    def send_update(self, position=None):
        if not (self.net.connected and self.net.proto_state == mcdata.PLAY_STATE):
            return
        if position is None:
            position = self.client_info.position
        self.net.push(mcpacket.Packet(
            ident='PLAY>Player Position and Look',
            data=position
        ))
