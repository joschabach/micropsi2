# -*- coding: utf-8 -*-

from micropsi_core.nodenet.node import Node, Gate, Slot
from micropsi_core.nodenet.theano_engine.theano_link import TheanoLink

import numpy as np


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
        return "sub"
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
    elif type == "Actor":
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
        stringtype = "Actor"
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
    return "n" + str(int(numericid))


def from_id(stringid):
    return int(stringid[1:])


class TheanoNode(Node):
    """
        theano node proxy class
    """

    _nodenet = None
    _id = -1

    def __init__(self, nodenet, uid, type, **_):

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
        return self._nodenet.positions[self._id]      # todo: get rid of positions

    @position.setter
    def position(self, position):
        self._nodenet.positions[self._id] = position  # todo: get rid of positions

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
        return float(self._nodenet.a.get_value(borrow=True, return_internal_type=True)[self._id * NUMBER_OF_ELEMENTS_PER_NODE + GEN])

    @property
    def activations(self):
        return {"default": self.activation}

    @activation.setter
    def activation(self, activation):
        a_array = self._nodenet.a.get_value(borrow=True, return_internal_type=True)
        a_array[self._id * NUMBER_OF_ELEMENTS_PER_NODE + GEN] = activation
        self._nodenet.a.set_value(a_array, borrow=True)

    def get_gate(self, type):
        return TheanoGate(type, self, self._nodenet)

    def set_gate_parameter(self, gate_type, parameter, value):

        # todo: implement the other gate parameters
        elementindex = self._id * NUMBER_OF_ELEMENTS_PER_NODE + get_numerical_gate_type(gate_type)
        if parameter == 'threshold':
            g_threshold_array = self._nodenet.g_threshold.get_value(borrow=True, return_internal_type=True)
            g_threshold_array[elementindex] = value
            self._nodenet.g_threshold.set_value(g_threshold_array, borrow=True)
        elif parameter == 'amplification':
            g_amplification_array = self._nodenet.g_amplification.get_value(borrow=True, return_internal_type=True)
            g_amplification_array[elementindex] = value
            self._nodenet.g_amplification.set_value(g_amplification_array, borrow=True)
        elif parameter == 'minimum':
            g_min_array = self._nodenet.g_min.get_value(borrow=True, return_internal_type=True)
            g_min_array[elementindex] = value
            self._nodenet.g_min.set_value(g_min_array, borrow=True)
        elif parameter == 'maximum':
            g_max_array = self._nodenet.g_max.get_value(borrow=True, return_internal_type=True)
            g_max_array[elementindex] = value
            self._nodenet.g_max.set_value(g_max_array, borrow=True)

    def get_gate_parameters(self):
        # todo: implement defaulting mechanism for gate parameters

        g_threshold_array = self._nodenet.g_threshold.get_value(borrow=True, return_internal_type=True)
        g_amplification_array = self._nodenet.g_amplification.get_value(borrow=True, return_internal_type=True)
        g_min_array = self._nodenet.g_min.get_value(borrow=True, return_internal_type=True)
        g_max_array = self._nodenet.g_max.get_value(borrow=True, return_internal_type=True)

        result = {}
        for numericalgate in range(0, NUMBER_OF_ELEMENTS_PER_NODE):
            gate_parameters = {
                'threshold': g_threshold_array[self._id * NUMBER_OF_ELEMENTS_PER_NODE + numericalgate],
                'amplification': g_amplification_array[self._id * NUMBER_OF_ELEMENTS_PER_NODE + numericalgate],
                'minimum': g_min_array[self._id * NUMBER_OF_ELEMENTS_PER_NODE + numericalgate],
                'maximum': g_max_array[self._id * NUMBER_OF_ELEMENTS_PER_NODE + numericalgate],
            }
            result[get_string_gate_type(numericalgate)] = gate_parameters
        return result

    def clone_non_default_gate_parameters(self, gate_type):
        return self.get_gate_parameters()               # todo: implement gate parameters

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

    def unlink_completely(self):

        # there's a simpler implementation for this that just clears the
        # node's row and column in the weight matrix. Probably depends on the matrix implementation
        # whether that's actually faster.

        links = []
        links.extend(self.get_gate("gen").get_links())
        links.extend(self.get_gate("por").get_links())
        links.extend(self.get_gate("ret").get_links())
        links.extend(self.get_gate("sub").get_links())
        links.extend(self.get_gate("sur").get_links())
        links.extend(self.get_gate("cat").get_links())
        links.extend(self.get_gate("exp").get_links())

        links.extend(self.get_slot("gen").get_links())
        links.extend(self.get_slot("por").get_links())
        links.extend(self.get_slot("ret").get_links())
        links.extend(self.get_slot("sub").get_links())
        links.extend(self.get_slot("sur").get_links())
        links.extend(self.get_slot("cat").get_links())
        links.extend(self.get_slot("exp").get_links())
        for link in links:
            self._nodenet.delete_link(link.source_node.uid, link.source_gate.type, link.target_node.uid, link.target_slot.type)

    def get_parameter(self, parameter):
        return self.clone_parameters().get(parameter)

    def set_parameter(self, parameter, value):
        if self.type == "Sensor" and parameter == "datasource":
            olddatasource = self._nodenet.inverted_sensor_map[self.uid]     # first, clear old data source association
            if self._id in self._nodenet.sensormap.get(olddatasource, []):
                self._nodenet.sensormap.get(olddatasource, []).remove(self._id)

            connectedsensors = self._nodenet.sensormap.get(value, [])       # then, set the new one
            connectedsensors.append(self._id)
            self._nodenet.sensormap[value] = connectedsensors
            self._nodenet.inverted_sensor_map[self.uid] = value
        if self.type == "Actor" and parameter == "datatarget":
            olddatatarget = self._nodenet.inverted_actuator_map[self.uid]     # first, clear old data target association
            if self._id in self._nodenet.actuatormap.get(olddatatarget, []):
                self._nodenet.actuatormap.get(olddatatarget, []).remove(self._id)

            connectedactuators = self._nodenet.actuatormap.get(value, [])       # then, set the new one
            connectedactuators.append(self._id)
            self._nodenet.actuatormap[value] = connectedactuators
            self._nodenet.inverted_actuator_map[self.uid] = value

    def clone_parameters(self):
        parameters = {}
        if self.type == "Sensor":
            parameters['datasource'] = self._nodenet.inverted_sensor_map[self.uid]
        elif self.type == "Actor":
            parameters['datatarget'] = self._nodenet.inverted_actuator_map[self.uid]
        return parameters

    def get_state(self, state):
        return None             # todo: implement node state

    def set_state(self, state, value):
        pass                    # todo: implement node state

    def clone_state(self):
        return {}               # todo: implement node szaze

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
        return float(self.__nodenet.a.get_value(borrow=True, return_internal_type=True)[from_id(self.__node.uid) * NUMBER_OF_ELEMENTS_PER_NODE + self.__numerictype])

    @activation.setter
    def activation(self, value):
        a_array = self.__nodenet.a.get_value(borrow=True, return_internal_type=True)
        a_array[from_id(self.__node.uid) * NUMBER_OF_ELEMENTS_PER_NODE + self.__numerictype] = value
        self.__nodenet.a.set_value(a_array, borrow=True)

    @property
    def activations(self):
        return {'default': self.activation}  # todo: implement sheaves

    def __init__(self, type, node, nodenet):
        self.__type = type
        self.__node = node
        self.__nodenet = nodenet
        self.__numerictype = get_numerical_gate_type(type)

    def get_links(self):
        links = []
        w_matrix = self.__nodenet.w.get_value(borrow=True, return_internal_type=True)
        gatecolumn = w_matrix[:, from_id(self.__node.uid) * NUMBER_OF_ELEMENTS_PER_NODE + self.__numerictype]
        links_indices = np.nonzero(gatecolumn)[0]
        for index in links_indices:
            target_slot_numerical = index % NUMBER_OF_ELEMENTS_PER_NODE
            target_uid = int(int(index - target_slot_numerical) / int(NUMBER_OF_ELEMENTS_PER_NODE))
            weight = gatecolumn[index]
            if self.__nodenet.sparse:               # sparse matrices return matrices of dimension (1,1) as values
                weight = float(weight.data)
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
        self.__numerictype = get_numerical_gate_type(type)

    def get_activation(self, sheaf="default"):
        return              # theano slots never report activation to anybody

    def get_links(self):
        links = []
        w_matrix = self.__nodenet.w.get_value(borrow=True, return_internal_type=True)
        slotrow = w_matrix[from_id(self.__node.uid) * NUMBER_OF_ELEMENTS_PER_NODE + self.__numerictype]
        links_indices = np.nonzero(slotrow)[1]
        for index in links_indices:
            source_gate_numerical = index % NUMBER_OF_ELEMENTS_PER_NODE
            source_uid = int(int(index - source_gate_numerical) / int(NUMBER_OF_ELEMENTS_PER_NODE))
            weight = slotrow[: , index]
            if self.__nodenet.sparse:               # sparse matrices return matrices of dimension (1,1) as values
                weight = float(weight.data)
            source_node = self.__nodenet.get_node(to_id(source_uid))
            source_gate = source_node.get_slot(get_string_gate_type(source_gate_numerical))
            link = TheanoLink(source_node, source_gate, self.__node, self, weight)
            links.append(link)
        return links
