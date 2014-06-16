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

    datasources = {}
    datatargets = {'fov_x': 0, 'fov_y': 0, 'fov_reset': 0, 'action_eat': 0, 'action_drink': 0}

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

        self.datasources["major-newscene"] = 0

        self.energy = 1.0
        self.water = 1.0
        self.integrity = 1.0
        self.is_dead = False

        self.action_cooloff = 5

        self.datasources['body-energy'] = self.energy
        self.datasources['body-water'] = self.water
        self.datasources['body-integrity'] = self.integrity

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

    def update(self):
        """called on every world simulation step to advance the life of the agent"""

        if self.is_dead:
            return

        ourname = self.world.agents[self.uid].name

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

        # manage body parameters
        for datatarget in self.datatargets.keys():
            if datatarget.startswith("action_"):
                self.datatarget_feedback[datatarget] = 0
                if self.datatargets[datatarget] >= 1 and self.action_cooloff <= 0:
                    self.datatargets[datatarget] = 0
                    if hasattr(nearest_worldobject, datatarget):
                        cando, delta_energy, delta_water, delta_integrity = nearest_worldobject.action_eat()
                    else:
                        cando, delta_energy, delta_water, delta_integrity = False, 0, 0, 0
                    if cando:
                        self.action_cooloff = 6
                        self.energy += delta_energy
                        self.water += delta_water
                        self.integrity += delta_integrity
                        self.datatarget_feedback[datatarget] = 1
                        logging.getLogger("world").debug("Agent "+ourname+" "+ datatarget +
                                                         "("+nearest_worldobject.data["type"]+") result: "+
                                                         " energy "+str(delta_energy)+
                                                         " water "+str(delta_water)+
                                                         " integrity "+str(delta_integrity))
                    else:
                        logging.getLogger("world").debug("Agent "+ourname+" "+ datatarget +
                                                         "("+nearest_worldobject.data["type"]+") result: "+
                                                         "cannot do.")

        self.action_cooloff -= 1
        self.energy -= 0.005
        self.water -= 0.005

        if self.energy > 1: self.energy = 1
        if self.water > 1: self.water = 1
        if self.integrity > 1: self.integrity = 1

        if self.energy <= 0 or self.water <= 0 or self.integrity <= 0:
            self.is_dead = True
            logging.getLogger("world").debug("Agent "+ourname+" has died:"+
                    " energy "+str(self.energy)+
                    " water "+str(self.water)+
                    " integrity "+str(self.integrity))

        self.datasources["body-energy"] = self.energy
        self.datasources["body-water"] = self.water
        self.datasources["body-integrity"] = self.integrity
