from micropsi_core.world.worldadapter import WorldAdapter
from micropsi_core import tools
from configuration import config as cfg
import random
import logging
import time
from functools import partial
from math import sqrt, radians, cos, sin, tan
from spock.mcp.mcpacket import Packet


class MinecraftGraphLocomotion(WorldAdapter):

    supported_datasources = [
        'fov_x',    # fovea sensors receive their input from the fovea actors
        'fov_y',
        'fov_hist__-01',  # these names must be the most commonly observed block types
        'fov_hist__000',
        'fov_hist__001',
        'fov_hist__002',
        'fov_hist__003',
        'fov_hist__004',
        'fov_hist__009',
        'fov_hist__012',
        'fov_hist__017',
        'fov_hist__018',
        'fov_hist__020',
        'fov_hist__026',
        'fov_hist__031',
        'fov_hist__064',
        'fov_hist__106',
        'health',
        'food',
        'temperature',
        'food_supply',
        'fatigue',
        'hack_situation',
        'hack_decay_factor',
        'current_location_index'
    ]

    supported_datatargets = [
        'orientation',
        'take_exit_one',
        'take_exit_two',
        'take_exit_three',
        'fov_x',
        'fov_y',
        'pitch',
        'yaw',
        'eat',
        'sleep'
    ]

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

    loco_nodes = {}

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

    loco_nodes_indexes = [None, 'home', 'underground garden', 'village', 'cathedral', 'summit', 'cloud', 'bungalow', 'farm', 'forest', 'desert outpost', 'swamp']

    loco_nodes[home_uid] = loco_node_template.copy()
    loco_nodes[home_uid]['name'] = "home"
    loco_nodes[home_uid]['uid'] = home_uid
    loco_nodes[home_uid]['x'] = -105
    loco_nodes[home_uid]['y'] = 63
    loco_nodes[home_uid]['z'] = 59
    loco_nodes[home_uid]['exit_one_uid'] = cloud_uid
    loco_nodes[home_uid]['exit_two_uid'] = cathedral_uid
    loco_nodes[home_uid]['exit_three_uid'] = village_uid

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

    tp_tolerance = 5

    action_timeout = 10

    actions = ['eat', 'sleep', 'take_exit_one', 'take_exit_two', 'take_exit_three']

    logger = None

    # specs for vision /fovea
    # focal length larger 0 means zoom in, smaller 0 means zoom out
    # ( small values of focal length distort the image if things are close )
    # image proportions define the part of the world that can be viewed
    # patch dimensions define the size of the sampled patch that's stored to file
    focal_length = 0.5    # distance of image plane from projective point /fovea
    max_dist = 64         # maximum distance for raytracing
    resolution_w = 1.0    # number of rays per tick in viewport /camera coordinate system
    resolution_h = 1.0    # number of rays per tick in viewport /camera coordinate system
    im_width = 128        # width of projection /image plane in the world
    im_height = 64        # height of projection /image plane in the world
    cam_width = 1.        # width of normalized device /camera /viewport
    cam_height = 1.       # height of normalized device /camera /viewport
    # Note: adapt patch width to be smaller than or equal to resolution x image dimension
    patch_width = 32      # width of a fovea patch  # 128 || 32
    patch_height = 32     # height of a patch  # 64 || 32
    num_fov = 6           # the root number of fov__ sensors, ie. there are num_fov x num_fov fov__ sensors
    num_steps_to_keep_vision_stable = 3

    # Note: actors fov_x, fov_y and the saccader's gates fov_x, fov_y ought to be parametrized [0.,2.] w/ threshold 1.
    # -- 0. means inactivity, values between 1. and 2. are the scaled down movement in x/y direction on the image plane

    def __init__(self, world, uid=None, **data):
        super(MinecraftGraphLocomotion, self).__init__(world, uid, **data)

        self.datatarget_feedback = {
            'orientation': 0,
            'take_exit_one': 0,
            'take_exit_two': 0,
            'take_exit_three': 0,
            'fov_x': 0,
            'fov_y': 0,
            'eat': 0,
            'sleep': 0
        }

        # prevent instabilities in datatargets: treat a continuous ( /unintermittent ) signal as a single trigger
        self.datatarget_history = {
            'orientation': 0,
            'take_exit_one': 0,
            'take_exit_two': 0,
            'take_exit_three': 0,
            'fov_x': 0,
            'fov_y': 0,
            'eat': 0,
            'sleep': 0
        }

        self.datasources['health'] = 1
        self.datasources['food'] = 1
        self.datasources['temperature'] = 0.5
        self.datasources['hack_situation'] = -1
        self.datasources['hack_decay_factor'] = 1

        # a collection of conditions to check on every update(..), eg., for action feedback
        self.waiting_list = []

        self.target_loco_node_uid = None

        self.current_loco_node = None

        self.last_slept = 0
        self.sleeping = False

        self.spockplugin = self.world.spockplugin
        self.waiting_for_spock = True
        self.logger = logging.getLogger("world")
        self.spockplugin.event.reg_event_handler('PLAY<Spawn Position', self.set_datasources)
        self.spockplugin.event.reg_event_handler('PLAY<Player Position and Look', self.server_set_position)
        self.spockplugin.event.reg_event_handler('PLAY<Chat Message', self.server_chat_message)

        # add datasources for fovea
        for i in range(self.num_fov):
            for j in range(self.num_fov):
                name = "fov__%02d_%02d" % (i, j)
                self.datasources[name] = 0.
                self.supported_datasources.append(name)

        self.simulated_vision = False
        if 'simulate_vision' in cfg['minecraft']:
            self.simulated_vision = True
            self.simulated_vision_datafile = cfg['minecraft']['simulate_vision']
            self.logger.info("Setting up minecraft_graph_locomotor to simulate vision from data file %s", self.simulated_vision_datafile)

            import os
            import csv
            self.simulated_vision_data = None
            self.simulated_vision_datareader = csv.reader(open(self.simulated_vision_datafile))
            if os.path.getsize(self.simulated_vision_datafile) < (500 * 1024 * 1024):
                self.simulated_vision_data = [[float(datapoint) for datapoint in sample] for sample in self.simulated_vision_datareader]
                self.simulated_data_entry_index = 0
                self.simulated_data_entry_max = len(self.simulated_vision_data) - 1

        if 'record_vision' in cfg['minecraft']:
            self.record_file = open(cfg['minecraft']['record_vision'], 'a')

    def server_chat_message(self, event, data):
        if data.data and 'json_data' in data.data:
            if data.data['json_data'].get('translate') == 'tile.bed.noSleep':
                self.datatarget_feedback['sleep'] = -1
                self.sleeping = False

    def server_set_position(self, event, data):
        """ Interprete this as waking up, if we're sleeping, and it's morning"""
        if (abs(round(data.data['x']) + 102.5)) < 1 and (abs(round(data.data['z']) - 59.5) < 1):
            # server set our position to bed
            self.sleeping = True
        elif self.sleeping:
            self.sleeping = False
            self.last_slept = self.spockplugin.world.age

    def set_datasources(self, event, data):
        self.datasources['health'] = self.spockplugin.clientinfo.health['health'] / 20
        self.datasources['food'] = self.spockplugin.clientinfo.health['food'] / 20

    def update_data_sources_and_targets(self):
        """called on every world simulation step to advance the life of the agent"""

        self.datasources['hack_decay_factor'] = 0 if self.sleeping else 1

        # first thing when spock initialization is done, determine current loco node
        if self.waiting_for_spock:
            # by substitution: spock init is considered done, when its client has a position unlike
            # {'on_ground': False, 'pitch': 0, 'x': 0, 'y': 0, 'yaw': 0, 'stance': 0, 'z': 0}:
            if not self.simulated_vision:
                if self.spockplugin.clientinfo.position['y'] != 0. \
                        and self.spockplugin.clientinfo.position['x'] != 0:
                    self.waiting_for_spock = False
                    x = int(self.spockplugin.clientinfo.position['x'])
                    y = int(self.spockplugin.clientinfo.position['y'])
                    z = int(self.spockplugin.clientinfo.position['z'])
                    for k, v in self.loco_nodes.items():
                        if abs(x - v['x']) <= self.tp_tolerance and abs(y - v['y']) <= self.tp_tolerance and abs(z - v['z']) <= self.tp_tolerance:
                            self.current_loco_node = self.loco_nodes[k]

                    self.last_slept = self.spockplugin.world.age
                    if self.current_loco_node is None:
                        # bot is outside our graph, teleport to a random graph location to get started.
                        target = random.choice(list(self.loco_nodes.keys()))
                        self.locomote(target)
                    # self.locomote(self.village_uid)
            else:
                self.waiting_for_spock = False
        else:

            # reset self.datatarget_feedback
            for k in self.datatarget_feedback.keys():
                # reset actions only if not requested anymore
                if k in self.actions:
                    if self.datatargets[k] == 0:
                        self.datatarget_feedback[k] = 0.
                else:
                    self.datatarget_feedback[k] = 0.

            if not self.simulated_vision:

                if not self.spockplugin.is_connected():
                    return

                # reset self.datasources
                # for k in self.datasources.keys():
                #     if k != 'hack_situation' and k != 'temperature':
                #         self.datasources[k] = 0.

                self.datasources['current_location_index'] = self.loco_nodes_indexes.index(self.current_loco_node['name'])

                # change pitch and yaw every x world steps to increase sensory variation
                # < ensures some stability to enable learning in the autoencoder
                if self.world.current_step % self.num_steps_to_keep_vision_stable == 0:
                    # for patches pitch = 10 and yaw = random.randint(-10,10) were used
                    # for visual field pitch = randint(0, 30) and yaw = randint(1, 360) were used
                    self.spockplugin.clientinfo.position['pitch'] = 10
                    self.spockplugin.clientinfo.position['yaw'] = random.randint(-10, 10)
                    self.datatargets['pitch'] = self.spockplugin.clientinfo.position['pitch']
                    self.datatargets['yaw'] = self.spockplugin.clientinfo.position['yaw']
                    # Note: datatargets carry spikes not continuous signals, ie. pitch & yaw will be 0 in the next step
                    self.datatarget_feedback['pitch'] = 1.0
                    self.datatarget_feedback['yaw'] = 1.0

                #
                orientation = self.datatargets['orientation']  # x_axis + 360 / orientation  degrees
                self.datatarget_feedback['orientation'] = 1.0
                # self.datatargets['orientation'] = 0

                # sample all the time
                # update fovea sensors, get sensory input, provide action feedback
                # make sure fovea datasources don't go below 0.
                self.datasources['fov_x'] = self.datatargets['fov_x'] - 1. if self.datatargets['fov_x'] > 0. else 0.
                self.datasources['fov_y'] = self.datatargets['fov_y'] - 1. if self.datatargets['fov_y'] > 0. else 0.
                loco_label = self.current_loco_node['name']  # because python uses call-by-object
                self.get_visual_input(self.datasources['fov_x'], self.datasources['fov_y'], loco_label)

                # Note: saccading can't fail because fov_x, fov_y are internal actors, hence we return immediate feedback
                if self.datatargets['fov_x'] > 0.0:
                    self.datatarget_feedback['fov_x'] = 1.0
                if self.datatargets['fov_y'] > 0.0:
                    self.datatarget_feedback['fov_y'] = 1.0

                # health and food are in [0;20]
                self.datasources['health'] = self.spockplugin.clientinfo.health['health'] / 20
                self.datasources['food'] = self.spockplugin.clientinfo.health['food'] / 20
                if self.spockplugin.get_temperature() is not None:
                    self.datasources['temperature'] = self.spockplugin.get_temperature()
                self.datasources['food_supply'] = self.spockplugin.count_inventory_item(297)  # count bread

                # compute fatigue: 0.2 per half a day:
                # timeofday = self.spockplugin.world.time_of_day % 24000
                no_sleep = ((self.spockplugin.world.age - self.last_slept) // 3000) / 2
                fatigue = no_sleep * 0.2
                if self.sleeping:
                    fatigue = 0
                self.datasources['fatigue'] = fatigue

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

                if self.datatargets['take_exit_three'] >= 1 and not self.datatarget_history['take_exit_three'] >=1:
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

                if self.datatargets['sleep'] >= 1 and not self.datatarget_history['sleep'] >= 1:
                    if self.check_movement_feedback(self.home_uid) and self.spockplugin.world.time_of_day % 24000 > 12500:
                        # we're home and it's night, so we can sleep now:
                        self.register_action('sleep', self.sleep, self.check_waking_up)
                    else:
                        self.datatarget_feedback['sleep'] = -1.

                # update datatarget history
                for k in self.datatarget_history.keys():
                    self.datatarget_history[k] = self.datatargets[k]

            else:
                self.simulate_visual_input()

    def locomote(self, target_loco_node_uid):
        new_loco_node = self.loco_nodes[target_loco_node_uid]

        self.logger.debug('locomoting to  %s' % new_loco_node['name'])

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
                    if self.datatargets[item['datatarget']] != 0:
                        self.datatarget_feedback[item['datatarget']] = 1.
                else:
                    new_waiting_list.append(item)

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
            self.datasources['hack_situation'] = self.loco_nodes_indexes.index(self.loco_nodes[target_loco_node]['name'])
            return True
        return False

    def check_waking_up(self):
        """ Checks whether we're done sleeping.
        Sets the datatarget_feedback to 1 and returns True if so, False otherwise"""
        if not self.sleeping:
            self.datatarget_feedback['sleep'] = 1
            return True
        return False

    def sleep(self):
        """ Attempts to use the bed located at -103/63/59"""
        logging.getLogger('world').debug('going to sleep')
        data = {
            'location': {
                'x': -103,
                'y': 63,
                'z': 59
            },
            'direction': 1,
            'held_item': {
                'id': 297,
                'amount': 0,
                'damage': 0
            },
            'cur_pos_x': -103,
            'cur_pos_y': 63,
            'cur_pos_z': 59
        }
        self.spockplugin.net.push(Packet(ident='PLAY>Player Block Placement', data=data))

    def get_visual_input(self, fov_x, fov_y, label):
        """
        Spans an image plane.

        Note that the image plane is walked left to right, top to bottom ( before rotation )!
        This means that fov__00_00 gets the top left pixel, fov__15_15 gets the bottom right pixel.
        """
        # set agent position
        pos_x = self.spockplugin.clientinfo.position['x']
        pos_y = self.spockplugin.clientinfo.position['y'] + 0.620  # add some stance to y pos ( which is ground + 1 )
        pos_z = self.spockplugin.clientinfo.position['z']

        # set yaw and pitch ( in degrees )
        yaw = self.spockplugin.clientinfo.position['yaw']
        # consider setting yaw to a random value between 0 and 359
        pitch = self.spockplugin.clientinfo.position['pitch']

        # compute ticks per dimension
        tick_w = self.cam_width / self.im_width / self.resolution_w
        tick_h = self.cam_height / self.im_height / self.resolution_h

        # span image plane
        # the horizontal plane is split half-half, the vertical plane is shifted upwards
        h_line = [i for i in self.frange(pos_x - 0.5 * self.cam_width, pos_x + 0.5 * self.cam_width, tick_w)]
        v_line = [i for i in self.frange(pos_y - 0.05 * self.cam_height, pos_y + 0.95 * self.cam_height, tick_h)]

        # scale up fov_x, fov_y
        fov_x = round(fov_x * (self.im_width * self.resolution_w - self.patch_width))
        fov_y = round(fov_y * (self.im_height * self.resolution_h - self.patch_height))

        x0, y0, z0 = pos_x, pos_y, pos_z  # agent's position aka projective point
        zi = z0 + self.focal_length

        v_line.reverse()

        # compute block type values for the whole patch /fovea
        patch = []
        for i in range(self.patch_height):
            for j in range(self.patch_width):
                try:
                    block_type, distance = self.project(h_line[fov_x + j], v_line[fov_y + i], zi, x0, y0, z0, yaw, pitch)
                except IndexError:
                    block_type, distance = -1, -1
                    self.logger.warning("IndexError at (%d,%d)" % (fov_x + j, fov_y + i))
                patch.append(block_type)

        # write block type histogram values to self.datasources['fov_hist__*']
        # for every block type seen in patch, if there's a datasource for it, fill it with its normalized frequency
        normalizer = self.patch_width * self.patch_height
        # reset fov_hist sensors, then fill them with new values
        for k in self.datasources.keys():
            if k.startswith('fov_hist__'):
                self.datasources[k] = 0.
        for bt in set(patch):
            name = "fov_hist__%03d" % bt
            if name in self.datasources:
                self.datasources[name] = patch.count(bt) / normalizer

        # COMPUTE VALUES FOR fov__%02d_%02d SENSORS
        # if all values in the patch are the same, write zeros
        if patch[1:] == patch[:-1]:

            zero_patch = True
            patch_resc = [0.0] * self.patch_width * self.patch_height

        else:

            zero_patch = False
            # convert block types into binary values: map air and emptiness to black (0), everything else to white (1)
            patch_ = [0.0 if v <= 0 else 1.0 for v in patch]

            # normalize block type values
            # subtract the sample mean from each of its pixels
            mean = float(sum(patch_)) / len(patch_)
            patch_avg = [x - mean for x in patch_]  # TODO: throws error in ipython - why not here !?

            # truncate to +/- 3 standard deviations and scale to -1 and +1

            var = [x ** 2.0 for x in patch_avg]
            std = (sum(var) / len(var)) ** 0.5  # ASSUMPTION: all values of x are equally likely
            pstd = 3.0 * std
            # if block types are all the same number, eg. -1, std will be 0, therefore
            if pstd == 0.0:
                patch_std = [0.0 for x in patch_avg]
            else:
                patch_std = [max(min(x, pstd), -pstd) / pstd for x in patch_avg]

            # scale from [-1,+1] to [0.1,0.9] and write values to sensors
            patch_resc = [(1.0 + x) * 0.4 + 0.1 for x in patch_std]

        self.write_visual_input_to_datasources(patch_resc, self.patch_width, self.patch_height)

        if 'record_vision' in cfg['minecraft']:
            # do *not* record homogeneous and replayed patches
            if not zero_patch and not self.simulated_vision:
                if label == self.current_loco_node['name']:
                    data = "{0}".format(",".join(str(b) for b in patch))
                    self.record_file.write("%s,%s,%d,%d,%d,%d\n" % (data, label, pitch, yaw, fov_x, fov_y))
                else:
                    self.logger.warn('potentially corrupt data were ignored')

    def simulate_visual_input(self):
        """
        Every <self.num_steps_to_keep_vision_stable> steps read the next line
        from the vision file and fill its values into fov__*_* datasources.
        """
        if self.world.current_step % self.num_steps_to_keep_vision_stable == 0:
            line = None
            if self.simulated_vision_data is None:
                line = next(self.simulated_vision_datareader, None)
                if line is None:
                    self.logger.info("Simulating vision from data file, starting over...")
                    import csv
                    self.simulated_vision_datareader = csv.reader(open(self.simulated_vision_datafile))
                    line = next(self.simulated_vision_datareader)
                line = [float(entry) for entry in line]
            else:
                self.simulated_data_entry_index += 1
                if self.simulated_data_entry_index > self.simulated_data_entry_max:
                    self.logger.info("Simulating vision from memory, starting over, %s entries.", self.simulated_data_entry_max + 1)
                    self.simulated_data_entry_index = 0
                line = self.simulated_vision_data[self.simulated_data_entry_index]
            self.write_visual_input_to_datasources(line, self.num_fov, self.num_fov)

    def write_visual_input_to_datasources(self, patch, patch_width, patch_height):
        """
        Write a patch of the size self.num_fov times self.num_fov to self.datasourcesp['fov__*_*'].
        If num_fov is less than patch height and width, chose the horizontally centered , vertically 3/4 lower patch.
        """
        left_margin = max(0, (int(patch_width - self.num_fov) // 2) - 1)
        top_margin = max(0, (int(patch_height - self.num_fov) // 4 * 3) - 1)
        for i in range(self.num_fov):
            for j in range(self.num_fov):
                name = 'fov__%02d_%02d' % (i, j)
                self.datasources[name] = patch[(patch_height * (i + top_margin)) + j + left_margin]

    def project(self, xi, yi, zi, x0, y0, z0, yaw, pitch):
        """
        Given a point on the projection plane and the agent's position, cast a
        ray to find the nearest block type that isn't air and its distance from
        the projective plane.
        """
        distance = 0    # just a counter
        block_type = -1  # consider mapping nothingness to air, ie. -1 to 0

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

        while block_type <= 0:  # which is air and nothingness

            # check block type of next distance point along ray
            # aka add normalized difference vector to image point
            # TODO: consider a more efficient way to move on the ray, eg. a log scale
            xb += norm[0]
            yb += norm[1]
            zb += norm[2]

            block_type = self.spockplugin.get_block_type(xb, yb, zb)

            distance += 1
            if distance >= self.max_dist:
                break

        return block_type, distance

    def rotate_around_x_axis(self, pos, angle):
        """ Rotate a 3D point around the x-axis given a specific angle. """

        # convert angle in degrees to radians
        theta = radians(angle)

        # rotate vector
        xx, y, z = pos
        yy = y * cos(theta) - z * sin(theta)
        zz = y * sin(theta) + z * cos(theta)

        return (xx, yy, zz)

    def rotate_around_y_axis(self, pos, angle):
        """ Rotate a 3D point around the y-axis given a specific angle. """

        # convert angle in degrees to radians
        theta = radians(angle)

        # rotate vector
        x, yy, z = pos
        xx = x * cos(theta) + z * sin(theta)
        zz = - x * sin(theta) + z * cos(theta)

        return (xx, yy, zz)

    def rotate_around_z_axis(self, pos, angle):
        """ Rotate a 3D point around the z-axis given a specific angle. """

        # convert angle in degrees to radians
        theta = radians(angle)

        # rotate vector
        x, y, zz = pos
        xx = x * cos(theta) - y * sin(theta)
        yy = x * sin(theta) + y * cos(theta)

        return (xx, yy, zz)

    def frange(self, start, end, step):
        """
        Range for floats.
        """
        while start < end:
            yield start
            start += step
