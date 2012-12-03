from micropsi_core.world.world import World

import json
import os
import png


class Island(World):

    """ mandatory: list of world adapters that are supported"""
    supported_worldadapters = ['Braitenberg']

    groundmap = {
        'image': "psi_1.png",
        'startpos': (100, 100),
        'scaling': (500, 500)
    }

    assets = {
        'background': "island/background.jpg",
        'js': "island/island.js"
    }

    def __init__(self, runtime, filename, world_type="Island", name="", owner="", uid=None, version=1):
        World.__init__(self, runtime, filename, world_type=world_type, name=name, owner=owner, uid=uid, version=version)
        self.load_groundmap()
        self.current_step = 0
        self.load_json_data()

    def load_json_data(self):
        filename = os.path.join(os.path.dirname(__file__), 'resources', 'island.json')
        with open(filename) as file:
            self.world_objects = json.load(file)

    def load_groundmap(self):
        """
        Imports a groundmap for an island world from a png file. We expect a bitdepth of 8 (i.e. each pixel defines
        a point with one of 256 possible values).
        """
        filename = os.path.join(os.path.dirname(__file__), 'resources', 'groundmaps', self.groundmap["image"])
        with open(filename) as file:
            png_reader = png.Reader(file)
            x, y, image_array, image_params = png_reader.read()
            self.ground_data = list(image_array)
            self.x_max = x-1
            self.y_max = y-1
            self.scale_x = float(x) / self.groundmap["scaling"][0]
            self.scale_y = float(y) / self.groundmap["scaling"][1]

    def get_ground_at(self, x, y):
        """
        returns the ground type (an integer) at the given position
        """
        _x = min(self.x_max, max(0, round(x*self.scale_x)))
        _y = min(self.y_max, max(0, round(y*self.scale_y)))
        return self.ground_data[_y][_x]

    def step(self):
        """ overwrite world.step """
        ret = super(Island, self).step()
        return ret
