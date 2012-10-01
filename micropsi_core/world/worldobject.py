"""
Superclass for world objects and agents.
objects are instances in the world, that are not connected to a nodenet.
Holds a reference to the serializeable data dict in the world.
"""

from micropsi_core.tools import generate_uid


class WorldObject(object):

    @property
    def uid(self):
        return self.data['uid']

    def __init__(self, world, type, uid=None, **data):
        self.world = world
        self.data = {}
        if uid is None:
            uid = generate_uid()
        if type not in self.world.data:
            self.world.data[type] = {}
        if uid not in self.world.data[type]:
            self.world.data[type][uid] = data
        self.data = self.world.data[type][uid]
        self.data["uid"] = uid
        self.initialize_worldobject(data)

    def initialize_worldobject(self, data):
        """ sets the values from the data """
        pass

    def update(self):
        """ Called by the world at each world iteration """
        pass
