__author__ = 'jonas'

solid_blocks = (1, 2, 3, 4, 5, 7, 10, 11, 12, 13, 14, 15, 16, 19, 21, 22, 24, 25, 35, 41, 42, 43, 45, 46, 47, 48, 49, 52, 56, 57, 73, 74, 80, 82, 84, 87, 88, 89, 97, 98, 103, 110, 112, 121, 123, 124, 125, 125, 129, 133, 137, 152, 153, 155, 159, 172, 173)

block_names = {'-1': "nothing_sky",
                            '0': "nothing_sky",
                            '1': "stone",
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
                            '173': "oreCoal"}

#def load_textures(self):
#        self.texture_human = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/human.png')
        #self.texture_activatorRail = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/activatorRail.png')
        #self.texture_activatorRail_powered = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/activatorRail_powered.png')
        #self.texture_anvil_base = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/anvil_base.png')
        #self.texture_anvil_top = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/anvil_top.png')
        #self.texture_anvil_top_damaged_1 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/anvil_top_damaged_1.png')
        #self.texture_anvil_top_damaged_2 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/anvil_top_damaged_2.png')
        #self.texture_beacon = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/beacon.png')
        #self.texture_bed_feet_end = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/bed_feet_end.png')
        #self.texture_bed_feet_side = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/bed_feet_side.png')
        #self.texture_bed_feet_top = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/bed_feet_top.png')
        #self.texture_bed_head_end = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/bed_head_end.png')
        #self.texture_bed_head_side = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/bed_head_side.png')
        #self.texture_bed_head_top = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/bed_head_top.png')
        #self.texture_bedrock = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/bedrock.png')
        #self.texture_blockDiamond = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/blockDiamond.png')
        #self.texture_blockEmerald = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/blockEmerald.png')
        #self.texture_blockGold = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/blockGold.png')
        #self.texture_blockIron = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/blockIron.png')
        #self.texture_blockLapis = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/blockLapis.png')
        #self.texture_blockRedstone = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/blockRedstone.png')
        #self.texture_bookshelf = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/bookshelf.png')
        #self.texture_brewingStand = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/brewingStand.png')
        #self.texture_brewingStand_base = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/brewingStand_base.png')
        #self.texture_brick = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/brick.png')
        #self.texture_cactus_bottom = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/cactus_bottom.png')
        #self.texture_cactus_side = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/cactus_side.png')
        #self.texture_cactus_top = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/cactus_top.png')
        #self.texture_cake_bottom = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/cake_bottom.png')
        #self.texture_cake_inner = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/cake_inner.png')
        #self.texture_cake_side = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/cake_side.png')
        #self.texture_cake_top = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/cake_top.png')
        #self.texture_carrots_0 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/carrots_0.png')
        #self.texture_carrots_1 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/carrots_1.png')
        #self.texture_carrots_2 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/carrots_2.png')
        #self.texture_carrots_3 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/carrots_3.png')
        #self.texture_cauldron_bottom = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/cauldron_bottom.png')
        #self.texture_cauldron_inner = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/cauldron_inner.png')
        #self.texture_cauldron_side = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/cauldron_side.png')
        #self.texture_cauldron_top = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/cauldron_top.png')
        #self.texture_clay = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/clay.png')
        #self.texture_cloth_0 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/cloth_0.png')
        #self.texture_cloth_1 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/cloth_1.png')
        #self.texture_cloth_10 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/cloth_10.png')
        #self.texture_cloth_11 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/cloth_11.png')
        #self.texture_cloth_12 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/cloth_12.png')
        #self.texture_cloth_13 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/cloth_13.png')
        #self.texture_cloth_14 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/cloth_14.png')
        #self.texture_cloth_15 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/cloth_15.png')
        #self.texture_cloth_2 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/cloth_2.png')
        #self.texture_cloth_3 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/cloth_3.png')
        #self.texture_cloth_4 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/cloth_4.png')
        #self.texture_cloth_5 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/cloth_5.png')
        #self.texture_cloth_6 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/cloth_6.png')
        #self.texture_cloth_7 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/cloth_7.png')
        #self.texture_cloth_8 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/cloth_8.png')
        #self.texture_cloth_9 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/cloth_9.png')
        #self.texture_cocoa_0 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/cocoa_0.png')
        #self.texture_cocoa_1 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/cocoa_1.png')
        #self.texture_cocoa_2 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/cocoa_2.png')
        #self.texture_commandBlock = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/commandBlock.png')
        #self.texture_comparator = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/comparator.png')
        #self.texture_comparator_lit = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/comparator_lit.png')
        #self.texture_crops_0 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/crops_0.png')
        #self.texture_crops_1 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/crops_1.png')
        #self.texture_crops_2 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/crops_2.png')
        #self.texture_crops_3 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/crops_3.png')
        #self.texture_crops_4 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/crops_4.png')
        #self.texture_crops_5 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/crops_5.png')
        #self.texture_crops_6 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/crops_6.png')
        #self.texture_crops_7 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/crops_7.png')
        #self.texture_daylightDetector_side = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/daylightDetector_side.png')
        #self.texture_daylightDetector_top = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/daylightDetector_top.png')
        #self.texture_deadbush = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/deadbush.png')
        #self.texture_destroy_0 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/destroy_0.png')
        #self.texture_destroy_1 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/destroy_1.png')
        #self.texture_destroy_2 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/destroy_2.png')
        #self.texture_destroy_3 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/destroy_3.png')
        #self.texture_destroy_4 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/destroy_4.png')
        #self.texture_destroy_5 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/destroy_5.png')
        #self.texture_destroy_6 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/destroy_6.png')
        #self.texture_destroy_7 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/destroy_7.png')
        #self.texture_destroy_8 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/destroy_8.png')
        #self.texture_destroy_9 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/destroy_9.png')
        #self.texture_detectorRail = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/detectorRail.png')
        #self.texture_dirt = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/dirt.png')
        #self.texture_dispenser_front = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/dispenser_front.png')
        #self.texture_dispenser_front_vertical = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/dispenser_front_vertical.png')
        #self.texture_doorIron_lower = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/doorIron_lower.png')
        #self.texture_doorIron_upper = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/doorIron_upper.png')
        #self.texture_doorWood_lower = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/doorWood_lower.png')
        #self.texture_doorWood_upper = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/doorWood_upper.png')
        #self.texture_dragonEgg = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/dragonEgg.png')
        #self.texture_dropper_front = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/dropper_front.png')
        #self.texture_dropper_front_vertical = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/dropper_front_vertical.png')
        #self.texture_enchantment_bottom = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/enchantment_bottom.png')
        #self.texture_enchantment_side = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/enchantment_side.png')
        #self.texture_enchantment_top = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/enchantment_top.png')
        #self.texture_endframe_eye = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/endframe_eye.png')
        #self.texture_endframe_side = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/endframe_side.png')
        #self.texture_endframe_top = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/endframe_top.png')
        #self.texture_farmland_dry = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/farmland_dry.png')
        #self.texture_farmland_wet = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/farmland_wet.png')
        #self.texture_fenceIron = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/fenceIron.png')
        #self.texture_fern = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/fern.png')
        #self.texture_fire_0 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/fire_0.png')
        #self.texture_fire_0 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/fire_0.png')
        #self.texture_fire_1 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/fire_1.png')
        #self.texture_fire_1 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/fire_1.png')
        #self.texture_flower = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/flower.png')
        #self.texture_flowerPot = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/flowerPot.png')
        #self.texture_furnace_front = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/furnace_front.png')
        #self.texture_furnace_front_lit = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/furnace_front_lit.png')
        #self.texture_furnace_side = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/furnace_side.png')
        #self.texture_furnace_top = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/furnace_top.png')
        #self.texture_glass = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/glass.png')
        #self.texture_goldenRail = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/goldenRail.png')
        #self.texture_goldenRail_powered = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/goldenRail_powered.png')
        #self.texture_grass_side = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/grass_side.png')
        #self.texture_grass_side_overlay = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/grass_side_overlay.png')
        #self.texture_grass_top = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/grass_top.png')
        #self.texture_gravel = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/gravel.png')
        #self.texture_hellrock = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/hellrock.png')
        #self.texture_hellsand = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/hellsand.png')
        #self.texture_hopper = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/hopper.png')
        #self.texture_hopper_inside = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/hopper_inside.png')
        #self.texture_hopper_top = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/hopper_top.png')
        #self.texture_ice = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/ice.png')
        #self.texture_itemframe_back = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/itemframe_back.png')
        #self.texture_jukebox_top = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/jukebox_top.png')
        #self.texture_ladder = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/ladder.png')
        #self.texture_lava = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/lava.png')
        #self.texture_lava = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/lava.png')
        #self.texture_lava_flow = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/lava_flow.png')
        #self.texture_lava_flow = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/lava_flow.png')
        #self.texture_leaves = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/leaves.png')
        #self.texture_leaves_jungle = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/leaves_jungle.png')
        #self.texture_leaves_jungle_opaque = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/leaves_jungle_opaque.png')
        #self.texture_leaves_opaque = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/leaves_opaque.png')
        #self.texture_leaves_spruce = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/leaves_spruce.png')
        #self.texture_leaves_spruce_opaque = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/leaves_spruce_opaque.png')
        #self.texture_lever = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/lever.png')
        #self.texture_lightgem = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/lightgem.png')
        #self.texture_melon_side = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/melon_side.png')
        #self.texture_melon_top = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/melon_top.png')
        #self.texture_mobSpawner = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/mobSpawner.png')
        #self.texture_mushroom_brown = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/mushroom_brown.png')
        #self.texture_mushroom_inside = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/mushroom_inside.png')
        #self.texture_mushroom_red = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/mushroom_red.png')
        #self.texture_mushroom_skin_brown = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/mushroom_skin_brown.png')
        #self.texture_mushroom_skin_red = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/mushroom_skin_red.png')
        #self.texture_mushroom_skin_stem = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/mushroom_skin_stem.png')
        #self.texture_musicBlock = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/musicBlock.png')
        #self.texture_mycel_side = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/mycel_side.png')
        #self.texture_mycel_top = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/mycel_top.png')
        #self.texture_netherBrick = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/netherBrick.png')
        #self.texture_netherStalk_0 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/netherStalk_0.png')
        #self.texture_netherStalk_1 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/netherStalk_1.png')
        #self.texture_netherStalk_2 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/netherStalk_2.png')
        #self.texture_netherquartz = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/netherquartz.png')
        #self.texture_obsidian = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/obsidian.png')
        #self.texture_oreCoal = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/oreCoal.png')
#        self.texture_oreDiamond = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/oreDiamond.png')
        #self.texture_oreEmerald = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/oreEmerald.png')
#        self.texture_oreGold = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/oreGold.png')
        #self.texture_oreIron = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/oreIron.png')
        #self.texture_oreLapis = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/oreLapis.png')
        #self.texture_oreRedstone = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/oreRedstone.png')
        #self.texture_piston_bottom = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/piston_bottom.png')
        #self.texture_piston_inner_top = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/piston_inner_top.png')
        #self.texture_piston_side = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/piston_side.png')
        #self.texture_piston_top = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/piston_top.png')
        #self.texture_piston_top_sticky = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/piston_top_sticky.png')
        #self.texture_potatoes_0 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/potatoes_0.png')
        #self.texture_potatoes_1 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/potatoes_1.png')
        #self.texture_potatoes_2 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/potatoes_2.png')
        #self.texture_potatoes_3 = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/potatoes_3.png')
        #self.texture_pumpkin_face = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/pumpkin_face.png')
        #self.texture_pumpkin_jack = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/pumpkin_jack.png')
        #self.texture_pumpkin_side = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/pumpkin_side.png')
        #self.texture_pumpkin_top = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/pumpkin_top.png')
        #self.texture_quartzblock_bottom = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/quartzblock_bottom.png')
        #self.texture_quartzblock_chiseled = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/quartzblock_chiseled.png')
        #self.texture_quartzblock_chiseled_top = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/quartzblock_chiseled_top.png')
        #self.texture_quartzblock_lines = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/quartzblock_lines.png')
        #self.texture_quartzblock_lines_top = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/quartzblock_lines_top.png')
        #self.texture_quartzblock_side = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/quartzblock_side.png')
        #self.texture_quartzblock_top = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/quartzblock_top.png')
        #self.texture_rail = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/rail.png')
        #self.texture_rail_turn = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/rail_turn.png')
        #self.texture_redstoneDust_cross = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/redstoneDust_cross.png')
        #self.texture_redstoneDust_cross_overlay = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/redstoneDust_cross_overlay.png')
        #self.texture_redstoneDust_line = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/redstoneDust_line.png')
        #self.texture_redstoneDust_line_overlay = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/redstoneDust_line_overlay.png')
        #self.texture_redstoneLight = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/redstoneLight.png')
        #self.texture_redstoneLight_lit = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/redstoneLight_lit.png')
        #self.texture_redtorch = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/redtorch.png')
        #self.texture_redtorch_lit = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/redtorch_lit.png')
        #self.texture_reeds = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/reeds.png')
        #self.texture_repeater = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/repeater.png')
        #self.texture_repeater_lit = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/repeater_lit.png')
        #self.texture_rose = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/rose.png')
        #self.texture_sand = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/sand.png')
        #self.texture_sandstone_bottom = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/sandstone_bottom.png')
        #self.texture_sandstone_carved = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/sandstone_carved.png')
        #self.texture_sandstone_side = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/sandstone_side.png')
        #self.texture_sandstone_smooth = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/sandstone_smooth.png')
        #self.texture_sandstone_top = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/sandstone_top.png')
        #self.texture_sapling = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/sapling.png')
        #self.texture_sapling_birch = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/sapling_birch.png')
        #self.texture_sapling_jungle = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/sapling_jungle.png')
        #self.texture_sapling_spruce = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/sapling_spruce.png')
        #self.texture_snow = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/snow.png')
        #self.texture_snow_side = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/snow_side.png')
        #self.texture_sponge = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/sponge.png')
        #self.texture_stem_bent = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/stem_bent.png')
        #self.texture_stem_straight = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/stem_straight.png')
        #self.texture_stone = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/stone.png')
        #self.texture_stoneMoss = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/stoneMoss.png')
        #self.texture_stonebrick = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/stonebrick.png')
        #self.texture_stonebricksmooth = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/stonebricksmooth.png')
        #self.texture_stonebricksmooth_carved = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/stonebricksmooth_carved.png')
        #self.texture_stonebricksmooth_cracked = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/stonebricksmooth_cracked.png')
        #self.texture_stonebricksmooth_mossy = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/stonebricksmooth_mossy.png')
        #self.texture_stoneslab_side = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/stoneslab_side.png')
        #self.texture_stoneslab_top = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/stoneslab_top.png')
        #self.texture_tallgrass = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/tallgrass.png')
        #self.texture_thinglass_top = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/thinglass_top.png')
        #self.texture_tnt_bottom = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/tnt_bottom.png')
        #self.texture_tnt_side = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/tnt_side.png')
        #self.texture_tnt_top = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/tnt_top.png')
        #self.texture_torch = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/torch.png')
        #self.texture_trapdoor = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/trapdoor.png')
        #self.texture_tree_birch = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/tree_birch.png')
        #self.texture_tree_jungle = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/tree_jungle.png')
        #self.texture_tree_side = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/tree_side.png')
        #self.texture_tree_spruce = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/tree_spruce.png')
        #self.texture_tree_top = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/tree_top.png')
        #self.texture_tripWire = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/tripWire.png')
        #self.texture_tripWireSource = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/tripWireSource.png')
        #self.texture_vine = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/vine.png')
        #self.texture_water = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/water.png')
        #self.texture_water = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/water.png')
        #self.texture_water_flow = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/water_flow.png')
        #self.texture_water_flow = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/water_flow.png')
        #self.texture_waterlily = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/waterlily.png')
        #self.texture_web = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/web.png')
        #self.texture_whiteStone = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/whiteStone.png')
        #self.texture_wood = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/wood.png')
        #self.texture_wood_birch = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/wood_birch.png')
        #self.texture_wood_jungle = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/wood_jungle.png')
        #self.texture_wood_spruce = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/wood_spruce.png')
        #self.texture_workbench_front = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/workbench_front.png')
        #self.texture_workbench_side = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/workbench_side.png')
        #self.texture_workbench_top = TextureGroup('micropsi_core/world/minecraft/visualisation/block_textures/workbench_top.png')

#        self.side_files = {"grass_top": self.texture_grass_side}

#        self.texturepack = {'human': self.texture_human,
                            #'activatorRail': self.texture_activatorRail,
                            #'activatorRail_powered': self.texture_activatorRail_powered,
                            #'anvil_base': self.texture_anvil_base,
                            #'anvil_top': self.texture_anvil_top,
                            #'anvil_top_damaged_1': self.texture_anvil_top_damaged_1,
                            #'anvil_top_damaged_2': self.texture_anvil_top_damaged_2,
                            #'beacon': self.texture_beacon,
                            #'bed_feet_end': self.texture_bed_feet_end,
                            #'bed_feet_side': self.texture_bed_feet_side,
                            #'bed_feet_top': self.texture_bed_feet_top,
                            #'bed_head_end': self.texture_bed_head_end,
                            #'bed_head_side': self.texture_bed_head_side,
                            #'bed_head_top': self.texture_bed_head_top,
                            #'bedrock': self.texture_bedrock,
                            #'blockDiamond': self.texture_blockDiamond,
                            #'blockEmerald': self.texture_blockEmerald,
                            #'blockGold': self.texture_blockGold,
                            #'blockIron': self.texture_blockIron,
                            #'blockLapis': self.texture_blockLapis,
                            #'blockRedstone': self.texture_blockRedstone,
                            #'bookshelf': self.texture_bookshelf,
                            #'brewingStand': self.texture_brewingStand,
                            #'brewingStand_base': self.texture_brewingStand_base,
                            #'brick': self.texture_brick,
                            #'cactus_bottom': self.texture_cactus_bottom,
                            #'cactus_side': self.texture_cactus_side,
                            #'cactus_top': self.texture_cactus_top,
                            #'cake_bottom': self.texture_cake_bottom,
                            #'cake_inner': self.texture_cake_inner,
                            #'cake_side': self.texture_cake_side,
                            #'cake_top': self.texture_cake_top,
                            #'carrots_0': self.texture_carrots_0,
                            #'carrots_1': self.texture_carrots_1,
                            #'carrots_2': self.texture_carrots_2,
                            #'carrots_3': self.texture_carrots_3,
                            #'cauldron_bottom': self.texture_cauldron_bottom,
                            #'cauldron_inner': self.texture_cauldron_inner,
                            #'cauldron_side': self.texture_cauldron_side,
                            #'cauldron_top': self.texture_cauldron_top,
                            #'clay': self.texture_clay,
                            #'cloth_0': self.texture_cloth_0,
                            #'cloth_1': self.texture_cloth_1,
                            #'cloth_10': self.texture_cloth_10,
                            #'cloth_11': self.texture_cloth_11,
                            #'cloth_12': self.texture_cloth_12,
                            #'cloth_13': self.texture_cloth_13,
                            #'cloth_14': self.texture_cloth_14,
                            #'cloth_15': self.texture_cloth_15,
                            #'cloth_2': self.texture_cloth_2,
                            #'cloth_3': self.texture_cloth_3,
                            #'cloth_4': self.texture_cloth_4,
                            #'cloth_5': self.texture_cloth_5,
                            #'cloth_6': self.texture_cloth_6,
                            #'cloth_7': self.texture_cloth_7,
                            #'cloth_8': self.texture_cloth_8,
                            #'cloth_9': self.texture_cloth_9,
                            #'cocoa_0': self.texture_cocoa_0,
                            #'cocoa_1': self.texture_cocoa_1,
                            #'cocoa_2': self.texture_cocoa_2,
                            #'commandBlock': self.texture_commandBlock,
                            #'comparator': self.texture_comparator,
                            #'comparator_lit': self.texture_comparator_lit,
                            #'crops_0': self.texture_crops_0,
                            #'crops_1': self.texture_crops_1,
                            #'crops_2': self.texture_crops_2,
                            #'crops_3': self.texture_crops_3,
                            #'crops_4': self.texture_crops_4,
                            #'crops_5': self.texture_crops_5,
                            #'crops_6': self.texture_crops_6,
                            #'crops_7': self.texture_crops_7,
                            #'daylightDetector_side': self.texture_daylightDetector_side,
                            #'daylightDetector_top': self.texture_daylightDetector_top,
                            #'deadbush': self.texture_deadbush,
                            #'destroy_0': self.texture_destroy_0,
                            #'destroy_1': self.texture_destroy_1,
                            #'destroy_2': self.texture_destroy_2,
                            #'destroy_3': self.texture_destroy_3,
                            #'destroy_4': self.texture_destroy_4,
                            #'destroy_5': self.texture_destroy_5,
                            #'destroy_6': self.texture_destroy_6,
                            #'destroy_7': self.texture_destroy_7,
                            #'destroy_8': self.texture_destroy_8,
                            #'destroy_9': self.texture_destroy_9,
                            #'detectorRail': self.texture_detectorRail,
                            #'dirt': self.texture_dirt,
                            #'dispenser_front': self.texture_dispenser_front,
                            #'dispenser_front_vertical': self.texture_dispenser_front_vertical,
                            #'doorIron_lower': self.texture_doorIron_lower,
                            #'doorIron_upper': self.texture_doorIron_upper,
                            #'doorWood_lower': self.texture_doorWood_lower,
                            #'doorWood_upper': self.texture_doorWood_upper,
                            #'dragonEgg': self.texture_dragonEgg,
                            #'dropper_front': self.texture_dropper_front,
                            #'dropper_front_vertical': self.texture_dropper_front_vertical,
                            #'enchantment_bottom': self.texture_enchantment_bottom,
                            #'enchantment_side': self.texture_enchantment_side,
                            #'enchantment_top': self.texture_enchantment_top,
                            #'endframe_eye': self.texture_endframe_eye,
                            #'endframe_side': self.texture_endframe_side,
                            #'endframe_top': self.texture_endframe_top,
                            #'farmland_dry': self.texture_farmland_dry,
                            #'farmland_wet': self.texture_farmland_wet,
                            #'fenceIron': self.texture_fenceIron,
                            #'fern': self.texture_fern,
                            #'fire_0': self.texture_fire_0,
                            #'fire_0': self.texture_fire_0,
                            #'fire_1': self.texture_fire_1,
                            #'fire_1': self.texture_fire_1,
                            #'flower': self.texture_flower,
                            #'flowerPot': self.texture_flowerPot,
                            #'furnace_front': self.texture_furnace_front,
                            #'furnace_front_lit': self.texture_furnace_front_lit,
                            #'furnace_side': self.texture_furnace_side,
                            #'furnace_top': self.texture_furnace_top,
                            #'glass': self.texture_glass,
                            #'goldenRail': self.texture_goldenRail,
                            #'goldenRail_powered': self.texture_goldenRail_powered,
                            #'grass_side': self.texture_grass_side,
                            #'grass_side_overlay': self.texture_grass_side_overlay,
                            #   'grass_top': self.texture_grass_top,
                            #'gravel': self.texture_gravel,
                            #'hellrock': self.texture_hellrock,
                            #'hellsand': self.texture_hellsand,
                            #'hopper': self.texture_hopper,
                            #'hopper_inside': self.texture_hopper_inside,
                            #'hopper_top': self.texture_hopper_top,
                            #'ice': self.texture_ice,
                            #'itemframe_back': self.texture_itemframe_back,
                            #'jukebox_top': self.texture_jukebox_top,
                            #'ladder': self.texture_ladder,
                            #'lava': self.texture_lava,
                            #'lava': self.texture_lava,
                            #'lava_flow': self.texture_lava_flow,
                            #'lava_flow': self.texture_lava_flow,
                            #'leaves': self.texture_leaves,
                            #'leaves_jungle': self.texture_leaves_jungle,
                            #'leaves_jungle_opaque': self.texture_leaves_jungle_opaque,
                            #'leaves_opaque': self.texture_leaves_opaque,
                            #'leaves_spruce': self.texture_leaves_spruce,
                            #'leaves_spruce_opaque': self.texture_leaves_spruce_opaque,
                            #'lever': self.texture_lever,
                            #'lightgem': self.texture_lightgem,
                            #'melon_side': self.texture_melon_side,
                            #'melon_top': self.texture_melon_top,
                            #'mobSpawner': self.texture_mobSpawner,
                            #'mushroom_brown': self.texture_mushroom_brown,
                            #'mushroom_inside': self.texture_mushroom_inside,
                            #'mushroom_red': self.texture_mushroom_red,
                            #'mushroom_skin_brown': self.texture_mushroom_skin_brown,
                            #'mushroom_skin_red': self.texture_mushroom_skin_red,
                            #'mushroom_skin_stem': self.texture_mushroom_skin_stem,
                            #'musicBlock': self.texture_musicBlock,
                            #'mycel_side': self.texture_mycel_side,
                            #'mycel_top': self.texture_mycel_top,
                            #'netherBrick': self.texture_netherBrick,
                            #'netherStalk_0': self.texture_netherStalk_0,
                            #'netherStalk_1': self.texture_netherStalk_1,
                            #'netherStalk_2': self.texture_netherStalk_2,
                            #'netherquartz': self.texture_netherquartz,
                            #'obsidian': self.texture_obsidian,
                            #'oreCoal': self.texture_oreCoal,
#                            'oreDiamond': self.texture_oreDiamond,
                            #'oreEmerald': self.texture_oreEmerald,
                       #     'oreGold': self.texture_oreGold,
                            #'oreIron': self.texture_oreIron,
                            #'oreLapis': self.texture_oreLapis,
                            #'oreRedstone': self.texture_oreRedstone,
                            #'piston_bottom': self.texture_piston_bottom,
                            #'piston_inner_top': self.texture_piston_inner_top,
                            #'piston_side': self.texture_piston_side,
                            #'piston_top': self.texture_piston_top,
                            #'piston_top_sticky': self.texture_piston_top_sticky,
                            #'potatoes_0': self.texture_potatoes_0,
                            #'potatoes_1': self.texture_potatoes_1,
                            #'potatoes_2': self.texture_potatoes_2,
                            #'potatoes_3': self.texture_potatoes_3,
                            #'pumpkin_face': self.texture_pumpkin_face,
                            #'pumpkin_jack': self.texture_pumpkin_jack,
                            #'pumpkin_side': self.texture_pumpkin_side,
                            #'pumpkin_top': self.texture_pumpkin_top,
                            #'quartzblock_bottom': self.texture_quartzblock_bottom,
                            #'quartzblock_chiseled': self.texture_quartzblock_chiseled,
                            #'quartzblock_chiseled_top': self.texture_quartzblock_chiseled_top,
                            #'quartzblock_lines': self.texture_quartzblock_lines,
                            #'quartzblock_lines_top': self.texture_quartzblock_lines_top,
                            #'quartzblock_side': self.texture_quartzblock_side,
                            #'quartzblock_top': self.texture_quartzblock_top,
                            #'rail': self.texture_rail,
                            #'rail_turn': self.texture_rail_turn,
                            #'redstoneDust_cross': self.texture_redstoneDust_cross,
                            #'redstoneDust_cross_overlay': self.texture_redstoneDust_cross_overlay,
                            #'redstoneDust_line': self.texture_redstoneDust_line,
                            #'redstoneDust_line_overlay': self.texture_redstoneDust_line_overlay,
                            #'redstoneLight': self.texture_redstoneLight,
                            #'redstoneLight_lit': self.texture_redstoneLight_lit,
                            #'redtorch': self.texture_redtorch,
                            #'redtorch_lit': self.texture_redtorch_lit,
                            #'reeds': self.texture_reeds,
                            #'repeater': self.texture_repeater,
                            #'repeater_lit': self.texture_repeater_lit,
                            #'rose': self.texture_rose,
                            #'sand': self.texture_sand,
                            #'sandstone_bottom': self.texture_sandstone_bottom,
                            #'sandstone_carved': self.texture_sandstone_carved,
                            #'sandstone_side': self.texture_sandstone_side,
                            #'sandstone_smooth': self.texture_sandstone_smooth,
                            #'sandstone_top': self.texture_sandstone_top,
                            #'sapling': self.texture_sapling,
                            #'sapling_birch': self.texture_sapling_birch,
                            #'sapling_jungle': self.texture_sapling_jungle,
                            #'sapling_spruce': self.texture_sapling_spruce,
                            #'snow': self.texture_snow,
                            #'snow_side': self.texture_snow_side,
                            #'sponge': self.texture_sponge,
                            #'stem_bent': self.texture_stem_bent,
                            #'stem_straight': self.texture_stem_straight,
                            #'stone': self.texture_stone,
                            #'stoneMoss': self.texture_stoneMoss,
                            #'stonebrick': self.texture_stonebrick,
                            #'stonebricksmooth': self.texture_stonebricksmooth,
                            #'stonebricksmooth_carved': self.texture_stonebricksmooth_carved,
                            #'stonebricksmooth_cracked': self.texture_stonebricksmooth_cracked,
                            #'stonebricksmooth_mossy': self.texture_stonebricksmooth_mossy,
                            #'stoneslab_side': self.texture_stoneslab_side,
                            #'stoneslab_top': self.texture_stoneslab_top,
                            #'tallgrass': self.texture_tallgrass,
                            #'thinglass_top': self.texture_thinglass_top,
                            #'tnt_bottom': self.texture_tnt_bottom,
                            #'tnt_side': self.texture_tnt_side,
                            #'tnt_top': self.texture_tnt_top,
                            #'torch': self.texture_torch,
                            #'trapdoor': self.texture_trapdoor,
                            #'tree_birch': self.texture_tree_birch,
                            #'tree_jungle': self.texture_tree_jungle,
                            #'tree_side': self.texture_tree_side,
                            #'tree_spruce': self.texture_tree_spruce,
                            #'tree_top': self.texture_tree_top,
                            #'tripWire': self.texture_tripWire,
                            #'tripWireSource': self.texture_tripWireSource,
                            #'vine': self.texture_vine,
                            #'water': self.texture_water,
                            #'water': self.texture_water,
                            #'water_flow': self.texture_water_flow,
                            #'water_flow': self.texture_water_flow,
                            #'waterlily': self.texture_waterlily,
                            #'web': self.texture_web,
                            #'whiteStone': self.texture_whiteStone,
                            #'wood': self.texture_wood,
                            #'wood_birch': self.texture_wood_birch,
                            #'wood_jungle': self.texture_wood_jungle,
                            #'wood_spruce': self.texture_wood_spruce,
                            #'workbench_front': self.texture_workbench_front,
                            #'workbench_side': self.texture_workbench_side,
                            #'workbench_top': self.texture_workbench_top
     #   }