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
        'scaling': (200, 200)
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
        self.data['assets'] = self.assets

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

    def get_ground_at(self, (x, y)):
        """
        returns the ground type (an integer) at the given position
        """
        _x = min(self.x_max, max(0, round(x*self.scale_x)))
        _y = min(self.y_max, max(0, round(y*self.scale_y)))
        return self.ground_data[_y][_x]

    def step(self):
        """ overwrite world.step """
        for agent in self.agents:
            agent.update()
        self.current_step +=1

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

    def get_brightness_at(self, position):
        """calculate the brightness of the world at the given position; used by sensors of agents"""
        brightness = 0
        for world_object in self.objects:
            if hasattr(world_object, "get_intensity"):
                brightness += world_object.get_intensity(_2d_distance_squared(world_object.pos, position))
        return brightness

    def get_movement_result(self, start_position, effort_vector, diameter = 0):
        """determine how much an agent moves in the direction of the effort vector, starting in the start position.
        Note that agents may be hindered by impassable terrain and other objects"""

        efficiency = ground_types[self.get_ground_at(start_position)]['move_efficiency']
        if not efficiency:
            return start_position
        movement_vector = (effort_vector[0] * efficiency, effort_vector[1] * efficiency)

        # make sure we don't bump into stuff
        target_position = None
        while target_position is None and _2d_distance_squared((0,0), movement_vector) > 0.01:
            target_position = _2d_translate(start_position, movement_vector)

            for i in self.objects:
                if _2d_distance_squared(target_position, i.pos) < (diameter + i.diameter)/2:
                    movement_vector = (movement_vector[0] * 0.5, movement_vector[1] * 0.5) # should be collision point
                    target_position = None
                    break

        if target_position is None:
            return start_position
        return target_position

    def set_object_properties(self, uid, type=None, position=None, orientation=None, name=None, parameters=None):
        """set attributes of the world object 'uid'; only supplied attributes will be changed.
        Returns True if object exists, otherwise False"""
        if uid in self.objects:
            if type: self.objects[uid].type = type
            if position: self.objects[uid].pos = position
            if orientation: self.objects[uid].direction = orientation
            if name: self.objects[uid].name = name
            if parameters: self.objects[uid].parameters = parameters
            return True
        return False


    def set_agent_properties(self, uid, position=None, orientation=None, name=None, parameters=None):
        """set attributes of the agent 'uid'; only supplied attributes will be changed.
        Returns True if agent exists, otherwise False"""

        if uid in self.agents:
            if type: self.agents[uid].type = type
            if position: self.agents[uid].pos = position
            if orientation: self.agents[uid].direction = orientation
            if name: self.agents[uid].name = name
            if parameters: self.agents[uid].parameters = parameters
            return True
        return False

class Lightsource(WorldObject):
    """A pretty inert and boring light source, with a square falloff"""
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
        self.data['direction'] = 0

    def initialize_worldobject(self, data):
        self.data = data

    def get_intensity(self, distance_squared):
        """returns the strength of the light, depending on the square of the distance
        (we are using the square to avoid a math.sqr elsewhere)"""
        return self.intensity*self.diameter*self.diameter/distance_squared

class Braitenberg(WorldAdapter):
    """A simple Braitenberg vehicle chassis, with two light sensitive sensors and two engines"""

    datasources = {'brightness_l': 1.7, 'brightness_r': 1.7}
    datatargets = {'engine_l':0, 'engine_r': 0}

    # positions of sensors, relative to origin of agent center
    brightness_l_offset = (-0.25, 0.25)
    brightness_r_offset = (0.25, 0.25)

    # positions of engines, relative to origin of agent center
    engine_l_offset = (-0.3, 0)
    engine_r_offset = (0.3, 0)

    # agent diameter
    diameter = 0.6

    # maximum speed
    speed_limit = 1.5

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
        self.data['direction'] = direction % 360

    def initialize_worldobject(self, data):
        self.data = data
        if not "pos" in data:
            self.pos = self.world.groundmap.startpos

    def update(self):
        """called on every world simulation step to advance the life of the agent"""

        # drive engines
        l_wheel_speed = self.get_datasource("engine_l")
        r_wheel_speed = self.get_datasource("engine_r")

        # constrain speed
        if l_wheel_speed + r_wheel_speed > 2 * self.speed_limit: # too fast
            f = 2 * self.speed_limit / (l_wheel_speed + r_wheel_speed)
            r_wheel_speed *= f
            l_wheel_speed *= f

        rotation = math.degrees((l_wheel_speed - r_wheel_speed) / (self.diameter))
        translation = _2d_rotate((0, (r_wheel_speed + l_wheel_speed)/2), rotation)
        self.direction += rotation
        # you may decide how far you want to go, but it is up the world to decide how far you make it
        self.pos = self.world.get_movement_result(self.pos, translation)

        # sense light sources

        brightness_l_pos = _2d_translate(_2d_rotate(self.brightness_l_offset, self.direction), self.pos)
        brightness_r_pos = _2d_translate(_2d_rotate(self.brightness_r_offset, self.direction), self.pos)

        brightness_l = self.world.get_brightness_at(brightness_l_pos)
        brightness_r = self.world.get_brightness_at(brightness_r_pos)

        self.set_datatarget('brightness_l', brightness_l)
        self.set_datatarget('brightness_r', brightness_r)


def _2d_rotate(position, angle_degrees):
    """rotate a 2d vector around an angle (in degrees)"""
    radians = math.radians(angle_degrees)
    cos = math.cos(radians)
    sin = math.sin(radians)
    x, y = position
    return x * cos - y * sin, x * sin + y * cos

def _2d_distance_squared(position1, position2):
    """calculate the square of the distance bwtween two 2D coordinate tuples"""
    return (position1[0] - position2[0]) ** 2 + (position1[0] - position2[1]) ** 2

def _2d_translate(position1, position2):
    """add two 2d vectors"""
    return (position1[0]+position2[0], position1[1]+position2[1])

# the indices of ground types correspond to the color numbers in the groundmap png
ground_types = (
    {
        'type': 'grass',
        'move_efficiency': 1.0,
        'agent_allowed': True,
    },
    {
        'type': 'sand',
        'move_efficiency': 1.0,
        'agent_allowed': True,
    },
    {
        'type': 'swamp',
        'move_efficiency': 0.5,
        'agent_allowed': True,
    },
    {
        'type': 'darkgrass',
        'move_efficiency': 1.0,
        'agent_allowed': True,
    },
    {
        'type': 'shallowwater',
        'move_efficiency': 0.2,
        'agent_allowed': True,
    },
    {
        'type': 'rock',
        'move_efficiency': 1.0,
        'agent_allowed': True,
    },
    {
        'type': 'clay',
        'move_efficiency': 0.7,
        'agent_allowed': True,
    },
    {
        'type': 'water',
        'move_efficiency': 0.0,
        'agent_allowed': False,
    },
    {
        'type': 'cliff',
        'move_efficiency': 1.0,
        'agent_allowed': False,
        }

)
