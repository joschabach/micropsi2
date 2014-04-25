__author__ = 'rvuine'

GRIDSIZE = 5


class Scene():

    __fovea_x = 2
    __fovea_y = 2

    __shape_grid = [[0]*GRIDSIZE for i in range(GRIDSIZE)]
    __shape_name = "none"

    __world = None
    __agent_id = None

    @property
    def fovea_x(self):
        return self.__fovea_x

    @property
    def fovea_y(self):
        return self.__fovea_y

    def __init__(self, world, agent_id):
        self.__world = world
        self.__agent_id = agent_id

    def reset_fovea(self):
        self.__fovea_x = 2
        self.__fovea_y = 2
        self.__update_world_data()

    def move_fovea_x(self, x):
        self.__fovea_x += x
        if self.__fovea_x > GRIDSIZE:
            self.__fovea_x = GRIDSIZE
        if self.__fovea_x < 0:
            self.__fovea_x = 0
        self.__update_world_data()

    def move_fovea_y(self, y):
        self.__fovea_y += y
        if self.__fovea_y > GRIDSIZE:
            self.__fovea_y = GRIDSIZE
        if self.__fovea_y < 0:
            self.__fovea_y = 0
        self.__update_world_data()

    def load_object(self, shape_name, shape_grid):
        self.__shape_grid = shape_grid
        self.__shape_name = shape_name
        self.__update_world_data()

    def is_fovea_on_shape_type(self, shapetype):
        return (self.__fovea_x < GRIDSIZE and
                self.__fovea_y < GRIDSIZE and
                (self.__shape_grid[self.__fovea_x][self.__fovea_y] is not None) and
                (self.__shape_grid[self.__fovea_x][self.__fovea_y].type is shapetype))

    def is_fovea_on_shape_color(self, shapecolor):
        return (self.__fovea_x < GRIDSIZE and
                self.__fovea_y < GRIDSIZE and
                (self.__shape_grid[self.__fovea_x][self.__fovea_y] is not None) and
                (self.__shape_grid[self.__fovea_x][self.__fovea_y].color is shapecolor))

    def is_shapetype_in_scene(self, shapetype):
        for shapeline in self.__shape_grid:
            for shape in shapeline:
                if self.__shape_grid[shapeline][shape].type is shapetype:
                    return True
        return False

    def is_shapecolor_in_scene(self, shapecolor):
        for shapeline in self.__shape_grid:
            for shape in shapeline:
                if self.__shape_grid[shapeline][shape].color is shapecolor:
                    return True
        return False

    def __update_world_data(self):
        if self.__world.data['agents'] is None:
            self.__world.data['agents'] = {}
        if self.__world.data['agents'][self.__agent_id] is None:
            self.__world.data['agents'][self.__agent_id] = {}
        self.__world.data['agents'][self.__agent_id]['scene'] = self.__serialize()

    def __serialize(self):
        shape_grid = [[None]*GRIDSIZE for i in range(GRIDSIZE)]
        for line in range(GRIDSIZE):
            for column in range(GRIDSIZE):
                if self.__shape_grid[line][column] is not None:
                    shape_grid[line][column] = {"type": self.__shape_grid[line][column].type,
                                            "color": self.__shape_grid[line][column].color}
        return {
            "shape_name": self.__shape_name,
            "shape_grid": shape_grid,
            "fovea_x": self.fovea_x,
            "fovea_y": self.fovea_y
        }

