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

    __name = None
    __parent_nodespace = None

    @property
    def data(self):
        data = {
            "uid": self.uid,
            "index": self.index,
            "name": self.name,
            "position": self.position,
            "parent_nodespace": self.parent_nodespace
        }
        return data

    @property
    def name(self):
        return self.__name or self.uid

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
            if self.entitytype not in nodespace.netentities:
                nodespace.netentities[self.entitytype] = []
            if self.uid not in nodespace.netentities[self.entitytype]:
                nodespace.netentities[self.entitytype].append(self.uid)
                # tell my old parent that I move out
                if self.__parent_nodespace is not None:
                    old_parent = self.nodenet.get_nodespace(self.__parent_nodespace)
                    if old_parent and old_parent.uid != uid and self.uid in old_parent.netentities.get(self.entitytype, []):
                        old_parent.netentities[self.entitytype].remove(self.uid)
        self.__parent_nodespace = uid

    def __init__(self, nodenet, parent_nodespace, position, name="", entitytype="abstract_entities",
                 uid=None, index=None):
        """create a net entity at a certain position and in a given node space"""

        self.uid = uid or micropsi_core.tools.generate_uid()
        self.nodenet = nodenet
        if not entitytype in nodenet.entitytypes:
            nodenet.entitytypes[entitytype] = {}
        if not uid in nodenet.entitytypes[entitytype]:
            nodenet.entitytypes[entitytype][uid] = {}
        self.__uid = uid
        self.index = index or len(nodenet.get_node_uids()) + len(nodenet.get_nodespace_uids())
        self.entitytype = entitytype
        self.name = name
        self.position = position
        if parent_nodespace:
            self.parent_nodespace = parent_nodespace
        else:
            self.parent_nodespace = None
