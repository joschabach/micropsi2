from micropsi_core.world.minecraft.spock.spock.mcp.mcpacket import Packet

__author__ = 'jonas'

class PsiDispatcher():
    
    def __init__(self, client):
        self.client = client
        
    def dispatchPsiCommands(self):
        #check for MicroPsi input
            if self.client.move_x > 0:
                self.client.push(Packet(ident = 0x0B, data = {
                    'x': (self.client.position['x'] - 1)  // 1,
                    'y': self.client.position['y'] // 1,
                    'z': self.client.position['z'] // 1,
                    'on_ground': False,
                    'stance': self.client.position['y'] + 0.11
                    }))
            if self.client.move_x < 0:
                self.client.push(Packet(ident = 0x0B, data = {
                    'x': (self.client.position['x'] + 1)  // 1,
                    'y': self.client.position['y'] // 1,
                    'z': self.client.position['z'] // 1,
                    'on_ground': False,
                    'stance': self.client.position['y'] + 0.11
                    }))
            if self.client.move_z > 0:
                self.client.push(Packet(ident = 0x0B, data = {
                    'x': (self.client.position['x']) // 1,
                    'y': self.client.position['y'] // 1,
                    'z': self.client.position['z'] - 1 // 1,
                    'on_ground': False,
                    'stance': self.client.position['y'] + 0.11
                    }))
            if self.client.move_z < 0:
                self.client.push(Packet(ident = 0x0B, data = {
                    'x': (self.client.position['x'])  // 1,
                    'y': self.client.position['y'] // 1,
                    'z': self.client.position['z'] + 1 // 1,
                    'on_ground': False,
                    'stance': self.client.position['y'] + 0.11
                    }))