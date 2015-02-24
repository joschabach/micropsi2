__author__ = 'rvuine'

import logging
from micropsi_core.world.island import island
from micropsi_core.world.island.structured_objects.objects import *
from micropsi_core.world.island.structured_objects.scene import Scene
from micropsi_core.world.worldadapter import WorldAdapter


class StructuredObjects(WorldAdapter):
    """A world adapter exposing objects composed of basic shapes and colors to the agent"""

    shapetypes = []
    shapecolors = []

    supported_datasources = ['fov-x', 'fov-y', 'major-newscene']
    supported_datatargets = ['fov_x', 'fov_y', 'fov_reset']

    for key, objecttype in OBJECTS.items():
        for shapeline in objecttype['shape_grid']:
            for shape in shapeline:
                if shape is not None and shape.type not in shapetypes:
                    shapetypes.append(shape.type)
                if shape is not None and shape.color not in shapecolors:
                    shapecolors.append(shape.color)

    for shapetype in shapetypes:
        supported_datasources.append('fovea-'+shapetype)
        supported_datasources.append('presence-'+shapetype)

    for shapecolor in shapecolors:
        supported_datasources.append("fovea-"+shapecolor)
        supported_datasources.append("presence-"+shapecolor)

    def __init__(self, world, uid=None, **data):
        super(StructuredObjects, self).__init__(world, uid, **data)

        self.currentobject = None
        self.scene = None

        self.scene = Scene(world, uid)
        self.scene.load_object("PalmTree", OBJECTS["PalmTree"]["shape_grid"])

    def initialize_worldobject(self, data):
        if not "position" in data:
            self.position = self.world.groundmap['start_position']

    def get_datasource(self, key):
        """
            allows the agent to read a value from a datasource.
            overrides default to make sure newscene signals are picked up by the node net
        """
        if key == "major-newscene":
            if self.datasource_snapshots[key] == 1:
                self.datasources[key] = 0
                return 1
        else:
            return WorldAdapter.get_datasource(self, key)

    def update_data_sources_and_targets(self):
        """called on every world simulation step to advance the life of the agent"""

        # we don't move, for now
        self.position = self.world.get_movement_result(self.position, (0, 0))

        #find nearest object to load into the scene
        lowest_distance_to_worldobject = float("inf")
        nearest_worldobject = None
        for key, worldobject in self.world.objects.items():
            # TODO: use a proper 2D geometry library
            distance = island._2d_distance_squared(self.position, worldobject.position)
            if distance < lowest_distance_to_worldobject:
                lowest_distance_to_worldobject = distance
                nearest_worldobject = worldobject

        if self.currentobject is not nearest_worldobject and nearest_worldobject.structured_object_type is not None:
            self.currentobject = nearest_worldobject
            self.scene.load_object(self.currentobject.structured_object_type,
                                   OBJECTS[self.currentobject.structured_object_type]['shape_grid'])
            self.datasources["major-newscene"] = 1
            logging.getLogger("world").debug("StructuredObjects WA selected new scene: %s",
                                             self.currentobject.structured_object_type)

        #manage the scene
        if self.datatargets['fov_reset'] > 0:
            self.scene.reset_fovea()

        self.scene.move_fovea_x(self.datatargets['fov_x'])
        self.scene.move_fovea_y(self.datatargets['fov_y'])

        self.datasources["fov-x"] = self.scene.fovea_x
        self.datasources["fov-y"] = self.scene.fovea_y

        for shapetype in self.shapetypes:
            self.datasources["fovea-"+shapetype] = 1 if self.scene.is_fovea_on_shape_type(shapetype) else 0
            self.datasources["presence-"+shapetype] = 1 if self.scene.is_shapetype_in_scene(shapetype) else 0

        for shapecolor in self.shapecolors:
            self.datasources["fovea-"+shapecolor] = 1 if self.scene.is_fovea_on_shape_color(shapecolor) else 0
            self.datasources["presence-"+shapecolor] = 1 if self.scene.is_shapecolor_in_scene(shapecolor) else 0
