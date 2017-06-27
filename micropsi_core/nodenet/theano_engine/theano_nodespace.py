# -*- coding: utf-8 -*-

from micropsi_core.nodenet.nodespace import Nodespace
from micropsi_core.nodenet.theano_engine.theano_definitions import *
import numpy as np


class TheanoNodespace(Nodespace):
    """
        theano nodespace implementation
    """

    @property
    def uid(self):
        return nodespace_to_id(self._id, self._partition.pid)

    @property
    def index(self):
        return self._id

    @index.setter
    def index(self, index):
        raise NotImplementedError("index can not be set in theano_engine")

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
        parent_nodespace_id = self._partition.allocated_nodespaces[self._id]
        if parent_nodespace_id == 0:
            if self._partition.spid in self._nodenet.inverted_partitionmap:
                return self._nodenet.inverted_partitionmap[self._partition.spid]
            else:
                return None
        else:
            return nodespace_to_id(parent_nodespace_id, self._partition.pid)

    @property
    def partition(self):
        return self._partition

    def __init__(self, nodenet, partition, uid):
        self.__activators = {}
        self._nodenet = nodenet
        self._partition = partition
        self._id = nodespace_from_id(uid)

    def get_known_ids(self, entitytype=None):
        if entitytype == 'nodes':
            return [node_to_id(id, self._partition.pid) for id in np.where(self._partition.allocated_node_parents == self._id)[0]]
        elif entitytype == 'nodespaces':
            uids = [nodespace_to_id(id, self._partition.pid) for id in np.where(self._partition.allocated_nodespaces == self._id)[0]]
            if self.uid in self._nodenet.partitionmap:
                for partition in self._nodenet.partitionmap[self.uid]:
                    uids.append(partition.rootnodespace_uid)
            return uids
        elif entitytype is None:
            ids = self.get_known_ids('nodes')
            ids.extend(self.get_known_ids('nodespaces'))
            return ids
        else:
            return []

    def has_activator(self, type):
        return type in self.__activators

    def get_activator_value(self, type):
        return self.__activators[type]

    def set_activator_value(self, type, value):
        self.__activators[type] = value

    def unset_activator_value(self, type):
        self.__activators.pop(type, None)
