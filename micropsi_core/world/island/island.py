import math
import micropsi_core
from micropsi_core.world.world import World

import json
import os
from micropsi_core.world.worldadapter import WorldAdapter
from micropsi_core.world.worldobject import WorldObject
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
        #for o in o
        ret = super(Island, self).step()
        return ret

    def add_object(self, type, position, orientation = 0.0, name = "", parameters = None, uid = None ):
        """
        Add a new object to the current world.

        Arguments:
            type: the type of the object (currently, only "light_source" is supported
            position: a (x, y) tuple with the coordinates
            orientation (optional): an angle, usually between 0 and 2*pi
            name (optional): a readable name for that object
            uid (optional): if omitted, a uid will be generated
        """
        if not uid: uid = micropsi_core.tools.generate_uid()
        self.objects[uid] = {
            "uid":uid,
            "type":type,
            "position":position,
            "orientation":orientation,
            "parameters":parameters
        }

    def set_object_properties(self, uid, type=None, position=None, orientation=None, name=None, parameters=None):
        pass

    def set_agent_properties(self, uid, position=None, orientation=None, name=None, parameters=None):
        pass


class Lightsource(WorldObject):

    @property
    def pos(self):
        return self.data.get('pos', 0)

    @pos.setter
    def pos(self, pos):
        self.data['pos'] = pos

    @property
    def diameter(self):
        return self.data.get('diameter', 0.0)

    @diameter.setter
    def diameter(self, diameter):
        self.data['diameter'] = diameter

    @property
    def intensity(self):
        return self.data.get('intensity', 0.0)

    @intensity.setter
    def intensity(self, intensity):
        self.data['intensity'] = intensity

    def __init__(self, world, uid=None, **data):
        WorldObject.__init__(self, world, "light_source", uid=uid, **data)
        self.intensity = data.get('intensity', 1.0)
        self.diameter = data.get('diameter' ,0.1)

    def initialize_worldobject(self, data):
        self.data = data

    def get_intensity(self, distance):
        """returns the strength of the light, depending on the distance"""
        return self.intensity*self.diameter*self.diameter/distance/distance

class Braitenberg(WorldAdapter):
    """A simple Braitenberg vehicle chassis, with two light sensitive sensors and two engines
    """

    datasources = {'brightness_l': 1.7, 'brightness_r': 1.7}
    datatargets = {'engine_l':0, 'engine_r': 0}

    # positions of sensors, relative to origin of agent center
    brightness_l_pos = (-0.25, 0.25)
    brightness_r_pos = (0.25, 0.25)

    # positions of engines, relative to origin of agent center
    engine_l_pos = (-0.3, 0)
    engine_r_pos = (0.3, 0)

    # agent diameter
    diameter = 0.3

    @property
    def pos(self):
        return self.data.get('pos', 0)

    @pos.setter
    def pos(self, pos):
        self.data['pos'] = pos

    @property
    def direction(self):
        return self.data.get('direction', 0)

    @direction.setter
    def direction(self, direction):
        self.data['direction'] = direction % (2.0*math.pi)

    def initialize_worldobject(self, data):
        self.data = data
        if not "pos" in data:
            self.pos = self.world.groundmap.startpos

    def update(self):
        """called on every world simulation step to advance the life of the agent"""
        for o in self.world.objects:
            if hasattr(o, "get_intensity"):
                pass



