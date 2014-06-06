from spock.mcp.mcpacket import Packet

__author__ = 'jonas'

class PsiDispatcher():
    
    def __init__(self, micropsiplugin):
        self.micropsiplugin = micropsiplugin
        
    def dispatchPsiCommands(self):
        #check for MicroPsi input

        x_chunk = self.micropsiplugin.position['x'] // 16
        z_chunk = self.micropsiplugin.position['z'] // 16
        bot_block = (self.micropsiplugin.position['x'], self.micropsiplugin.position['y'], self.micropsiplugin.position['z'])
        current_column = self.micropsiplugin.world.columns[(x_chunk, z_chunk)]
        current_section = current_column.chunks[int((bot_block[1]) // 16)]
        if self.micropsiplugin.move_x > 0:
            current_block = current_section['block_data'].get(int((self.micropsiplugin.position['x'] - 1)  // 1 % 16),
                                                              int(self.micropsiplugin.position['y'] // 1 % 16),
                                                              int(self.micropsiplugin.position['z'] // 1 % 16))
            if current_block == 0:
                self.micropsiplugin.net.push(Packet(ident = 0x0B, data = {
                    'x': (self.micropsiplugin.position['x'] - 1)  // 1,
                    'y': self.micropsiplugin.position['y'] // 1,
                    'z': self.micropsiplugin.position['z'] // 1,
                    'on_ground': False,
                    'stance': self.micropsiplugin.position['y'] + 0.11
                    }))
        if self.micropsiplugin.move_x_ > 0:
            current_block = current_section['block_data'].get(int((self.micropsiplugin.position['x'] + 1)  // 1 % 16),
                                                              int(self.micropsiplugin.position['y'] // 1 % 16),
                                                              int(self.micropsiplugin.position['z'] // 1 % 16))
            if current_block == 0:
                self.micropsiplugin.net.push(Packet(ident = 0x0B, data = {
                    'x': (self.micropsiplugin.position['x'] + 1)  // 1,
                    'y': self.micropsiplugin.position['y'] // 1,
                    'z': self.micropsiplugin.position['z'] // 1,
                    'on_ground': False,
                    'stance': self.micropsiplugin.position['y'] + 0.11
                    }))
        if self.micropsiplugin.move_z > 0:
            current_block = current_section['block_data'].get(int(self.micropsiplugin.position['x']  // 1 % 16),
                                                              int(self.micropsiplugin.position['y'] // 1 % 16),
                                                              int((self.micropsiplugin.position['z'] - 1) // 1 % 16))
            if current_block == 0:
                self.micropsiplugin.net.push(Packet(ident = 0x0B, data = {
                    'x': (self.micropsiplugin.position['x']) // 1,
                    'y': self.micropsiplugin.position['y'] // 1,
                    'z': self.micropsiplugin.position['z'] - 1 // 1,
                    'on_ground': False,
                    'stance': self.micropsiplugin.position['y'] + 0.11
                    }))
        if self.micropsiplugin.move_z_ > 0:
            current_block = current_section['block_data'].get(int(self.micropsiplugin.position['x']  // 1 % 16),
                                                              int(self.micropsiplugin.position['y'] // 1 % 16),
                                                              int((self.micropsiplugin.position['z'] + 1) // 1 % 16))
            if current_block == 0:
                self.micropsiplugin.net.push(Packet(ident = 0x0B, data = {
                    'x': (self.micropsiplugin.position['x'])  // 1,
                    'y': self.micropsiplugin.position['y'] // 1,
                    'z': self.micropsiplugin.position['z'] + 1 // 1,
                    'on_ground': False,
                    'stance': self.micropsiplugin.position['y'] + 0.11
                    }))