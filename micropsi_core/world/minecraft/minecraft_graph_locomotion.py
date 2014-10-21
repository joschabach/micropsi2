from micropsi_core.world.worldadapter import WorldAdapter
from micropsi_core import tools


class MinecraftGraphLocomotion(WorldAdapter):

    datasources = {}
    datatargets = {'orientation': 0, 'take_exit_one': 0, 'take_exit_two': 0, 'take_exit_three':0}
    datatarget_feedback = {'orientation': 0, 'take_exit_one': 0, 'take_exit_two': 0, 'take_exit_three':0}

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

    uid = tools.generate_uid()
    loco_nodes[uid] = loco_node_template.copy()
    loco_nodes[uid]['uid'] = uid
    loco_nodes[uid]['name'] = "home"
    loco_nodes[uid]['x'] = -105
    loco_nodes[uid]['y'] = 65
    loco_nodes[uid]['z'] = 59
    loco_nodes[uid]['exit_one_uid'] = uid

    current_loco_node = loco_nodes[uid]

    def __init__(self, world, uid=None, **data):
        super(MinecraftGraphLocomotion, self).__init__(world, uid, **data)
        self.spockplugin = self.world.spockplugin

    def update(self):
        """called on every world simulation step to advance the life of the agent"""

        self.datatarget_feedback['orientation'] = 0
        self.datatarget_feedback['take_exit_one'] = 0
        self.datatarget_feedback['take_exit_two'] = 0
        self.datatarget_feedback['take_exit_three'] = 0

        orientation = self.datatargets['orientation']  # x_axis + 360 / orientation  degrees
        self.datatarget_feedback['orientation'] = 1

        if self.datatargets['take_exit_one'] >= 1:
            if self.current_loco_node['exit_one_uid'] is not None:
                self.locomote(self.current_loco_node['exit_one_uid'])
                self.datatarget_feedback['take_exit_one'] = 1
            else:
                self.datatarget_feedback['take_exit_one'] = -1

        if self.datatargets['take_exit_two'] >= 1:
            if self.current_loco_node['exit_two_uid'] is not None:
                self.locomote(self.current_loco_node['exit_two_uid'])
                self.datatarget_feedback['take_exit_two'] = 1
            else:
                self.datatarget_feedback['take_exit_two'] = -1


        if self.datatargets['take_exit_three'] >= 1:
            if self.current_loco_node['exit_three_uid'] is not None:
                self.locomote(self.current_loco_node['exit_three_uid'])
                self.datatarget_feedback['take_exit_three'] = 1
            else:
                self.datatarget_feedback['take_exit_three'] = -1

        self.datatargets['orientation'] = 0
        self.datatargets['take_exit_one'] = 0
        self.datatargets['take_exit_two'] = 0
        self.datatargets['take_exit_three'] = 0


    def locomote(self, target_loco_node_uid):
        new_loco_node = self.loco_nodes[target_loco_node_uid]

        self.spockplugin.chat("/tppos {0} {1} {2}".format(
            new_loco_node['x'],
            new_loco_node['y'],
            new_loco_node['z']))

        self.current_loco_node = new_loco_node