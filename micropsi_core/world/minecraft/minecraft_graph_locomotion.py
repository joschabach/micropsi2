from micropsi_core.world.worldadapter import WorldAdapter
from micropsi_core import tools
import random
import logging
import time
from functools import partial
from spock.mcp.mcpacket import Packet


class MinecraftGraphLocomotion(WorldAdapter):

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

    def __init__(self, world, uid=None, **data):
        super().__init__(world, uid, **data)

        self.datasources = {
            'health': 1,
            'food': 1,
            'temperature': 0.5,
            'food_supply': 0,
            'fatigue': 0,
            'awake': 1,
            'current_location_index': 0
        }

        targets = ['take_exit_one', 'take_exit_two', 'take_exit_three', 'pitch', 'yaw', 'eat', 'sleep']
        self.datatarget_history = {}
        for t in targets:
            self.datatargets[t] = 0
            self.datatarget_feedback[t] = 0
            self.datatarget_history[t] = 0

        # a collection of conditions to check on every update(..), eg., for action feedback
        self.waiting_list = []

        self.target_loco_node_uid = None

        self.current_loco_node = None

        self.last_slept = 0
        self.sleeping = False

        self.spockplugin = self.world.spockplugin
        self.spockplugin.worldadapter = self
        self.waiting_for_spock = True
        self.logger = logging.getLogger("agent.%s" % self.uid)
        self.spockplugin.event.reg_event_handler('PLAY<Spawn Position', self.set_datasources)
        self.spockplugin.event.reg_event_handler('PLAY<Player Position and Look', self.server_set_position)
        self.spockplugin.event.reg_event_handler('PLAY<Chat Message', self.server_chat_message)

    def server_chat_message(self, event, data):
        if data.data and 'json_data' in data.data:
            if data.data['json_data'].get('translate') == 'tile.bed.noSleep':
                self.datatarget_feedback['sleep'] = -1
                self.sleeping = False

    def server_set_position(self, event, data):
        """ Interprete this as waking up, if we're sleeping, and it's morning"""
        if (abs(round(data.data['x']) + 102.5)) < 1 and (abs(round(data.data['z']) - 59.5) < 1):
            # server set our position to bed
            self.sleeping = self.spockplugin.world.age
        elif self.sleeping:
            self.logger.info('WAKE UP!')
            self.sleeping = False
            self.last_slept = self.spockplugin.world.age

    def set_datasources(self, event, data):
        self.datasources['health'] = self.spockplugin.clientinfo.health['health'] / 20
        self.datasources['food'] = self.spockplugin.clientinfo.health['food'] / 20

    def update_data_sources_and_targets(self):
        """called on every world calculation step to advance the life of the agent"""

        self.datasources['awake'] = 0 if self.sleeping else 1

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

                self.last_slept = self.spockplugin.world.age
                if self.current_loco_node is None:
                    # bot is outside our graph, teleport to a random graph location to get started.
                    target = random.choice(list(self.loco_nodes.keys()))
                    self.locomote(target)
                # self.locomote(self.forest_uid)

        else:

            # reset self.datatarget_feedback
            for k in self.datatarget_feedback.keys():
                # reset actions only if not requested anymore
                if k in self.actions:
                    if self.datatargets[k] == 0:
                        self.datatarget_feedback[k] = 0.
                else:
                    self.datatarget_feedback[k] = 0.

            if not self.spockplugin.is_connected():
                return

            self.datasources['current_location_index'] = self.loco_nodes_indexes.index(self.current_loco_node['name'])

            # health and food are in [0;20]
            self.datasources['health'] = self.spockplugin.clientinfo.health['health'] / 20
            self.datasources['food'] = self.spockplugin.clientinfo.health['food'] / 20
            if self.spockplugin.get_temperature() is not None:
                self.datasources['temperature'] = self.spockplugin.get_temperature()
            self.datasources['food_supply'] = self.spockplugin.count_inventory_item(297)  # count bread

            # compute fatigue: 0.1 per half a day:
            # timeofday = self.spockplugin.world.time_of_day % 24000
            if self.sleeping:
                no_sleep = ((self.sleeping - self.last_slept) // 3000) / 2
            else:
                no_sleep = ((self.spockplugin.world.age - self.last_slept) // 3000) / 2
            fatigue = no_sleep * 0.05
            self.datasources['fatigue'] = round(fatigue, 2)

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
        for idx, item in enumerate(self.spockplugin.quickslots):
            if item.get('id', 0) == 297:
                self.spockplugin.change_held_item(idx)
                return True
        self.logger.debug('Agent has no bread!')
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

    def check_waking_up(self):
        """ Checks whether we're done sleeping.
        Sets the datatarget_feedback to 1 and returns True if so, False otherwise"""
        if not self.sleeping:
            self.datatarget_feedback['sleep'] = 1
            return True
        return False

    def sleep(self):
        """ Attempts to use the bed located at -103/63/59"""
        self.logger.debug('going to sleep')
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
