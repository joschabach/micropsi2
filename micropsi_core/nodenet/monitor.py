# -*- coding: utf-8 -*-

"""
Monitor definition
"""

import micropsi_core.tools

__author__ = 'joscha'
__date__ = '09.05.12'


class Monitor(object):
    """A gate or slot monitor watching the activation of the given slot or gate over time

    Attributes:
        nodenet: the parent Nodenet
        node: the parent Node
        type: either "slot" or "gate"
        target: the name of the observerd Slot or Gate
    """

    def __init__(self, nodenet, node_uid, type, target, node_name='', uid=None, **_):
        if 'monitors' not in nodenet.state:
            nodenet.state['monitors'] = {}
        self.uid = uid or micropsi_core.tools.generate_uid()
        self.data = {'uid': self.uid}
        self.nodenet = nodenet
        nodenet.state['monitors'][self.uid] = self.data
        self.data['values'] = self.values = {}
        self.data['node_uid'] = self.node_uid = node_uid
        self.data['node_name'] = self.node_name = node_name
        self.data['type'] = self.type = type
        self.data['target'] = self.target = target

    def step(self, step):
        if self.node_uid in self.nodenet.nodes:
            if self.target in getattr(self.nodenet.nodes[self.node_uid], self.type + 's'):
                self.values[step] = getattr(self.nodenet.nodes[self.node_uid], self.type + 's')[self.target].sheaves['default']['activation']

    def clear(self):
        self.data['values'] = {}
