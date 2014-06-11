__author__ = 'rvuine'

from micropsi_core.world.worldobject import WorldObject


class Tree(WorldObject):
    """A tree"""

    def __init__(self, world, uid=None, **data):
        WorldObject.__init__(self, world, category="objects", uid=uid, **data)
        self.structured_object_type = "Tree"


class Pole(WorldObject):
    """A pole"""

    def __init__(self, world, uid=None, **data):
        WorldObject.__init__(self, world, category="objects", uid=uid, **data)
        self.structured_object_type = "Pole"


class Shape():

    def __init__(self, type, color):
        self.type = type
        self.color = color

VER_B = Shape("ver", "brown")
COM_G = Shape("com", "green")

OBJECTS = {
    "Tree": {
        "type": "Tree",
        "shape_grid": [
        [None,      None,       COM_G,      None,       None],      #                   0/-2
        [None,      COM_G,      COM_G,      COM_G,      None],      #           -1/-1   0/-1    1/-1
        [None,      None,       COM_G,      None,       None],      #                   0/ 0
        [None,      None,       VER_B,      None,       None],      #                   0/ 1
        [None,      None,       VER_B,      None,       None]       #                   0/ 2
        ]
    },
    "Pole": {
        "type": "Tree",
        "shape_grid": [
        [None,      None,       None,       None,       None],      #
        [None,      None,       None,       None,       None],      #
        [None,      None,       VER_B,      None,       None],      #                   0/ 0
        [None,      None,       VER_B,      None,       None],      #                   0/ 1
        [None,      None,       VER_B,      None,       None]       #                   0/ 2
        ]
    }

}
