__author__ = 'jonas'

def tex_coord(x, y, n=1): #TODO probably not needed anymore because every texture is a single file
    m = 1.0 / n
    dx = x * m
    dy = y * m
    return dx, dy, dx + m, dy, dx + m, dy + m, dx, dy + m

def tex_coords(top, bottom, side): #TODO probably just to get different amounts of the same texture
    top = tex_coord(*top)
    bottom = tex_coord(*bottom)
    side = tex_coord(*side)
    result = []
    result.extend(top)
    result.extend(bottom)
    result.extend(side * 4)
    return result

def tex_coords_top(top, bottom, side):
    top = tex_coord(*top)
    result = []
    result.extend(top)
    return result

def tex_coords_sides(top, bottom, side):
    side = tex_coord(*side)
    result = []
    result.extend(side * 4)
    return result