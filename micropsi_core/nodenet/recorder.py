# -*- coding: utf-8 -*-


"""
Recorder

Recorders need nummpy, record things like activation, linkweights, biases over time,
and persist to their own files. they can be imported and exported as numpy npz
"""

import os
try:
    import numpy as np
except ImportError:
    pass
from abc import ABCMeta, abstractmethod
from micropsi_core import tools


class Recorder(metaclass=ABCMeta):

    """A recorder will record values from section of the nodenet
    and offer import/export functionaliy
    Recorders need numpy."""

    initial_size = 10000

    def __init__(self, nodenet, name="", uid="", interval=1, first_step=0, current_index=-1):
        self._nodenet = nodenet
        self.name = name
        self.uid = uid or tools.generate_uid()
        self.interval = interval
        self.filename = os.path.join(nodenet.persistency_path, 'recorder_%s.npz' % self.uid)
        self.first_step = first_step
        self.current_index = current_index
        self.shapes = {}
        self.values = {}
        if os.path.isfile(self.filename):
            self.load()

    def get_data(self):
        data = {
            "uid": self.uid,
            "name": self.name,
            "interval": self.interval,
            "filename": self.filename,
            "current_index": self.current_index,
            "first_step": self.first_step,
            "classname": self.__class__.__name__
        }
        return data

    def step(self, step):
        if step % self.interval == 0:
            self.current_index += 1
            values = self.get_values()
            for key in values:
                if key not in self.values:
                    self.first_step = step
                    self.values[key] = np.zeros(shape=self.shapes[key], dtype=self._nodenet.numpyfloatX)
                    self.values[key][:] = np.NAN
                if step - self.first_step >= len(self.values[key]):
                    newshapes = list(self.shapes[key])
                    newshapes[0] += self.initial_size
                    self.shapes[key] = tuple(newshapes)
                    new_values = np.zeros(shape=self.shapes[key], dtype=self._nodenet.numpyfloatX)
                    new_values[0:len(self.values[key])] = self.values[key]
                    self.values[key] = new_values
                self.values[key][self.current_index] = values[key]

    @abstractmethod
    def get_values(self):
        pass  # pragma: no cover

    def export_data(self):
        data = {}
        for key in self.values:
            data["%s_%s" % (self.name, key)] = self.values[key]
            data['%s_meta' % self.name] = [self.first_step, self.interval]
        return data

    def save(self, filename=None):
        data = self.export_data()
        if data:
            np.savez(filename if filename is not None else self.filename, **data)

    def load(self, filename=None):
        data = np.load(filename if filename is not None else self.filename)
        for key in data:
            if key.endswith('_meta'):
                self.first_step = int(data[key][0])
                self.interval = int(data[key][1])
            else:
                self.values[key] = data[key]

    def clear(self):
        self.values = {}
        self.current_index = -1

    def import_file(self, filename):
        self.load(filename)


class GateActivationRecorder(Recorder):
    """ An activation recorder to record activaitons of nodegroups"""

    def __init__(self, nodenet, group_config={}, name="", uid="", interval=1, first_step=0, current_index=-1, **_):
        super().__init__(nodenet, name, uid, interval, first_step=first_step, current_index=current_index)
        if 'group_name' not in group_config:
            group_config['group_name'] = name
        self.group_config = group_config
        self.nodespace = group_config['nodespace_uid']
        self.group_name = group_config['group_name']

        if not group_config.get('node_uids', []):
            self._nodenet.group_nodes_by_names(**group_config)
        else:
            self._nodenet.group_nodes_by_ids(**group_config)

        uids = self._nodenet.get_node_uids(self.nodespace, self.group_name)
        self.shapes = {'activations': (self.initial_size, len(uids))}

    def get_data(self):
        data = super().get_data()
        data.update({
            "group_config": self.group_config,
        })
        return data

    def get_values(self):
        return {'activations': self._nodenet.get_activations(self.nodespace, self.group_name)}


class NodeActivationRecorder(Recorder):
    """ An activation recorder to record activaitons of nodegroups"""

    def __init__(self, nodenet, group_config={}, name="", uid="", interval=1, first_step=0, current_index=-1, **_):
        super().__init__(nodenet, name, uid, interval, first_step=first_step, current_index=current_index)

        self.group_config = group_config
        self.nodespace = group_config['nodespace_uid']
        self.base_group_name = group_config.pop('group_name', name)

        if not group_config.get('node_uids', []):
            nodes = self._nodenet.netapi.get_nodes(nodespace=self.nodespace, node_name_prefix=group_config['node_name_prefix'], sortby=group_config.get('sortby', 'ids'))
        else:
            nodes = [self._nodenet.get_node(uid) for uid in group_config['node_uids']]

        node_uids = [n.uid for n in nodes]
        assert len(set([n.type for n in nodes])) == 1  # assert we have a homogeneous group
        self.gatetypes = nodes[0].get_gate_types()
        self.groupnames = []
        for g in self.gatetypes:
            group_name = self.base_group_name + '_%s' % g
            self.groupnames.append(group_name)
            self._nodenet.group_nodes_by_ids(self.nodespace, node_uids, gatetype=g, group_name=group_name, sortby=group_config.get('sortby', 'id'))

        self.shapes = {'activations': (self.initial_size, len(self.gatetypes), len(nodes))}

    def get_data(self):
        data = super().get_data()
        data.update({
            "group_config": self.group_config,
        })
        return data

    def get_values(self):
        return {'activations': [self._nodenet.get_activations(self.nodespace, groupname) for groupname in self.groupnames]}


class LinkweightRecorder(Recorder):
    """ An activation recorder to biases and the linkweights of two nodegroups"""

    def __init__(self, nodenet, from_group_config={}, to_group_config={}, name="", uid="", interval=1, first_step=0, current_index=-1, **_):
        super().__init__(nodenet, name, uid, interval, first_step=first_step, current_index=current_index)

        if 'group_name' not in from_group_config:
            from_group_config['group_name'] = "%s_from" % name
        if 'group_name' not in to_group_config:
            to_group_config['group_name'] = "%s_to" % name

        self.from_group_config = from_group_config
        self.to_group_config = to_group_config

        self.from_nodespace = from_group_config['nodespace_uid']
        self.to_nodespace = to_group_config['nodespace_uid']
        self.from_name = from_group_config['group_name']
        self.to_name = to_group_config['group_name']

        if not from_group_config.get('node_uids', []):
            self._nodenet.group_nodes_by_names(**from_group_config)
        else:
            self._nodenet.group_nodes_by_ids(**from_group_config)

        if not to_group_config.get('node_uids', []):
            self._nodenet.group_nodes_by_names(**to_group_config)
        else:
            self._nodenet.group_nodes_by_ids(**to_group_config)

        weights = self._nodenet.get_link_weights(self.from_nodespace, self.from_name, self.to_nodespace, self.to_name)
        from_uids = self._nodenet.get_node_uids(self.from_nodespace, self.from_name)
        to_uids = self._nodenet.get_node_uids(self.to_nodespace, self.to_name)
        self.shapes = {
            'linkweights': (self.initial_size, weights.shape[0], weights.shape[1]),
            'from_bias': (self.initial_size, len(from_uids)),
            'to_bias': (self.initial_size, len(to_uids))
        }

    def get_data(self):
        data = super().get_data()
        data.update({
            'from_group_config': self.from_group_config,
            'to_group_config': self.to_group_config
        })
        return data

    def get_values(self):
        from_config = self._nodenet.get_gate_configurations(self.from_nodespace, self.from_name, 'bias')
        to_config = self._nodenet.get_gate_configurations(self.to_nodespace, self.to_name, 'bias')
        return {
            'linkweights': self._nodenet.get_link_weights(self.from_nodespace, self.from_name, self.to_nodespace, self.to_name),
            'from_bias': from_config['parameter_values'],
            'to_bias': to_config['parameter_values']
        }
