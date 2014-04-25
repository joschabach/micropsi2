__author__ = 'rvuine'

GRIDSIZE = 5


class Scene():

    __fovea_x = (GRIDSIZE-1) / 2
    __fovea_y = (GRIDSIZE-1) / 2

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
        """
        Resets the fovea to the center of the grid
        """
        self.__fovea_x = (GRIDSIZE-1) / 2
        self.__fovea_y = (GRIDSIZE-1) / 2
        self.__update_world_data()

    def move_fovea_x(self, x):
        """
        Horizontally moves the fovea by x elements on the grid
        """
        self.__fovea_x += x
        if self.__fovea_x > GRIDSIZE:
            self.__fovea_x = GRIDSIZE
        if self.__fovea_x < 0:
            self.__fovea_x = 0
        self.__update_world_data()

    def move_fovea_y(self, y):
        """
        Vertically moves the fovea by y elements on the grid
        """
        self.__fovea_y += y
        if self.__fovea_y > GRIDSIZE:
            self.__fovea_y = GRIDSIZE
        if self.__fovea_y < 0:
            self.__fovea_y = 0
        self.__update_world_data()

    def load_object(self, shape_name, shape_grid):
        """
        Loads an object into the grid.
        shape_grid is a two-dimensional array of size GRIDSIZExGRIDSIZE, containing None or Shape objects
        """
        self.__shape_grid = shape_grid
        self.__shape_name = shape_name
        self.__update_world_data()

    def is_fovea_on_shape_type(self, shapetype):
        """
        Returns true if the shape unter the fovea is of type shapetype
        """
        return (self.__fovea_x < GRIDSIZE and
                self.__fovea_y < GRIDSIZE and
                (self.__shape_grid[self.__fovea_y][self.__fovea_x] is not None) and
                (self.__shape_grid[self.__fovea_y][self.__fovea_x].type is shapetype))

    def is_fovea_on_shape_color(self, shapecolor):
        """
        Returns true if the shape unter the fovea is shapecolor-colored
        """
        return (self.__fovea_x < GRIDSIZE and
                self.__fovea_y < GRIDSIZE and
                (self.__shape_grid[self.__fovea_y][self.__fovea_x] is not None) and
                (self.__shape_grid[self.__fovea_y][self.__fovea_x].color is shapecolor))

    def is_shapetype_in_scene(self, shapetype):
        """
        Returns true if a shape of type shapetype is in the scene (ignoring fovea position)
        """
        for shapeline in self.__shape_grid:
            for shape in shapeline:
                if shape is not None and shape.type is shapetype:
                    return True
        return False

    def is_shapecolor_in_scene(self, shapecolor):
        """
        Returns true if a shapecolor-colored shape is in the scene (ignoring fovea position)
        """
        for shapeline in self.__shape_grid:
            for shape in shapeline:
                if shape is not None and shape.color is shapecolor:
                    return True
        return False

    def __update_world_data(self):
        """
        Updates the world's data object with scene information
        """
        if self.__world.data['agents'] is None:
            self.__world.data['agents'] = {}
        if self.__world.data['agents'][self.__agent_id] is None:
            self.__world.data['agents'][self.__agent_id] = {}
        self.__world.data['agents'][self.__agent_id]['scene'] = self.__serialize()

    def __serialize(self):
        """
        Serializes the scene into a dict, containing the shape grid array
        """
        shape_grid = [[None]*GRIDSIZE for i in range(GRIDSIZE)]
        for line in range(GRIDSIZE):
            for column in range(GRIDSIZE):
                if self.__shape_grid[line][column] is not None:
                    shape_grid[line][column] = {"type": self.__shape_grid[line][column].type,
                                            "color": self.__shape_grid[line][column].color}
        return {
            "type": "structured_object",
            "shape_name": self.__shape_name,
            "shape_grid": shape_grid,
            "fovea_x": self.fovea_x,
            "fovea_y": self.fovea_y
        }

