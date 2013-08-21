from __future__ import division
from shutil import move

from pyglet.gl import *
from pyglet.window import key
import sys
import math
import time
import os

SECTOR_SIZE = 16

WINDOW = None


if sys.version_info[0] >= 3:
    xrange = range

def cube_vertices(x, y, z, n):
    return [
        x-n,y+n,z-n, x-n,y+n,z+n, x+n,y+n,z+n, x+n,y+n,z-n, # top
        x-n,y-n,z-n, x+n,y-n,z-n, x+n,y-n,z+n, x-n,y-n,z+n, # bottom
        x-n,y-n,z-n, x-n,y-n,z+n, x-n,y+n,z+n, x-n,y+n,z-n, # left
        x+n,y-n,z+n, x+n,y-n,z-n, x+n,y+n,z-n, x+n,y+n,z+n, # right
        x-n,y-n,z+n, x+n,y-n,z+n, x+n,y+n,z+n, x-n,y+n,z+n, # front
        x+n,y-n,z-n, x-n,y-n,z-n, x-n,y+n,z-n, x+n,y+n,z-n, # back
    ]

def tex_coord(x, y, n=1):
    m = 1.0 / n
    dx = x * m
    dy = y * m
    return dx, dy, dx + m, dy, dx + m, dy + m, dx, dy + m

def tex_coords(top, bottom, side):
    top = tex_coord(*top)
    bottom = tex_coord(*bottom)
    side = tex_coord(*side)
    result = []
    result.extend(top)
    result.extend(bottom)
    result.extend(side * 4)
    return result

GRASS = tex_coords((1, 0), (0, 1), (0, 0))# (row, line)
SAND = tex_coords((1, 1), (1, 1), (1, 1))
BRICK = tex_coords((2, 0), (2, 0), (2, 0))
GOLDORE = tex_coords((0, 0), (0, 0), (0, 0))
STONE = tex_coords((2, 1), (2, 1), (2, 1))
HUMAN = tex_coords((3, 2), (3, 2), (3, 1))

FACES = [
    ( 0, 1, 0),
    ( 0,-1, 0),
    (-1, 0, 0),
    ( 1, 0, 0),
    ( 0, 0, 1),
    ( 0, 0,-1),
]

class TextureGroup(pyglet.graphics.Group):
    def __init__(self, path):
        super(TextureGroup, self).__init__()
        self.texture = pyglet.image.load(path).get_texture()
    def set_state(self):
        glEnable(self.texture.target)
        glBindTexture(self.texture.target, self.texture.id)
    def unset_state(self):
        glDisable(self.texture.target)

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
        self.group = TextureGroup('micropsi_core/world/minecraft/vis/texture.png')
        self.texture_activatorRail = TextureGroup('micropsi_core/world/minecraft/vis/activatorRail.png')
        self.texture_activatorRail_powered = TextureGroup('micropsi_core/world/minecraft/vis/activatorRail_powered.png')
        self.texture_anvil_base = TextureGroup('micropsi_core/world/minecraft/vis/anvil_base.png')
        self.texture_anvil_top = TextureGroup('micropsi_core/world/minecraft/vis/anvil_top.png')
        self.texture_anvil_top_damaged_1 = TextureGroup('micropsi_core/world/minecraft/vis/anvil_top_damaged_1.png')
        self.texture_anvil_top_damaged_2 = TextureGroup('micropsi_core/world/minecraft/vis/anvil_top_damaged_2.png')
        self.texture_beacon = TextureGroup('micropsi_core/world/minecraft/vis/beacon.png')
        self.texture_bed_feet_end = TextureGroup('micropsi_core/world/minecraft/vis/bed_feet_end.png')
        self.texture_bed_feet_side = TextureGroup('micropsi_core/world/minecraft/vis/bed_feet_side.png')
        self.texture_bed_feet_top = TextureGroup('micropsi_core/world/minecraft/vis/bed_feet_top.png')
        self.texture_bed_head_end = TextureGroup('micropsi_core/world/minecraft/vis/bed_head_end.png')
        self.texture_bed_head_side = TextureGroup('micropsi_core/world/minecraft/vis/bed_head_side.png')
        self.texture_bed_head_top = TextureGroup('micropsi_core/world/minecraft/vis/bed_head_top.png')
        self.texture_bedrock = TextureGroup('micropsi_core/world/minecraft/vis/bedrock.png')
        self.texture_blockDiamond = TextureGroup('micropsi_core/world/minecraft/vis/blockDiamond.png')
        self.texture_blockEmerald = TextureGroup('micropsi_core/world/minecraft/vis/blockEmerald.png')
        self.texture_blockGold = TextureGroup('micropsi_core/world/minecraft/vis/blockGold.png')
        self.texture_blockIron = TextureGroup('micropsi_core/world/minecraft/vis/blockIron.png')
        self.texture_blockLapis = TextureGroup('micropsi_core/world/minecraft/vis/blockLapis.png')
        self.texture_blockRedstone = TextureGroup('micropsi_core/world/minecraft/vis/blockRedstone.png')
        self.texture_bookshelf = TextureGroup('micropsi_core/world/minecraft/vis/bookshelf.png')
        self.texture_brewingStand = TextureGroup('micropsi_core/world/minecraft/vis/brewingStand.png')
        self.texture_brewingStand_base = TextureGroup('micropsi_core/world/minecraft/vis/brewingStand_base.png')
        self.texture_brick = TextureGroup('micropsi_core/world/minecraft/vis/brick.png')
        self.texture_cactus_bottom = TextureGroup('micropsi_core/world/minecraft/vis/cactus_bottom.png')
        self.texture_cactus_side = TextureGroup('micropsi_core/world/minecraft/vis/cactus_side.png')
        self.texture_cactus_top = TextureGroup('micropsi_core/world/minecraft/vis/cactus_top.png')
        self.texture_cake_bottom = TextureGroup('micropsi_core/world/minecraft/vis/cake_bottom.png')
        self.texture_cake_inner = TextureGroup('micropsi_core/world/minecraft/vis/cake_inner.png')
        self.texture_cake_side = TextureGroup('micropsi_core/world/minecraft/vis/cake_side.png')
        self.texture_cake_top = TextureGroup('micropsi_core/world/minecraft/vis/cake_top.png')
        self.texture_carrots_0 = TextureGroup('micropsi_core/world/minecraft/vis/carrots_0.png')
        self.texture_carrots_1 = TextureGroup('micropsi_core/world/minecraft/vis/carrots_1.png')
        self.texture_carrots_2 = TextureGroup('micropsi_core/world/minecraft/vis/carrots_2.png')
        self.texture_carrots_3 = TextureGroup('micropsi_core/world/minecraft/vis/carrots_3.png')
        self.texture_cauldron_bottom = TextureGroup('micropsi_core/world/minecraft/vis/cauldron_bottom.png')
        self.texture_cauldron_inner = TextureGroup('micropsi_core/world/minecraft/vis/cauldron_inner.png')
        self.texture_cauldron_side = TextureGroup('micropsi_core/world/minecraft/vis/cauldron_side.png')
        self.texture_cauldron_top = TextureGroup('micropsi_core/world/minecraft/vis/cauldron_top.png')
        self.texture_clay = TextureGroup('micropsi_core/world/minecraft/vis/clay.png')
        self.texture_cloth_0 = TextureGroup('micropsi_core/world/minecraft/vis/cloth_0.png')
        self.texture_cloth_1 = TextureGroup('micropsi_core/world/minecraft/vis/cloth_1.png')
        self.texture_cloth_10 = TextureGroup('micropsi_core/world/minecraft/vis/cloth_10.png')
        self.texture_cloth_11 = TextureGroup('micropsi_core/world/minecraft/vis/cloth_11.png')
        self.texture_cloth_12 = TextureGroup('micropsi_core/world/minecraft/vis/cloth_12.png')
        self.texture_cloth_13 = TextureGroup('micropsi_core/world/minecraft/vis/cloth_13.png')
        self.texture_cloth_14 = TextureGroup('micropsi_core/world/minecraft/vis/cloth_14.png')
        self.texture_cloth_15 = TextureGroup('micropsi_core/world/minecraft/vis/cloth_15.png')
        self.texture_cloth_2 = TextureGroup('micropsi_core/world/minecraft/vis/cloth_2.png')
        self.texture_cloth_3 = TextureGroup('micropsi_core/world/minecraft/vis/cloth_3.png')
        self.texture_cloth_4 = TextureGroup('micropsi_core/world/minecraft/vis/cloth_4.png')
        self.texture_cloth_5 = TextureGroup('micropsi_core/world/minecraft/vis/cloth_5.png')
        self.texture_cloth_6 = TextureGroup('micropsi_core/world/minecraft/vis/cloth_6.png')
        self.texture_cloth_7 = TextureGroup('micropsi_core/world/minecraft/vis/cloth_7.png')
        self.texture_cloth_8 = TextureGroup('micropsi_core/world/minecraft/vis/cloth_8.png')
        self.texture_cloth_9 = TextureGroup('micropsi_core/world/minecraft/vis/cloth_9.png')
        self.texture_cocoa_0 = TextureGroup('micropsi_core/world/minecraft/vis/cocoa_0.png')
        self.texture_cocoa_1 = TextureGroup('micropsi_core/world/minecraft/vis/cocoa_1.png')
        self.texture_cocoa_2 = TextureGroup('micropsi_core/world/minecraft/vis/cocoa_2.png')
        self.texture_commandBlock = TextureGroup('micropsi_core/world/minecraft/vis/commandBlock.png')
        self.texture_comparator = TextureGroup('micropsi_core/world/minecraft/vis/comparator.png')
        self.texture_comparator_lit = TextureGroup('micropsi_core/world/minecraft/vis/comparator_lit.png')
        self.texture_crops_0 = TextureGroup('micropsi_core/world/minecraft/vis/crops_0.png')
        self.texture_crops_1 = TextureGroup('micropsi_core/world/minecraft/vis/crops_1.png')
        self.texture_crops_2 = TextureGroup('micropsi_core/world/minecraft/vis/crops_2.png')
        self.texture_crops_3 = TextureGroup('micropsi_core/world/minecraft/vis/crops_3.png')
        self.texture_crops_4 = TextureGroup('micropsi_core/world/minecraft/vis/crops_4.png')
        self.texture_crops_5 = TextureGroup('micropsi_core/world/minecraft/vis/crops_5.png')
        self.texture_crops_6 = TextureGroup('micropsi_core/world/minecraft/vis/crops_6.png')
        self.texture_crops_7 = TextureGroup('micropsi_core/world/minecraft/vis/crops_7.png')
        self.texture_daylightDetector_side = TextureGroup('micropsi_core/world/minecraft/vis/daylightDetector_side.png')
        self.texture_daylightDetector_top = TextureGroup('micropsi_core/world/minecraft/vis/daylightDetector_top.png')
        self.texture_deadbush = TextureGroup('micropsi_core/world/minecraft/vis/deadbush.png')
        self.texture_destroy_0 = TextureGroup('micropsi_core/world/minecraft/vis/destroy_0.png')
        self.texture_destroy_1 = TextureGroup('micropsi_core/world/minecraft/vis/destroy_1.png')
        self.texture_destroy_2 = TextureGroup('micropsi_core/world/minecraft/vis/destroy_2.png')
        self.texture_destroy_3 = TextureGroup('micropsi_core/world/minecraft/vis/destroy_3.png')
        self.texture_destroy_4 = TextureGroup('micropsi_core/world/minecraft/vis/destroy_4.png')
        self.texture_destroy_5 = TextureGroup('micropsi_core/world/minecraft/vis/destroy_5.png')
        self.texture_destroy_6 = TextureGroup('micropsi_core/world/minecraft/vis/destroy_6.png')
        self.texture_destroy_7 = TextureGroup('micropsi_core/world/minecraft/vis/destroy_7.png')
        self.texture_destroy_8 = TextureGroup('micropsi_core/world/minecraft/vis/destroy_8.png')
        self.texture_destroy_9 = TextureGroup('micropsi_core/world/minecraft/vis/destroy_9.png')
        self.texture_detectorRail = TextureGroup('micropsi_core/world/minecraft/vis/detectorRail.png')
        self.texture_dirt = TextureGroup('micropsi_core/world/minecraft/vis/dirt.png')
        self.texture_dispenser_front = TextureGroup('micropsi_core/world/minecraft/vis/dispenser_front.png')
        self.texture_dispenser_front_vertical = TextureGroup('micropsi_core/world/minecraft/vis/dispenser_front_vertical.png')
        self.texture_doorIron_lower = TextureGroup('micropsi_core/world/minecraft/vis/doorIron_lower.png')
        self.texture_doorIron_upper = TextureGroup('micropsi_core/world/minecraft/vis/doorIron_upper.png')
        self.texture_doorWood_lower = TextureGroup('micropsi_core/world/minecraft/vis/doorWood_lower.png')
        self.texture_doorWood_upper = TextureGroup('micropsi_core/world/minecraft/vis/doorWood_upper.png')
        self.texture_dragonEgg = TextureGroup('micropsi_core/world/minecraft/vis/dragonEgg.png')
        self.texture_dropper_front = TextureGroup('micropsi_core/world/minecraft/vis/dropper_front.png')
        self.texture_dropper_front_vertical = TextureGroup('micropsi_core/world/minecraft/vis/dropper_front_vertical.png')
        self.texture_enchantment_bottom = TextureGroup('micropsi_core/world/minecraft/vis/enchantment_bottom.png')
        self.texture_enchantment_side = TextureGroup('micropsi_core/world/minecraft/vis/enchantment_side.png')
        self.texture_enchantment_top = TextureGroup('micropsi_core/world/minecraft/vis/enchantment_top.png')
        self.texture_endframe_eye = TextureGroup('micropsi_core/world/minecraft/vis/endframe_eye.png')
        self.texture_endframe_side = TextureGroup('micropsi_core/world/minecraft/vis/endframe_side.png')
        self.texture_endframe_top = TextureGroup('micropsi_core/world/minecraft/vis/endframe_top.png')
        self.texture_farmland_dry = TextureGroup('micropsi_core/world/minecraft/vis/farmland_dry.png')
        self.texture_farmland_wet = TextureGroup('micropsi_core/world/minecraft/vis/farmland_wet.png')
        self.texture_fenceIron = TextureGroup('micropsi_core/world/minecraft/vis/fenceIron.png')
        self.texture_fern = TextureGroup('micropsi_core/world/minecraft/vis/fern.png')
        self.texture_fire_0 = TextureGroup('micropsi_core/world/minecraft/vis/fire_0.png')
        self.texture_fire_0 = TextureGroup('micropsi_core/world/minecraft/vis/fire_0.png')
        self.texture_fire_1 = TextureGroup('micropsi_core/world/minecraft/vis/fire_1.png')
        self.texture_fire_1 = TextureGroup('micropsi_core/world/minecraft/vis/fire_1.png')
        self.texture_flower = TextureGroup('micropsi_core/world/minecraft/vis/flower.png')
        self.texture_flowerPot = TextureGroup('micropsi_core/world/minecraft/vis/flowerPot.png')
        self.texture_furnace_front = TextureGroup('micropsi_core/world/minecraft/vis/furnace_front.png')
        self.texture_furnace_front_lit = TextureGroup('micropsi_core/world/minecraft/vis/furnace_front_lit.png')
        self.texture_furnace_side = TextureGroup('micropsi_core/world/minecraft/vis/furnace_side.png')
        self.texture_furnace_top = TextureGroup('micropsi_core/world/minecraft/vis/furnace_top.png')
        self.texture_glass = TextureGroup('micropsi_core/world/minecraft/vis/glass.png')
        self.texture_goldenRail = TextureGroup('micropsi_core/world/minecraft/vis/goldenRail.png')
        self.texture_goldenRail_powered = TextureGroup('micropsi_core/world/minecraft/vis/goldenRail_powered.png')
        self.texture_grass_side = TextureGroup('micropsi_core/world/minecraft/vis/grass_side.png')
        self.texture_grass_side_overlay = TextureGroup('micropsi_core/world/minecraft/vis/grass_side_overlay.png')
        self.texture_grass_top = TextureGroup('micropsi_core/world/minecraft/vis/grass_top.png')
        self.texture_gravel = TextureGroup('micropsi_core/world/minecraft/vis/gravel.png')
        self.texture_hellrock = TextureGroup('micropsi_core/world/minecraft/vis/hellrock.png')
        self.texture_hellsand = TextureGroup('micropsi_core/world/minecraft/vis/hellsand.png')
        self.texture_hopper = TextureGroup('micropsi_core/world/minecraft/vis/hopper.png')
        self.texture_hopper_inside = TextureGroup('micropsi_core/world/minecraft/vis/hopper_inside.png')
        self.texture_hopper_top = TextureGroup('micropsi_core/world/minecraft/vis/hopper_top.png')
        self.texture_ice = TextureGroup('micropsi_core/world/minecraft/vis/ice.png')
        self.texture_itemframe_back = TextureGroup('micropsi_core/world/minecraft/vis/itemframe_back.png')
        self.texture_jukebox_top = TextureGroup('micropsi_core/world/minecraft/vis/jukebox_top.png')
        self.texture_ladder = TextureGroup('micropsi_core/world/minecraft/vis/ladder.png')
        self.texture_lava = TextureGroup('micropsi_core/world/minecraft/vis/lava.png')
        self.texture_lava = TextureGroup('micropsi_core/world/minecraft/vis/lava.png')
        self.texture_lava_flow = TextureGroup('micropsi_core/world/minecraft/vis/lava_flow.png')
        self.texture_lava_flow = TextureGroup('micropsi_core/world/minecraft/vis/lava_flow.png')
        self.texture_leaves = TextureGroup('micropsi_core/world/minecraft/vis/leaves.png')
        self.texture_leaves_jungle = TextureGroup('micropsi_core/world/minecraft/vis/leaves_jungle.png')
        self.texture_leaves_jungle_opaque = TextureGroup('micropsi_core/world/minecraft/vis/leaves_jungle_opaque.png')
        self.texture_leaves_opaque = TextureGroup('micropsi_core/world/minecraft/vis/leaves_opaque.png')
        self.texture_leaves_spruce = TextureGroup('micropsi_core/world/minecraft/vis/leaves_spruce.png')
        self.texture_leaves_spruce_opaque = TextureGroup('micropsi_core/world/minecraft/vis/leaves_spruce_opaque.png')
        self.texture_lever = TextureGroup('micropsi_core/world/minecraft/vis/lever.png')
        self.texture_lightgem = TextureGroup('micropsi_core/world/minecraft/vis/lightgem.png')
        self.texture_melon_side = TextureGroup('micropsi_core/world/minecraft/vis/melon_side.png')
        self.texture_melon_top = TextureGroup('micropsi_core/world/minecraft/vis/melon_top.png')
        self.texture_mobSpawner = TextureGroup('micropsi_core/world/minecraft/vis/mobSpawner.png')
        self.texture_mushroom_brown = TextureGroup('micropsi_core/world/minecraft/vis/mushroom_brown.png')
        self.texture_mushroom_inside = TextureGroup('micropsi_core/world/minecraft/vis/mushroom_inside.png')
        self.texture_mushroom_red = TextureGroup('micropsi_core/world/minecraft/vis/mushroom_red.png')
        self.texture_mushroom_skin_brown = TextureGroup('micropsi_core/world/minecraft/vis/mushroom_skin_brown.png')
        self.texture_mushroom_skin_red = TextureGroup('micropsi_core/world/minecraft/vis/mushroom_skin_red.png')
        self.texture_mushroom_skin_stem = TextureGroup('micropsi_core/world/minecraft/vis/mushroom_skin_stem.png')
        self.texture_musicBlock = TextureGroup('micropsi_core/world/minecraft/vis/musicBlock.png')
        self.texture_mycel_side = TextureGroup('micropsi_core/world/minecraft/vis/mycel_side.png')
        self.texture_mycel_top = TextureGroup('micropsi_core/world/minecraft/vis/mycel_top.png')
        self.texture_netherBrick = TextureGroup('micropsi_core/world/minecraft/vis/netherBrick.png')
        self.texture_netherStalk_0 = TextureGroup('micropsi_core/world/minecraft/vis/netherStalk_0.png')
        self.texture_netherStalk_1 = TextureGroup('micropsi_core/world/minecraft/vis/netherStalk_1.png')
        self.texture_netherStalk_2 = TextureGroup('micropsi_core/world/minecraft/vis/netherStalk_2.png')
        self.texture_netherquartz = TextureGroup('micropsi_core/world/minecraft/vis/netherquartz.png')
        self.texture_obsidian = TextureGroup('micropsi_core/world/minecraft/vis/obsidian.png')
        self.texture_oreCoal = TextureGroup('micropsi_core/world/minecraft/vis/oreCoal.png')
        self.texture_oreDiamond = TextureGroup('micropsi_core/world/minecraft/vis/oreDiamond.png')
        self.texture_oreEmerald = TextureGroup('micropsi_core/world/minecraft/vis/oreEmerald.png')
        self.texture_oreGold = TextureGroup('micropsi_core/world/minecraft/vis/oreGold.png')
        self.texture_oreIron = TextureGroup('micropsi_core/world/minecraft/vis/oreIron.png')
        self.texture_oreLapis = TextureGroup('micropsi_core/world/minecraft/vis/oreLapis.png')
        self.texture_oreRedstone = TextureGroup('micropsi_core/world/minecraft/vis/oreRedstone.png')
        self.texture_piston_bottom = TextureGroup('micropsi_core/world/minecraft/vis/piston_bottom.png')
        self.texture_piston_inner_top = TextureGroup('micropsi_core/world/minecraft/vis/piston_inner_top.png')
        self.texture_piston_side = TextureGroup('micropsi_core/world/minecraft/vis/piston_side.png')
        self.texture_piston_top = TextureGroup('micropsi_core/world/minecraft/vis/piston_top.png')
        self.texture_piston_top_sticky = TextureGroup('micropsi_core/world/minecraft/vis/piston_top_sticky.png')
        self.texture_potatoes_0 = TextureGroup('micropsi_core/world/minecraft/vis/potatoes_0.png')
        self.texture_potatoes_1 = TextureGroup('micropsi_core/world/minecraft/vis/potatoes_1.png')
        self.texture_potatoes_2 = TextureGroup('micropsi_core/world/minecraft/vis/potatoes_2.png')
        self.texture_potatoes_3 = TextureGroup('micropsi_core/world/minecraft/vis/potatoes_3.png')
        self.texture_pumpkin_face = TextureGroup('micropsi_core/world/minecraft/vis/pumpkin_face.png')
        self.texture_pumpkin_jack = TextureGroup('micropsi_core/world/minecraft/vis/pumpkin_jack.png')
        self.texture_pumpkin_side = TextureGroup('micropsi_core/world/minecraft/vis/pumpkin_side.png')
        self.texture_pumpkin_top = TextureGroup('micropsi_core/world/minecraft/vis/pumpkin_top.png')
        self.texture_quartzblock_bottom = TextureGroup('micropsi_core/world/minecraft/vis/quartzblock_bottom.png')
        self.texture_quartzblock_chiseled = TextureGroup('micropsi_core/world/minecraft/vis/quartzblock_chiseled.png')
        self.texture_quartzblock_chiseled_top = TextureGroup('micropsi_core/world/minecraft/vis/quartzblock_chiseled_top.png')
        self.texture_quartzblock_lines = TextureGroup('micropsi_core/world/minecraft/vis/quartzblock_lines.png')
        self.texture_quartzblock_lines_top = TextureGroup('micropsi_core/world/minecraft/vis/quartzblock_lines_top.png')
        self.texture_quartzblock_side = TextureGroup('micropsi_core/world/minecraft/vis/quartzblock_side.png')
        self.texture_quartzblock_top = TextureGroup('micropsi_core/world/minecraft/vis/quartzblock_top.png')
        self.texture_rail = TextureGroup('micropsi_core/world/minecraft/vis/rail.png')
        self.texture_rail_turn = TextureGroup('micropsi_core/world/minecraft/vis/rail_turn.png')
        self.texture_redstoneDust_cross = TextureGroup('micropsi_core/world/minecraft/vis/redstoneDust_cross.png')
        self.texture_redstoneDust_cross_overlay = TextureGroup('micropsi_core/world/minecraft/vis/redstoneDust_cross_overlay.png')
        self.texture_redstoneDust_line = TextureGroup('micropsi_core/world/minecraft/vis/redstoneDust_line.png')
        self.texture_redstoneDust_line_overlay = TextureGroup('micropsi_core/world/minecraft/vis/redstoneDust_line_overlay.png')
        self.texture_redstoneLight = TextureGroup('micropsi_core/world/minecraft/vis/redstoneLight.png')
        self.texture_redstoneLight_lit = TextureGroup('micropsi_core/world/minecraft/vis/redstoneLight_lit.png')
        self.texture_redtorch = TextureGroup('micropsi_core/world/minecraft/vis/redtorch.png')
        self.texture_redtorch_lit = TextureGroup('micropsi_core/world/minecraft/vis/redtorch_lit.png')
        self.texture_reeds = TextureGroup('micropsi_core/world/minecraft/vis/reeds.png')
        self.texture_repeater = TextureGroup('micropsi_core/world/minecraft/vis/repeater.png')
        self.texture_repeater_lit = TextureGroup('micropsi_core/world/minecraft/vis/repeater_lit.png')
        self.texture_rose = TextureGroup('micropsi_core/world/minecraft/vis/rose.png')
        self.texture_sand = TextureGroup('micropsi_core/world/minecraft/vis/sand.png')
        self.texture_sandstone_bottom = TextureGroup('micropsi_core/world/minecraft/vis/sandstone_bottom.png')
        self.texture_sandstone_carved = TextureGroup('micropsi_core/world/minecraft/vis/sandstone_carved.png')
        self.texture_sandstone_side = TextureGroup('micropsi_core/world/minecraft/vis/sandstone_side.png')
        self.texture_sandstone_smooth = TextureGroup('micropsi_core/world/minecraft/vis/sandstone_smooth.png')
        self.texture_sandstone_top = TextureGroup('micropsi_core/world/minecraft/vis/sandstone_top.png')
        self.texture_sapling = TextureGroup('micropsi_core/world/minecraft/vis/sapling.png')
        self.texture_sapling_birch = TextureGroup('micropsi_core/world/minecraft/vis/sapling_birch.png')
        self.texture_sapling_jungle = TextureGroup('micropsi_core/world/minecraft/vis/sapling_jungle.png')
        self.texture_sapling_spruce = TextureGroup('micropsi_core/world/minecraft/vis/sapling_spruce.png')
        self.texture_snow = TextureGroup('micropsi_core/world/minecraft/vis/snow.png')
        self.texture_snow_side = TextureGroup('micropsi_core/world/minecraft/vis/snow_side.png')
        self.texture_sponge = TextureGroup('micropsi_core/world/minecraft/vis/sponge.png')
        self.texture_stem_bent = TextureGroup('micropsi_core/world/minecraft/vis/stem_bent.png')
        self.texture_stem_straight = TextureGroup('micropsi_core/world/minecraft/vis/stem_straight.png')
        self.texture_stone = TextureGroup('micropsi_core/world/minecraft/vis/stone.png')
        self.texture_stoneMoss = TextureGroup('micropsi_core/world/minecraft/vis/stoneMoss.png')
        self.texture_stonebrick = TextureGroup('micropsi_core/world/minecraft/vis/stonebrick.png')
        self.texture_stonebricksmooth = TextureGroup('micropsi_core/world/minecraft/vis/stonebricksmooth.png')
        self.texture_stonebricksmooth_carved = TextureGroup('micropsi_core/world/minecraft/vis/stonebricksmooth_carved.png')
        self.texture_stonebricksmooth_cracked = TextureGroup('micropsi_core/world/minecraft/vis/stonebricksmooth_cracked.png')
        self.texture_stonebricksmooth_mossy = TextureGroup('micropsi_core/world/minecraft/vis/stonebricksmooth_mossy.png')
        self.texture_stoneslab_side = TextureGroup('micropsi_core/world/minecraft/vis/stoneslab_side.png')
        self.texture_stoneslab_top = TextureGroup('micropsi_core/world/minecraft/vis/stoneslab_top.png')
        self.texture_tallgrass = TextureGroup('micropsi_core/world/minecraft/vis/tallgrass.png')
        self.texture_thinglass_top = TextureGroup('micropsi_core/world/minecraft/vis/thinglass_top.png')
        self.texture_tnt_bottom = TextureGroup('micropsi_core/world/minecraft/vis/tnt_bottom.png')
        self.texture_tnt_side = TextureGroup('micropsi_core/world/minecraft/vis/tnt_side.png')
        self.texture_tnt_top = TextureGroup('micropsi_core/world/minecraft/vis/tnt_top.png')
        self.texture_torch = TextureGroup('micropsi_core/world/minecraft/vis/torch.png')
        self.texture_trapdoor = TextureGroup('micropsi_core/world/minecraft/vis/trapdoor.png')
        self.texture_tree_birch = TextureGroup('micropsi_core/world/minecraft/vis/tree_birch.png')
        self.texture_tree_jungle = TextureGroup('micropsi_core/world/minecraft/vis/tree_jungle.png')
        self.texture_tree_side = TextureGroup('micropsi_core/world/minecraft/vis/tree_side.png')
        self.texture_tree_spruce = TextureGroup('micropsi_core/world/minecraft/vis/tree_spruce.png')
        self.texture_tree_top = TextureGroup('micropsi_core/world/minecraft/vis/tree_top.png')
        self.texture_tripWire = TextureGroup('micropsi_core/world/minecraft/vis/tripWire.png')
        self.texture_tripWireSource = TextureGroup('micropsi_core/world/minecraft/vis/tripWireSource.png')
        self.texture_vine = TextureGroup('micropsi_core/world/minecraft/vis/vine.png')
        self.texture_water = TextureGroup('micropsi_core/world/minecraft/vis/water.png')
        self.texture_water = TextureGroup('micropsi_core/world/minecraft/vis/water.png')
        self.texture_water_flow = TextureGroup('micropsi_core/world/minecraft/vis/water_flow.png')
        self.texture_water_flow = TextureGroup('micropsi_core/world/minecraft/vis/water_flow.png')
        self.texture_waterlily = TextureGroup('micropsi_core/world/minecraft/vis/waterlily.png')
        self.texture_web = TextureGroup('micropsi_core/world/minecraft/vis/web.png')
        self.texture_whiteStone = TextureGroup('micropsi_core/world/minecraft/vis/whiteStone.png')
        self.texture_wood = TextureGroup('micropsi_core/world/minecraft/vis/wood.png')
        self.texture_wood_birch = TextureGroup('micropsi_core/world/minecraft/vis/wood_birch.png')
        self.texture_wood_jungle = TextureGroup('micropsi_core/world/minecraft/vis/wood_jungle.png')
        self.texture_wood_spruce = TextureGroup('micropsi_core/world/minecraft/vis/wood_spruce.png')
        self.texture_workbench_front = TextureGroup('micropsi_core/world/minecraft/vis/workbench_front.png')
        self.texture_workbench_side = TextureGroup('micropsi_core/world/minecraft/vis/workbench_side.png')
        self.texture_workbench_top = TextureGroup('micropsi_core/world/minecraft/vis/workbench_top.png')
        self.block_names = {'1': "stone",
                            '2': "grass_top",
                            '3': "dirt",
                            '4': "stonebrick",
                            '5': "wood",
                            '6': "sapling",
                            '7': "bedrock",
                            '8': "water",
                            '9': "water",
                            '10': "lava",
                            '11': "lava",
                            '12': "sand",
                            '13': "gravel",
                            '14': "oreGold",
                            '15': "oreIron",
                            '16': "oreCoal",
                            '17': "tree_top",
                            '18': "leaves",
                            '19': "sponge",
                            '20': "glass",
                            '21': "oreLapis",
                            '22': "blockLapis",
                            '23': "furnace_top",
                            '24': "sandstone_top",
                            '25': "musicBlock",
                            '26': "bed_feet_top",
                            '27': "goldenRail_powered",
                            '28': "detectorRail_on",
                            '29': "piston_inner_top",
                            '30': "web",
                            '31': "fern",
                            '32': "deadbush",
                            '33': "piston_top",
                            '34': "piston_top_sticky",
                            '35': "cloth_0",
                            '37': "flower",
                            '38': "rose",
                            '39': "mushroom_brown",
                            '40': "mushroom_red",
                            '41': "blockGold",
                            '42': "blockIron",
                            '43': "stoneslab_top",
                            '44': "stoneslab_top",
                            '45': "brick",
                            '46': "tnt_top",
                            '47': "wood",
                            '48': "stoneMoss",
                            '49': "obsidian",
                            '50': "torch",
                            '51': "fire_0",
                            '52': "mobSpawner",
                            '53': "wood",
                            '55': "redstoneDust_line",
                            '56': "oreDiamond",
                            '57': "blockDiamond",
                            '58': "workbench_front",
                            '59': "crops_7",
                            '60': "dirt",
                            '61': "furnace_front",
                            '62': "furnace_front_lit",
                            '63': "wood",
                            '64': "doorWood_lower",
                            '65': "ladder",
                            '66': "rail",
                            '67': "stonebrick",
                            '68': "wood",
                            '69': "stonebrick",
                            '70': "stone",
                            '71': "doorIron_lower",
                            '72': "wood",
                            '73': "oreRedstone",
                            '74': "oreRedstone",
                            '75': "redtorch",
                            '76': "redtorch_lit",
                            '77': "stone",
                            '78': "snow",
                            '79': "ice",
                            '80': "snow",
                            '81': "cactus_top",
                            '82': "clay",
                            '83': "reeds",
                            '84': "jukebox_top",
                            '85': "wood",
                            '86': "ppumpkin_face",
                            '87': "hellrock",
                            '88': "hellsand",
                            '89': "lightgem",
                            '91': "pumpkin_jack",
                            '92': "cake_inner",
                            '93': "redtorch",
                            '94': "redtorch_lit",
                            '95': "cactus_bottom",
                            '96': "trapdoor",
                            '97': "stone",
                            '98': "stonebricksmooth",
                            '99': "mushroom_skin_stem",
                            '100': "mushroom_skin_stem",
                            '101': "fenceIron",
                            '102': "glass",
                            '103': "melon_top",
                            '104': "stem_bent",
                            '105': "bentStem=stem_bent",
                            '106': "vine",
                            '107': "wood",
                            '108': "brick",
                            '109': "stonebricksmooth",
                            '110': "mycel_top",
                            '111': "waterlily",
                            '112': "netherBrick",
                            '113': "netherBrick",
                            '114': "netherBrick",
                            '115': "netherStalk_2",
                            '116': "enchantment_bottom",
                            '117': "brewingStand",
                            '118': "water",
                            '120': "endframe_eye",
                            '121': "whiteStone",
                            '122': "dragonEgg",
                            '123': "redstoneLight",
                            '124': "redstoneLight_lit",
                            '125': "wood",
                            '127': "cocoa_2",
                            '128': "sandstone_side",
                            '129': "oreEmerald",
                            '131': "wood",
                            '133': "blockEmerald",
                            '134': "wood_spruce",
                            '135': "wood_birch",
                            '136': "wood_jungle",
                            '137': "commandBlock",
                            '138': "obsidian",
                            '139': "stonebrick",
                            '139': "stoneMoss",
                            '141': "carrots_3",
                            '142': "potatoes_2",
                            '143': "wood",
                            '145': "anvil_top_damaged_2",
                            '147': "blockGold",
                            '148': "blockIron",
                            '149': "comparator_lit",
                            '150': "redtorch_lit",
                            '151': "daylightDetector_side",
                            '152': "blockRedstone",
                            '153': "netherquartz",
                            '154': "hopper_inside",
                            '155': "quartzblock_top",
                            '156': "quartzblock_top",
                            '157': "activatorRail_powered",
                            '158': "dropper_front",
                            '159': "clayHardenedStained_0",
                            '170': "hayBlock_top",
                            '171': "cloth_0",
                            '171': "cloth_1",
                            '172': "clayHardened",
                            '173': "blockCoal"}

        self.texturepack = {'activatorRail': self.texture_activatorRail,
                            'activatorRail_powered': self.texture_activatorRail_powered,
                            'anvil_base': self.texture_anvil_base,
                            'anvil_top': self.texture_anvil_top,
                            'anvil_top_damaged_1': self.texture_anvil_top_damaged_1,
                            'anvil_top_damaged_2': self.texture_anvil_top_damaged_2,
                            'beacon': self.texture_beacon,
                            'bed_feet_end': self.texture_bed_feet_end,
                            'bed_feet_side': self.texture_bed_feet_side,
                            'bed_feet_top': self.texture_bed_feet_top,
                            'bed_head_end': self.texture_bed_head_end,
                            'bed_head_side': self.texture_bed_head_side,
                            'bed_head_top': self.texture_bed_head_top,
                            'bedrock': self.texture_bedrock,
                            'blockDiamond': self.texture_blockDiamond,
                            'blockEmerald': self.texture_blockEmerald,
                            'blockGold': self.texture_blockGold,
                            'blockIron': self.texture_blockIron,
                            'blockLapis': self.texture_blockLapis,
                            'blockRedstone': self.texture_blockRedstone,
                            'bookshelf': self.texture_bookshelf,
                            'brewingStand': self.texture_brewingStand,
                            'brewingStand_base': self.texture_brewingStand_base,
                            'brick': self.texture_brick,
                            'cactus_bottom': self.texture_cactus_bottom,
                            'cactus_side': self.texture_cactus_side,
                            'cactus_top': self.texture_cactus_top,
                            'cake_bottom': self.texture_cake_bottom,
                            'cake_inner': self.texture_cake_inner,
                            'cake_side': self.texture_cake_side,
                            'cake_top': self.texture_cake_top,
                            'carrots_0': self.texture_carrots_0,
                            'carrots_1': self.texture_carrots_1,
                            'carrots_2': self.texture_carrots_2,
                            'carrots_3': self.texture_carrots_3,
                            'cauldron_bottom': self.texture_cauldron_bottom,
                            'cauldron_inner': self.texture_cauldron_inner,
                            'cauldron_side': self.texture_cauldron_side,
                            'cauldron_top': self.texture_cauldron_top,
                            'clay': self.texture_clay,
                            'cloth_0': self.texture_cloth_0,
                            'cloth_1': self.texture_cloth_1,
                            'cloth_10': self.texture_cloth_10,
                            'cloth_11': self.texture_cloth_11,
                            'cloth_12': self.texture_cloth_12,
                            'cloth_13': self.texture_cloth_13,
                            'cloth_14': self.texture_cloth_14,
                            'cloth_15': self.texture_cloth_15,
                            'cloth_2': self.texture_cloth_2,
                            'cloth_3': self.texture_cloth_3,
                            'cloth_4': self.texture_cloth_4,
                            'cloth_5': self.texture_cloth_5,
                            'cloth_6': self.texture_cloth_6,
                            'cloth_7': self.texture_cloth_7,
                            'cloth_8': self.texture_cloth_8,
                            'cloth_9': self.texture_cloth_9,
                            'cocoa_0': self.texture_cocoa_0,
                            'cocoa_1': self.texture_cocoa_1,
                            'cocoa_2': self.texture_cocoa_2,
                            'commandBlock': self.texture_commandBlock,
                            'comparator': self.texture_comparator,
                            'comparator_lit': self.texture_comparator_lit,
                            'crops_0': self.texture_crops_0,
                            'crops_1': self.texture_crops_1,
                            'crops_2': self.texture_crops_2,
                            'crops_3': self.texture_crops_3,
                            'crops_4': self.texture_crops_4,
                            'crops_5': self.texture_crops_5,
                            'crops_6': self.texture_crops_6,
                            'crops_7': self.texture_crops_7,
                            'daylightDetector_side': self.texture_daylightDetector_side,
                            'daylightDetector_top': self.texture_daylightDetector_top,
                            'deadbush': self.texture_deadbush,
                            'destroy_0': self.texture_destroy_0,
                            'destroy_1': self.texture_destroy_1,
                            'destroy_2': self.texture_destroy_2,
                            'destroy_3': self.texture_destroy_3,
                            'destroy_4': self.texture_destroy_4,
                            'destroy_5': self.texture_destroy_5,
                            'destroy_6': self.texture_destroy_6,
                            'destroy_7': self.texture_destroy_7,
                            'destroy_8': self.texture_destroy_8,
                            'destroy_9': self.texture_destroy_9,
                            'detectorRail': self.texture_detectorRail,
                            'dirt': self.texture_dirt,
                            'dispenser_front': self.texture_dispenser_front,
                            'dispenser_front_vertical': self.texture_dispenser_front_vertical,
                            'doorIron_lower': self.texture_doorIron_lower,
                            'doorIron_upper': self.texture_doorIron_upper,
                            'doorWood_lower': self.texture_doorWood_lower,
                            'doorWood_upper': self.texture_doorWood_upper,
                            'dragonEgg': self.texture_dragonEgg,
                            'dropper_front': self.texture_dropper_front,
                            'dropper_front_vertical': self.texture_dropper_front_vertical,
                            'enchantment_bottom': self.texture_enchantment_bottom,
                            'enchantment_side': self.texture_enchantment_side,
                            'enchantment_top': self.texture_enchantment_top,
                            'endframe_eye': self.texture_endframe_eye,
                            'endframe_side': self.texture_endframe_side,
                            'endframe_top': self.texture_endframe_top,
                            'farmland_dry': self.texture_farmland_dry,
                            'farmland_wet': self.texture_farmland_wet,
                            'fenceIron': self.texture_fenceIron,
                            'fern': self.texture_fern,
                            'fire_0': self.texture_fire_0,
                            'fire_0': self.texture_fire_0,
                            'fire_1': self.texture_fire_1,
                            'fire_1': self.texture_fire_1,
                            'flower': self.texture_flower,
                            'flowerPot': self.texture_flowerPot,
                            'furnace_front': self.texture_furnace_front,
                            'furnace_front_lit': self.texture_furnace_front_lit,
                            'furnace_side': self.texture_furnace_side,
                            'furnace_top': self.texture_furnace_top,
                            'glass': self.texture_glass,
                            'goldenRail': self.texture_goldenRail,
                            'goldenRail_powered': self.texture_goldenRail_powered,
                            'grass_side': self.texture_grass_side,
                            'grass_side_overlay': self.texture_grass_side_overlay,
                            'grass_top': self.texture_grass_top,
                            'gravel': self.texture_gravel,
                            'hellrock': self.texture_hellrock,
                            'hellsand': self.texture_hellsand,
                            'hopper': self.texture_hopper,
                            'hopper_inside': self.texture_hopper_inside,
                            'hopper_top': self.texture_hopper_top,
                            'ice': self.texture_ice,
                            'itemframe_back': self.texture_itemframe_back,
                            'jukebox_top': self.texture_jukebox_top,
                            'ladder': self.texture_ladder,
                            'lava': self.texture_lava,
                            'lava': self.texture_lava,
                            'lava_flow': self.texture_lava_flow,
                            'lava_flow': self.texture_lava_flow,
                            'leaves': self.texture_leaves,
                            'leaves_jungle': self.texture_leaves_jungle,
                            'leaves_jungle_opaque': self.texture_leaves_jungle_opaque,
                            'leaves_opaque': self.texture_leaves_opaque,
                            'leaves_spruce': self.texture_leaves_spruce,
                            'leaves_spruce_opaque': self.texture_leaves_spruce_opaque,
                            'lever': self.texture_lever,
                            'lightgem': self.texture_lightgem,
                            'melon_side': self.texture_melon_side,
                            'melon_top': self.texture_melon_top,
                            'mobSpawner': self.texture_mobSpawner,
                            'mushroom_brown': self.texture_mushroom_brown,
                            'mushroom_inside': self.texture_mushroom_inside,
                            'mushroom_red': self.texture_mushroom_red,
                            'mushroom_skin_brown': self.texture_mushroom_skin_brown,
                            'mushroom_skin_red': self.texture_mushroom_skin_red,
                            'mushroom_skin_stem': self.texture_mushroom_skin_stem,
                            'musicBlock': self.texture_musicBlock,
                            'mycel_side': self.texture_mycel_side,
                            'mycel_top': self.texture_mycel_top,
                            'netherBrick': self.texture_netherBrick,
                            'netherStalk_0': self.texture_netherStalk_0,
                            'netherStalk_1': self.texture_netherStalk_1,
                            'netherStalk_2': self.texture_netherStalk_2,
                            'netherquartz': self.texture_netherquartz,
                            'obsidian': self.texture_obsidian,
                            'oreCoal': self.texture_oreCoal,
                            'oreDiamond': self.texture_oreDiamond,
                            'oreEmerald': self.texture_oreEmerald,
                            'oreGold': self.texture_oreGold,
                            'oreIron': self.texture_oreIron,
                            'oreLapis': self.texture_oreLapis,
                            'oreRedstone': self.texture_oreRedstone,
                            'piston_bottom': self.texture_piston_bottom,
                            'piston_inner_top': self.texture_piston_inner_top,
                            'piston_side': self.texture_piston_side,
                            'piston_top': self.texture_piston_top,
                            'piston_top_sticky': self.texture_piston_top_sticky,
                            'potatoes_0': self.texture_potatoes_0,
                            'potatoes_1': self.texture_potatoes_1,
                            'potatoes_2': self.texture_potatoes_2,
                            'potatoes_3': self.texture_potatoes_3,
                            'pumpkin_face': self.texture_pumpkin_face,
                            'pumpkin_jack': self.texture_pumpkin_jack,
                            'pumpkin_side': self.texture_pumpkin_side,
                            'pumpkin_top': self.texture_pumpkin_top,
                            'quartzblock_bottom': self.texture_quartzblock_bottom,
                            'quartzblock_chiseled': self.texture_quartzblock_chiseled,
                            'quartzblock_chiseled_top': self.texture_quartzblock_chiseled_top,
                            'quartzblock_lines': self.texture_quartzblock_lines,
                            'quartzblock_lines_top': self.texture_quartzblock_lines_top,
                            'quartzblock_side': self.texture_quartzblock_side,
                            'quartzblock_top': self.texture_quartzblock_top,
                            'rail': self.texture_rail,
                            'rail_turn': self.texture_rail_turn,
                            'redstoneDust_cross': self.texture_redstoneDust_cross,
                            'redstoneDust_cross_overlay': self.texture_redstoneDust_cross_overlay,
                            'redstoneDust_line': self.texture_redstoneDust_line,
                            'redstoneDust_line_overlay': self.texture_redstoneDust_line_overlay,
                            'redstoneLight': self.texture_redstoneLight,
                            'redstoneLight_lit': self.texture_redstoneLight_lit,
                            'redtorch': self.texture_redtorch,
                            'redtorch_lit': self.texture_redtorch_lit,
                            'reeds': self.texture_reeds,
                            'repeater': self.texture_repeater,
                            'repeater_lit': self.texture_repeater_lit,
                            'rose': self.texture_rose,
                            'sand': self.texture_sand,
                            'sandstone_bottom': self.texture_sandstone_bottom,
                            'sandstone_carved': self.texture_sandstone_carved,
                            'sandstone_side': self.texture_sandstone_side,
                            'sandstone_smooth': self.texture_sandstone_smooth,
                            'sandstone_top': self.texture_sandstone_top,
                            'sapling': self.texture_sapling,
                            'sapling_birch': self.texture_sapling_birch,
                            'sapling_jungle': self.texture_sapling_jungle,
                            'sapling_spruce': self.texture_sapling_spruce,
                            'snow': self.texture_snow,
                            'snow_side': self.texture_snow_side,
                            'sponge': self.texture_sponge,
                            'stem_bent': self.texture_stem_bent,
                            'stem_straight': self.texture_stem_straight,
                            'stone': self.texture_stone,
                            'stoneMoss': self.texture_stoneMoss,
                            'stonebrick': self.texture_stonebrick,
                            'stonebricksmooth': self.texture_stonebricksmooth,
                            'stonebricksmooth_carved': self.texture_stonebricksmooth_carved,
                            'stonebricksmooth_cracked': self.texture_stonebricksmooth_cracked,
                            'stonebricksmooth_mossy': self.texture_stonebricksmooth_mossy,
                            'stoneslab_side': self.texture_stoneslab_side,
                            'stoneslab_top': self.texture_stoneslab_top,
                            'tallgrass': self.texture_tallgrass,
                            'thinglass_top': self.texture_thinglass_top,
                            'tnt_bottom': self.texture_tnt_bottom,
                            'tnt_side': self.texture_tnt_side,
                            'tnt_top': self.texture_tnt_top,
                            'torch': self.texture_torch,
                            'trapdoor': self.texture_trapdoor,
                            'tree_birch': self.texture_tree_birch,
                            'tree_jungle': self.texture_tree_jungle,
                            'tree_side': self.texture_tree_side,
                            'tree_spruce': self.texture_tree_spruce,
                            'tree_top': self.texture_tree_top,
                            'tripWire': self.texture_tripWire,
                            'tripWireSource': self.texture_tripWireSource,
                            'vine': self.texture_vine,
                            'water': self.texture_water,
                            'water': self.texture_water,
                            'water_flow': self.texture_water_flow,
                            'water_flow': self.texture_water_flow,
                            'waterlily': self.texture_waterlily,
                            'web': self.texture_web,
                            'whiteStone': self.texture_whiteStone,
                            'wood': self.texture_wood,
                            'wood_birch': self.texture_wood_birch,
                            'wood_jungle': self.texture_wood_jungle,
                            'wood_spruce': self.texture_wood_spruce,
                            'workbench_front': self.texture_workbench_front,
                            'workbench_side': self.texture_workbench_side,
                            'workbench_top': self.texture_workbench_top
        }
        self.world = {}
        self.type = {}
        self.shown = {}
        self._shown = {}
        self.sectors = {}
        self.queue = []
        self.client = client
        self.initialize()
        self.last_known_botblock = (0,0,0)
    def initialize(self):
        n = 16
        s = 1
        y = 0

        x_chunk = self.client.position['x'] // 16
        z_chunk = self.client.position['z'] // 16

        bot_block = [self.client.position['x'], self.client.position['y'], self.client.position['z']]
        current_column = self.client.world.columns[(x_chunk, z_chunk)]
        current_section = current_column.chunks[int((bot_block[1] + y % 16) // 16)]

        for x in xrange(0, n):
            for y in xrange(0, n):
                for z in xrange(0, n):
                    if current_section != None:
                        current_block = current_column.chunks[int((bot_block[1] + y - 10 // 2) // 16)]['block_data'].get(x, int((bot_block[1] + y - 10 // 2) % 16), z)
                        if (current_block in (1, 2, 3, 4, 5, 7, 10, 11, 12, 13, 14, 15, 16, 19, 21, 22, 24, 25, 35, 41, 42, 43, 45, 46, 47, 48, 49, 52, 56, 57, 73, 74, 80, 82, 84, 87, 88, 89, 97, 98, 103, 110, 112, 121, 123, 124, 125, 125, 129, 133, 137, 152, 153, 155, 159, 172, 173)):
                            #print(current_block)
                            #print(self.block_names[str(current_block)])
                            self.init_block((x, y, z), GOLDORE, self.block_names[str(current_block)])

    def reload(self):
        n = 16
        s = 1
        y = 0

        x_chunk = self.client.position['x'] // 16
        z_chunk = self.client.position['z'] // 16

        bot_block = [self.client.position['x'], self.client.position['y'], self.client.position['z']]
        current_column = self.client.world.columns[(x_chunk, z_chunk)]
        current_section = current_column.chunks[int((bot_block[1] + y % 16) // 16)]

        for x in xrange(0, n):
            for y in xrange(0, n):
                for z in xrange(0, n):
                    if current_section != None:
                        current_block = current_column.chunks[int((bot_block[1] + y - 10 // 2) // 16)][
                            'block_data'].get(x, int((bot_block[1] + y - 10 // 2) % 16), z)
                        if current_block == 14:
                           #self.add_block((x, y, z), GOLDORE)
                            pass
                        elif current_block == 3:
                           #self.add_block((x, y, z), SAND)
                            pass
                        elif current_block == 1:
                           #self.add_block((x, y, z), STONE)
                            pass
                        elif current_block == 13:
                           #self.add_block((x, y, z), STONE)
                            pass
                        elif current_block == 2:
                           #self.add_block((x, y, z), GRASS)
                            pass
                        if [int(self.client.position['x'] % 16), int((bot_block[1] + y - 10 // 2) // 16), int(self.client.position['z'] % 16)] == [x,y,z]:
                            print("BotBlock @ x %s y %s z %s" % (x,y,z))
                            self.remove_block(self.last_known_botblock)
                            self.add_block((x, y+1, z), HUMAN, "oreGold" )
                            self.last_known_botblock = (x, y+1, z)
                            
    def hit_test(self, position, vector, max_distance=8):
        m = 8
        x, y, z = position
        dx, dy, dz = vector
        previous = None
        for _ in xrange(max_distance * m):
            key = normalize((x, y, z))
            if key != previous and key in self.world:
                return key, previous
            previous = key
            x, y, z = x + dx / m, y + dy / m, z + dz / m
        return None, None
    def exposed(self, position):
        x, y, z = position
        for dx, dy, dz in FACES:
            if (x + dx, y + dy, z + dz) not in self.world:
                return True
        return False
    def init_block(self, position, texture, type):
        self.add_block(position, texture, type, False)
    def own_init_block(self, position, texture):
        self.own_add_block(position, texture, False)
    def own_add_block(self, position, texture, sync=True):
        if position in self.world:
            self.remove_block(position, sync)
        self.world[position] = texture
        self.sectors.setdefault(sectorize(position), []).append(position)
        if sync:
            if self.exposed(position):
                self.show_own_block(position)
            self.check_neighbors(position)
    def add_block(self, position, texture, type, sync=True):
        if position in self.world:
            self.remove_block(position, sync)
        self.type[position] = type
        self.world[position] = texture
        self.sectors.setdefault(sectorize(position), []).append(position)
        if sync:
            if self.exposed(position):
                self.show_block(position)
            self.check_neighbors(position)
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
        # only show exposed faces
        index = 0
        count = 24
        vertex_data = cube_vertices(x, y, z, 0.5)
        texture_data = list(texture)
        for dx, dy, dz in []:#FACES:
            if (x + dx, y + dy, z + dz) in self.world:
                count -= 4
                i = index * 12
                j = index * 8
                del vertex_data[i:i + 12]
                del texture_data[j:j + 8]
            else:
                index += 1
        # create vertex list
        self._shown[position] = self.batch.add(count, GL_QUADS, self.texturepack[self.type[position]],
                ('v3f/static', vertex_data),
                ('t2f/static', texture_data))

    def _show_own_block(self, position, texture):
        x, y, z = position
        # only show exposed faces
        index = 0
        count = 24
        vertex_data = cube_vertices(x, y, z, 0.5)
        texture_data = list(texture)
        for dx, dy, dz in []:#FACES:
            if (x + dx, y + dy, z + dz) in self.world:
                count -= 4
                i = index * 12
                j = index * 8
                del vertex_data[i:i + 12]
                del texture_data[j:j + 8]
            else:
                index += 1
        # create vertex list
        self._shown[position] = self.batch.add(count, GL_QUADS, self.group,
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
                if self.type[position] == "GOLDORE":
                    self.show_own_block(position, False)
                else:
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
        self.flying = False
        self.strafe = [0, 0]
        self.position = (0, 16, 16)
        self.rotation = (45, -45) # first left,right - second up,down
        self.sector = None
        self.reticle = None
        self.dy = 0
        self.inventory = [BRICK, GRASS, SAND]
        self.block = self.inventory[0]
        self.num_keys = [
            key._1, key._2, key._3, key._4, key._5,
            key._6, key._7, key._8, key._9, key._0]
        self.client = client
        self.model = Model(self.client)
        self.label = pyglet.text.Label('', font_name='Arial', font_size=18, 
            x=10, y=self.height - 10, anchor_x='left', anchor_y='top', 
            color=(0, 0, 0, 255))
        pyglet.clock.schedule_interval(self.update, 1.0 / 60)
    def set_exclusive_mouse(self, exclusive):
        super(Window, self).set_exclusive_mouse(exclusive)
        self.exclusive = exclusive
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
    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        return
        x, y, z = self.position
        dx, dy, dz = self.get_sight_vector()
        d = scroll_y * 10
        self.position = (x + dx * d, y + dy * d, z + dz * d)
    def on_mouse_press(self, x, y, button, modifiers):
        if self.exclusive:
            vector = self.get_sight_vector()
            block, previous = self.model.hit_test(self.position, vector)
            if button == pyglet.window.mouse.LEFT:
                if block:
                    texture = self.model.world[block]
                    if texture != STONE:
                        self.model.remove_block(block)
            else:
                if previous:
                    self.model.add_block(previous, self.block)
        else:
            self.set_exclusive_mouse(True)
    def on_mouse_motion(self, x, y, dx, dy):
        if self.exclusive:
            m = 0.15
            x, y = self.rotation
            x, y = x + dx * m, y + dy * m
            y = max(-90, min(90, y))
            self.rotation = (x, y)
    def on_key_press(self, symbol, modifiers):
        if symbol == key.W:
            self.strafe[0] -= 1
        elif symbol == key.S:
            self.strafe[0] += 1
        elif symbol == key.A:
            self.strafe[1] -= 1
        elif symbol == key.D:
            self.strafe[1] += 1
        elif symbol == key.SPACE:
            if self.dy == 0:
                self.dy = 0.015 # jump speed
        elif symbol == key.ESCAPE:
            self.set_exclusive_mouse(False)
        elif symbol == key.TAB:
            self.flying = not self.flying
        elif symbol in self.num_keys:
            index = (symbol - self.num_keys[0]) % len(self.inventory)
            self.block = self.inventory[index]
    def on_key_release(self, symbol, modifiers):
        if symbol == key.W:
            self.strafe[0] += 1
        elif symbol == key.S:
            self.strafe[0] -= 1
        elif symbol == key.A:
            self.strafe[1] += 1
        elif symbol == key.D:
            self.strafe[1] -= 1
    def on_resize(self, width, height):
        # label
        self.label.y = height - 10
        # reticle
        if self.reticle:
            self.reticle.delete()
        x, y = self.width // 2, self.height // 2
        n = 10
        self.reticle = pyglet.graphics.vertex_list(4,
            ('v2i', (x - n, y, x + n, y, x, y - n, x, y + n))
        )
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
        self.draw_focused_block()
        self.set_2d()
        self.draw_label()
        #self.draw_reticle()
    def draw_focused_block(self):
        vector = self.get_sight_vector()
        block = self.model.hit_test(self.position, vector)[0]
        if block:
            x, y, z = block
            vertex_data = cube_vertices(x, y, z, 0.51)
            glColor3d(0, 0, 0)
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            pyglet.graphics.draw(24, GL_QUADS, ('v3f/static', vertex_data))
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    def draw_label(self):
        x, y, z = self.position
        self.label.text = '%02d (%.2f, %.2f, %.2f) %d / %d' % (
            pyglet.clock.get_fps(), x, y, z, 
            len(self.model._shown), len(self.model.world))
        self.label.draw()
    def draw_reticle(self):
        glColor3d(0, 0, 0)
        self.reticle.draw(GL_LINES)

def setup_fog():
    glEnable(GL_FOG)
    glFogfv(GL_FOG_COLOR, (GLfloat * 4)(0.5, 0.69, 1.0, 1))
    glHint(GL_FOG_HINT, GL_DONT_CARE)
    glFogi(GL_FOG_MODE, GL_LINEAR)
    glFogf(GL_FOG_DENSITY, 0.35)
    glFogf(GL_FOG_START, 20.0)
    glFogf(GL_FOG_END, 60.0)

def setup():
    glClearColor(0.5, 0.69, 1.0, 1)
    glEnable(GL_CULL_FACE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    setup_fog()

def commence_vis(client):
    global window
    window = Window(client, width=800, height=600, caption='Pyglet', resizable=True, visible=False)
    #window.set_exclusive_mouse(True)
    setup()
    for i in range(0,50):
        step_vis()

def step_vis():
    pyglet.clock.tick()
    pyglet.image.get_buffer_manager().get_color_buffer().save('./micropsi_server/static/minecraft/screenshot_write.jpg')
    move('./micropsi_server/static/minecraft/screenshot_write.jpg', './micropsi_server/static/minecraft/screenshot.jpg')
    global window
    window.switch_to()
    window.model.reload()
    window.dispatch_events()
    window.dispatch_event('on_draw')
    window.flip()