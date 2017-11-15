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
    def name(self):
        return self.__name

    @name.setter
    def name(self, name):
        self.__name = name

    @property
    def parent_nodespace(self):
        return self.__parent_nodespace

    def __init__(self, nodenet, parent_nodespace, name="", entitytype="abstract_entities",
                 uid=None, index=None):
        """create a net entity in a given node space"""
        self.__uid = None
        self.__index = 0
        self.__name = None
        self.__parent_nodespace = None

        self.uid = uid or nodenet.generate_uid(entitytype)
        self.nodenet = nodenet
        self.index = index or len(nodenet.get_node_uids()) + len(nodenet.get_nodespace_uids())
        self.entitytype = entitytype
        self.name = name
        if parent_nodespace:
            self.__parent_nodespace = parent_nodespace
            nodespace = self.nodenet.get_nodespace(parent_nodespace)
            if not nodespace.is_entity_known_as(self.entitytype, self.uid):
                nodespace._register_entity(self)
        else:
            self.__parent_nodespace = None
