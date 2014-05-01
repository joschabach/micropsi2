__author__ = 'rvuine'

from micropsi_core.world.island import island
from micropsi_core.world.island.structured_objects.objects import *
from micropsi_core.world.island.structured_objects.scene import Scene
from micropsi_core.world.worldadapter import WorldAdapter


class StructuredObjects(WorldAdapter):
    """A world adapter exposing objects composed of basic shapes and colors to the agent"""

    shapetypes = []
    shapecolors = []

    datasources = {}
    datatargets = {'fov_x': 0, 'fov_y': 0, 'fov_reset': 0}

    currentobject = None
    scene = None

    def __init__(self, world, uid=None, **data):
        super(StructuredObjects, self).__init__(world, uid, **data)

        for key, objecttype in OBJECTS.items():
            for shapeline in objecttype['shape_grid']:
                for shape in shapeline:
                    if shape is not None and shape.type not in self.shapetypes:
                        self.shapetypes.append(shape.type)
                    if shape is not None and shape.color not in self.shapecolors:
                        self.shapecolors.append(shape.color)

        for shapetype in self.shapetypes:
            self.datasources["fovea-"+shapetype] = 0
            self.datasources["presence-"+shapetype] = 0

        for shapecolor in self.shapecolors:
            self.datasources["fovea-"+shapecolor] = 0
            self.datasources["presence-"+shapecolor] = 0

        self.datasources["fov-x"] = 0
        self.datasources["fov-y"] = 0

        self.scene = Scene(world, uid)
        self.scene.load_object("Tree", OBJECTS["Tree"]["shape_grid"])

    def initialize_worldobject(self, data):
        if not "position" in data:
            self.position = self.world.groundmap['start_position']

    def update(self):
        """called on every world simulation step to advance the life of the agent"""

        # we don't move, for now
        self.position = self.world.get_movement_result(self.position, (0, 0))

        #find nearest object to load into the scene
        lowest_distance_to_worldobject = float("inf")
        nearest_worldobject = None
        for key, worldobject in self.world.get_world_objects().items():
            # TODO: WTF world API? why do I get a dict instead of the actual objects?
            # I understand hating OOP is very fashionable and all, but this might be overdoing it slightly :-)
            non_bullshit_world_object = self.world.objects[key]
            # TODO: use a proper 2D geometry library
            distance = island._2d_distance_squared(self.position, non_bullshit_world_object.position)
            if distance < lowest_distance_to_worldobject:
                lowest_distance_to_worldobject = distance
                nearest_worldobject = non_bullshit_world_object

        if self.currentobject is not nearest_worldobject and nearest_worldobject.structured_object_type is not None:
            self.currentobject = nearest_worldobject
            self.scene.load_object(self.currentobject.structured_object_type,
                                   OBJECTS[self.currentobject.structured_object_type]['shape_grid'])

        #manage the scene
        if self.datatargets['fov_reset'] > 0:
            self.scene.reset_fovea()

        self.scene.move_fovea_x(self.datatargets['fov_x'])
        self.scene.move_fovea_y(self.datatargets['fov_y'])

        self.datasources["fov-x"] = self.scene.fovea_x
        self.datasources["fov-y"] = self.scene.fovea_y

        for shapetype in self.shapetypes:
            self.datasources["fovea-"+shapetype] = self.scene.is_fovea_on_shape_type(shapetype)
            self.datasources["presence-"+shapetype] = self.scene.is_shapetype_in_scene(shapetype)

        for shapecolor in self.shapecolors:
            self.datasources["fovea-"+shapecolor] = self.scene.is_fovea_on_shape_color(shapecolor)
            self.datasources["presence-"+shapecolor] = self.scene.is_shapecolor_in_scene(shapecolor)
