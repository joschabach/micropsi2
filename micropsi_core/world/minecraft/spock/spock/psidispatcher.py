from micropsi_core.world.minecraft.spock.spock.mcp.mcpacket import Packet

__author__ = 'jonas'

class PsiDispatcher():
    
    def __init__(self, client):
        self.client = client
        
    def dispatchPsiCommands(self):
        #check for MicroPsi input

        x_chunk = self.client.position['x'] // 16
        z_chunk = self.client.position['z'] // 16
        bot_block = (self.client.position['x'], self.client.position['y'], self.client.position['z'])
        #if x_chunk != 0:
        #    current_column = self.client.world.columns[(x_chunk, z_chunk)]
        #    current_section = current_column.chunks[int((bot_block[1] + y - 10 // 2) // 16)]
        #if self.client.move_x > 0:
        #    current_block = current_section['block_data'].get((self.client.position['x'] - 1)  // 1, self.client.position['y'] // 1, self.client.position['z'] // 1)
        #    if current_block == 0:
        #        self.client.push(Packet(ident = 0x0B, data = {
        #            'x': (self.client.position['x'] - 1)  // 1,
        #            'y': self.client.position['y'] // 1,
        #            'z': self.client.position['z'] // 1,
        #            'on_ground': False,
        #            'stance': self.client.position['y'] + 0.11
        #            }))
        #if self.client.move_x_ > 0:
        #    current_block = current_section['block_data'].get((self.client.position['x'] + 1)  // 1, self.client.position['y'] // 1, self.client.position['z'] // 1)
        #    if current_block == 0:
        #        self.client.push(Packet(ident = 0x0B, data = {
        #            'x': (self.client.position['x'] + 1)  // 1,
        #            'y': self.client.position['y'] // 1,
        #            'z': self.client.position['z'] // 1,
        #            'on_ground': False,
        #            'stance': self.client.position['y'] + 0.11
        #            }))
        #if self.client.move_z > 0:
        #    current_block = current_section['block_data'].get(self.client.position['x']  // 1, self.client.position['y'] // 1, (self.client.position['z'] - 1) // 1)
        #    if current_block == 0:
        #        self.client.push(Packet(ident = 0x0B, data = {
        #            'x': (self.client.position['x']) // 1,
        #            'y': self.client.position['y'] // 1,
        #            'z': self.client.position['z'] - 1 // 1,
        #            'on_ground': False,
        #            'stance': self.client.position['y'] + 0.11
        #            }))
        #if self.client.move_z_ > 0:
        #    current_block = current_section['block_data'].get(self.client.position['x']  // 1, self.client.position['y'] // 1, (self.client.position['z'] + 1) // 1)
        #    if current_block == 0:
        #        self.client.push(Packet(ident = 0x0B, data = {
        #            'x': (self.client.position['x'])  // 1,
        #            'y': self.client.position['y'] // 1,
        #            'z': self.client.position['z'] + 1 // 1,
        #            'on_ground': False,
        #            'stance': self.client.position['y'] + 0.11
        #            }))