__author__ = 'rvuine'

from micropsi_core.world.worldobject import WorldObject


class PalmTree(WorldObject):
    def __init__(self, world, uid=None, **data):
        WorldObject.__init__(self, world, category="objects", uid=uid, **data)
        self.structured_object_type = "PalmTree"


class Maple(WorldObject):
    def __init__(self, world, uid=None, **data):
        WorldObject.__init__(self, world, category="objects", uid=uid, **data)
        self.structured_object_type = "Maple"


class Braintree(WorldObject):
    def __init__(self, world, uid=None, **data):
        WorldObject.__init__(self, world, category="objects", uid=uid, **data)
        self.structured_object_type = "Braintree"


class Wirselkraut(WorldObject):
    def __init__(self, world, uid=None, **data):
        WorldObject.__init__(self, world, category="objects", uid=uid, **data)
        self.structured_object_type = "Wirselkraut"


class Thornbush(WorldObject):
    def __init__(self, world, uid=None, **data):
        WorldObject.__init__(self, world, category="objects", uid=uid, **data)
        self.structured_object_type = "Thornbush"


class Juniper(WorldObject):
    def __init__(self, world, uid=None, **data):
        WorldObject.__init__(self, world, category="objects", uid=uid, **data)
        self.structured_object_type = "Juniper"


class Champignon(WorldObject):
    def __init__(self, world, uid=None, **data):
        WorldObject.__init__(self, world, category="objects", uid=uid, **data)
        self.structured_object_type = "Champignon"


class FlyAgaric(WorldObject):
    def __init__(self, world, uid=None, **data):
        WorldObject.__init__(self, world, category="objects", uid=uid, **data)
        self.structured_object_type = "FlyAgaric"


class Stone(WorldObject):
    def __init__(self, world, uid=None, **data):
        WorldObject.__init__(self, world, category="objects", uid=uid, **data)
        self.structured_object_type = "Stone"


class Boulder(WorldObject):
    def __init__(self, world, uid=None, **data):
        WorldObject.__init__(self, world, category="objects", uid=uid, **data)
        self.structured_object_type = "Boulder"


class Menhir(WorldObject):
    def __init__(self, world, uid=None, **data):
        WorldObject.__init__(self, world, category="objects", uid=uid, **data)
        self.structured_object_type = "Menhir"


class Waterhole(WorldObject):
    def __init__(self, world, uid=None, **data):
        WorldObject.__init__(self, world, category="objects", uid=uid, **data)
        self.structured_object_type = "Waterhole"


class Shape():

    def __init__(self, type, color):
        self.type = type
        self.color = color

VER_B = Shape("ver", "brown")
COM_G = Shape("com", "green")
CIR_P = Shape("cir", "purple")
CIR_B = Shape("cir", "brown")
CIR_R = Shape("cir", "red")
COM_C = Shape("com", "charcoal")
COM_N = Shape("com", "navy")

OBJECTS = {
    "PalmTree": {
        "type": "PalmTree",
        "shape_grid": [
        [None,      None,       COM_G,      None,       None],      #                   0/-2
        [None,      COM_G,      VER_B,      COM_G,      None],      #           -1/-1   0/-1    1/-1
        [None,      None,       VER_B,      None,       None],      #                   0/ 0
        [None,      None,       VER_B,      None,       None],      #                   0/ 1
        [None,      None,       VER_B,      None,       None]       #                   0/ 2
        ]
    },
    "MapleTree": {
        "type": "MapleTree",
        "shape_grid": [
        [None,      None,       COM_G,      None,       None],
        [None,      COM_G,      COM_G,      COM_G,      None],
        [None,      COM_G,      VER_B,      COM_G,      None],
        [None,      None,       VER_B,      None,       None],
        [None,      None,       VER_B,      None,       None]
        ]
    },
    "BrainTree": {
        "type": "BrainTree",
        "shape_grid": [
        [None,      None,       None,       None,       None],
        [None,      COM_G,      COM_G,      COM_G,      None],
        [None,      COM_G,      COM_G,      COM_G,      None],
        [None,      VER_B,      COM_G,      None,       None],
        [None,      None,       VER_B,      None,       None]
        ]
    },
    "Wirselkraut": {
        "type": "Wirselkraut",
        "shape_grid": [
        [None,      None,       None,       None,       None],
        [None,      None,       None,       None,       None],
        [None,      None,       None,       None,       None],
        [None,      None,       None,       None,       None],
        [None,      None,       COM_G,      None,       None]
        ]
    },
    "Thornbush": {
        "type": "Thornbush",
        "shape_grid": [
        [None,      None,       None,       None,       None],
        [None,      None,       None,       None,       None],
        [None,      None,       None,       None,       None],
        [None,      None,       COM_G,      None,       None],
        [None,      COM_G,      COM_G,      COM_G,      None]
        ]
    },
    "Juniper": {
        "type": "Juniper",
        "shape_grid": [
        [None,      None,       None,       None,       None],
        [None,      None,       None,       None,       None],
        [None,      None,       CIR_P,      None,       None],
        [None,      CIR_P,      COM_G,      CIR_P,      None],
        [None,      COM_G,      COM_G,      COM_G,      None]
        ]
    },
    "Champignon": {
        "type": "Champignon",
        "shape_grid": [
        [None,      None,       None,       None,       None],
        [None,      None,       None,       None,       None],
        [None,      None,       None,       None,       None],
        [None,      None,       None,       None,       None],
        [None,      None,      CIR_B,       None,       None]
        ]
    },
    "FlyAgaric": {
        "type": "FlyAgaric",
        "shape_grid": [
        [None,      None,       None,       None,       None],
        [None,      None,       None,       None,       None],
        [None,      None,       None,       None,       None],
        [None,      None,       None,       None,       None],
        [None,      None,      CIR_R,       None,       None]
        ]
    },
    "Stone": {
        "type": "Stone",
        "shape_grid": [
        [None,      None,       None,       None,       None],
        [None,      None,       None,       None,       None],
        [None,      None,       None,       None,       None],
        [None,      None,       None,       None,       None],
        [None,      None,      COM_C,       None,       None]
        ]
    },
    "Boulder": {
        "type": "Boulder",
        "shape_grid": [
        [None,      None,       None,       None,       None],
        [None,      None,       None,       None,       None],
        [None,      None,       None,       None,       None],
        [None,      None,       COM_G,      COM_C,      None],
        [None,      COM_C,      COM_C,      COM_C,      None]
        ]
    },
    "Menhir": {
        "type": "Menhir",
        "shape_grid": [
        [None,      None,       None,       None,       None],
        [None,      None,      COM_C,       None,       None],
        [None,      None,      COM_C,       None,       None],
        [None,      None,      COM_C,       None,       None],
        [None,      None,      COM_C,      COM_C,       None]
        ]
    },
    "Waterhole": {
        "type": "Waterhole",
        "shape_grid": [
        [None,      None,       None,       None,       None],
        [None,      None,       None,       None,       None],
        [None,      None,       None,       None,       None],
        [None,      None,       None,       None,       None],
        [None,     COM_N,      COM_N,      COM_N,      COM_N]
        ]
    }
}
