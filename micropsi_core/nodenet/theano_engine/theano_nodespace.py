# -*- coding: utf-8 -*-

from micropsi_core.nodenet.nodespace import Nodespace
import numpy as np


def to_id(numericid):
    return "s" + str(int(numericid))


def from_id(stringid):
    return int(stringid[1:])


class TheanoNodespace(Nodespace):
    """
        theano nodespace implementation
    """

    _nodenet = None
    _id = -1

    @property
    def data(self):
        data = {
            "uid": self.uid,
            "index": 0,
            "name": self.name,
            "position": self.position,
            "parent_nodespace": self.parent_nodespace
        }
        return data

    @property
    def uid(self):
        return to_id(self._id)

    @property
    def index(self):
        return 0

    @index.setter
    def index(self, index):
        pass

    @property
    def position(self):
        return self._nodenet.positions.get(self.uid, (10,10))       # todo: get rid of positions

    @position.setter
    def position(self, position):
        if position is None and self.uid in self._nodenet.positions:
            del self._nodenet.positions[self.uid]
        else:
            self._nodenet.positions[self.uid] = position         # todo: get rid of positions

    @property
    def name(self):
        return self._nodenet.names.get(self.uid, self.uid)

    @name.setter
    def name(self, name):
        if name is None or name == "" or name == self.uid:
            if self.uid in self._nodenet.names:
                del self._nodenet.names[self.uid]
        else:
            self._nodenet.names[self.uid] = name

    @property
    def parent_nodespace(self):
        parent_nodespace_id = self._nodenet.allocated_nodespaces[self._id]
        if parent_nodespace_id == 0:
            return None
        else:
            return to_id(parent_nodespace_id)

    @parent_nodespace.setter
    def parent_nodespace(self, uid):
        self._nodenet.allocated_nodespaces[self._id] = from_id(uid)

    def __init__(self, nodenet, uid):
        self.__activators = {}
        self._nodenet = nodenet
        self._id = from_id(uid)

    def get_known_ids(self, entitytype=None):
        if entitytype == 'nodes':
            from micropsi_core.nodenet.theano_engine.theano_node import to_id as node_to_id
            return [node_to_id(id) for id in np.where(self._nodenet.allocated_node_parents == self._id)[0]]
        else:
            return [to_id(id) for id in np.where(self._nodenet.allocated_nodespaces == self._id)[0]]

    def has_activator(self, type):
        return type in self.__activators

    def get_activator_value(self, type):
        return self.__activators[type]

    def set_activator_value(self, type, value):
        self.__activators[type] = value

    def unset_activator_value(self, type):
        self.__activators.pop(type, None)
