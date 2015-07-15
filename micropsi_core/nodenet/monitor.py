# -*- coding: utf-8 -*-

"""
Monitor definition
"""

import random
import micropsi_core.tools
from abc import ABCMeta, abstractmethod


__author__ = 'joscha'
__date__ = '09.05.12'


class Monitor(metaclass=ABCMeta):
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
            "color": self.color,
            "classname": self.__class__.__name__
        }
        return data

    def __init__(self, nodenet, name='', uid=None, color=None):
        self.uid = uid or micropsi_core.tools.generate_uid()
        self.nodenet = nodenet
        self.values = {}
        self.name = name or "some monitor"
        self.color = color or "#%02d%02d%02d" % (random.randint(0,99), random.randint(0,99), random.randint(0,99))
        nodenet._register_monitor(self)

    @abstractmethod
    def step(self, step):
        pass  # pragma: no cover

    def clear(self):
        self.values = {}


class NodeMonitor(Monitor):

    @property
    def data(self):
        data = super(NodeMonitor, self).data
        data.update({
            "node_uid": self.node_uid,
            "type": self.type,
            "target": self.target,
            "sheaf": self.sheaf,
        })
        return data

    def __init__(self, nodenet, node_uid, type, target, sheaf=None, name=None, uid=None, color=None, **_):
        name = name or "%s %s @ Node %s" % (type, target, nodenet.netapi.get_node(node_uid).name or nodenet.netapi.get_node(node_uid).uid)
        super(NodeMonitor, self).__init__(nodenet, name, uid, color=color)
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
        else:
            self.values[step] = None


class LinkMonitor(Monitor):

    @property
    def data(self):
        data = super(LinkMonitor, self).data
        data.update({
            "source_node_uid": self.source_node_uid,
            "target_node_uid": self.target_node_uid,
            "gate_type": self.gate_type,
            "slot_type": self.slot_type,
            "property": self.property,
        })
        return data

    def __init__(self, nodenet, source_node_uid, gate_type, target_node_uid, slot_type, property=None, name=None, uid=None, color=None, **_):
        api = nodenet.netapi
        name = name or "%s:%s -> %s:%s" % (api.get_node(source_node_uid).name, gate_type, api.get_node(source_node_uid).name, slot_type)
        super(LinkMonitor, self).__init__(nodenet, name, uid, color=color)
        self.source_node_uid = source_node_uid
        self.target_node_uid = target_node_uid
        self.gate_type = gate_type
        self.slot_type = slot_type
        self.property = property or 'weight'

    def find_link(self):
        if self.nodenet.is_node(self.source_node_uid) and self.nodenet.is_node(self.target_node_uid):
            gate = self.nodenet.netapi.get_node(self.source_node_uid).get_gate(self.gate_type)
            if gate:
                links = gate.get_links()
                for l in links:
                    if l.target_node.uid == self.target_node_uid and l.target_slot.type == self.slot_type:
                        return l
        return None

    def step(self, step):
        link = self.find_link()
        if link:
            self.values[step] = getattr(self.find_link(), self.property)
        else:
            self.values[step] = None


class ModulatorMonitor(Monitor):

    @property
    def data(self):
        data = super(ModulatorMonitor, self).data
        data.update({
            "modulator": self.modulator
        })
        return data

    def __init__(self, nodenet, modulator, name=None, uid=None, color=None, **_):
        name = name or "Modulator: %s" % modulator
        super(ModulatorMonitor, self).__init__(nodenet, name, uid, color=color)
        self.modulator = modulator
        self.nodenet = nodenet

    def step(self, step):
        self.values[step] = self.nodenet.get_modulator(self.modulator)


class CustomMonitor(Monitor):

    @property
    def data(self):
        data = super(CustomMonitor, self).data
        data.update({
            "function": self.function,
        })
        return data

    def __init__(self, nodenet, function, name=None, uid=None, color=None, **_):
        super(CustomMonitor, self).__init__(nodenet, name, uid, color=color)
        self.function = function
        self.compiled_function = micropsi_core.tools.create_function(self.function, parameters="netapi")

    def step(self, step):
        self.values[step] = self.compiled_function(self.nodenet.netapi)
