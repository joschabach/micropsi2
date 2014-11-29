# -*- coding: utf-8 -*-
"""
Nodespace definition
"""

from .netentity import NetEntity
import micropsi_core.tools
import warnings

__author__ = 'joscha'
__date__ = '09.05.12'


class Nodespace(NetEntity):
    """A container for net entities.

    One nodespace is marked as root, all others are contained in
    exactly one other nodespace.

    Attributes:
        activators: a dictionary of activators that control the spread of activation, via activator nodes
        netentities: a dictionary containing all the contained nodes and nodespaces, to speed up drawing
    """

    __gatefunction_strings = {}

    @property
    def data(self):
        data = NetEntity.data.fget(self)
        data.update({
            "uid": self.uid,
            "gatefunctions": self.__gatefunction_strings
        })
        return data

    def __init__(self, nodenet, parent_nodespace, position, name="", uid=None, index=None, gatefunction_strings=None):
        """create a node space at a given position and within a given node space"""
        self.__activators = {}
        self.__netentities = {}
        uid = uid or micropsi_core.tools.generate_uid()
        NetEntity.__init__(self, nodenet, parent_nodespace, position, name, "nodespaces", uid, index)
        nodenet._register_nodespace(self)
        self.__gatefunctions = {}
        self.__gatefunction_strings = gatefunction_strings or {}
        for nodetype in self.__gatefunction_strings:
            for gatetype in self.__gatefunction_strings[nodetype]:
                self.set_gate_function(nodetype, gatetype, self.__gatefunction_strings[nodetype][gatetype])

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

    def set_gate_function(self, nodetype, gatetype, gatefunction, parameters=None):
        """Sets the gatefunction for a given node- and gatetype within this nodespace"""
        if gatefunction:
            if nodetype not in self.__gatefunction_strings:
                self.__gatefunction_strings[nodetype] = {}
            self.__gatefunction_strings[nodetype][gatetype] = gatefunction
            if nodetype not in self.__gatefunctions:
                self.__gatefunctions[nodetype] = {}
            try:
                import math
                self.__gatefunctions[nodetype][gatetype] = micropsi_core.tools.create_function(gatefunction, parameters="x, r, t", additional_symbols={'math': math})
            except SyntaxError as err:
                warnings.warn("Syntax error while compiling gate function: %s, %s" % (gatefunction, str(err)))
                raise err
        else:
            if nodetype in self.__gatefunctions and gatetype in self.__gatefunctions[nodetype]:
                del self.__gatefunctions[nodetype][gatetype]
            if nodetype in self.__gatefunction_strings[nodetype] and gatetype in self.__gatefunction_strings[nodetype][nodetype]:
                del self.__gatefunction_strings[nodetype][nodetype][gatetype]

    def get_gatefunction(self, nodetype, gatetype):
        """Retrieve a bytecode-compiled gatefunction for a given node- and gatetype"""
        if nodetype in self.__gatefunctions and gatetype in self.__gatefunctions[nodetype]:
            return self.__gatefunctions[nodetype][gatetype]

    def get_gatefunction_string(self, nodetype, gatetype):
        """Retrieve a string gatefunction for a given node- and gatetype"""
        if nodetype in self.__gatefunctions and gatetype in self.__gatefunctions[nodetype]:
            return self.__gatefunction_strings[nodetype][gatetype]
        else:
            return ''

    def get_gatefunction_strings(self):
        """Retrieve all string gatefunctions """
        return self.__gatefunction_strings
