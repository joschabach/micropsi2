import math
import os
from micropsi_core.world.world import World
from micropsi_core.world.worldadapter import WorldAdapter
from micropsi_core.world.worldobject import WorldObject
import png


class Island(World):

    """ mandatory: list of world adapters that are supported"""
    supported_worldadapters = ['Braitenberg']

    groundmap = {
        'image': "psi_1.png",
        'start_position': (100, 100),
        'scaling': (200, 200)
    }

    assets = {
        'background': "island/psi_1.png",
        'js': "island/island.js",
        'x': 2048,
        'y': 2048,
        'icons': {'Lightsource': 'island/lamp.png'}
    }

    def __init__(self, filename, world_type="Island", name="", owner="", uid=None, version=1):
        World.__init__(self, filename, world_type=world_type, name=name, owner=owner, uid=uid, version=version)
        self.load_groundmap()
        self.current_step = 0
        self.data['assets'] = self.assets

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
            self.x_max = x - 1
            self.y_max = y - 1
            self.scale_x = float(x) / self.groundmap["scaling"][0]
            self.scale_y = float(y) / self.groundmap["scaling"][1]

    def get_ground_at(self, (x, y)):
        """
        returns the ground type (an integer) at the given position
        """
        _x = min(self.x_max, max(0, round(x * self.scale_x)))
        _y = min(self.y_max, max(0, round(y * self.scale_y)))
        return self.ground_data[_y][_x]

    def step(self):
        """ overwrite world.step """
        for agent in self.agents:
            agent.update()
        self.current_step += 1

    def get_brightness_at(self, position):
        """calculate the brightness of the world at the given position; used by sensors of agents"""
        brightness = 0
        for world_object in self.objects:
            if hasattr(world_object, "get_intensity"):
                brightness += world_object.get_intensity(_2d_distance_squared(world_object.position, position))
        return brightness

    def get_movement_result(self, start_position, effort_vector, diameter=0):
        """determine how much an agent moves in the direction of the effort vector, starting in the start position.
        Note that agents may be hindered by impassable terrain and other objects"""

        efficiency = ground_types[self.get_ground_at(start_position)]['move_efficiency']
        if not efficiency:
            return start_position
        movement_vector = (effort_vector[0] * efficiency, effort_vector[1] * efficiency)

        # make sure we don't bump into stuff
        target_position = None
        while target_position is None and _2d_distance_squared((0, 0), movement_vector) > 0.01:
            target_position = _2d_translate(start_position, movement_vector)

            for i in self.objects:
                if _2d_distance_squared(target_position, i.position) < (diameter + i.diameter) / 2:
                    movement_vector = (movement_vector[0] * 0.5, movement_vector[1] * 0.5)  # should be collision point
                    target_position = None
                    break

        if target_position is None:
            return start_position
        return target_position


class Lightsource(WorldObject):
    """A pretty inert and boring light source, with a square falloff"""

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
        WorldObject.__init__(self, world, category="objects", uid=uid, **data)

    def get_intensity(self, distance_squared):
        """returns the strength of the light, depending on the square of the distance
        (we are using the square to avoid a math.sqr elsewhere)"""
        return self.intensity * self.diameter * self.diameter / distance_squared


class Braitenberg(WorldAdapter):
    """A simple Braitenberg vehicle chassis, with two light sensitive sensors and two engines"""

    datasources = {'brightness_l': 1.7, 'brightness_r': 1.7}
    datatargets = {'engine_l': 0, 'engine_r': 0}

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

    def initialize_worldobject(self, data):
        if not "position" in data:
            self.position = self.world.groundmap['start_position']

    def update(self):
        """called on every world simulation step to advance the life of the agent"""

        # drive engines
        l_wheel_speed = self.get_datasource("engine_l")
        r_wheel_speed = self.get_datasource("engine_r")

        # constrain speed
        if l_wheel_speed + r_wheel_speed > 2 * self.speed_limit:  # too fast
            f = 2 * self.speed_limit / (l_wheel_speed + r_wheel_speed)
            r_wheel_speed *= f
            l_wheel_speed *= f

        rotation = math.degrees((l_wheel_speed - r_wheel_speed) / (self.diameter))
        translation = _2d_rotate((0, (r_wheel_speed + l_wheel_speed) / 2), rotation)
        self.orientation += rotation
        # you may decide how far you want to go, but it is up the world to decide how far you make it
        self.position = self.world.get_movement_result(self.position, translation)

        # sense light sources

        brightness_l_position = _2d_translate(_2d_rotate(self.brightness_l_offset, self.orientation), self.position)
        brightness_r_position = _2d_translate(_2d_rotate(self.brightness_r_offset, self.orientation), self.position)

        brightness_l = self.world.get_brightness_at(brightness_l_position)
        brightness_r = self.world.get_brightness_at(brightness_r_position)

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
    return (position1[0] + position2[0], position1[1] + position2[1])


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
