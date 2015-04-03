# -*- coding: utf-8 -*-

from micropsi_core.nodenet.node import Node, Gate, Slot
from micropsi_core.nodenet.theano_engine.theano_link import TheanoLink
from micropsi_core.nodenet.theano_engine.theano_stepoperators import *

import numpy as np


REGISTER = 1
SENSOR = 2
ACTUATOR = 3
ACTIVATOR = 4
CONCEPT = 5
SCRIPT = 6
PIPE = 7
TRIGGER = 8

MAX_STD_NODETYPE = TRIGGER


GEN = 0
POR = 1
RET = 2
SUB = 3
SUR = 4
CAT = 5
EXP = 6


def get_numerical_gate_type(type, nodetype=None):
    if nodetype is not None and len(nodetype.gatetypes) > 0:
        return nodetype.gatetypes.index(type)
    elif type == "gen":
        return GEN
    elif type == "por":
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
        raise ValueError("Supplied type is not a valid gate type: "+str(type))


def get_string_gate_type(type, nodetype=None):
    if nodetype is not None and len(nodetype.gatetypes) > 0:
        return nodetype.gatetypes[type]
    elif type == GEN:
        return "gen"
    elif type == POR:
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
        raise ValueError("Supplied type is not a valid gate type: "+str(type))


def get_numerical_slot_type(type, nodetype=None):
    if nodetype is not None and len(nodetype.slottypes) > 0:
        return nodetype.slottypes.index(type)
    elif type == "gen":
        return GEN
    elif type == "por":
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
        raise ValueError("Supplied type is not a valid slot type: "+str(type))


def get_string_slot_type(type, nodetype=None):
    if nodetype is not None and len(nodetype.slottypes) > 0:
        return nodetype.slottypes[type]
    elif type == GEN:
        return "gen"
    elif type == POR:
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
        raise ValueError("Supplied type is not a valid slot type: "+str(type))


def get_numerical_node_type(type, nativemodules=None):
    if type == "Register":
        return REGISTER
    elif type == "Actor":
        return ACTUATOR
    elif type == "Sensor":
        return SENSOR
    elif type == "Activator":
        return ACTIVATOR
    elif type == "Concept":
        numerictype = CONCEPT
    elif type == "Script":
        return SCRIPT
    elif type == "Pipe":
        return PIPE
    elif type == "Trigger":
        return TRIGGER
    elif nativemodules is not None and type in nativemodules:
        return MAX_STD_NODETYPE + 1 + sorted(nativemodules).index(type)
    else:
        raise ValueError("Supplied type is not a valid node type: "+str(type))


def get_string_node_type(type, nativemodules=None):
    if type == REGISTER:
        return "Register"
    elif type == ACTUATOR:
        return "Actor"
    elif type == SENSOR:
        return "Sensor"
    elif type == ACTIVATOR:
        return "Activator"
    elif type == CONCEPT:
        return "Concept"
    elif type == SCRIPT:
        return "Script"
    elif type == PIPE:
        return "Pipe"
    elif type == TRIGGER:
        return "Trigger"
    elif nativemodules is not None and len(nativemodules) >= (type - MAX_STD_NODETYPE):
        return sorted(nativemodules)[(type-1) - MAX_STD_NODETYPE]
    else:
        raise ValueError("Supplied type is not a valid node type: "+str(type))


def get_numerical_gatefunction_type(type):
    if type == "identity":
        return GATE_FUNCTION_IDENTITY
    elif type == "abs":
        return GATE_FUNCTION_ABSOLUTE
    elif type == "sigmoid":
        return GATE_FUNCTION_SIGMOID
    elif type == "tanh":
        return GATE_FUNCTION_TANH
    elif type == "rect":
        return GATE_FUNCTION_RECT
    elif type == "dist":
        return GATE_FUNCTION_DIST
    else:
        raise ValueError("Supplied gatefunction type is not a valid type: "+str(type))


def get_string_gatefunction_type(type):
    if type == GATE_FUNCTION_IDENTITY:
        return "identity"
    elif type == GATE_FUNCTION_ABSOLUTE:
        return "abs"
    elif type == GATE_FUNCTION_SIGMOID:
        return "sigmoid"
    elif type == GATE_FUNCTION_TANH:
        return "tanh"
    elif type == GATE_FUNCTION_RECT:
        return "rect"
    elif type == GATE_FUNCTION_DIST:
        return "dist"
    else:
        raise ValueError("Supplied gatefunction type is not a valid type: "+str(type))


def get_elements_per_type(type, nativemodules=None):
    if type == REGISTER:
        return 1
    elif type == SENSOR:
        return 1
    elif type == ACTUATOR:
        return 1
    elif type == ACTIVATOR:
        return 1
    elif type == CONCEPT:
        return 7
    elif type == SCRIPT:
        return 7
    elif type == PIPE:
        return 7
    elif type == TRIGGER:
        return 3
    elif nativemodules is not None and get_string_node_type(type, nativemodules) in nativemodules:
        native_module_definition = nativemodules[get_string_node_type(type, nativemodules)]
        return max(len(native_module_definition.gatetypes), len(native_module_definition.slottypes))
    else:
        raise ValueError("Supplied type is not a valid node type: "+str(type))


def to_id(numericid):
    return "n" + str(int(numericid))


def from_id(stringid):
    return int(stringid[1:])


class TheanoNode(Node):
    """
        theano node proxy class
    """

    _nodenet = None
    _numerictype = 0
    _id = -1

    parameters = None

    def __init__(self, nodenet, uid, type, parameters={}, **_):

        self._numerictype = type
        strtype = get_string_node_type(type, nodenet.native_modules)

        Node.__init__(self, strtype, nodenet.get_nodetype(strtype))

        if strtype in nodenet.native_modules:
            self.slot_activation_snapshot = {}

            if parameters is not None:
                self.parameters = parameters.copy()
            else:
                self.parameters = {}

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
        return self._nodenet.positions.get(self.uid, None)       # todo: get rid of positions

    @position.setter
    def position(self, position):
        if position is None and self.uid in self._nodenet.positions:
            del self._nodenet.positions[self.uid]
        else:
            self._nodenet.positions[self.uid] = position         # todo: get rid of positions

    @property
    def name(self):
        return self._nodenet.names.get(self.uid, self.uid)

    @name.setter
    def name(self, name):
        if name is None or name == "" or name == self.uid:
            if self.uid in self._nodenet.names:
                del self._nodenet.names[self.uid]
        else:
            self._nodenet.names[self.uid] = name

    @property
    def parent_nodespace(self):
        return "Root"           # todo: implement nodespace

    @parent_nodespace.setter
    def parent_nodespace(self, uid):
        pass                    # todo: implement nodespace

    @property
    def activation(self):
        return float(self._nodenet.a.get_value(borrow=True, return_internal_type=True)[self._nodenet.allocated_node_offsets[self._id] + GEN])

    @property
    def activations(self):
        return {"default": self.activation}

    @activation.setter
    def activation(self, activation):
        a_array = self._nodenet.a.get_value(borrow=True, return_internal_type=True)
        a_array[self._nodenet.allocated_node_offsets[self._id] + GEN] = activation
        self._nodenet.a.set_value(a_array, borrow=True)

    def get_gate(self, type):
        return TheanoGate(type, self, self._nodenet)

    def set_gate_parameter(self, gate_type, parameter, value):

        # todo: implement the other gate parameters
        elementindex = self._nodenet.allocated_node_offsets[self._id] + get_numerical_gate_type(gate_type, self.nodetype)
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
        elif parameter == 'gatefunction':
            g_function_selector = self._nodenet.g_function_selector.get_value(borrow=True, return_internal_type=True)
            g_function_selector[elementindex] = get_numerical_gatefunction_type(value)
            self._nodenet.g_function_selector.set_value(g_function_selector, borrow=True)
        elif parameter == 'theta':
            g_theta_array = self._nodenet.g_theta.get_value(borrow=True, return_internal_type=True)
            g_theta_array[elementindex] = value
            self._nodenet.g_theta.set_value(g_theta_array, borrow=True)

    def get_gate_parameters(self):
        # todo: implement defaulting mechanism for gate parameters

        g_threshold_array = self._nodenet.g_threshold.get_value(borrow=True, return_internal_type=True)
        g_amplification_array = self._nodenet.g_amplification.get_value(borrow=True, return_internal_type=True)
        g_min_array = self._nodenet.g_min.get_value(borrow=True, return_internal_type=True)
        g_max_array = self._nodenet.g_max.get_value(borrow=True, return_internal_type=True)
        g_function_selector = self._nodenet.g_function_selector.get_value(borrow=True, return_internal_type=True)
        g_theta = self._nodenet.g_theta.get_value(borrow=True, return_internal_type=True)

        result = {}
        for numericalgate in range(0, get_elements_per_type(self._numerictype, self._nodenet.native_modules)):
            gate_parameters = {
                'threshold': g_threshold_array[self._nodenet.allocated_node_offsets[self._id] + numericalgate],
                'amplification': g_amplification_array[self._nodenet.allocated_node_offsets[self._id] + numericalgate],
                'minimum': g_min_array[self._nodenet.allocated_node_offsets[self._id] + numericalgate],
                'maximum': g_max_array[self._nodenet.allocated_node_offsets[self._id] + numericalgate],
                'gatefunction': get_string_gatefunction_type(g_function_selector[self._nodenet.allocated_node_offsets[self._id] + numericalgate]),
                'theta': g_theta[self._nodenet.allocated_node_offsets[self._id] + numericalgate]
            }
            result[get_string_gate_type(numericalgate, self.nodetype)] = gate_parameters
        return result

    def clone_non_default_gate_parameters(self, gate_type):
        return self.get_gate_parameters()               # todo: implement gate parameter defaulting

    def take_slot_activation_snapshot(self):
        a_array = self._nodenet.a.get_value(borrow=True, return_internal_type=True)
        self.slot_activation_snapshot.clear()
        for slottype in self.nodetype.slottypes:
            self.slot_activation_snapshot[slottype] =  \
                a_array[self._nodenet.allocated_node_offsets[self._id] + get_numerical_slot_type(slottype, self.nodetype)]

    def get_slot(self, type):
        return TheanoSlot(type, self, self._nodenet)

    def get_associated_links(self):
        links = []
        for gatetype in self.nodetype.gatetypes:
            links.extend(self.get_gate(gatetype).get_links())
        return links

    def unlink_completely(self):

        # there's a simpler implementation for this that just clears the
        # node's row and column in the weight matrix. Probably depends on the matrix implementation
        # whether that's actually faster.

        links = self.get_associated_links()
        for slottype in self.nodetype.slottypes:
            links.extend(self.get_slot(slottype).get_links())
        for link in links:
            self._nodenet.delete_link(link.source_node.uid, link.source_gate.type, link.target_node.uid, link.target_slot.type)

    def get_parameter(self, parameter):
        if self.type == "Sensor" and parameter == "datasource":
            return self._nodenet.inverted_sensor_map[self.uid]
        elif self.type == "Actor" and parameter == "datatarget":
            return self._nodenet.inverted_actuator_map[self.uid]
        elif self.type in self._nodenet.native_modules:
            return self.parameters.get(parameter, None)

    def set_parameter(self, parameter, value):
        if self.type == "Sensor" and parameter == "datasource":
            olddatasource = self._nodenet.inverted_sensor_map[self.uid]     # first, clear old data source association
            if self._id in self._nodenet.sensormap.get(olddatasource, []):
                self._nodenet.sensormap.get(olddatasource, []).remove(self._id)

            connectedsensors = self._nodenet.sensormap.get(value, [])       # then, set the new one
            connectedsensors.append(self._id)
            self._nodenet.sensormap[value] = connectedsensors
            self._nodenet.inverted_sensor_map[self.uid] = value
        elif self.type == "Actor" and parameter == "datatarget":
            olddatatarget = self._nodenet.inverted_actuator_map[self.uid]     # first, clear old data target association
            if self._id in self._nodenet.actuatormap.get(olddatatarget, []):
                self._nodenet.actuatormap.get(olddatatarget, []).remove(self._id)

            connectedactuators = self._nodenet.actuatormap.get(value, [])       # then, set the new one
            connectedactuators.append(self._id)
            self._nodenet.actuatormap[value] = connectedactuators
            self._nodenet.inverted_actuator_map[self.uid] = value
        elif self.type in self._nodenet.native_modules:
            self.parameters[parameter] = value

    def clone_parameters(self):
        parameters = {}
        if self.type == "Sensor":
            parameters['datasource'] = self._nodenet.inverted_sensor_map[self.uid]
        elif self.type == "Actor":
            parameters['datatarget'] = self._nodenet.inverted_actuator_map[self.uid]
        elif self.type in self._nodenet.native_modules:
            parameters = self.parameters.copy()
            for parameter in self.nodetype.parameters:
                if parameter not in parameters:
                    if parameter in self.nodetype.parameter_values:
                        parameters[parameter] = self.nodetype.parameter_values[parameter]
                    else:
                        parameters[parameter] = None

        return parameters

    def get_state(self, state):
        return None             # todo: implement node state

    def set_state(self, state, value):
        pass                    # todo: implement node state

    def clone_state(self):
        return {}               # todo: implement node state

    def clone_sheaves(self):
        return {"default": dict(uid="default", name="default", activation=self.activation)}  # todo: implement sheaves

    def node_function(self):
        try:
            self.nodetype.nodefunction(netapi=self._nodenet.netapi, node=self, sheaf="default")
        except Exception:
            self._nodenet.is_active = False
            #self.activation = -1
            raise


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
        w_matrix = self.__nodenet.w.get_value(borrow=True, return_internal_type=True)
        gatecolumn = w_matrix[:, self.__nodenet.allocated_node_offsets[from_id(self.__node.uid)] + self.__numerictype]
        return len(np.nonzero(gatecolumn)[0]) == 0

    @property
    def activation(self):
        return float(self.__nodenet.a.get_value(borrow=True, return_internal_type=True)[self.__nodenet.allocated_node_offsets[from_id(self.__node.uid)] + self.__numerictype])

    @activation.setter
    def activation(self, value):
        a_array = self.__nodenet.a.get_value(borrow=True, return_internal_type=True)
        a_array[self.__nodenet.allocated_node_offsets[from_id(self.__node.uid)] + self.__numerictype] = value
        self.__nodenet.a.set_value(a_array, borrow=True)

    @property
    def activations(self):
        return {'default': self.activation}  # todo: implement sheaves

    def __init__(self, type, node, nodenet):
        self.__type = type
        self.__node = node
        self.__nodenet = nodenet
        self.__numerictype = get_numerical_gate_type(type, node.nodetype)

    def get_links(self):
        links = []
        w_matrix = self.__nodenet.w.get_value(borrow=True, return_internal_type=True)
        gatecolumn = w_matrix[:, self.__nodenet.allocated_node_offsets[from_id(self.__node.uid)] + self.__numerictype]
        links_indices = np.nonzero(gatecolumn)[0]
        for index in links_indices:
            target_uid = self.__nodenet.allocated_elements_to_nodes[index]
            target_slot_numerical = index - self.__nodenet.allocated_node_offsets[target_uid]
            weight = gatecolumn[index]
            if self.__nodenet.sparse:               # sparse matrices return matrices of dimension (1,1) as values
                weight = float(weight.data)
            target_node = self.__nodenet.get_node(to_id(target_uid))
            target_slot = target_node.get_slot(get_string_slot_type(target_slot_numerical, target_node.nodetype))
            link = TheanoLink(self.__node, self, target_node, target_slot, weight)
            links.append(link)
        return links

    def get_parameter(self, parameter_name):
        return self.__node.get_gate_parameters(self.__type)[parameter_name]

    def clone_sheaves(self):
        return {"default": dict(uid="default", name="default", activation=self.activation)}  # todo: implement sheaves

    def gate_function(self, input_activation, sheaf="default"):
        # in the theano implementation, this will only be called for native module gates, and simply write
        # the value back to the activation vector for the theano math to take over
        self.activation = input_activation

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
        w_matrix = self.__nodenet.w.get_value(borrow=True, return_internal_type=True)
        slotrow = w_matrix[self.__nodenet.allocated_node_offsets[from_id(self.__node.uid)] + self.__numerictype]
        return len(np.nonzero(slotrow)[1]) == 0

    @property
    def activation(self):
        return self.__node.slot_activation_snapshot[self.__type]

    @property
    def activations(self):
        return {
            "default": self.activation
        }

    def __init__(self, type, node, nodenet):
        self.__type = type
        self.__node = node
        self.__nodenet = nodenet
        self.__numerictype = get_numerical_slot_type(type, node.nodetype)

    def get_activation(self, sheaf="default"):
        return self.activation

    def get_links(self):
        links = []
        w_matrix = self.__nodenet.w.get_value(borrow=True, return_internal_type=True)
        slotrow = w_matrix[self.__nodenet.allocated_node_offsets[from_id(self.__node.uid)] + self.__numerictype]
        links_indices = np.nonzero(slotrow)[1]
        for index in links_indices:
            source_uid = self.__nodenet.allocated_elements_to_nodes[index]
            source_gate_numerical = index - self.__nodenet.allocated_node_offsets[source_uid]
            weight = slotrow[: , index]
            if self.__nodenet.sparse:               # sparse matrices return matrices of dimension (1,1) as values
                weight = float(weight.data)
            source_node = self.__nodenet.get_node(to_id(source_uid))
            source_gate = source_node.get_gate(get_string_gate_type(source_gate_numerical, source_node.nodetype))
            link = TheanoLink(source_node, source_gate, self.__node, self, weight)
            links.append(link)
        return links
