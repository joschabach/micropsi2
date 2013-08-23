__author__ = 'jonas'

def cube_vertices(x, y, z, n):
    return [
        x-n,y+n,z-n, x-n,y+n,z+n, x+n,y+n,z+n, x+n,y+n,z-n, # top
        x-n,y-n,z-n, x+n,y-n,z-n, x+n,y-n,z+n, x-n,y-n,z+n, # bottom
        x-n,y-n,z-n, x-n,y-n,z+n, x-n,y+n,z+n, x-n,y+n,z-n, # left
        x+n,y-n,z+n, x+n,y-n,z-n, x+n,y+n,z-n, x+n,y+n,z+n, # right
        x-n,y-n,z+n, x+n,y-n,z+n, x+n,y+n,z+n, x-n,y+n,z+n, # front
        x+n,y-n,z-n, x-n,y-n,z-n, x-n,y+n,z-n, x+n,y+n,z-n, # back
    ]

def cube_vertices_top(x, y, z, n):
    return [
        x-n,y+n,z-n, x-n,y+n,z+n, x+n,y+n,z+n, x+n,y+n,z-n, # top
    ]

def cube_vertices_sides(x, y, z, n):
    return [
        x-n,y-n,z-n, x-n,y-n,z+n, x-n,y+n,z+n, x-n,y+n,z-n, # left
        x+n,y-n,z+n, x+n,y-n,z-n, x+n,y+n,z-n, x+n,y+n,z+n, # right
        x-n,y-n,z+n, x+n,y-n,z+n, x+n,y+n,z+n, x-n,y+n,z+n, # front
        x+n,y-n,z-n, x-n,y-n,z-n, x-n,y+n,z-n, x+n,y+n,z-n, # back
    ]

def human_vertices(x, y, z, n): #two blocks high
    return [
        x-n,y+n+1,z-n, x-n,y+n+1,z+n, x+n,y+n+1,z+n, x+n,y+n+1,z-n, # top
        x-n,y-n,z-n, x+n,y-n,z-n, x+n,y-n,z+n, x-n,y-n,z+n, # bottom
        x-n,y-n,z-n, x-n,y-n,z+n, x-n,y+n+1,z+n, x-n,y+n+1,z-n, # left
        x+n,y-n,z+n, x+n,y-n,z-n, x+n,y+n+1,z-n, x+n,y+n+1,z+n, # right
        x-n,y-n,z+n, x+n,y-n,z+n, x+n,y+n+1,z+n, x-n,y+n+1,z+n, # front
        x+n,y-n,z-n, x-n,y-n,z-n, x-n,y+n+1,z-n, x+n,y+n+1,z-n, # back
    ]