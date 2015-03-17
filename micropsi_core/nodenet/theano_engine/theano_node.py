# -*- coding: utf-8 -*-

from micropsi_core.nodenet.node import Node, Gate, Slot
from micropsi_core.nodenet.theano_engine.theano_link import TheanoLink

import theano
from theano import tensor as T
import numpy as np

import warnings
import micropsi_core.tools
import logging

REGISTER = 1
SENSOR = 2
ACTUATOR = 3
ACTIVATOR = 4
CONCEPT = 5
SCRIPT = 6
PIPE = 7
TRIGGER = 8


GEN = 0
POR = 1
RET = 2
SUB = 3
SUR = 4
CAT = 5
EXP = 6

NUMBER_OF_ELEMENTS_PER_NODE = 7


def get_numerical_gate_type(type):
    if type == "por":
        return POR
    elif type == "ret":
        return RET
    elif type == "sub":
        return SUB
    elif type == "sur":
        return SUR
    elif type == "cat":
        return CAT
    elif type == "exp":
        return EXP
    else:
        return GEN


def get_string_gate_type(type):
    if type == POR:
        return "por"
    elif type == RET:
        return "ret"
    elif type == SUB:
        return "ret"
    elif type == SUR:
        return "sur"
    elif type == CAT:
        return "cat"
    elif type == EXP:
        return "exp"
    else:
        return "gen"


def get_numerical_node_type(type):
    numerictype = 0
    if type == "Register":
        numerictype = REGISTER
    elif type == "Actuator":
        numerictype = ACTUATOR
    elif type == "Sensor":
        numerictype = SENSOR
    elif type == "Activator":
        numerictype = ACTIVATOR
    elif type == "Concept":
        numerictype = CONCEPT
    elif type == "Script":
        numerictype = SCRIPT
    elif type == "Pipe":
        numerictype = PIPE
    elif type == "Trigger":
        numerictype = TRIGGER
    return numerictype


def get_string_node_type(type):
    stringtype = 0
    if type == REGISTER:
        stringtype = "Register"
    elif type == ACTUATOR:
        stringtype = "Actuator"
    elif type == SENSOR:
        stringtype = "Sensor"
    elif type == ACTIVATOR:
        stringtype = "Activator"
    elif type == CONCEPT:
        stringtype = "Concept"
    elif type == SCRIPT:
        stringtype = "Script"
    elif type == PIPE:
        stringtype = "Pipe"
    elif type == TRIGGER:
        stringtype = "Trigger"
    return stringtype


def to_id(numericid):
    return "n"+str(int(numericid))


def from_id(stringid):
    return int(stringid[1:])


class TheanoNode(Node):
    """
        theano node proxy class
    """

    _nodenet = None
    _id =-1

    def __init__(self, nodenet, uid=0, type=0, **_):

        strtype = get_string_node_type(type)

        Node.__init__(self, strtype, nodenet.get_nodetype(strtype))

        self._nodenet = nodenet
        self._id = from_id(uid)

    @property
    def uid(self):
        return to_id(self._id)

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
        return float(self._nodenet.a.get_value(borrow=True, return_internal_type=True)[self._id*NUMBER_OF_ELEMENTS_PER_NODE + GEN])

    @property
    def activations(self):
        return {"default": self.activation}

    @activation.setter
    def activation(self, activation):
        self._nodenet.a_array[self._id*NUMBER_OF_ELEMENTS_PER_NODE + GEN] = activation
        self._nodenet.a.set_value(self._nodenet.a_array, borrow=True)

    def get_gate(self, type):
        return TheanoGate(type, self, self._nodenet)

    def set_gate_parameter(self, gate_type, parameter, value):
        pass                    # todo: implement gate parameters

    def clone_non_default_gate_parameters(self, gate_type):
        pass                    # todo: implement gate parameters

    def get_slot(self, type):
        return TheanoSlot(type, self, self._nodenet)

    def get_associated_links(self):
        links = []
        links.extend(self.get_gate("gen").get_links())
        links.extend(self.get_gate("por").get_links())
        links.extend(self.get_gate("ret").get_links())
        links.extend(self.get_gate("sub").get_links())
        links.extend(self.get_gate("sur").get_links())
        links.extend(self.get_gate("cat").get_links())
        links.extend(self.get_gate("exp").get_links())
        return links

    def get_parameter(self, parameter):
        pass                    # todo: implement node parameters

    def set_parameter(self, parameter, value):
        pass                    # todo: implement node parameters

    def clone_parameters(self):
        pass

    def get_gate_parameters(self):
        return {}               # todo: implement gate parameters

    def get_state(self, state):
        pass

    def set_state(self, state, value):
        pass

    def clone_state(self):
        pass

    def clone_sheaves(self):
        return {"default": dict(uid="default", name="default", activation=self.activation)}  # todo: implement sheaves

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
        return float(self.__nodenet.a.get_value(borrow=True, return_internal_type=True)[from_id(self.__node.uid)*NUMBER_OF_ELEMENTS_PER_NODE + self.__numerictype])

    @property
    def activations(self):
        return {'default': self.activation} # todo: implement sheaves

    def __init__(self, type, node, nodenet):
        self.__type = type
        self.__node = node
        self.__nodenet = nodenet
        self.__numerictype = get_numerical_gate_type(type)

    def get_links(self):
        links = []
        gaterow = self.__nodenet.w_matrix[from_id(self.__node.uid)*NUMBER_OF_ELEMENTS_PER_NODE+self.__numerictype]
        linksIndices = np.nonzero(gaterow)[0]
        for index in linksIndices:
            target_slot_numerical = index % NUMBER_OF_ELEMENTS_PER_NODE
            target_uid = int(int(index - target_slot_numerical) / int(NUMBER_OF_ELEMENTS_PER_NODE))
            weight = gaterow[index]
            target_node = self.__nodenet.get_node(to_id(target_uid))
            target_slot = target_node.get_slot(get_string_gate_type(target_slot_numerical))
            link = TheanoLink(self.__node, self, target_node, target_slot, weight)
            links.append(link)
        return links

    def get_parameter(self, parameter_name):
        pass            # todo: implement parameters

    def clone_sheaves(self):
        return {"default": dict(uid="default", name="default", activation=self.activation)}  # todo: implement sheaves

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
        self.__tyoe = get_numerical_gate_type(type)

    def get_activation(self, sheaf="default"):
        return              # theano slots never report activation to anybody


    def get_links(self):
        pass                # todo: implement links