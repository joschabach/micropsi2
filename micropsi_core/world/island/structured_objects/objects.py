__author__ = 'rvuine'

from micropsi_core.world.worldobject import WorldObject


class Tree(WorldObject):
    """A tree"""

    def __init__(self, world, uid=None, **data):
        WorldObject.__init__(self, world, category="objects", uid=uid, **data)
        self.structured_object_type = "Tree"

class Shape():

    def __init__(self, type, color):
        self.type = type
        self.color = color

HOR_B = Shape("ver", "brown")
COM_G = Shape("com", "green")

OBJECTS = {
    "Tree": {
        "type": "Tree",
        "shape_grid": [
        [None,      None,       COM_G,      None,       None],
        [None,      COM_G,      COM_G,      COM_G,      None],
        [None,      None,       COM_G,      None,       None],
        [None,      None,       HOR_B,      None,       None],
        [None,      None,       HOR_B,      None,       None]
        ]
    }
}
