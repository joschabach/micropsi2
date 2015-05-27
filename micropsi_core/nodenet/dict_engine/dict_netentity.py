# -*- coding: utf-8 -*-

"""
Netentity definition
"""

import micropsi_core.tools

__author__ = 'joscha'
__date__ = '09.05.12'


class NetEntity(object):
    """The basic building blocks of node nets.

    Attributes:
        uid: the unique identifier of the net entity
        index: an attempt at creating an ordering criterion for net entities
        name: a human readable name (optional)
        position: a pair of coordinates on the screen
        nodenet: the node net in which the entity resides
        parent_nodespace: the node space this entity is contained in
    """

    @property
    def uid(self):
        return self.__uid

    @uid.setter
    def uid(self, uid):
        self.__uid = uid

    @property
    def index(self):
        return self.__index

    @index.setter
    def index(self, index):
        self.__index = index

    @property
    def position(self):
        return self.__position

    @position.setter
    def position(self, position):
        self.__position = position

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, name):
        self.__name = name

    @property
    def parent_nodespace(self):
        return self.__parent_nodespace

    @parent_nodespace.setter
    def parent_nodespace(self, uid):
        if uid:
            nodespace = self.nodenet.get_nodespace(uid)
            if not nodespace.is_entity_known_as(self.entitytype, self.uid):
                nodespace._register_entity(self)
                # tell my old parent that I move out
                if self.__parent_nodespace is not None:
                    old_parent = self.nodenet.get_nodespace(self.__parent_nodespace)
                    if old_parent and old_parent.uid != uid and old_parent.is_entity_known_as(self.entitytype, self.uid):
                        old_parent._unregister_entity(self.entitytype, self.uid)
        self.__parent_nodespace = uid

    def __init__(self, nodenet, parent_nodespace, position, name="", entitytype="abstract_entities",
                 uid=None, index=None):
        """create a net entity at a certain position and in a given node space"""
        self.__uid = None
        self.__index = 0
        self.__name = None
        self.__parent_nodespace = None
        self.__position = None

        self.uid = uid or micropsi_core.tools.generate_uid()
        self.nodenet = nodenet
        self.index = index or len(nodenet.get_node_uids()) + len(nodenet.get_nodespace_uids())
        self.entitytype = entitytype
        self.name = name
        self.position = position
        if parent_nodespace:
            self.parent_nodespace = parent_nodespace
        else:
            self.parent_nodespace = None
