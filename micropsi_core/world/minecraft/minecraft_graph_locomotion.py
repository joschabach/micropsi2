from micropsi_core.world.worldadapter import WorldAdapter
from micropsi_core import tools

import time


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
        'fov_x': 0,  # the fovea sensors receive their input from the fovea actors
        'fov_y': 0   #
    }

    datatargets = {
        'orientation': 0,
        'take_exit_one': 0,
        'take_exit_two': 0,
        'take_exit_three': 0,
        'fov_x': 0,
        'fov_y': 0,
        # 'fov_reset': 0,
    }

    datatarget_feedback = {
        'orientation': 0,
        'take_exit_one': 0,
        'take_exit_two': 0,
        'take_exit_three': 0,
        'fov_x': 0,
        'fov_y': 0,
        # 'fov_reset': 0
    }

    # prevent instabilities in datatargets: treat a continuous ( /unintermittent ) signal as a single trigger
    datatarget_history = {
        'take_exit_one': 0,
        'take_exit_two': 0,
        'take_exit_three': 0,
        'fov_x': 0,
        'fov_y': 0
    }

    # a collection of conditions to check on every update(..), eg., for action feedback
    waiting_list = {
        # str(time.time()): {
        #     'target': <key in self.datatarget_feedbacks>,
        #     'condition': '<variable> != <value>'
        # }
    }

    # specs for vision /fovea
    horizontal_angle = 90    # angles defining the agent's visual field
    vertical_angle = 60
    focal_length = 1         # distance of image plane from projective point /fovea
    resolution = 40          # camera resolution for a specific visual field
    max_dist = 250           # maximum distance for raytracing

    loco_nodes = {}

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
    loco_nodes[home_uid]['y'] = 65
    loco_nodes[home_uid]['z'] = 59
    loco_nodes[home_uid]['exit_one_uid'] = cloud_uid
    loco_nodes[home_uid]['exit_two_uid'] = cathedral_uid
    loco_nodes[home_uid]['exit_three_uid'] = village_uid

    # assuming we start at the home position
    current_loco_node = loco_nodes[home_uid]

    loco_nodes[underground_garden_uid] = loco_node_template.copy()
    loco_nodes[underground_garden_uid]['name'] = "underground garden"
    loco_nodes[underground_garden_uid]['uid'] = underground_garden_uid
    loco_nodes[underground_garden_uid]['x'] = -264
    loco_nodes[underground_garden_uid]['y'] = 65
    loco_nodes[underground_garden_uid]['z'] = 65
    loco_nodes[underground_garden_uid]['exit_one_uid'] = home_uid
    loco_nodes[underground_garden_uid]['exit_two_uid'] = village_uid

    loco_nodes[village_uid] = loco_node_template.copy()
    loco_nodes[village_uid]['name'] = "village"
    loco_nodes[village_uid]['uid'] = village_uid
    loco_nodes[village_uid]['x'] = -293
    loco_nodes[village_uid]['y'] = 65
    loco_nodes[village_uid]['z'] = -220
    loco_nodes[village_uid]['exit_one_uid'] = underground_garden_uid
    loco_nodes[village_uid]['exit_two_uid'] = home_uid

    loco_nodes[cathedral_uid] = loco_node_template.copy()
    loco_nodes[cathedral_uid]['name'] = "cathedral"
    loco_nodes[cathedral_uid]['uid'] = cathedral_uid
    loco_nodes[cathedral_uid]['x'] = -100
    loco_nodes[cathedral_uid]['y'] = 65
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
    loco_nodes[cloud_uid]['y'] = 65
    loco_nodes[cloud_uid]['z'] = 198
    loco_nodes[cloud_uid]['exit_one_uid'] = home_uid
    loco_nodes[cloud_uid]['exit_two_uid'] = cathedral_uid

    loco_nodes[bungalow_uid] = loco_node_template.copy()
    loco_nodes[bungalow_uid]['name'] = "bungalow"
    loco_nodes[bungalow_uid]['uid'] = bungalow_uid
    loco_nodes[bungalow_uid]['x'] = 28
    loco_nodes[bungalow_uid]['y'] = 65
    loco_nodes[bungalow_uid]['z'] = 292
    loco_nodes[bungalow_uid]['exit_one_uid'] = cathedral_uid
    loco_nodes[bungalow_uid]['exit_two_uid'] = farm_uid

    loco_nodes[farm_uid] = loco_node_template.copy()
    loco_nodes[farm_uid]['name'] = "farm"
    loco_nodes[farm_uid]['uid'] = farm_uid
    loco_nodes[farm_uid]['x'] = -50
    loco_nodes[farm_uid]['y'] = 65
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
    loco_nodes[desert_outpost_uid]['y'] = 65
    loco_nodes[desert_outpost_uid]['z'] = 958
    loco_nodes[desert_outpost_uid]['exit_one_uid'] = forest_uid

    loco_nodes[swamp_uid] = loco_node_template.copy()
    loco_nodes[swamp_uid]['name'] = "swamp"
    loco_nodes[swamp_uid]['uid'] = swamp_uid
    loco_nodes[swamp_uid]['x'] = -529
    loco_nodes[swamp_uid]['y'] = 65
    loco_nodes[swamp_uid]['z'] = 504
    loco_nodes[swamp_uid]['exit_one_uid'] = forest_uid
    loco_nodes[swamp_uid]['exit_two_uid'] = summit_uid

    def __init__(self, world, uid=None, **data):
        super(MinecraftGraphLocomotion, self).__init__(world, uid, **data)
        self.spockplugin = self.world.spockplugin

    def update(self):
        """called on every world simulation step to advance the life of the agent"""

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

        # check if waiting list contains confirmations for datatarget_feedback, if so overwrite resp. value
        mark_for_deletion = []
        if self.waiting_list:
            for k, item in self.waiting_list.items():
                if eval(item['condition']):
                    self.datatarget_feedback[item['target']] = 1.
                    mark_for_deletion.append(k)

        # delete processed items from waiting_list
        for i in mark_for_deletion:
            del self.waiting_list[i]

        # read locomotor values, trigger teleportation in the world, and provide action feedback
        # don't trigger another teleportation if the datatargets was on continuously, cf. pipe logic
        if self.datatargets['take_exit_one'] >= 1 and not self.datatarget_history['take_exit_one'] >= 1:
            # if the current node on the transition graph has the chose exit
            if self.current_loco_node['exit_one_uid'] is not None:
                # add request for action feedback in case of success to self.waiting_list
                # ie. if future position is different from current position, teleport must have succeeded
                # < unreliable condition can be used here because w/out timeout feedback is blocking wrt further locomotion
                # in case we add timeout, a timeout should also delete the item from the waiting_list
                # TODO: add timeout
                self.add_to_waiting_list(
                    'take_exit_one',
                    "%d != int(self.spockplugin.clientinfo.position['x']) or \
                     %d != int(self.spockplugin.clientinfo.position['y']) or \
                     %d != int(self.spockplugin.clientinfo.position['z'])"
                    % (int(self.spockplugin.clientinfo.position['x']),
                       int(self.spockplugin.clientinfo.position['y']),
                       int(self.spockplugin.clientinfo.position['z'])))
                self.locomote(self.current_loco_node['exit_one_uid'])
            else:
                self.datatarget_feedback['take_exit_one'] = -1.

        if self.datatargets['take_exit_two'] >= 1 and not self.datatarget_history['take_exit_two'] >= 1:
            if self.current_loco_node['exit_two_uid'] is not None:
                self.add_to_waiting_list(
                    'take_exit_two',
                    "%d != int(self.spockplugin.clientinfo.position['x']) or \
                     %d != int(self.spockplugin.clientinfo.position['y']) or \
                     %d != int(self.spockplugin.clientinfo.position['z'])"
                    % (int(self.spockplugin.clientinfo.position['x']),
                       int(self.spockplugin.clientinfo.position['y']),
                       int(self.spockplugin.clientinfo.position['z'])))
                self.locomote(self.current_loco_node['exit_two_uid'])
            else:
                self.datatarget_feedback['take_exit_two'] = -1.

        if self.datatargets['take_exit_three'] >= 1 and not self.datatarget_history['take_exit_three'] >= 1:
            if self.current_loco_node['exit_three_uid'] is not None:
                self.add_to_waiting_list(
                    'take_exit_three',
                    "%d != int(self.spockplugin.clientinfo.position['x']) or \
                     %d != int(self.spockplugin.clientinfo.position['y']) or \
                     %d != int(self.spockplugin.clientinfo.position['z'])"
                    % (int(self.spockplugin.clientinfo.position['x']),
                       int(self.spockplugin.clientinfo.position['y']),
                       int(self.spockplugin.clientinfo.position['z'])))
                self.locomote(self.current_loco_node['exit_three_uid'])
            else:
                self.datatarget_feedback['take_exit_three'] = -1.

        # read fovea actors, trigger sampling, and provide action feedback
        if self.datatargets['fov_x'] > 0 and self.datatargets['fov_y'] > 0 \
                and not self.datatarget_history['fov_x'] > 0 and not self.datatarget_history['fov_y'] > 0:
            # get block type for current fovea position
            block_type = self.get_visual_input(int(self.datatargets['fov_x'] - 1), int(self.datatargets['fov_y'] - 1))
            # map block type to one of the sensors
            self.map_block_type_to_sensor(block_type)
            # set fovea sensors; sic because fovea value is used as link weight
            self.datasources['fov_x'] = self.datatargets['fov_x']
            self.datasources['fov_y'] = self.datatargets['fov_y']
            # provide action feedback
            self.datatarget_feedback['fov_x'] = 1
            self.datatarget_feedback['fov_y'] = 1
        # note: fovea saccading can't fail because it involves only internal actors, not ones granted by the world

        # update datatarget history
        for k in self.datatarget_history.keys():
            self.datatarget_history[k] = self.datatargets[k]

    def locomote(self, target_loco_node_uid):

        new_loco_node = self.loco_nodes[target_loco_node_uid]

        self.spockplugin.chat("/tppos {0} {1} {2}".format(
            new_loco_node['x'],
            new_loco_node['y'],
            new_loco_node['z']))

        self.current_loco_node = new_loco_node

    def get_visual_input(self, fov_x, fov_y):
        """
        """
        from math import radians, tan

        # set agent position
        pos_x = self.spockplugin.clientinfo.position['x']
        pos_y = self.spockplugin.clientinfo.position['y']
        pos_z = self.spockplugin.clientinfo.position['z']

        # set yaw and pitch ( in degrees )
        yaw = self.spockplugin.clientinfo.position['yaw']
        pitch = self.spockplugin.clientinfo.position['pitch']

        # compute parameters from specs
        width = 2 * tan(radians(self.horizontal_angle / 2)) * self.focal_length
        height = 2 * tan(radians(self.vertical_angle / 2)) * self.focal_length

        # span image plane
        # such that height is mostly above y and width is to left and right of x in equal shares
        tick = 1. / self.resolution
        # split height 95 to 5
        h_low = height * 0.5 / 10
        h_up = height - h_low
        h_line = [i for i in self.frange(pos_x - width / 2, pos_x + width / 2, tick)]
        v_line = [i for i in self.frange(pos_y - h_low, pos_y + h_up, tick)]

        # compute pixel values of image plane
        block_types = tuple()
        distances = tuple()

        x0, y0, z0 = pos_x, pos_y, pos_z  # agent's position aka projective point
        zi = z0 + self.focal_length

        h_line.reverse()
        v_line.reverse()

        return self.project(h_line[fov_x], v_line[fov_y], zi, x0, y0, z0, yaw, pitch)

    def project(self, xi, yi, zi, x0, y0, z0, yaw, pitch):
        """
        """
        from math import sqrt

        distance = 0    # just a counter
        block_type = 0
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

            block_type = self.get_block_type(
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
        if block_type == -1:
            self.datasources['nothing'] = 1.

        elif block_type == 0:
            self.datasources['air'] = 1.

        elif block_type == 1 or block_type == 4 or block_type == 7:
            self.datasources['stone'] = 1.

        elif block_type == 2 or block_type == 31:
            self.datasources['grass'] = 1.

        elif block_type == 3:
            self.datasources['dirt'] = 1.

        elif block_type == 5 or block_type == 17:
            self.datasources['wood'] = 1.

        elif block_type == 8 or block_type == 9:
            self.datasources['water'] = 1.

        elif block_type == 12:
            self.datasources['sand'] = 1.

        elif block_type == 13:
            self.datasources['gravel'] = 1.

        elif block_type == 18:
            self.datasources['leaves'] = 1.

        elif block_type == 14 or block_type == 15 or block_type == 16 or \
            block_type == 20 or block_type == 41 or block_type == 42 or \
            block_type == 43 or block_type == 44 or block_type == 45 or \
                block_type == 47 or block_type == 48 or block_type == 49:
            self.datasources['solids'] = 1.

        else:
            self.datasources['otter'] = 1.

    def get_block_type(self, x, y, z):
        """ """
        key = (x // 16, z // 16)
        columns = self.spockplugin.world.map.columns
        if key not in columns:
            return -1
        current_column = columns[key]
        if len(current_column.chunks) <= y // 16:
            return -1
        try:
            current_section = current_column.chunks[y // 16]
        except IndexError:
            return -1
        if current_section is None:
            return -1
        else:
            return current_section.get(x % 16, y % 16, z % 16).id

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

    def add_to_waiting_list(self, target, condition):
        """
        """
        key = str(time.time())
        self.waiting_list[key] = {}
        self.waiting_list[key]['target'] = target
        self.waiting_list[key]['condition'] = condition
