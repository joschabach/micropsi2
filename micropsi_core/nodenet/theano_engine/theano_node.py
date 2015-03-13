# -*- coding: utf-8 -*-

from micropsi_core.nodenet.node import Node, Gate, Slot

import theano
from theano import tensor as T
import numpy as np

import warnings
import micropsi_core.tools
import logging

GEN = 0
POR = 1
RET = 2
SUB = 3
SUR = 4
CAT = 5
EXP = 6


class TheanoNode(Node):
    """
        theano node proxy class
    """

    _nodenet = None
    _id =-1

    def __init__(self, nodenet, uid=0, **_):

        self._nodenet = nodenet
        self._id = int(uid)

    @property
    def uid(self):
        return str(self._id)

    @property
    def index(self):
        return 0                # todo: implement index

    @index.setter
    def index(self, index):
        pass                    # todo: implement index

    @property
    def position(self):
        return (0,0,)           # todo: implement position

    @position.setter
    def position(self, position):
        pass                    # todo: implement position

    @property
    def name(self):
        return self.uid         # todo: implement name

    @name.setter
    def name(self, name):
        pass                    # todo: implement name

    @property
    def parent_nodespace(self):
        return "Root"           # todo: implement nodespace

    @parent_nodespace.setter
    def parent_nodespace(self, uid):
        pass                    # todo: implement nodespace

    @property
    def activation(self):
        return self._nodenet.a.get_value(borrow=True, return_internal_type=True)[self._id + GEN]

    @property
    def activations(self):
        return {"default": self.activation}

    @activation.setter
    def activation(self, activation):
        self._nodenet.a_array[self._id + GEN] = activation
        self._nodenet.a.set_value(self._nodenet.a_array, borrow=True)

    def get_gate(self, type):
        return TheanoGate(type, self, self._nodenet)

    def set_gate_parameter(self, gate_type, parameter, value):
        pass                    # todo: implement gate parameters

    def clone_non_default_gate_parameters(self, gate_type):
        pass                    # todo: implement gate parameters

    def get_slot(self, type):
        pass

    def get_parameter(self, parameter):
        pass                    # todo: implement node parameters

    def set_parameter(self, parameter, value):
        pass                    # todo: implement node parameters

    def clone_parameters(self):
        pass

    def get_state(self, state):
        pass

    def set_state(self, state, value):
        pass

    def clone_state(self):
        pass

    def clone_sheaves(self):
        pass                    # todo: implement sheaves

    def node_function(self):
        pass


class TheanoGate(Gate):
    """
        theano gate proxy clas
    """

    __numerictype = GEN
    __type = None
    __node = None
    __nodenet = None

    @property
    def type(self):
        return self.__type

    @property
    def node(self):
        return self.__node

    @property
    def empty(self):
       return True              # todo: implement empty

    @property
    def activation(self):
        return self.__nodenet.a.get_value(borrow=True, return_internal_type=True)[int(self.__node.uid) + self.__numerictype]

    @property
    def activations(self):
        return {'default': self.activation} # todo: implement sheaves

    def __init__(self, type, node, nodenet):
        self.__type = type
        self.__node = node
        self.__nodenet = nodenet
        if type == "POR":
            self.__numerictype = POR
        elif type == "RET":
            self.__numerictype = RET
        elif type == "SUB":
            self.__numerictype = SUB
        elif type == "SUR":
            self.__numerictype = SUR
        elif type == "CAT":
            self.__numerictype = CAT
        elif type == "EXP":
            self.__numerictype = EXP

    def get_links(self):
        pass            # todo: implement links

    def get_parameter(self, parameter_name):
        pass            # todo: implement parameters

    def clone_sheaves(self):
        pass            # tod: implement sheaves

    def gate_function(self, input_activation, sheaf="default"):
        pass            # todo: implement gate function - or rather, don't, who'd be calling this?

    def open_sheaf(self, input_activation, sheaf="default"):
        pass            # todo: implement sheaves


class TheanoSlot(Slot):
    """
        theano slot proxy class
    """

    __numerictype = GEN
    __type = None
    __node = None
    __nodenet = None

    @property
    def type(self):
        return self.__type

    @property
    def node(self):
        return self.__node

    @property
    def empty(self):
        pass                    # implement links

    @property
    def activation(self):
        return 0                # theano slots never report activation to anybody

    @property
    def activations(self):
        return None             # theano slots never report activation to anybody

    def __init__(self, type, node, nodenet):
        self.__type = type
        self.__node = node
        self.__nodenet = nodenet
        if type == "POR":
            self.__numerictype = POR
        elif type == "RET":
            self.__numerictype = RET
        elif type == "SUB":
            self.__numerictype = SUB
        elif type == "SUR":
            self.__numerictype = SUR
        elif type == "CAT":
            self.__numerictype = CAT
        elif type == "EXP":
            self.__numerictype = EXP

    def get_activation(self, sheaf="default"):
        return              # theano slots never report activation to anybody


    def get_links(self):
        pass                # todo: implement links