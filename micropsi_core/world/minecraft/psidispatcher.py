from spock.mcp.mcpacket import Packet

__author__ = 'jonas'

STANCE_ADDITION = 1.620

class PsiDispatcher():
    
    def __init__(self, micropsiplugin):
        self.micropsiplugin = micropsiplugin
        
    def dispatchPsiCommands(self):
        #check for MicroPsi input

        x_chunk = self.micropsiplugin.clientinfo.position['x'] // 16
        z_chunk = self.micropsiplugin.clientinfo.position['z'] // 16
        bot_block = (self.micropsiplugin.clientinfo.position['x'], self.micropsiplugin.clientinfo.position['y'], self.micropsiplugin.clientinfo.position['z'])
        current_column = self.micropsiplugin.world.map.columns[(x_chunk, z_chunk)]
        current_section = current_column.chunks[int((bot_block[1]) // 16)]
        if self.micropsiplugin.move_x > 0:
            current_block = current_section.get(int((self.micropsiplugin.clientinfo.position['x'] - 1)  // 1 % 16),
                                                              int(self.micropsiplugin.clientinfo.position['y'] // 1 % 16),
                                                              int(self.micropsiplugin.clientinfo.position['z'] // 1 % 16)).id
            if current_block == 0:
                self.micropsiplugin.move(position = {
                    'x': (self.micropsiplugin.clientinfo.position['x'] - 0.1),
                    'y': self.micropsiplugin.clientinfo.position['y'],
                    'z': self.micropsiplugin.clientinfo.position['z'],
                    'yaw': self.micropsiplugin.clientinfo.position['yaw'],
                    'pitch': self.micropsiplugin.clientinfo.position['pitch'],
                    'on_ground': self.micropsiplugin.clientinfo.position['on_ground'],
                    'stance': self.micropsiplugin.clientinfo.position['y'] + STANCE_ADDITION
                    })
        if self.micropsiplugin.move_x_ > 0:
            current_block = current_section.get(int((self.micropsiplugin.clientinfo.position['x'] + 1)  // 1 % 16),
                                                              int(self.micropsiplugin.clientinfo.position['y'] // 1 % 16),
                                                              int(self.micropsiplugin.clientinfo.position['z'] // 1 % 16)).id
            if current_block == 0:
                self.micropsiplugin.move(position = {
                    'x': (self.micropsiplugin.clientinfo.position['x'] + 0.1),
                    'y': self.micropsiplugin.clientinfo.position['y'],
                    'z': self.micropsiplugin.clientinfo.position['z'],
                    'yaw': self.micropsiplugin.clientinfo.position['yaw'],
                    'pitch': self.micropsiplugin.clientinfo.position['pitch'],
                    'on_ground': self.micropsiplugin.clientinfo.position['on_ground'],
                    'stance': self.micropsiplugin.clientinfo.position['y'] + STANCE_ADDITION
                    })
        if self.micropsiplugin.move_z > 0:
            current_block = current_section.get(int(self.micropsiplugin.clientinfo.position['x']  // 1 % 16),
                                                              int(self.micropsiplugin.clientinfo.position['y'] // 1 % 16),
                                                              int((self.micropsiplugin.clientinfo.position['z'] - 1) // 1 % 16)).id
            if current_block == 0:
                self.micropsiplugin.move(position = {
                    'x': (self.micropsiplugin.clientinfo.position['x']),
                    'y': self.micropsiplugin.clientinfo.position['y'],
                    'z': self.micropsiplugin.clientinfo.position['z'] - 0.1,
                    'yaw': self.micropsiplugin.clientinfo.position['yaw'],
                    'pitch': self.micropsiplugin.clientinfo.position['pitch'],
                    'on_ground': self.micropsiplugin.clientinfo.position['on_ground'],
                    'stance': self.micropsiplugin.clientinfo.position['y'] + STANCE_ADDITION
                    })
        if self.micropsiplugin.move_z_ > 0:
            current_block = current_section.get(int(self.micropsiplugin.clientinfo.position['x']  // 1 % 16),
                                                              int(self.micropsiplugin.clientinfo.position['y'] // 1 % 16),
                                                              int((self.micropsiplugin.clientinfo.position['z'] + 1) // 1 % 16)).id
            if current_block == 0:
                self.micropsiplugin.move(position = {
                    'x': (self.micropsiplugin.clientinfo.position['x']),
                    'y': self.micropsiplugin.clientinfo.position['y'],
                    'z': self.micropsiplugin.clientinfo.position['z'] + 0.1,
                    'yaw': self.micropsiplugin.clientinfo.position['yaw'],
                    'pitch': self.micropsiplugin.clientinfo.position['pitch'],
                    'on_ground': self.micropsiplugin.clientinfo.position['on_ground'],
                    'stance': self.micropsiplugin.clientinfo.position['y'] + STANCE_ADDITION
                    })