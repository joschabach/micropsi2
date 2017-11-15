# -*- coding: utf-8 -*-

"""
Monitor definition
"""

import math
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
    def __init__(self, nodenet, name='', uid=None, color=None, values={}):
        self.uid = uid or micropsi_core.tools.generate_uid()
        self.nodenet = nodenet
        self.values = {}
        for key in sorted(values.keys()):
            self.values[int(key)] = values[key]
        self.name = name or "some monitor"
        self.color = color or "#%02d%02d%02d" % (random.randint(0,99), random.randint(0,99), random.randint(0,99))

    def get_data(self, with_values=True):
        data = {
            "uid": self.uid,
            "name": self.name,
            "color": self.color,
            "classname": self.__class__.__name__
        }
        if with_values:
            data["values"] = self.values
        return data

    @abstractmethod
    def getvalue(self):
        pass  # pragma: no cover

    def step(self, step):
        self.values[step] = self.getvalue()

    def clear(self):
        self.values = {}


class GroupMonitor(Monitor):

    def __init__(self, nodenet, nodespace, name, name_prefix='', node_uids=[], gate='gen', uid=None, color=None, values={}, **_):
        super().__init__(nodenet, name=name, uid=uid, color=color, values=values)
        self.nodespace = nodespace
        self.node_uids = node_uids
        self.name_prefix = name_prefix
        self.gate = gate
        if len(node_uids) == 0:
            self.nodenet.group_nodes_by_names(nodespace, name_prefix, gatetype=gate, group_name=name, sortby='name')
            self.node_uids = self.nodenet.get_node_uids(nodespace, name)
        else:
            self.nodenet.group_nodes_by_ids(nodespace, node_uids, name, gatetype=gate)

    def get_data(self, with_values=True):
        data = super().get_data(with_values=with_values)
        data.update({
            "nodespace": self.nodespace,
            "node_uids": self.node_uids,
            "gate": self.gate
        })
        return data

    def getvalue(self):
        data = self.nodenet.get_activations(self.nodespace, self.name)
        if type(data) == list:
            return data
        else:
            return data.tolist()


class NodeMonitor(Monitor):

    def __init__(self, nodenet, node_uid, type, target, name=None, uid=None, color=None, values={}, **_):
        name = name or "%s %s @ Node %s" % (type, target, nodenet.get_node(node_uid).name or nodenet.get_node(node_uid).uid)
        super(NodeMonitor, self).__init__(nodenet, name, uid, color=color, values=values)
        self.node_uid = node_uid
        self.type = type
        self.target = target or 'gen'

    def get_data(self, with_values=True):
        data = super().get_data(with_values=with_values)
        data.update({
            "node_uid": self.node_uid,
            "type": self.type,
            "target": self.target
        })
        return data

    def getvalue(self):
        value = None
        if self.nodenet.is_node(self.node_uid):
            if self.type == 'gate' and self.target in self.nodenet.get_node(self.node_uid).get_gate_types():
                value = self.nodenet.get_node(self.node_uid).get_gate(self.target).activation
            if self.type == 'slot' and self.target in self.nodenet.get_node(self.node_uid).get_slot_types():
                value = self.nodenet.get_node(self.node_uid).get_slot(self.target).activation

        if value is not None and not math.isnan(value):
            return value
        else:
            return None


class LinkMonitor(Monitor):

    def __init__(self, nodenet, source_node_uid, gate_type, target_node_uid, slot_type, name=None, uid=None, color=None, values={}, **_):
        api = nodenet.netapi
        name = name or "%s:%s -> %s:%s" % (api.get_node(source_node_uid).name, gate_type, api.get_node(source_node_uid).name, slot_type)
        super(LinkMonitor, self).__init__(nodenet, name, uid, color=color, values=values)
        self.source_node_uid = source_node_uid
        self.target_node_uid = target_node_uid
        self.gate_type = gate_type
        self.slot_type = slot_type

    def get_data(self, with_values=True):
        data = super().get_data(with_values=with_values)
        data.update({
            "source_node_uid": self.source_node_uid,
            "target_node_uid": self.target_node_uid,
            "gate_type": self.gate_type,
            "slot_type": self.slot_type
        })
        return data

    def find_link(self):
        if self.nodenet.is_node(self.source_node_uid) and self.nodenet.is_node(self.target_node_uid):
            gate = self.nodenet.netapi.get_node(self.source_node_uid).get_gate(self.gate_type)
            if gate:
                links = gate.get_links()
                for l in links:
                    if l.target_node.uid == self.target_node_uid and l.target_slot.type == self.slot_type:
                        return l
        return None

    def getvalue(self):
        link = self.find_link()
        if link:
            return self.find_link().weight
        else:
            return None


class ModulatorMonitor(Monitor):

    def __init__(self, nodenet, modulator, name=None, uid=None, color=None, values={}, **_):
        name = name or "Modulator: %s" % modulator
        super(ModulatorMonitor, self).__init__(nodenet, name, uid, color=color, values=values)
        self.modulator = modulator
        self.nodenet = nodenet

    def get_data(self, with_values=True):
        data = super().get_data(with_values=with_values)
        data.update({
            "modulator": self.modulator
        })
        return data

    def getvalue(self):
        return self.nodenet.get_modulator(self.modulator)


class CustomMonitor(Monitor):

    def __init__(self, nodenet, function, name=None, uid=None, color=None, values={}, **_):
        super(CustomMonitor, self).__init__(nodenet, name, uid, color=color, values=values)
        self.function = function
        self.compiled_function = micropsi_core.tools.create_function(self.function, parameters="netapi")

    def get_data(self, with_values=True):
        data = super().get_data(with_values=with_values)
        data.update({
            "function": self.function,
        })
        return data

    def getvalue(self):
        return self.compiled_function(self.nodenet.netapi)


class AdhocMonitor(Monitor):

    def __init__(self, nodenet, function, name=None, uid=None, color=None, values={}, parameters={}, **_):
        super().__init__(nodenet, name, uid, color=color, values=values)
        self.function = function
        self.parameters = parameters

    def get_data(self, with_values=True):
        data = super().get_data(with_values=with_values)
        data.update({
            "function": "%s.%s" % (self.function.__module__, self.function.__name__)
        })
        return data

    def getvalue(self):
        return self.function(**self.parameters)
