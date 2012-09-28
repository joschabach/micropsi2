
from micropsi_core.world.worldobject import WorldObject


class Station(WorldObject):

    def __init__(self, world, type, uid=None, **data):
        WorldObject.__init__(self, world, type, uid=uid, **data)
        self.lon = data.get('lon')
        self.lat = data.get('lat')
        self.lines = data.get('line_names')
        self.name = data.get('name')
