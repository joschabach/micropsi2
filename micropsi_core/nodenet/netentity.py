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
        return self.data.get("uid")

    @property
    def index(self):
        return self.data.get("index")

    @property
    def name(self):
        return self.data.get("name") or self.data.get("uid")

    @name.setter
    def name(self, string):
        self.data["name"] = string

    @property
    def position(self):
        return self.data.get("position", (0, 0))

    @position.setter
    def position(self, pos):
        self.data["position"] = pos

    @property
    def parent_nodespace(self):
        return self.data.get("parent_nodespace", 0)

    @parent_nodespace.setter
    def parent_nodespace(self, uid):
        nodespace = self.nodenet.nodespaces[uid]
        if self.entitytype not in nodespace.netentities:
            nodespace.netentities[self.entitytype] = []
        if self.uid not in nodespace.netentities[self.entitytype]:
            nodespace.netentities[self.entitytype].append(self.uid)
            #if uid in self.nodenet.state["nodespaces"][uid][self.entitytype]:
            #    self.nodenet.state["nodespaces"][uid][self.entitytype] = self.uid
            # tell my old parent that I move out
            if "parent_nodespace" in self.data:
                old_parent = self.nodenet.nodespaces.get(self.data["parent_nodespace"])
                if old_parent and old_parent.uid != uid and self.uid in old_parent.netentities.get(self.entitytype, []):
                    old_parent.netentities[self.entitytype].remove(self.uid)
        self.data['parent_nodespace'] = uid

    def __init__(self, nodenet, parent_nodespace, position, name="", entitytype="abstract_entities",
                 uid=None, index=None):
        """create a net entity at a certain position and in a given node space"""

        uid = uid or micropsi_core.tools.generate_uid()
        self.nodenet = nodenet
        if not entitytype in nodenet.entitytypes:
            nodenet.entitytypes[entitytype] = {}
        if not uid in nodenet.entitytypes[entitytype]:
            nodenet.entitytypes[entitytype][uid] = {}
        self.data = nodenet.entitytypes[entitytype][uid]
        self.data["uid"] = uid
        self.data["index"] = index or len(nodenet.nodes) + len(nodenet.nodespaces)
        self.entitytype = entitytype
        self.name = name
        self.position = position
        if parent_nodespace:
            self.parent_nodespace = parent_nodespace
        else:
            self.data['parent_nodespace'] = None
