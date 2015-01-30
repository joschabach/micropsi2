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
        nodenet: the parent nodenet
        uid: the uid of this monitor
        name: a name for this monitor
        values: the observed values

    """
    @property
    def data(self):
        data = {
            "uid": self.uid,
            "values": self.values,
            "name": self.name,
            "classname": "Monitor"
        }
        return data

    def __init__(self, nodenet, name='', uid=None, **_):
        self.uid = uid or micropsi_core.tools.generate_uid()
        self.nodenet = nodenet
        self.values = {}
        self.name = name or "some monitor"
        nodenet._register_monitor(self)

    def step(self, step):
        pass

    def clear(self):
        self.values = {}


class NodeMonitor(Monitor):

    @property
    def data(self):
        data = {
            "uid": self.uid,
            "values": self.values,
            "node_uid": self.node_uid,
            "name": self.name,
            "type": self.type,
            "target": self.target,
            "sheaf": self.sheaf,
            "classname": "NodeMonitor"
        }
        return data

    def __init__(self, nodenet, node_uid, type, target, sheaf=None, name=None, uid=None):
        super(NodeMonitor, self).__init__(nodenet, name, uid)
        self.node_uid = node_uid
        self.type = type
        self.target = target or 'gen'
        self.sheaf = sheaf or 'default'

    def step(self, step):
        if self.nodenet.is_node(self.node_uid):
            if self.type == 'gate' and self.target in self.nodenet.get_node(self.node_uid).get_gate_types():
                self.values[step] = self.nodenet.get_node(self.node_uid).get_gate(self.target).activations[self.sheaf]
            if self.type == 'slot' and self.target in self.nodenet.get_node(self.node_uid).get_slot_types():
                self.values[step] = self.nodenet.get_node(self.node_uid).get_slot(self.target).activations[self.sheaf]


class LinkMonitor(Monitor):

    @property
    def data(self):
        data = {
            "uid": self.uid,
            "values": self.values,
            "source_node_uid": self.source_node_uid,
            "target_node_uid": self.target_node_uid,
            "gate_type": self.gate_type,
            "slot_type": self.slot_type,
            "property": self.property,
            "classname": "LinkMonitor"
        }
        return data

    def __init__(self, nodenet, source_node_uid, gate_type, target_node_uid, slot_type, property=None, name=None, uid=None):
        super(LinkMonitor, self).__init__(nodenet, name, uid)
        self.source_node_uid = source_node_uid
        self.target_node_uid = target_node_uid
        self.gate_type = gate_type
        self.slot_type = slot_type
        self.property = property or 'weight'
        self.link = self.findLink()

    def findLink(self):
        links = self.nodenet.netapi.get_node(self.source_node_uid).get_gate(self.gate_type).get_links()
        for l in links:
            if l.target_node.uid == self.target_node_uid and l.target_slot.type == self.slot_type:
                return l
        return None

    def step(self, step):
        self.values[step] = getattr(self.link, self.property)


class CustomMonitor(Monitor):

    @property
    def data(self):
        data = {
            "uid": self.uid,
            "values": self.values,
            "name": self.name,
            "function": self.function,
            "classname": "CustomMonitor"
        }
        return data

    def __init__(self, nodenet, function, name=None, uid=None):
        super(CustomMonitor, self).__init__(nodenet, name, uid)
        self.function = function
        self.compiled_function = micropsi_core.tools.create_function(self.function, parameters="netapi")

    def step(self, step):
        self.values[step] = self.compiled_function(self.nodenet.netapi)
