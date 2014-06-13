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

        x = self.micropsiplugin.clientinfo.position['x']
        y = self.micropsiplugin.clientinfo.position['y']
        z = self.micropsiplugin.clientinfo.position['z']

        x_chunk = x // 16
        z_chunk = z // 16
        current_column = self.micropsiplugin.world.map.columns[(x_chunk, z_chunk)]
        current_section = current_column.chunks[int(y) // 16]

        move_x = self.micropsiplugin.move_x
        move_z = self.micropsiplugin.move_z

        target_coords = (self.normalize_coordinate(x + (STEP_LENGTH if (move_z < 0) else 0) + (-STEP_LENGTH if (move_z > 0) else 0)),
                         y,
                         self.normalize_coordinate(z + (STEP_LENGTH if (move_x < 0) else 0) + (-STEP_LENGTH if (move_x > 0) else 0)))

        self.move(target_coords, current_section)


    def move(self, target_coords, current_section):
            target_block_coords = (self.normalize_block_coordinate(target_coords[0]),
                                   self.normalize_block_coordinate(target_coords[1]),
                                   self.normalize_block_coordinate(target_coords[2]))

            ground_offset = 0
            for y in range(0,10): # TODO Hack - it should be 16!
                if current_section.get(target_block_coords[0], y, target_block_coords[2]).id != 0:
                    ground_offset = y+1

            self.micropsiplugin.move(position = {
                'x': target_coords[0],
                'y': target_coords[1] // 16 * 16 + ground_offset,
                #'y': target_coords[1],
                'z': target_coords[2],
                'yaw': self.micropsiplugin.clientinfo.position['yaw'],
                'pitch': self.micropsiplugin.clientinfo.position['pitch'],
                'on_ground': self.micropsiplugin.clientinfo.position['on_ground'],
                'stance': target_coords[1] // 16 * 16 + ground_offset + STANCE_ADDITION
                #'stance': target_coords[1] + STANCE_ADDITION
                })

    def normalize_coordinate(self, coordinate):
        return coordinate // 1 + 0.5

    def normalize_block_coordinate(self, coordinate):
        return int(coordinate // 1 % 16)