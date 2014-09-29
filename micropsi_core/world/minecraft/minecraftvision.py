from micropsi_core.world.worldadapter import WorldAdapter
from micropsi_core.world.minecraft.minecraft_helpers import get_voxel_blocktype
from micropsi_core.world.minecraft import structs
import math

_SIDE_RELATION = 700/500
_HEIGHT = 10 # it starts to look super weird with values over 20 and I have no idea why
_WIDTH = int(_HEIGHT * _SIDE_RELATION)
_VIEW_ANGLE = 60

class MinecraftVision(WorldAdapter):

    datasources = {}
    datatargets = {'orientation': 0}


    def __init__(self, world, uid=None, **data):
        super(MinecraftVision, self).__init__(world, uid, **data)

        for x_pixel in range(-_WIDTH//2, _WIDTH//2):
            for y_pixel in range(_HEIGHT//2, -_HEIGHT//2, -1):
                self.datasources['vision_x_' + str(x_pixel) + '_y_' + str(y_pixel)] = 0

    def update(self):
        """called on every world simulation step to advance the life of the agent"""
        #find pixel

        bot_x = int(self.world.spockplugin.clientinfo.position['x'])
        y = int(self.world.spockplugin.clientinfo.position['y'] + 2)
        bot_z = int(self.world.spockplugin.clientinfo.position['z'])


        minecraft_vision_pixel = ()
        sighted_block = 0

        orientation = self.datatargets['orientation'] # x_axis + 360 / orientation  degrees

        for x_pixel in range(-_WIDTH//2, _WIDTH//2):
            for y_pixel in range(_HEIGHT//2, -_HEIGHT//2, -1):
                x_angle = x_pixel * _VIEW_ANGLE // -_HEIGHT
                x_angle = x_angle / 360
                y_angle = y_pixel * _VIEW_ANGLE // -_HEIGHT
                #x_blocks_per_distance = math.tan(x_angle)
                y_blocks_per_distance = math.tan(y_angle)
                sighted_block = 0
                distance = 0
                while sighted_block == 0:
                    sighted_block = get_voxel_blocktype(self, bot_x + int(distance * math.cos((orientation + x_angle) * 2 * math.pi)), y + int(y_blocks_per_distance * distance), bot_z + int(distance * math.sin((orientation + x_angle) * 2 * math.pi)))
                    distance += 1
                minecraft_vision_pixel = minecraft_vision_pixel + (structs.block_names[str(sighted_block)],  distance)
                self.datasources['vision_x_' + str(x_pixel) + '_y_' + str(y_pixel)] = 1 / distance if sighted_block > 0 else 0


        if self.world.data['agents'] is None:
            self.world.data['agents'] = {}
        if self.world.data['agents'][self.uid] is None:
            self.world.data['agents'][self.uid] = {}
        self.world.data['agents'][self.uid]['minecraft_vision_pixel'] = minecraft_vision_pixel



