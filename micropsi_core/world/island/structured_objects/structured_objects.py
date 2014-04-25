__author__ = 'rvuine'

from micropsi_core.world.island.structured_objects.objects import OBJECTS
from micropsi_core.world.island.structured_objects.scene import Scene
from micropsi_core.world.world import World
from micropsi_core.world.worldadapter import WorldAdapter
from micropsi_core.world.worldobject import WorldObject

class StructuredObjects(WorldAdapter):
    """A world adapter exposing objects composed of basic shapes and colors to the agent"""

    shapetypes = []
    shapecolors = []

    datasources = {}
    datatargets = {'fovea_x': 0, 'fovea_y': 0, 'fovea_reset': 0}

    scene = None

    def __init__(self, world, uid=None, **data):
        super(StructuredObjects, self).__init__(world, uid)

        for key, objecttype in OBJECTS.items():
            for shapeline in objecttype['shape_grid']:
                for shape in shapeline:
                    if shape is not None and shape.type not in self.shapetypes:
                        self.shapetypes.append(shape.type)
                    if shape is not None and shape.color not in self.shapecolors:
                        self.shapecolors.append(shape.color)

        for shapetype in self.shapetypes:
            self.datasources[shapetype] = 0
            self.datasources[shapetype+'-presence'] = 0

        for shapecolor in self.shapecolors:
            self.datasources[shapecolor] = 0
            self.datasources[shapecolor+'-presence'] = 0

        self.scene = Scene(world, uid)
        self.scene.load_object("Tree", OBJECTS["Tree"]["shape_grid"])

    def initialize_worldobject(self, data):
        if not "position" in data:
            self.position = self.world.groundmap['start_position']

    def update(self):
        """called on every world simulation step to advance the life of the agent"""
        pass
