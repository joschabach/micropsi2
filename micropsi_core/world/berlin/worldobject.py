
from micropsi_core.world.worldobject import WorldObject


class Station(WorldObject):

    @property
    def pos(self):
        return self.data.get('pos', 0)

    @pos.setter
    def pos(self, pos):
        self.data['pos'] = pos

    def __init__(self, world, type, uid=None, **data):
        WorldObject.__init__(self, world, type, uid=uid, **data)
        self.lines = data.get('line_names')
        self.name = data.get('name')

    def initialize_worldobject(self, data):
        self.data = data


class Train(WorldObject):

    @property
    def pos(self):
        return self.data.get('pos', 0)

    @pos.setter
    def pos(self, pos):
        self.data['pos'] = pos

    def __init__(self, world, type, uid=None, **data):
        WorldObject.__init__(self, world, type, uid=uid, **data)
        self.lines = data.get('line_names')
        self.name = data.get('name')

    def initialize_worldobject(self, data):
        self.data = data

    def update(self):
        self.pos = map(sum, zip(self.pos, (1.0, 1.0)))
