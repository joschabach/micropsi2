"""
Superclass for world objects and agents.
objects are instances in the world, that are not connected to a nodenet.
Holds a reference to the serializeable data dict in the world.
"""

from micropsi_core.tools import generate_uid


class WorldObject(object):

    @property
    def diameter(self):
        return self.data.get('diameter', 1)

    @property
    def position(self):
        return self.data.get('position', 0)

    @position.setter
    def position(self, position):
        self.data['position'] = position

    @property
    def orientation(self):
        return self.data.get('orientation', 0)

    @orientation.setter
    def orientation(self, orientation):
        self.data['orientation'] = orientation % 360

    @property
    def name(self):
        return self.data.get('name', self.uid)

    @name.setter
    def name(self, name):
        self.data['name'] = name

    @property
    def parameters(self):
        return self.data.get('parameters', {})

    @parameters.setter
    def parameters(self, parameters={}):
        self.data['parameters'] = parameters

    @property
    def uid(self):
        return self.data['uid']

    def __init__(self, world, category='objects', uid=None, **data):
        self.world = world
        if uid is None:
            uid = generate_uid()
        if category not in self.world.data:
            self.world.data[category] = {}
        if uid not in self.world.data[category]:
            self.world.data[category][uid] = data
        self.data = self.world.data[category][uid]
        self.data["type"] = data.get('type', self.__class__.__name__)
        self.data["uid"] = uid
        self.initialize_worldobject(data)

    def initialize_worldobject(self, data):
        """ sets the values from the data """
        pass

    def update(self, step_inteval_ms):
        """ Called by the world at each world iteration """
        pass


class TestObject(WorldObject):
    pass
