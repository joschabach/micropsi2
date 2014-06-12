from spock.mcp.mcpacket import Packet

__author__ = 'jonas'

STANCE_ADDITION = 1.620
STEP_LENGTH = 1.0
JUMPING_MAGIC_NUMBER = 0 # 2 used to work

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

        if self.micropsiplugin.move_z < 0:
            target_coords = ((self.micropsiplugin.clientinfo.position['x'] + STEP_LENGTH) // 1 + 0.5,
                              self.micropsiplugin.clientinfo.position['y'],
                              self.micropsiplugin.clientinfo.position['z'] // 1 + 0.5)
            self.move(target_coords, current_section, "z+")
        if self.micropsiplugin.move_z > 0:
            target_coords = ((self.micropsiplugin.clientinfo.position['x'] - STEP_LENGTH) // 1 + 0.5,
                              self.micropsiplugin.clientinfo.position['y'],
                              self.micropsiplugin.clientinfo.position['z'] // 1 + 0.5)
            self.move(target_coords, current_section, "z-")
        if self.micropsiplugin.move_x < 0:
            target_coords = (self.micropsiplugin.clientinfo.position['x'] // 1 + 0.5,
                              self.micropsiplugin.clientinfo.position['y'],
                              (self.micropsiplugin.clientinfo.position['z'] + STEP_LENGTH) // 1 + 0.5)
            self.move(target_coords, current_section, "x+")
        if self.micropsiplugin.move_x > 0:
            target_coords = (self.micropsiplugin.clientinfo.position['x'] // 1 + 0.5,
                              self.micropsiplugin.clientinfo.position['y'],
                              (self.micropsiplugin.clientinfo.position['z'] - STEP_LENGTH) // 1 + 0.5)
            self.move(target_coords, current_section, "x-")


    def move(self, target_coords, current_section, direction):
            if direction == "x+":
                target_block_coords = (int((1 * JUMPING_MAGIC_NUMBER * STEP_LENGTH + target_coords[0]) // 1 % 16),
                                       int(target_coords[1] // 1 % 16),
                                       int(target_coords[2] // 1 % 16))
            if direction == "x-":
                target_block_coords = (int((-1 * JUMPING_MAGIC_NUMBER * STEP_LENGTH + target_coords[0]) // 1 % 16),
                                       int(target_coords[1] // 1 % 16),
                                       int(target_coords[2] // 1 % 16))
            if direction == "z+":
                target_block_coords = (int(target_coords[0] // 1 % 16),
                                       int(target_coords[1] // 1 % 16),
                                       int((1 * JUMPING_MAGIC_NUMBER * STEP_LENGTH + target_coords[2]) // 1 % 16))
            if direction == "z-":
                target_block_coords = (int(target_coords[0] // 1 % 16),
                                       int(target_coords[1] // 1 % 16),
                                       int((-1 * JUMPING_MAGIC_NUMBER * STEP_LENGTH + target_coords[2]) // 1 % 16))

            target_block = current_section.get(*target_block_coords).id
            if target_block != 0:
                 #print("target_block != 0 ... preparing to jump!")
                 self.micropsiplugin.move(position = {
                'x': target_coords[0],
                'y': target_coords[1] + 1.0,
                'z': target_coords[2],
                'yaw': self.micropsiplugin.clientinfo.position['yaw'],
                'pitch': self.micropsiplugin.clientinfo.position['pitch'],
                'on_ground': self.micropsiplugin.clientinfo.position['on_ground'],
                'stance': target_coords[1] + 1.0 + STANCE_ADDITION
                })
            else:
                highest_ground = 0
                for y in range(0,16):
                    if (current_section.get(target_block_coords[0], y, target_block_coords[2]).id != 0):
                     highest_ground = y+1

                self.micropsiplugin.move(position = {
                    'x': target_coords[0],
                    'y': target_coords[1] // 16 * 16 + highest_ground,
                    'z': target_coords[2],
                    'yaw': self.micropsiplugin.clientinfo.position['yaw'],
                    'pitch': self.micropsiplugin.clientinfo.position['pitch'],
                    'on_ground': self.micropsiplugin.clientinfo.position['on_ground'],
                    'stance': target_coords[1] // 16 * 16 + highest_ground + STANCE_ADDITION
                    })