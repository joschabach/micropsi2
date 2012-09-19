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
        if type not in self.world.data:
            self.world.data[type] = {}
        self.data = self.world.data[type][self.uid]
        self.data["uid"] = uid or generate_uid()
        self.initialize_worldobject()

    def initialize_worldobject(self, data):
        """ sets the values from the data """
        pass

    def update():
        """ Called by the world at each world iteration """
        pass
