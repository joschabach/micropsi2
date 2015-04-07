# -*- coding: utf-8 -*-
"""
Nodespace definition
"""

import warnings

from micropsi_core.nodenet.dict_engine.dict_netentity import NetEntity
from micropsi_core.nodenet.nodespace import Nodespace
import micropsi_core.tools


__author__ = 'joscha'
__date__ = '09.05.12'


class DictNodespace(NetEntity, Nodespace):
    """A container for net entities.

    One nodespace is marked as root, all others are contained in
    exactly one other nodespace.

    Attributes:
        activators: a dictionary of activators that control the spread of activation, via activator nodes
        netentities: a dictionary containing all the contained nodes and nodespaces, to speed up drawing
    """

    @property
    def data(self):
        data = {
            "uid": self.uid,
            "index": self.index,
            "name": self.name,
            "position": self.position,
            "parent_nodespace": self.parent_nodespace,
        }
        return data

    def __init__(self, nodenet, parent_nodespace, position, name="", uid=None, index=None):
        """create a node space at a given position and within a given node space"""
        self.__activators = {}
        self.__netentities = {}
        uid = uid or micropsi_core.tools.generate_uid()
        NetEntity.__init__(self, nodenet, parent_nodespace, position, name, "nodespaces", uid, index)
        nodenet._register_nodespace(self)

    def get_known_ids(self, entitytype=None):
        if entitytype:
            if entitytype not in self.__netentities:
                return []
            return self.__netentities[entitytype]
        else:
            return [uid for uid_list in self.__netentities.values() for uid in uid_list]

    def is_entity_known_as(self, entitytype, uid):
        if entitytype not in self.__netentities:
            self.__netentities[entitytype] = []
        return uid in self.__netentities[entitytype]

    def has_activator(self, type):
        return type in self.__activators

    def get_activator_value(self, type):
        return self.__activators[type]

    def set_activator_value(self, type, value):
        self.__activators[type] = value

    def unset_activator_value(self, type):
        self.__activators.pop(type, None)

    def _register_entity(self, entity):
        if entity.entitytype not in self.__netentities:
            self.__netentities[entity.entitytype] = []
        self.__netentities[entity.entitytype].append(entity.uid)

    def _unregister_entity(self, entitytype, uid):
        self.__netentities[entitytype].remove(uid)
