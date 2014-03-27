from __future__ import division
from shutil import move

from pyglet.gl import * #TODO write tutorial onto how to install pyglet (latest version from mercurial repo), offer binaries
from pyglet.window import key
import sys
import math
import time
import os


from micropsi_core.world.MinecraftWorld.MinecraftVisualisation.structs import block_names, load_textures, has_sides, solid_blocks
from micropsi_core.world.MinecraftWorld.MinecraftVisualisation.vertices import cube_vertices, cube_vertices_sides, cube_vertices_top, human_vertices
from micropsi_core.world.MinecraftWorld.MinecraftVisualisation.tex_coords import tex_coords, tex_coords_sides, tex_coords_top

import io

SECTOR_SIZE = 16

WINDOW = None

vis_counter = 0


if sys.version_info[0] >= 3:
    xrange = range

FACES = [ #TODO find out what this is used for
    ( 0, 1, 0),
    #( 0,-1, 0),
    #(-1, 0, 0),
    #( 1, 0, 0),
    #( 0, 0, 1),
    #( 0, 0,-1),
]

def normalize(position):
    x, y, z = position
    x, y, z = (int(round(x)), int(round(y)), int(round(z)))
    return (x, y, z)

def sectorize(position):
    x, y, z = normalize(position)
    x, y, z = x // SECTOR_SIZE, y // SECTOR_SIZE, z // SECTOR_SIZE
    return (x, 0, z)

class Model(object):
    def __init__(self, client):
        self.batch = pyglet.graphics.Batch()
        print(os.getcwd())
        load_textures(self) #load custom texture pack
        self.world = {}
        self.type = {}
        self.shown = {}
        self._shown = {}
        self.sectors = {}
        self.queue = []
        self.client = client # Minecraft client "spock"
        self.initialize()
        self.last_known_botblock = (0,0,0)

    def initialize(self):
        n = 16 #What exactly does this do?

        x_chunk = self.client.position['x'] // 16
        z_chunk = self.client.position['z'] // 16
        bot_block = [self.client.position['x'], self.client.position['y'], self.client.position['z']]
        current_column = self.client.world.columns[(x_chunk, z_chunk)]

        for y in xrange(0, n):
            current_section = current_column.chunks[int((bot_block[1] + y - 10 // 2) // 16)] #TODO explain formula
            if current_section != None:
                for x in xrange(0, n):
                    for z in xrange(0, n):
                        current_block = current_section['block_data'].get(x, int((bot_block[1] + y - 10 // 2) % 16), z) #TODO explain formula
                        if (current_block in solid_blocks and current_block in (2, 14, 46)):
                            self.init_block((x, y, z), tex_coords((0, 0), (0, 0), (0, 0)), block_names[str(current_block)])
                        self.add_block((0, 0, 0), tex_coords((0, 0), (0, 0), (0, 0)), "human" )

    def reload(self):
        n = 16 #What exactly does this do?

        x_chunk = self.client.position['x'] // 16
        z_chunk = self.client.position['z'] // 16

        bot_block = [self.client.position['x'], self.client.position['y'], self.client.position['z']]
        current_column = self.client.world.columns[(x_chunk, z_chunk)]

        for y in xrange(0, n):
            current_section = current_column.chunks[int((bot_block[1] + y - 10 // 2) // 16)] #TODO explain formula
            if current_section != None:
                for x in xrange(0, n):
                    for z in xrange(0, n):
                        current_block = current_section['block_data'].get(x, int((bot_block[1] + y - 10 // 2) % 16), z) #TODO explain formula
                        if (current_block in solid_blocks and current_block in (2, 14, 56)):
                            self.init_block((x, y, z), tex_coords((0, 0), (0, 0), (0, 0)), block_names[str(current_block)])
                        if [int(self.client.position['x'] % 16), int((bot_block[1] + y - 10 // 2) // 16), int(self.client.position['z'] % 16)] == [x,y,z]:  #TODO explain formula
                            self.remove_block(self.last_known_botblock)
                            self.add_block((x, y+1, z), tex_coords((0, 0), (0, 0), (0, 0)), "human" )
                            self.last_known_botblock = (x, y+1, z)

    def exposed(self, position):
        x, y, z = position
        for dx, dy, dz in FACES:
            if (x + dx, y + dy, z + dz) not in self.world:
                return True
        return False

    def init_block(self, position, texture, type):
        self.add_block(position, texture, type, False)

    def add_block(self, position, texture, type, sync=True):
        if position in self.world:
            self.remove_block(position, sync)
        self.type[position] = type
        self.world[position] = texture
        self.sectors.setdefault(sectorize(position), []).append(position)
        #if sync:
        #    if self.exposed(position): #TODO if this is active, only blocks on top get drawn. why?
        self.show_block(position)
        #    self.check_neighbors(position)

    def remove_block(self, position, sync=True):
        del self.world[position]
        self.sectors[sectorize(position)].remove(position)
        if sync:
            if position in self.shown:
                self.hide_block(position)
            self.check_neighbors(position)

    def check_neighbors(self, position):
        x, y, z = position
        for dx, dy, dz in FACES:
            key = (x + dx, y + dy, z + dz)
            if key not in self.world:
                continue
            if self.exposed(key):
                if key not in self.shown:
                    self.show_own_block(key)
            else:
                if key in self.shown:
                    self.hide_block(key)

    def show_blocks(self):
        for position in self.world:
            if position not in self.shown and self.exposed(position):
                self.show_own_block(position)

    def show_block(self, position, immediate=True):
        texture = self.world[position]
        self.shown[position] = texture
        if immediate:
            self._show_block(position, texture)
        else:
            self.enqueue(self._show_block, position, texture)

    def show_own_block(self, position, immediate=True):
        texture = self.world[position]
        self.shown[position] = texture
        if immediate:
            self._show_own_block(position, texture)
        else:
            self.enqueue(self._show_own_block, position, texture)

    def _show_block(self, position, texture):
        x, y, z = position

        if self.type[position] in has_sides: #TODO make smarter
            count = 4
            vertex_data = cube_vertices_top(x, y, z, 0.5)
            texture_data = list(tex_coords_top((0, 0), (0, 0), (0, 0)))
            self._shown[position] = self.batch.add(count, GL_QUADS, self.texturepack[self.type[position]],
                    ('v3f/static', vertex_data),
                    ('t2f/static', texture_data))

            vertex_data = cube_vertices_sides(x, y, z, 0.5)
            texture_data = list(tex_coords_sides((0, 0), (0, 0), (0, 0)))
            self._shown[position] = self.batch.add(16, GL_QUADS, self.side_files[self.type[position]],
                ('v3f/static', vertex_data),
                ('t2f/static', texture_data))

        if self.type[position] == "human":
            count = 24
            vertex_data = human_vertices(x, y, z, 0.5)
            texture_data = list(tex_coords((0, 0), (0, 0), (0, 0)))
            # create vertex list
            self._shown[position] = self.batch.add(count, GL_QUADS, self.texturepack[self.type[position]],
                    ('v3f/static', vertex_data),
                    ('t2f/static', texture_data))

        else:
            count = 24
            vertex_data = cube_vertices(x, y, z, 0.5)
            texture_data = list(tex_coords((0, 0), (0, 0), (0, 0)))
            # create vertex list
            self._shown[position] = self.batch.add(count, GL_QUADS, self.texturepack[self.type[position]],
                    ('v3f/static', vertex_data),
                    ('t2f/static', texture_data))

    def hide_block(self, position, immediate=True):
        self.shown.pop(position)
        if immediate:
            self._hide_block(position)
        else:
            self.enqueue(self._hide_block, position)

    def _hide_block(self, position):
        self._shown.pop(position).delete()

    def show_sector(self, sector):
        for position in self.sectors.get(sector, []):
            if position not in self.shown and self.exposed(position):
                self.show_block(position, False)

    def hide_sector(self, sector):
        for position in self.sectors.get(sector, []):
            if position in self.shown:
                self.hide_block(position, False)

    def change_sectors(self, before, after):
        before_set = set()
        after_set = set()
        pad = 4
        for dx in xrange(-pad, pad + 1):
            for dy in [0]: # xrange(-pad, pad + 1):
                for dz in xrange(-pad, pad + 1):
                    if dx ** 2 + dy ** 2 + dz ** 2 > (pad + 1) ** 2:
                        continue
                    if before:
                        x, y, z = before
                        before_set.add((x + dx, y + dy, z + dz))
                    if after:
                        x, y, z = after
                        after_set.add((x + dx, y + dy, z + dz))
        show = after_set - before_set
        hide = before_set - after_set
        for sector in show:
            self.show_sector(sector)
        for sector in hide:
            self.hide_sector(sector)

    def enqueue(self, func, *args):
        self.queue.append((func, args))

    def dequeue(self):
        func, args = self.queue.pop(0)
        func(*args)

    def process_queue(self):
        start = time.clock()
        while self.queue and time.clock() - start < 1 / 60.0:
            self.dequeue()

    def process_entire_queue(self):
        while self.queue:
            self.dequeue()

class Window(pyglet.window.Window):
    def __init__(self, client, *args, **kwargs):
        super(Window, self).__init__(*args, **kwargs)
        self.exclusive = False
        self.flying = True
        self.strafe = [0, 0]
        self.position = (0, 16, 16)
        self.rotation = (45, -45) # first left,right - second up,down
        self.sector = None
        self.reticle = None
        self.dy = 0
        self.num_keys = [
            key._1, key._2, key._3, key._4, key._5,
            key._6, key._7, key._8, key._9, key._0]
        self.client = client #Minecraft Client "spock"
        self.model = Model(self.client)
        self.label = pyglet.text.Label('', font_name='Arial', font_size=18, 
            x=10, y=self.height - 10, anchor_x='left', anchor_y='top', 
            color=(0, 0, 0, 255))
        pyglet.clock.schedule_interval(self.update, 1.0 / 60)

    def get_sight_vector(self):
        x, y = self.rotation
        m = math.cos(math.radians(y))
        dy = math.sin(math.radians(y))
        dx = math.cos(math.radians(x - 90)) * m
        dz = math.sin(math.radians(x - 90)) * m
        return (dx, dy, dz)

    def get_motion_vector(self):
        if any(self.strafe):
            x, y = self.rotation
            strafe = math.degrees(math.atan2(*self.strafe))
            if self.flying:
                m = math.cos(math.radians(y))
                dy = math.sin(math.radians(y))
                if self.strafe[1]:
                    dy = 0.0
                    m = 1
                if self.strafe[0] > 0:
                    dy *= -1
                dx = math.cos(math.radians(x + strafe)) * m
                dz = math.sin(math.radians(x + strafe)) * m
            else:
                dy = 0.0
                dx = math.cos(math.radians(x + strafe))
                dz = math.sin(math.radians(x + strafe))
        else:
            dy = 0.0
            dx = 0.0
            dz = 0.0
        return (dx, dy, dz)

    def update(self, dt):
        self.model.process_queue()
        sector = sectorize(self.position)
        if sector != self.sector:
            self.model.change_sectors(self.sector, sector)
            if self.sector is None:
                self.model.process_entire_queue()
            self.sector = sector
        m = 8
        dt = min(dt, 0.2)
        for _ in xrange(m):
            self._update(dt / m)

    def _update(self, dt):
        # walking
        speed = 15 if self.flying else 5
        d = dt * speed
        dx, dy, dz = self.get_motion_vector()
        dx, dy, dz = dx * d, dy * d, dz * d
        # gravity
        if not self.flying:
            self.dy -= dt * 0.00044 # g force, should be = jump_speed * 0.5 / max_jump_height
            self.dy = max(self.dy, -0.5) # terminal velocity
            dy += self.dy
        # collisions
        x, y, z = self.position
        x, y, z = self.collide((x + dx, y + dy, z + dz), 2)
        self.position = (x, y, z)

    def collide(self, position, height):
        pad = 0.25
        p = list(position)
        np = normalize(position)
        for face in FACES: # check all surrounding blocks
            for i in xrange(3): # check each dimension independently
                if not face[i]:
                    continue
                d = (p[i] - np[i]) * face[i]
                if d < pad:
                    continue
                for dy in xrange(height): # check each height
                    op = list(np)
                    op[1] -= dy
                    op[i] += face[i]
                    op = tuple(op)
                    if op not in self.model.world:
                        continue
                    p[i] -= (d - pad) * face[i]
                    if face == (0, -1, 0) or face == (0, 1, 0):
                        self.dy = 0
                    break
        return tuple(p)

    def set_2d(self):
        width, height = self.get_size()
        glDisable(GL_DEPTH_TEST)
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, width, 0, height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def set_3d(self):
        width, height = self.get_size()
        glEnable(GL_DEPTH_TEST)
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(65.0, width / float(height), 0.1, 60.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        x, y = self.rotation
        glRotatef(x, 0, 1, 0)
        glRotatef(-y, math.cos(math.radians(x)), 0, math.sin(math.radians(x)))
        x, y, z = self.position
        glTranslatef(-x, -y, -z)

    def on_draw(self):
        self.clear()
        self.set_3d()
        glColor3d(1, 1, 1)
        self.model.batch.draw()
        self.set_2d()
        self.draw_label()

    def draw_label(self):
        x, y, z = self.position
        global vis_counter
        self.label.text = 'i=%d %02d (%.2f, %.2f, %.2f) %d / %d i=%d' % (vis_counter,
            pyglet.clock.get_fps(), x, y, z, 
            len(self.model._shown), len(self.model.world), vis_counter)
        vis_counter += 1
        self.label.draw()

class MinecraftVisualisation:
    def __init__(self, minecraftClient):
        self.minecraftClient = minecraftClient

    def setup(self):
        glClearColor(0.5, 0.69, 1.0, 1)
        glEnable(GL_CULL_FACE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

    def commence_vis(self):
        global window
        window = Window(self.minecraftClient, width=400, height=300, caption='Pyglet', resizable=True, visible=False)
        self.setup()
        for i in range(0,3): #TODO make smarter
            self.advanceVisualisation()

    def advanceVisualisation(self):
        pyglet.clock.tick()
        output = io.BytesIO()
        pyglet.image.get_buffer_manager().get_color_buffer().save(file=output)
        #image = output.getvalue()
        ##output.close()

        global window #TODO try to avoid global
        window.switch_to()
        window.model.reload()
        window.dispatch_events()
        window.dispatch_event('on_draw')
        window.flip()
        return output