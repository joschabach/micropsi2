from micropsi_core.world.worldadapter import WorldAdapter
from micropsi_core import tools
import random
import logging
import time
from functools import partial


class MinecraftGraphLocomotion(WorldAdapter):

    datasources = {
        'nothing': 0,  # -1
        'air': 0,      # 0
        'stone': 0,    # 1, 4, 7, 24 ( sand stone )
        'grass': 0,    # 2
        'dirt': 0,     # 3
        'wood': 0,     # 5, 17
        'water': 0,    # 8, 9
        'sand': 0,     # 12
        'gravel': 0,   # 13
        'leaves': 0,   # 18
        'solids': 0,   # 14, 15, 16, 20, 41, 42, 43, 44, 45, 47, 48, 49
        'otter': 0,    # miscellaneous /otter

        'fov_x': 0,    # fovea sensors receive their input from the fovea actors
        'fov_y': 0,

        'fov__0_0': 0,
        'fov__0_1': 0,
        'fov__0_2': 0,
        'fov__0_3': 0,
        'fov__0_4': 0,
        'fov__0_5': 0,
        'fov__0_6': 0,
        'fov__0_7': 0,

        'fov__1_0': 0,
        'fov__1_1': 0,
        'fov__1_2': 0,
        'fov__1_3': 0,
        'fov__1_4': 0,
        'fov__1_5': 0,
        'fov__1_6': 0,
        'fov__1_7': 0,

        'fov__2_0': 0,
        'fov__2_1': 0,
        'fov__2_2': 0,
        'fov__2_3': 0,
        'fov__2_4': 0,
        'fov__2_5': 0,
        'fov__2_6': 0,
        'fov__2_7': 0,

        'fov__3_0': 0,
        'fov__3_1': 0,
        'fov__3_2': 0,
        'fov__3_3': 0,
        'fov__3_4': 0,
        'fov__3_5': 0,
        'fov__3_6': 0,
        'fov__3_7': 0,

        'fov__4_0': 0,
        'fov__4_1': 0,
        'fov__4_2': 0,
        'fov__4_3': 0,
        'fov__4_4': 0,
        'fov__4_5': 0,
        'fov__4_6': 0,
        'fov__4_7': 0,

        'fov__5_0': 0,
        'fov__5_1': 0,
        'fov__5_2': 0,
        'fov__5_3': 0,
        'fov__5_4': 0,
        'fov__5_5': 0,
        'fov__5_6': 0,
        'fov__5_7': 0,

        'fov__6_0': 0,
        'fov__6_1': 0,
        'fov__6_2': 0,
        'fov__6_3': 0,
        'fov__6_4': 0,
        'fov__6_5': 0,
        'fov__6_6': 0,
        'fov__6_7': 0,

        'fov__7_0': 0,
        'fov__7_1': 0,
        'fov__7_2': 0,
        'fov__7_3': 0,
        'fov__7_4': 0,
        'fov__7_5': 0,
        'fov__7_6': 0,
        'fov__7_7': 0,

        'health': 1,
        'food': 1
    }

    datatargets = {
        'orientation': 0,
        'take_exit_one': 0,
        'take_exit_two': 0,
        'take_exit_three': 0,
        'fov_x': 0,
        'fov_y': 0,
        'eat': 0
    }

    datatarget_feedback = {
        'orientation': 0,
        'take_exit_one': 0,
        'take_exit_two': 0,
        'take_exit_three': 0,
        'fov_x': 0,
        'fov_y': 0,
        'eat': 0
    }

    # prevent instabilities in datatargets: treat a continuous ( /unintermittent ) signal as a single trigger
    datatarget_history = {
        'take_exit_one': 0,
        'take_exit_two': 0,
        'take_exit_three': 0,
        'fov_x': 0,
        'fov_y': 0,
        'eat': 0
    }

    # a collection of conditions to check on every update(..), eg., for action feedback
    waiting_list = []

    # specs for vision /fovea
    focal_length = 1  # distance of image plane from projective point /fovea
    max_dist = 200    # maximum distance for raytracing
    resolution = 4    # number of rays per tick in viewport /camera coordinate system
    im_width = 32     # width of projection /image plane in the world
    im_height = 16    # height of projection /image plane in the world
    cam_width = 1.    # width of normalized device /camera /viewport
    cam_height = 1.   # height of normalized device /camera /viewport
    patch_len = 8     # side length of a fovea patch

    # Note: actors fov_x, fov_y and the saccader's gates fov_x, fov_y ought to be parametrized [0.,2.] w/ threshold 1.
    # -- 0. means inactivity, values between 1. and 2. are the scaled down movement in x/y direction on the image plane

    loco_nodes = {}

    target_loco_node_uid = None

    loco_node_template = {
        'uid': "",
        'name': "",
        'x': 0,
        'y': 0,
        'z': 0,
        'exit_one_uid': None,
        'exit_two_uid': None,
        'exit_three_uid': None,
    }

    home_uid = tools.generate_uid()
    underground_garden_uid = tools.generate_uid()
    village_uid = tools.generate_uid()
    cathedral_uid = tools.generate_uid()
    summit_uid = tools.generate_uid()
    cloud_uid = tools.generate_uid()
    bungalow_uid = tools.generate_uid()
    farm_uid = tools.generate_uid()
    forest_uid = tools.generate_uid()
    desert_outpost_uid = tools.generate_uid()
    swamp_uid = tools.generate_uid()

    loco_nodes[home_uid] = loco_node_template.copy()
    loco_nodes[home_uid]['name'] = "home"
    loco_nodes[home_uid]['uid'] = home_uid
    loco_nodes[home_uid]['x'] = -105
    loco_nodes[home_uid]['y'] = 63
    loco_nodes[home_uid]['z'] = 59
    loco_nodes[home_uid]['exit_one_uid'] = cloud_uid
    loco_nodes[home_uid]['exit_two_uid'] = cathedral_uid
    loco_nodes[home_uid]['exit_three_uid'] = village_uid

    current_loco_node = None

    loco_nodes[underground_garden_uid] = loco_node_template.copy()
    loco_nodes[underground_garden_uid]['name'] = "underground garden"
    loco_nodes[underground_garden_uid]['uid'] = underground_garden_uid
    loco_nodes[underground_garden_uid]['x'] = -264
    loco_nodes[underground_garden_uid]['y'] = 62
    loco_nodes[underground_garden_uid]['z'] = 65
    loco_nodes[underground_garden_uid]['exit_one_uid'] = home_uid
    loco_nodes[underground_garden_uid]['exit_two_uid'] = village_uid

    loco_nodes[village_uid] = loco_node_template.copy()
    loco_nodes[village_uid]['name'] = "village"
    loco_nodes[village_uid]['uid'] = village_uid
    loco_nodes[village_uid]['x'] = -293
    loco_nodes[village_uid]['y'] = 64
    loco_nodes[village_uid]['z'] = -220
    loco_nodes[village_uid]['exit_one_uid'] = underground_garden_uid
    loco_nodes[village_uid]['exit_two_uid'] = home_uid

    loco_nodes[cathedral_uid] = loco_node_template.copy()
    loco_nodes[cathedral_uid]['name'] = "cathedral"
    loco_nodes[cathedral_uid]['uid'] = cathedral_uid
    loco_nodes[cathedral_uid]['x'] = -100
    loco_nodes[cathedral_uid]['y'] = 63
    loco_nodes[cathedral_uid]['z'] = 282
    loco_nodes[cathedral_uid]['exit_one_uid'] = home_uid
    loco_nodes[cathedral_uid]['exit_two_uid'] = cloud_uid
    loco_nodes[cathedral_uid]['exit_three_uid'] = bungalow_uid

    loco_nodes[summit_uid] = loco_node_template.copy()
    loco_nodes[summit_uid]['name'] = "summit"
    loco_nodes[summit_uid]['uid'] = summit_uid
    loco_nodes[summit_uid]['x'] = -233
    loco_nodes[summit_uid]['y'] = 102
    loco_nodes[summit_uid]['z'] = 307
    loco_nodes[summit_uid]['exit_one_uid'] = swamp_uid

    loco_nodes[cloud_uid] = loco_node_template.copy()
    loco_nodes[cloud_uid]['name'] = "cloud"
    loco_nodes[cloud_uid]['uid'] = cloud_uid
    loco_nodes[cloud_uid]['x'] = -98
    loco_nodes[cloud_uid]['y'] = 63
    loco_nodes[cloud_uid]['z'] = 198
    loco_nodes[cloud_uid]['exit_one_uid'] = home_uid
    loco_nodes[cloud_uid]['exit_two_uid'] = cathedral_uid

    loco_nodes[bungalow_uid] = loco_node_template.copy()
    loco_nodes[bungalow_uid]['name'] = "bungalow"
    loco_nodes[bungalow_uid]['uid'] = bungalow_uid
    loco_nodes[bungalow_uid]['x'] = 28
    loco_nodes[bungalow_uid]['y'] = 63
    loco_nodes[bungalow_uid]['z'] = 292
    loco_nodes[bungalow_uid]['exit_one_uid'] = cathedral_uid
    loco_nodes[bungalow_uid]['exit_two_uid'] = farm_uid

    loco_nodes[farm_uid] = loco_node_template.copy()
    loco_nodes[farm_uid]['name'] = "farm"
    loco_nodes[farm_uid]['uid'] = farm_uid
    loco_nodes[farm_uid]['x'] = -50
    loco_nodes[farm_uid]['y'] = 64
    loco_nodes[farm_uid]['z'] = 410
    loco_nodes[farm_uid]['exit_one_uid'] = bungalow_uid
    loco_nodes[farm_uid]['exit_two_uid'] = cathedral_uid
    loco_nodes[farm_uid]['exit_three_uid'] = forest_uid

    loco_nodes[forest_uid] = loco_node_template.copy()
    loco_nodes[forest_uid]['name'] = "forest"
    loco_nodes[forest_uid]['uid'] = forest_uid
    loco_nodes[forest_uid]['x'] = -273
    loco_nodes[forest_uid]['y'] = 65
    loco_nodes[forest_uid]['z'] = 782
    loco_nodes[forest_uid]['exit_one_uid'] = farm_uid
    loco_nodes[forest_uid]['exit_two_uid'] = desert_outpost_uid
    loco_nodes[forest_uid]['exit_three_uid'] = swamp_uid

    loco_nodes[desert_outpost_uid] = loco_node_template.copy()
    loco_nodes[desert_outpost_uid]['name'] = "desert outpost"
    loco_nodes[desert_outpost_uid]['uid'] = desert_outpost_uid
    loco_nodes[desert_outpost_uid]['x'] = -243
    loco_nodes[desert_outpost_uid]['y'] = 64
    loco_nodes[desert_outpost_uid]['z'] = 958
    loco_nodes[desert_outpost_uid]['exit_one_uid'] = forest_uid

    loco_nodes[swamp_uid] = loco_node_template.copy()
    loco_nodes[swamp_uid]['name'] = "swamp"
    loco_nodes[swamp_uid]['uid'] = swamp_uid
    loco_nodes[swamp_uid]['x'] = -529
    loco_nodes[swamp_uid]['y'] = 63
    loco_nodes[swamp_uid]['z'] = 504
    loco_nodes[swamp_uid]['exit_one_uid'] = forest_uid
    loco_nodes[swamp_uid]['exit_two_uid'] = summit_uid

    logger = None

    tp_tolerance = 5
    action_timeout = 10

    def __init__(self, world, uid=None, **data):
        super(MinecraftGraphLocomotion, self).__init__(world, uid, **data)
        self.spockplugin = self.world.spockplugin
        self.waiting_for_spock = True
        self.logger = logging.getLogger("world")
        self.spockplugin.event.reg_event_handler('PLAY<Spawn Position', self.set_datasources)

    def set_datasources(self, event, data):
        self.datasources['health'] = self.spockplugin.clientinfo.health['health'] / 20
        self.datasources['food'] = self.spockplugin.clientinfo.health['food'] / 20

    def update(self):
        """called on every world simulation step to advance the life of the agent"""

        if not self.spockplugin.is_connected():
            raise RuntimeError("Lost connection to minecraft server")

        # first thing when spock initialization is done, determine current loco node
        if self.waiting_for_spock:
            # by substitution: spock init is considered done, when its client has a position unlike
            # {'on_ground': False, 'pitch': 0, 'x': 0, 'y': 0, 'yaw': 0, 'stance': 0, 'z': 0}:
            if self.spockplugin.clientinfo.position['y'] != 0. \
                    and self.spockplugin.clientinfo.position['x'] != 0:
                self.waiting_for_spock = False
                x = int(self.spockplugin.clientinfo.position['x'])
                y = int(self.spockplugin.clientinfo.position['y'])
                z = int(self.spockplugin.clientinfo.position['z'])
                for k, v in self.loco_nodes.items():
                    if abs(x - v['x']) <= self.tp_tolerance and abs(y - v['y']) <= self.tp_tolerance and abs(z - v['z']) <= self.tp_tolerance:
                        self.current_loco_node = self.loco_nodes[k]

                if self.current_loco_node is None:
                    # bot is outside our graph, teleport to a random graph location to get started.
                    target = random.choice(list(self.loco_nodes.keys()))
                    self.locomote(target)

        else:

            #
            orientation = self.datatargets['orientation']  # x_axis + 360 / orientation  degrees
            self.datatarget_feedback['orientation'] = 1
            # self.datatargets['orientation'] = 0

            # reset self.datasources
            for k in self.datasources.keys():
                self.datasources[k] = 0.

            # reset self.datatarget_feedback
            for k in self.datatarget_feedback.keys():
                self.datatarget_feedback[k] = 0.

            # don't reset self.datatargets because their activation is processed differently
            # depending on whether they fire continuously or not, see self.datatarget_history

            # health and food are in [0;20]
            self.datasources['health'] = self.spockplugin.clientinfo.health['health'] / 20
            self.datasources['food'] = self.spockplugin.clientinfo.health['food'] / 20

            self.check_for_action_feedback()

            # read locomotor values, trigger teleportation in the world, and provide action feedback
            # don't trigger another teleportation if the datatargets was on continuously, cf. pipe logic
            if self.datatargets['take_exit_one'] >= 1 and not self.datatarget_history['take_exit_one'] >= 1:
                # if the current node on the transition graph has the selected exit
                if self.current_loco_node['exit_one_uid'] is not None:
                    self.register_action(
                        'take_exit_one',
                        partial(self.locomote, self.current_loco_node['exit_one_uid']),
                        partial(self.check_movement_feedback, self.current_loco_node['exit_one_uid'])
                    )
                else:
                    self.datatarget_feedback['take_exit_one'] = -1.

            if self.datatargets['take_exit_two'] >= 1 and not self.datatarget_history['take_exit_two'] >= 1:
                if self.current_loco_node['exit_two_uid'] is not None:
                    self.register_action(
                        'take_exit_two',
                        partial(self.locomote, self.current_loco_node['exit_two_uid']),
                        partial(self.check_movement_feedback, self.current_loco_node['exit_two_uid'])
                    )
                else:
                    self.datatarget_feedback['take_exit_two'] = -1.

            if self.datatargets['take_exit_three'] >= 1 and not self.datatarget_history['take_exit_three'] >= 1:
                if self.current_loco_node['exit_three_uid'] is not None:
                    self.register_action(
                        'take_exit_three',
                        partial(self.locomote, self.current_loco_node['exit_three_uid']),
                        partial(self.check_movement_feedback, self.current_loco_node['exit_three_uid'])
                    )
                else:
                    self.datatarget_feedback['take_exit_three'] = -1.

            if self.datatargets['eat'] >= 1 and not self.datatarget_history['eat'] >= 1:
                if self.has_bread() and self.datasources['food'] < 1:
                    self.register_action(
                        'eat',
                        self.spockplugin.eat,
                        partial(self.check_eat_feedback, self.spockplugin.clientinfo.health['food'])
                    )
                else:
                    self.datatarget_feedback['eat'] = -1.

            # read fovea actors, trigger sampling, and provide action feedback
            if not (self.datatargets['fov_x'] == 0. and self.datatargets['fov_y'] == 0.):
                # update fovea sensors
                self.datasources['fov_x'] = self.datatargets['fov_x'] - 1.
                self.datasources['fov_y'] = self.datatargets['fov_y'] - 1.
                # print("fovea values (%.3f,%.3f)" % (self.datasources['fov_x'], self.datasources['fov_y']))
                self.get_visual_input(self.datasources['fov_x'], self.datasources['fov_y'])

            # provide action feedback
            # Note: saccading can't fail because fov_x, fov_y are internal actors, hence we return immediate feedback
            self.datatarget_feedback['fov_x'] = 1
            self.datatarget_feedback['fov_y'] = 1

            # impatience!
            self.check_for_action_feedback()

            # update datatarget history
            for k in self.datatarget_history.keys():
                self.datatarget_history[k] = self.datatargets[k]

    def locomote(self, target_loco_node_uid):

        new_loco_node = self.loco_nodes[target_loco_node_uid]

        self.spockplugin.chat("/tppos {0} {1} {2}".format(
            new_loco_node['x'],
            new_loco_node['y'],
            new_loco_node['z']))

        self.target_loco_node_uid = target_loco_node_uid

        self.current_loco_node = new_loco_node

    def check_for_action_feedback(self):
        """ """
        # check if any pending datatarget_feedback can be confirmed with data from the world
        if self.waiting_list:
            new_waiting_list = []
            for index, item in enumerate(self.waiting_list):
                if item['validation']():
                    self.datatarget_feedback[item['datatarget']] = 1.
                else:
                    new_waiting_list.append(item)

            for item in new_waiting_list:
                if time.clock() - item['time'] > self.action_timeout:
                    # re-trigger action
                    item['action']()
                    item['time'] = time.clock()

            self.waiting_list = new_waiting_list

    def register_action(self, datatarget, action_function, validation_function):
        """ registers an action to be performed by the agent. Will wait, and eventually re-trigger the action
            until the validation function returns true, signalling success of the action"""
        self.waiting_list.append({
            'datatarget': datatarget,
            'action': action_function,
            'validation': validation_function,
            'time': time.clock()
        })
        action_function()

    def has_bread(self):
        for item in self.spockplugin.inventory:
            if item.get('id', 0) == 297:
                return True
        return False

    def check_eat_feedback(self, old_value):
        food = self.spockplugin.clientinfo.health['food']
        return food > old_value or food == 20

    def check_movement_feedback(self, target_loco_node):
        if abs(self.loco_nodes[target_loco_node]['x'] - int(self.spockplugin.clientinfo.position['x'])) <= self.tp_tolerance \
           and abs(self.loco_nodes[target_loco_node]['y'] - int(self.spockplugin.clientinfo.position['y'])) <= self.tp_tolerance \
           and abs(self.loco_nodes[target_loco_node]['z'] - int(self.spockplugin.clientinfo.position['z'])) <= self.tp_tolerance:
            # hand the agent a bread, if it just arrived at the farm, or at the village
            if target_loco_node == self.village_uid or target_loco_node == self.farm_uid:
                self.spockplugin.give_item('bread')
            return True
        return False

    def get_visual_input(self, fov_x, fov_y):
        """
        Spans an image plane
        """
        from math import radians, tan

        # set agent position
        pos_x = self.spockplugin.clientinfo.position['x']
        pos_y = self.spockplugin.clientinfo.position['y']  # + 1.620
        pos_z = self.spockplugin.clientinfo.position['z']

        # set yaw and pitch ( in degrees )
        yaw = self.spockplugin.clientinfo.position['yaw']
        # consider setting yaw to a random value between 0 and 359
        pitch = self.spockplugin.clientinfo.position['pitch']

        # compute ticks per dimension
        tick_w = self.cam_width / self.im_width / self.resolution
        tick_h = self.cam_height / self.im_height / self.resolution

        # span image plane
        # the horizontal plane is split half-half, the vertical plane is shifted upwards
        h_line = [i for i in self.frange(pos_x - 0.5 * self.cam_width, pos_x + 0.5 * self.cam_width, tick_w)]
        v_line = [i for i in self.frange(pos_y - 0.05 * self.cam_height, pos_y + 0.95 * self.cam_height, tick_h)]

        # scale up fov_x, fov_y
        fov_x = round(fov_x * (self.im_width * self.resolution - self.patch_len))
        fov_y = round(fov_y * (self.im_height * self.resolution - self.patch_len))

        x0, y0, z0 = pos_x, pos_y, pos_z  # agent's position aka projective point
        zi = z0 + self.focal_length

        h_line.reverse()
        v_line.reverse()

        # compute block type values for the whole patch /fovea
        patch = []
        for i in range(self.patch_len):
            for j in range(self.patch_len):
                try:
                    block_type, distance = self.project(h_line[fov_x + j], v_line[fov_y + i], zi, x0, y0, z0, yaw, pitch)
                except IndexError:
                    block_type, distance = -1, -1
                    self.logger.warning("IndexError at (%d,%d)" % (fov_x + j, fov_y + i))
                patch.append(block_type)
                # for now, keep block type sensors and activate them respectively
                block_type_pooled = self.map_block_type_to_sensor(block_type)
                # patch.append(block_type_pooled)

        # normalize block type values
        # subtract patch mean
        mean = float(sum(patch)) / len(patch)
        patch_avg = [x - mean for x in patch]

        # truncate to +/- 3 standard deviations and scale to -1 and +1
        var = [x ** 2 for x in patch_avg]
        std = (sum(var) / len(var)) ** 0.5
        pstd = 3 * std
        # if block types are all the same number, eg. -1, std will be 0, therefore
        if pstd == 0:
            patch_std = [0 for x in patch_avg]
        else:
            patch_std = [max(min(x, pstd), -pstd) / pstd for x in patch_avg]

        # scale from [-1,+1] to [0.1,0.9] and write values to sensors
        patch_resc = [(1 + x) * 0.4 + 0.1 for x in patch_std]
        for i in range(self.patch_len):
            for j in range(self.patch_len):
                str_name = 'fov__%d_%d' % (j, i)  # Beware: magic name
                # write values to self.datasources aka sensors
                self.datasources[str_name] = patch_resc[self.patch_len * i + j]

    def project(self, xi, yi, zi, x0, y0, z0, yaw, pitch):
        """
        Given a point on the projection plane and the agent's position, cast a
        ray to find the nearest block type that isn't air and its distance from
        the projective plane.
        """
        from math import sqrt

        distance = 0    # just a counter
        block_type = -1
        xb, yb, zb = xi, yi, zi

        # compute difference vector between projective point and image point
        diff = (xi - x0, yi - y0, zi - z0)

        # normalize difference vector
        magnitude = sqrt(diff[0] ** 2 + diff[1] ** 2 + diff[2] ** 2)
        if magnitude == 0.:
            magnitude = 1.
        norm = (diff[0] / magnitude, diff[1] / magnitude, diff[2] / magnitude)

        # rotate norm vector
        norm = self.rotate_around_x_axis(norm, pitch)
        norm = self.rotate_around_y_axis(norm, yaw)

        # rotate diff vector
        diff = self.rotate_around_x_axis(diff, pitch)
        diff = self.rotate_around_y_axis(diff, yaw)

        # add diff to projection point aka agent's position
        xb, yb, zb = x0 + diff[0], y0 + diff[1], z0 + diff[2]

        while block_type <= 0:  # which is air

            # check block type of next distance point along ray
            # aka add normalized difference vector to image point
            xb = xb + norm[0]
            yb = yb + norm[1]
            zb = zb + norm[2]

            block_type = self.spockplugin.get_block_type(
                int(xb),
                int(yb),
                int(zb),
            )

            distance += 1
            if distance >= self.max_dist:
                break

        return block_type, distance

    def map_block_type_to_sensor(self, block_type):
        """
        Map block type given by an integer to a block sensor;
        cf. http://minecraft.gamepedia.com/Data_values#Block_IDs.
        """
        if block_type < 0:
            self.datasources['nothing'] = 1.
            return -1

        elif block_type == 0:
            self.datasources['air'] = 1.
            return 0

        elif block_type == 1 or block_type == 4 or block_type == 7:
            self.datasources['stone'] = 1.
            return 1

        elif block_type == 2 or block_type == 31:
            self.datasources['grass'] = 1.
            return 2

        elif block_type == 3:
            self.datasources['dirt'] = 1.
            return 3

        elif block_type == 5 or block_type == 17:
            self.datasources['wood'] = 1.
            return 4

        elif block_type == 8 or block_type == 9:
            self.datasources['water'] = 1.
            return 5

        elif block_type == 12:
            self.datasources['sand'] = 1.
            return 6

        elif block_type == 13:
            self.datasources['gravel'] = 1.
            return 7

        elif block_type == 18:
            self.datasources['leaves'] = 1.
            return 8

        elif block_type == 14 or block_type == 15 or block_type == 16 or \
            block_type == 20 or block_type == 41 or block_type == 42 or \
            block_type == 43 or block_type == 44 or block_type == 45 or \
                block_type == 47 or block_type == 48 or block_type == 49:
            self.datasources['solids'] = 1.
            return 9

        else:
            self.datasources['otter'] = 1.
            return 10


    def rotate_around_x_axis(self, pos, angle):
        """ Rotate a 3D point around the x-axis given a specific angle. """
        from math import radians, cos, sin

        # convert angle in degrees to radians
        theta = radians(angle)

        # rotate vector
        x = pos[0]
        y = pos[1] * cos(theta) - pos[2] * sin(theta)
        z = pos[1] * sin(theta) + pos[2] * cos(theta)

        return (x, y, z)

    def rotate_around_y_axis(self, pos, angle):
        """ Rotate a 3D point around the y-axis given a specific angle. """
        from math import radians, cos, sin

        # convert angle in degrees to radians
        theta = radians(angle)

        # rotate vector
        x = pos[0] * cos(theta) + pos[2] * sin(theta)
        y = pos[1]
        z = - pos[0] * sin(theta) + pos[2] * cos(theta)

        return (x, y, z)

    def rotate_around_z_axis(self, pos, angle):
        """ Rotate a 3D point around the z-axis given a specific angle. """
        from math import radians, cos, sin

        # convert angle in degrees to radians
        theta = radians(angle)

        # rotate vector
        x = pos[0] * cos(theta) - pos[1] * sin(theta)
        y = pos[0] * sin(theta) + pos[1] * cos(theta)
        z = pos[2]

        return (x, y, z)

    def frange(self, start, end, step):
        """
        Range for floats.
        """
        while start < end:
            yield start
            start += step
