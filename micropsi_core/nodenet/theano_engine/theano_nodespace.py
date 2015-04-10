# -*- coding: utf-8 -*-

from micropsi_core.nodenet.nodespace import Nodespace
from micropsi_core.nodenet.theano_engine.theano_node import *


class TheanoNodespace(Nodespace):
    """
        theano nodespace implementation
    """
    @property
    def data(self):
        data = {
            "uid": "Root",
            "index": 0,
            "name": "Root",
            "position": (0, 0),
            "parent_nodespace": None
        }
        return data

    @property
    def uid(self):
        return "Root"

    @property
    def index(self):
        return 0

    @index.setter
    def index(self, index):
        pass

    @property
    def position(self):
        return (0,0)

    @position.setter
    def position(self, position):
        pass

    @property
    def name(self):
        return "Root"

    @name.setter
    def name(self, name):
        pass

    @property
    def parent_nodespace(self):
        return None

    @parent_nodespace.setter
    def parent_nodespace(self, uid):
        pass

    def __init__(self, nodenet):
        self.__activators = {}
        self.__nodenet = nodenet
        uid = "Root"                    # todo: find out how to implement hierarchy of spaces

    def get_known_ids(self, entitytype=None):
        if entitytype == 'nodes':
            return self.__nodenet.get_node_uids()
        else:
            return ["Root"]

    def has_activator(self, type):
        return type in self.__activators

    def get_activator_value(self, type):
        return self.__activators[type]

    def set_activator_value(self, type, value):
        self.__activators[type] = value

    def unset_activator_value(self, type):
        self.__activators.pop(type, None)
