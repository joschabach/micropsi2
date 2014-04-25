__author__ = 'rvuine'


class Shape():

    def __init__(self, type, color):
        self.type = type
        self.color = color

HOR_B = Shape("ver", "brown")
COM_G = Shape("com", "green")

OBJECTS = {
    "Tree": {
        "name": "Tree",
        "shape_grid": [
        [None,      None,       COM_G,      None,       None],
        [None,      COM_G,      COM_G,      COM_G,      None],
        [None,      None,       COM_G,      None,       None],
        [None,      None,       HOR_B,      None,       None],
        [None,      None,       HOR_B,      None,       None]
        ]
    }
}
