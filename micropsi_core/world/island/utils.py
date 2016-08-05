import math


def _2d_rotate(position, angle_degrees):
    """rotate a 2d vector around an angle (in degrees)"""
    radians = math.radians(angle_degrees)
    # take the negative of the angle because the orientation circle works clockwise in this world
    cos = math.cos(-radians)
    sin = math.sin(-radians)
    x, y = position
    return x * cos - y * sin, - (x * sin + y * cos)


def _2d_distance_squared(position1, position2):
    """calculate the square of the distance bwtween two 2D coordinate tuples"""
    return (position1[0] - position2[0]) ** 2 + (position1[1] - position2[1]) ** 2


def _2d_translate(position1, position2):
    """add two 2d vectors"""
    return (position1[0] + position2[0], position1[1] + position2[1])


def _2d_vector_norm(vector):
    """Calculates the length /norm of a given vector."""
    return math.sqrt(sum(i**2 for i in vector))
