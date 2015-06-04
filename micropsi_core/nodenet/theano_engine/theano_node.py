# -*- coding: utf-8 -*-

from micropsi_core.nodenet.node import Node, Gate, Slot
from micropsi_core.nodenet.theano_engine.theano_link import TheanoLink
from micropsi_core.nodenet.theano_engine.theano_stepoperators import *
from micropsi_core.nodenet.theano_engine.theano_definitions import *
from micropsi_core.nodenet.theano_engine import theano_nodespace as nodespace
import numpy as np


class TheanoNode(Node):
    """
        theano node proxy class
    """

    def __init__(self, nodenet, parent_uid, uid, type, parameters={}, **_):

        self._numerictype = type
        self._id = node_from_id(uid)
        self._uid = uid
        self._parent_id = nodespace_from_id(parent_uid)
        self._nodenet = nodenet
        self._state = {}

        self.parameters = None

        strtype = get_string_node_type(type, nodenet.native_modules)

        Node.__init__(self, strtype, nodenet.get_nodetype(strtype))

        if strtype in nodenet.native_modules or strtype == "Comment":
            self.slot_activation_snapshot = {}
            self._state = {}

            if parameters is not None:
                self.parameters = parameters.copy()
            else:
                self.parameters = {}

    @property
    def uid(self):
        return self._uid

    @property
    def index(self):
        return self._id

    @index.setter
    def index(self, index):
        raise NotImplementedError("index can not be set in theano_engine")

    @property
    def position(self):
        return self._nodenet.positions.get(self.uid, (10,10))

    @position.setter
    def position(self, position):
        if position is None and self.uid in self._nodenet.positions:
            del self._nodenet.positions[self.uid]
        else:
            self._nodenet.positions[self.uid] = position

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
        return nodespace_to_id(self._parent_id)

    @parent_nodespace.setter
    def parent_nodespace(self, uid):
        self._nodenet.allocated_node_parents[self._id] = nodespace_from_id(uid)

    @property
    def activation(self):
        return float(self._nodenet.a.get_value(borrow=True)[self._nodenet.allocated_node_offsets[self._id] + GEN])

    @property
    def activations(self):
        return {"default": self.activation}

    @activation.setter
    def activation(self, activation):
        a_array = self._nodenet.a.get_value(borrow=True)
        a_array[self._nodenet.allocated_node_offsets[self._id] + GEN] = activation
        self._nodenet.a.set_value(a_array, borrow=True)

    def get_gate(self, type):
        return TheanoGate(type, self, self._nodenet)

    def set_gatefunction_name(self, gate_type, gatefunction_name):
        elementindex = self._nodenet.allocated_node_offsets[self._id] + get_numerical_gate_type(gate_type, self.nodetype)
        g_function_selector = self._nodenet.g_function_selector.get_value(borrow=True)
        g_function_selector[elementindex] = get_numerical_gatefunction_type(gatefunction_name)
        self._nodenet.g_function_selector.set_value(g_function_selector, borrow=True)
        if g_function_selector[elementindex] == GATE_FUNCTION_ABSOLUTE:
            self._nodenet.has_gatefunction_absolute = True
        elif g_function_selector[elementindex] == GATE_FUNCTION_SIGMOID:
            self._nodenet.has_gatefunction_sigmoid = True
        elif g_function_selector[elementindex] == GATE_FUNCTION_TANH:
            self._nodenet.has_gatefunction_tanh = True
        elif g_function_selector[elementindex] == GATE_FUNCTION_RECT:
            self._nodenet.has_gatefunction_rect = True
        elif g_function_selector[elementindex] == GATE_FUNCTION_DIST:
            self._nodenet.has_gatefunction_one_over_x = True

    def get_gatefunction_name(self, gate_type):
        g_function_selector = self._nodenet.g_function_selector.get_value(borrow=True)
        return get_string_gatefunction_type(g_function_selector[self._nodenet.allocated_node_offsets[self._id] + get_numerical_gate_type(gate_type, self.nodetype)])

    def get_gatefunction_names(self):
        result = {}
        g_function_selector = self._nodenet.g_function_selector.get_value(borrow=True)
        for numericalgate in range(0, get_gates_per_type(self._numerictype, self._nodenet.native_modules)):
            result[get_string_gate_type(numericalgate, self.nodetype)] = \
                get_string_gatefunction_type(g_function_selector[self._nodenet.allocated_node_offsets[self._id] + numericalgate])
        return result

    def set_gate_parameter(self, gate_type, parameter, value):

        elementindex = self._nodenet.allocated_node_offsets[self._id] + get_numerical_gate_type(gate_type, self.nodetype)
        if parameter == 'threshold':
            g_threshold_array = self._nodenet.g_threshold.get_value(borrow=True)
            g_threshold_array[elementindex] = value
            self._nodenet.g_threshold.set_value(g_threshold_array, borrow=True)
        elif parameter == 'amplification':
            g_amplification_array = self._nodenet.g_amplification.get_value(borrow=True)
            g_amplification_array[elementindex] = value
            self._nodenet.g_amplification.set_value(g_amplification_array, borrow=True)
        elif parameter == 'minimum':
            g_min_array = self._nodenet.g_min.get_value(borrow=True)
            g_min_array[elementindex] = value
            self._nodenet.g_min.set_value(g_min_array, borrow=True)
        elif parameter == 'maximum':
            g_max_array = self._nodenet.g_max.get_value(borrow=True)
            g_max_array[elementindex] = value
            self._nodenet.g_max.set_value(g_max_array, borrow=True)
        elif parameter == 'theta':
            g_theta_array = self._nodenet.g_theta.get_value(borrow=True)
            g_theta_array[elementindex] = value
            self._nodenet.g_theta.set_value(g_theta_array, borrow=True)

    def get_gate_parameters(self):
        return self.clone_non_default_gate_parameters()

    def clone_non_default_gate_parameters(self, gate_type=None):
        g_threshold_array = self._nodenet.g_threshold.get_value(borrow=True)
        g_amplification_array = self._nodenet.g_amplification.get_value(borrow=True)
        g_min_array = self._nodenet.g_min.get_value(borrow=True)
        g_max_array = self._nodenet.g_max.get_value(borrow=True)
        g_theta = self._nodenet.g_theta.get_value(borrow=True)

        gatemap = {}
        gate_types = self.nodetype.gate_defaults.keys()
        if gate_type is not None:
            if gate_type in gate_types:
                gate_types = [gate_type]
            else:
                return None

        for gate_type in gate_types:
            numericalgate = get_numerical_gate_type(gate_type, self.nodetype)
            gate_parameters = {}

            threshold = g_threshold_array[self._nodenet.allocated_node_offsets[self._id] + numericalgate].item()
            if 'threshold' not in self.nodetype.gate_defaults[gate_type] or threshold != self.nodetype.gate_defaults[gate_type]['threshold']:
                gate_parameters['threshold'] = threshold

            amplification = g_amplification_array[self._nodenet.allocated_node_offsets[self._id] + numericalgate].item()
            if 'amplification' not in self.nodetype.gate_defaults[gate_type] or amplification != self.nodetype.gate_defaults[gate_type]['amplification']:
                gate_parameters['amplification'] = amplification

            minimum = g_min_array[self._nodenet.allocated_node_offsets[self._id] + numericalgate].item()
            if 'minimum' not in self.nodetype.gate_defaults[gate_type] or minimum != self.nodetype.gate_defaults[gate_type]['minimum']:
                gate_parameters['minimum'] = minimum

            maximum = g_max_array[self._nodenet.allocated_node_offsets[self._id] + numericalgate].item()
            if 'maximum' not in self.nodetype.gate_defaults[gate_type] or maximum != self.nodetype.gate_defaults[gate_type]['maximum']:
                gate_parameters['maximum'] = maximum

            theta = g_theta[self._nodenet.allocated_node_offsets[self._id] + numericalgate].item()
            if 'theta' not in self.nodetype.gate_defaults[gate_type] or theta != self.nodetype.gate_defaults[gate_type]['theta']:
                gate_parameters['theta'] = theta

            if not len(gate_parameters) == 0:
                gatemap[gate_type] = gate_parameters

        return gatemap

    def take_slot_activation_snapshot(self):
        a_array = self._nodenet.a.get_value(borrow=True)
        self.slot_activation_snapshot.clear()
        for slottype in self.nodetype.slottypes:
            self.slot_activation_snapshot[slottype] =  \
                a_array[self._nodenet.allocated_node_offsets[self._id] + get_numerical_slot_type(slottype, self.nodetype)]

    def get_slot(self, type):
        return TheanoSlot(type, self, self._nodenet)

    def unlink_completely(self):

        # there's a simpler implementation for this that just clears the
        # node's row and column in the weight matrix. Probably depends on the matrix implementation
        # whether that's actually faster.

        links = self.get_associated_links()
        for slottype in self.nodetype.slottypes:
            links.extend(self.get_slot(slottype).get_links())
        for link in links:
            self._nodenet.delete_link(link.source_node.uid, link.source_gate.type, link.target_node.uid, link.target_slot.type)

    def unlink(self, gate_name=None, target_node_uid=None, slot_name=None):
        for gate_name_candidate in self.nodetype.gatetypes:
            if gate_name is None or gate_name == gate_name_candidate:
                for link_candidate in self.get_gate(gate_name_candidate).get_links():
                    if target_node_uid is None or target_node_uid == link_candidate.target_node.uid:
                        if slot_name is None or slot_name == link_candidate.target_slot.type:
                            self._nodenet.delete_link(self.uid, gate_name_candidate, link_candidate.target_node.uid, link_candidate.target_slot.type)

    def get_parameter(self, parameter):
        return self.clone_parameters().get(parameter, None)

    def set_parameter(self, parameter, value):
        if value == '' or value is None:
            if parameter in self.nodetype.parameter_defaults:
                value = self.nodetype.parameter_defaults[parameter]
            else:
                value = None
        if self.type == "Sensor" and parameter == "datasource":
            if self.uid in self._nodenet.inverted_sensor_map:
                olddatasource = self._nodenet.inverted_sensor_map[self.uid]     # first, clear old data source association
                if self._id in self._nodenet.sensormap.get(olddatasource, []):
                    self._nodenet.sensormap.get(olddatasource, []).remove(self._id)

            connectedsensors = self._nodenet.sensormap.get(value, [])       # then, set the new one
            connectedsensors.append(self._id)
            self._nodenet.sensormap[value] = connectedsensors
            self._nodenet.inverted_sensor_map[self.uid] = value
        elif self.type == "Actor" and parameter == "datatarget":
            if self.uid in self._nodenet.inverted_actuator_map:
                olddatatarget = self._nodenet.inverted_actuator_map[self.uid]     # first, clear old data target association
                if self._id in self._nodenet.actuatormap.get(olddatatarget, []):
                    self._nodenet.actuatormap.get(olddatatarget, []).remove(self._id)

            connectedactuators = self._nodenet.actuatormap.get(value, [])       # then, set the new one
            connectedactuators.append(self._id)
            self._nodenet.actuatormap[value] = connectedactuators
            self._nodenet.inverted_actuator_map[self.uid] = value
        elif self.type == "Activator" and parameter == "type":
            self._nodenet.set_nodespace_gatetype_activator(self.parent_nodespace, value, self.uid)
        elif self.type == "Pipe" and parameter == "expectation":
            g_expect_array = self._nodenet.g_expect.get_value(borrow=True)
            g_expect_array[self._nodenet.allocated_node_offsets[self._id] + get_numerical_gate_type("sur")] = float(value)
            g_expect_array[self._nodenet.allocated_node_offsets[self._id] + get_numerical_gate_type("por")] = float(value)
            self._nodenet.g_expect.set_value(g_expect_array, borrow=True)
        elif self.type == "Pipe" and parameter == "wait":
            g_wait_array = self._nodenet.g_wait.get_value(borrow=True)
            g_wait_array[self._nodenet.allocated_node_offsets[self._id] + get_numerical_gate_type("sur")] = min(int(value), 128)
            g_wait_array[self._nodenet.allocated_node_offsets[self._id] + get_numerical_gate_type("por")] = min(int(value), 128)
            self._nodenet.g_wait.set_value(g_wait_array, borrow=True)
        elif self.type == "Comment" and parameter == "comment":
            self.parameters[parameter] = value
        elif self.type in self._nodenet.native_modules:
            self.parameters[parameter] = value

    def clear_parameter(self, parameter):
        if self.type in self._nodenet.native_modules and parameter in self.parameters:
            del self.parameters[parameter]

    def clone_parameters(self):
        parameters = {}
        if self.type == "Sensor":
            parameters['datasource'] = self._nodenet.inverted_sensor_map.get(self.uid, None)
        elif self.type == "Actor":
            parameters['datatarget'] = self._nodenet.inverted_actuator_map.get(self.uid, None)
        elif self.type == "Activator":
            activator_type = None
            if self._id in self._nodenet.allocated_nodespaces_por_activators:
                activator_type = "por"
            elif self._id in self._nodenet.allocated_nodespaces_ret_activators:
                activator_type = "ret"
            elif self._id in self._nodenet.allocated_nodespaces_sub_activators:
                activator_type = "sub"
            elif self._id in self._nodenet.allocated_nodespaces_sur_activators:
                activator_type = "sur"
            elif self._id in self._nodenet.allocated_nodespaces_cat_activators:
                activator_type = "cat"
            elif self._id in self._nodenet.allocated_nodespaces_exp_activators:
                activator_type = "exp"
            parameters['type'] = activator_type
        elif self.type == "Pipe":
            g_expect_array = self._nodenet.g_expect.get_value(borrow=True)
            value = g_expect_array[self._nodenet.allocated_node_offsets[self._id] + get_numerical_gate_type("sur")].item()
            parameters['expectation'] = value
            g_wait_array = self._nodenet.g_wait.get_value(borrow=True)
            parameters['wait'] = g_wait_array[self._nodenet.allocated_node_offsets[self._id] + get_numerical_gate_type("sur")].item()
        elif self.type == "Comment":
            parameters['comment'] = self.parameters['comment']
        elif self.type in self._nodenet.native_modules:
            # handle the defined ones, the ones with defaults and value ranges
            for parameter in self.nodetype.parameters:
                value = None
                if parameter in self.parameters:
                    value = self.parameters[parameter]
                elif parameter in self.nodetype.parameter_defaults:
                    value = self.nodetype.parameter_defaults[parameter]
                parameters[parameter] = value
            # see if something else has been set and return, if so
            for parameter in self.parameters:
                if parameter not in parameters:
                    parameters[parameter] = self.parameters[parameter]

        return parameters

    def get_state(self, state):
        return self._state.get(state)

    def set_state(self, state, value):
        if isinstance(value, np.floating):
            value = float(value)
        self._state[state] = value

    def clone_state(self):
        if self._numerictype > MAX_STD_NODETYPE:
            return self._state.copy()
        else:
            return None

    def clone_sheaves(self):
        return {"default": dict(uid="default", name="default", activation=self.activation)}  # todo: implement sheaves

    def node_function(self):
        try:
            self.nodetype.nodefunction(netapi=self._nodenet.netapi, node=self, sheaf="default", **self.clone_parameters())
        except Exception:
            self._nodenet.is_active = False
            # self.activation = -1
            raise


class TheanoGate(Gate):
    """
        theano gate proxy clas
    """

    @property
    def type(self):
        return self.__type

    @property
    def node(self):
        return self.__node

    @property
    def empty(self):
        w_matrix = self.__nodenet.w.get_value(borrow=True)
        gatecolumn = w_matrix[:, self.__nodenet.allocated_node_offsets[node_from_id(self.__node.uid)] + self.__numerictype]
        return len(np.nonzero(gatecolumn)[0]) == 0

    @property
    def activation(self):
        return float(self.__nodenet.a.get_value(borrow=True)[self.__nodenet.allocated_node_offsets[node_from_id(self.__node.uid)] + self.__numerictype])

    @activation.setter
    def activation(self, value):
        a_array = self.__nodenet.a.get_value(borrow=True)
        a_array[self.__nodenet.allocated_node_offsets[node_from_id(self.__node.uid)] + self.__numerictype] = value
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
        w_matrix = self.__nodenet.w.get_value(borrow=True)
        gatecolumn = w_matrix[:, self.__nodenet.allocated_node_offsets[node_from_id(self.__node.uid)] + self.__numerictype]
        links_indices = np.nonzero(gatecolumn)[0]
        for index in links_indices:
            target_id = self.__nodenet.allocated_elements_to_nodes[index]
            target_type = self.__nodenet.allocated_nodes[target_id]
            target_nodetype = self.__nodenet.get_nodetype(get_string_node_type(target_type, self.__nodenet.native_modules))
            target_slot_numerical = index - self.__nodenet.allocated_node_offsets[target_id]
            target_slot_type = get_string_slot_type(target_slot_numerical, target_nodetype)
            linkid = "%s:%s:%s:n%i" % (self.node.uid, self.__type, target_slot_type, target_id)
            if linkid in self.__nodenet.proxycache:
                links.append(self.__nodenet.proxycache[linkid])
            else:
                link = TheanoLink(self.__nodenet, self.__node.uid, self.__type, node_to_id(target_id), target_slot_type)
                self.__nodenet.proxycache[link.uid] = link
                links.append(link)
        return links

    def get_parameter(self, parameter_name):
        gate_parameters = self.__node.nodetype.gate_defaults[self.type]
        gate_parameters.update(self.__node.clone_non_default_gate_parameters(self.type))
        return gate_parameters[parameter_name]

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

    @property
    def type(self):
        return self.__type

    @property
    def node(self):
        return self.__node

    @property
    def empty(self):
        w_matrix = self.__nodenet.w.get_value(borrow=True)
        slotrow = w_matrix[self.__nodenet.allocated_node_offsets[node_from_id(self.__node.uid)] + self.__numerictype]
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
        w_matrix = self.__nodenet.w.get_value(borrow=True)
        slotrow = w_matrix[self.__nodenet.allocated_node_offsets[node_from_id(self.__node.uid)] + self.__numerictype]
        if self.__nodenet.sparse:
            links_indices = np.nonzero(slotrow)[1]
        else:
            links_indices = np.nonzero(slotrow)[0]
        for index in links_indices:
            source_id = self.__nodenet.allocated_elements_to_nodes[index]
            source_type = self.__nodenet.allocated_nodes[source_id]
            source_gate_numerical = index - self.__nodenet.allocated_node_offsets[source_id]
            source_nodetype = self.__nodenet.get_nodetype(get_string_node_type(source_type, self.__nodenet.native_modules))
            source_gate_type = get_string_gate_type(source_gate_numerical, source_nodetype)
            linkid = "n%i:%s:%s:%s" % (source_id, source_gate_type, self.__type, self.node.uid)
            if linkid in self.__nodenet.proxycache:
                links.append(self.__nodenet.proxycache[linkid])
            else:
                link = TheanoLink(self.__nodenet, node_to_id(source_id), source_gate_type, self.__node.uid, self.__type)
                self.__nodenet.proxycache[link.uid] = link
                links.append(link)
        return links
