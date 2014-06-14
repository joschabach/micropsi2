__author__ = 'jonas'

STANCE_ADDITION = 1.620
STEP_LENGTH = 1.0
JUMPING_MAGIC_NUMBER = 0 # 2 used to work

class PsiDispatcher():
    
    def __init__(self, micropsiplugin):
        self.micropsiplugin = micropsiplugin


    def dispatchPsiCommands(self, bot_coords, current_section, move_x, move_z):

        target_coords = (self.normalize_coordinate(bot_coords[0] + (STEP_LENGTH if (move_x > 0) else 0) + (-STEP_LENGTH if (move_x < 0) else 0)),
                         bot_coords[1],
                         self.normalize_coordinate(bot_coords[2] + (STEP_LENGTH if (move_z > 0) else 0) + (-STEP_LENGTH if (move_z < 0) else 0)))

        self.move(target_coords, current_section)


    def move(self, target_coords, current_section):
        target_block_coords = (self.normalize_block_coordinate(target_coords[0]),
                               self.normalize_block_coordinate(target_coords[1]),
                               self.normalize_block_coordinate(target_coords[2]))
        ground_offset = 0
        for y in range(0,16):
            if current_section.get(target_block_coords[0], y, target_block_coords[2]).id != 0:
                ground_offset = y+1
        if target_coords[1] // 16 * 16 + ground_offset - target_coords[1] <= 1:
            self.micropsiplugin.move(position = {
                'x': target_coords[0],
                'y': target_coords[1] // 16 * 16 + ground_offset,
                'z': target_coords[2],
                'yaw': self.micropsiplugin.clientinfo.position['yaw'],
                'pitch': self.micropsiplugin.clientinfo.position['pitch'],
                'on_ground': self.micropsiplugin.clientinfo.position['on_ground'],
                'stance': target_coords[1] // 16 * 16 + ground_offset + STANCE_ADDITION
                })

    def normalize_coordinate(self, coordinate):
        return coordinate // 1 + 0.5

    def normalize_block_coordinate(self, coordinate):
        return int(coordinate // 1 % 16)