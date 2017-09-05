# -*- coding: utf-8 -*-

import os
import numpy as np

from micropsi_core.nodenet.node import Node, Gate, Slot, HighdimensionalNodetype
from micropsi_core.nodenet.theano_engine.theano_link import TheanoLink
from micropsi_core.nodenet.theano_engine.theano_stepoperators import *
from micropsi_core.nodenet.theano_engine.theano_definitions import *


class TheanoNode(Node):
    """
        theano node proxy class
    """

    def __init__(self, nodenet, partition, parent_uid, uid, numerictype, parameters={}, **_):

        self._numerictype = numerictype
        self._id = node_from_id(uid)
        self._uid = uid
        self._parent_id = nodespace_from_id(parent_uid)
        self._partition = partition
        self._state = {}

        self.__gatecache = {}
        self.__slotcache = {}

        self.parameters = None
        strtype = get_string_node_type(numerictype, nodenet.native_modules)

        Node.__init__(self, nodenet, strtype, nodenet.get_nodetype(strtype))

        self.is_highdimensional = type(self._nodetype) == HighdimensionalNodetype

        self.datafile = os.path.join(nodenet.persistency_path, '%s_node_%s.npz' % (self._nodenet.uid, self.uid))

        if strtype in nodenet.native_modules or strtype == "Comment":
            self.slot_activation_snapshot = {}
            self.take_slot_activation_snapshot()
            self._state = {}

            if parameters is not None:
                self.parameters = parameters.copy()
            else:
                self.parameters = {}

            if self.is_highdimensional:
                self.slot_fat_snapshot = None

    @property
    def uid(self):
        return self._uid

    @property
    def pid(self):
        return self._partition.pid

    @property
    def index(self):
        return self._id

    @index.setter
    def index(self, index):
        raise NotImplementedError("index can not be set in theano_engine")

    @property
    def position(self):
        return self._nodenet.positions.get(self.uid, [10, 10, 0])

    @position.setter
    def position(self, position):
        if position is None and self.uid in self._nodenet.positions:
            del self._nodenet.positions[self.uid]
        else:
            position = list(position)
            position = (position + [0] * 3)[:3]
            self._nodenet.positions[self.uid] = position
        self._partition.node_changed(self.uid)

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
        return nodespace_to_id(self._parent_id, self._partition.pid)

    @property
    def activation(self):
        return float(self._partition.a.get_value(borrow=True)[self._partition.allocated_node_offsets[self._id] + GEN])

    @activation.setter
    def activation(self, activation):
        a_array = self._partition.a.get_value(borrow=True)
        a_array[self._partition.allocated_node_offsets[self._id] + GEN] = activation
        self._partition.a.set_value(a_array, borrow=True)

    def get_data(self, complete=False, include_links=True):
        nspace = {
            self._partition.spid: [self._parent_id]
        }
        data = self._partition.get_node_data(nodespaces_by_partition=nspace, ids=[self._id], complete=complete, include_links=include_links)[0][self.uid]
        return data

    def get_gate(self, type):
        if type not in self.__gatecache:
            if type not in self.get_gate_types():
                return None
            self.__gatecache[type] = TheanoGate(type, self, self._nodenet, self._partition)
        return self.__gatecache[type]

    # def get_gatefunction_names(self):
    #     result = {}
    #     g_function_selector = self._partition.g_function_selector.get_value(borrow=True)
    #     for numericalgate in range(0, get_gates_per_type(self._numerictype, self._nodenet.native_modules)):
    #         result[get_string_gate_type(numericalgate, self.nodetype)] = \
    #             get_string_gatefunction_type(g_function_selector[self._partition.allocated_node_offsets[self._id] + numericalgate])
    #     return result

    def get_gate_configuration(self, gate_type=None):
        g_function_selector = self._partition.g_function_selector.get_value(borrow=True)
        offset = self._partition.allocated_node_offsets[self._id]
        indexes = []
        gate_types = self.get_gate_types()
        if gate_type is None:
            indexes = [offset + get_numerical_gate_type(gate, self.nodetype) for gate in gate_types]
        else:
            indexes = [offset + get_numerical_gate_type(gate_type, self.nodetype)]

        data = {}
        for i, elementindex in enumerate(indexes):
            gfunc = g_function_selector[elementindex]
            if gfunc != GATE_FUNCTION_IDENTITY:
                data[gate_types[i]] = {
                    'gatefunction': get_string_gatefunction_type(gfunc),
                    'gatefunction_parameters': {}
                }
                if gfunc == GATE_FUNCTION_SIGMOID or gfunc == GATE_FUNCTION_ELU or gfunc == GATE_FUNCTION_RELU:
                    g_bias = self._partition.g_bias.get_value(borrow=True)
                    data[gate_types[i]]['gatefunction_parameters'] = {'bias': g_bias[elementindex]}
                elif gfunc == GATE_FUNCTION_THRESHOLD:
                    g_min = self._partition.g_min.get_value(borrow=True)
                    g_max = self._partition.g_max.get_value(borrow=True)
                    g_amplification = self._partition.g_amplification.get_value(borrow=True)
                    g_threshold = self._partition.g_threshold.get_value(borrow=True)
                    data[gate_types[i]]['gatefunction_parameters'] = {
                        'minimum': g_min[elementindex],
                        'maximum': g_max[elementindex],
                        'amplification': g_amplification[elementindex],
                        'threshold': g_threshold[elementindex]
                    }

        if gate_type is None:
            return data
        else:
            return data[gate_type]

    def set_gate_configuration(self, gate_type, gatefunction, gatefunction_parameters={}):
        elementindex = self._partition.allocated_node_offsets[self._id] + get_numerical_gate_type(gate_type, self.nodetype)
        self._partition._set_gate_config_for_elements([elementindex], gatefunction)
        for param, value in gatefunction_parameters.items():
            self._partition._set_gate_config_for_elements([elementindex], gatefunction, param, [value])

    def take_slot_activation_snapshot(self):
        a_array = self._partition.a.get_value(borrow=True)
        self.slot_activation_snapshot.clear()
        if self.is_highdimensional:
            start = self._partition.allocated_node_offsets[self._id]
            end = start + len(self._nodetype.slottypes)
            self.slot_fat_snapshot = np.array(a_array[start:end])
        else:
            for slottype in self.nodetype.slottypes:
                self.slot_activation_snapshot[slottype] =  \
                    a_array[self._partition.allocated_node_offsets[self._id] + get_numerical_slot_type(slottype, self.nodetype)]

    def get_slot(self, type):
        if type not in self.__slotcache:
            self.__slotcache[type] = TheanoSlot(type, self, self._nodenet, self._partition)
        return self.__slotcache[type]

    def unlink_completely(self):
        self._partition.unlink_node_completely(self._id)
        if self.uid in self._nodenet.proxycache:
            del self._nodenet.proxycache[self.uid]

    def unlink(self, gate_name=None, target_node_uid=None, slot_name=None):
        for gate_name_candidate in self.nodetype.gatetypes:
            if gate_name is None or gate_name == gate_name_candidate:
                for link_candidate in self.get_gate(gate_name_candidate).get_links():
                    if target_node_uid is None or target_node_uid == link_candidate.target_node.uid:
                        if slot_name is None or slot_name == link_candidate.target_slot.type:
                            self._nodenet.delete_link(self.uid, gate_name_candidate, link_candidate.target_node.uid, link_candidate.target_slot.type)

    def get_associated_node_uids(self):
        numeric_ids_in_same_partition = self._partition.get_associated_node_ids(self._id)
        ids = [node_to_id(id, self._partition.pid) for id in numeric_ids_in_same_partition]

        # find this node in links coming in from other partitions to this node's partition
        for partition_from_spid, inlinks in self._partition.inlinks.items():
            for numeric_slot in range(0, get_slots_per_type(self._numerictype, self._nodenet.native_modules)):
                element = self._partition.allocated_node_offsets[self._id] + numeric_slot
                from_elements = inlinks[0].get_value(borrow=True)
                to_elements = inlinks[1].get_value(borrow=True)
                if element in to_elements:
                    inlink_type = inlinks[4]
                    from_partition = self._nodenet.partitions[partition_from_spid]
                    element_index = np.where(to_elements == element)[0][0]

                    if inlink_type == "dense":
                        weights = inlinks[2].get_value(borrow=True)
                        slotrow = weights[element_index]
                        links_indices = np.nonzero(slotrow)[0]
                    elif inlink_type == "identity":
                        links_indices = [element_index]

                    for link_index in links_indices:
                        source_id = from_partition.allocated_elements_to_nodes[from_elements[link_index]]
                        ids.append(node_to_id(source_id, from_partition.pid))

        # find this node in links going out to other partitions
        for partition_to_spid, to_partition in self._nodenet.partitions.items():
            if self._partition.spid in to_partition.inlinks:
                for numeric_gate in range(0, get_gates_per_type(self._numerictype, self._nodenet.native_modules)):
                    element = self._partition.allocated_node_offsets[self._id] + numeric_gate
                    inlinks = to_partition.inlinks[self._partition.spid]
                    from_elements = inlinks[0].get_value(borrow=True)
                    to_elements = inlinks[1].get_value(borrow=True)
                    inlink_type = inlinks[4]

                    if element in from_elements:
                        element_index = np.where(from_elements == element)[0][0]

                        if inlink_type == "dense":
                            weights = inlinks[2].get_value(borrow=True)
                            gatecolumn = weights[:, element_index]
                            links_indices = np.nonzero(gatecolumn)[0]
                        elif inlink_type == "identity":
                            links_indices = [element_index]

                        for link_index in links_indices:
                            target_id = to_partition.allocated_elements_to_nodes[to_elements[link_index]]
                            ids.append(node_to_id(target_id, to_partition.pid))

        return ids

    def get_parameter(self, parameter):
        if self.type in self._nodenet.native_modules:
            return self.parameters.get(parameter, self.nodetype.parameter_defaults.get(parameter, None))
        else:
            return self.clone_parameters().get(parameter, None)

    def set_parameter(self, parameter, value):
        if value == '' or value is None:
            if parameter in self.nodetype.parameter_defaults:
                value = self.nodetype.parameter_defaults[parameter]
            else:
                value = None
        if self.type == "Sensor" and parameter == "datasource":
            if value is not None and value != "":
                datasources = self._nodenet.get_datasources()
                sensor_element = self._partition.allocated_node_offsets[self._id] + GEN
                old_datasource_index = np.where(self._partition.sensor_indices == sensor_element)[0]

                self._partition.sensor_indices[old_datasource_index] = -1
                if value not in datasources:
                    self.logger.warning("Datasource %s not known, will not be assigned." % value)
                    return

                datasource_index = datasources.index(value)

                if self._partition.sensor_indices[datasource_index] != sensor_element and \
                        self._partition.sensor_indices[datasource_index] > 0:

                    other_sensor_element = self._partition.sensor_indices[datasource_index]
                    other_sensor_id = node_to_id(self._partition.allocated_elements_to_nodes[other_sensor_element], self._partition.pid)

                    self.logger.warning("Datasource %s had already been assigned to sensor %s, which will now be unassigned." % (value, other_sensor_id))

                self._nodenet.sensormap[value] = self.uid
                self._partition.sensor_indices[datasource_index] = sensor_element

                if self.name is None or self.name == "" or self.name == self.uid:
                    self.name = value

        elif self.type == "Actuator" and parameter == "datatarget":
            if value is not None and value != "":
                datatargets = self._nodenet.get_datatargets()
                actuator_element = self._partition.allocated_node_offsets[self._id] + GEN
                old_datatarget_index = np.where(self._partition.actuator_indices == actuator_element)[0]
                self._partition.actuator_indices[old_datatarget_index] = -1
                if value not in datatargets:
                    self.logger.warning("Datatarget %s not known, will not be assigned." % value)
                    return

                datatarget_index = datatargets.index(value)

                if self._partition.actuator_indices[datatarget_index] != actuator_element and \
                        self._partition.actuator_indices[datatarget_index] > 0:

                    other_actuator_element = self._partition.actuator_indices[datatarget_index]
                    other_actuator_id = node_to_id(self._partition.allocated_elements_to_nodes[other_actuator_element], self._partition.pid)

                    self.logger.warning("Datatarget %s had already been assigned to actuator %s, which will now be unassigned." % (value, other_actuator_id))

                self._nodenet.actuatormap[value] = self.uid
                self._partition.actuator_indices[datatarget_index] = actuator_element

                if self.name is None or self.name == "" or self.name == self.uid:
                    self.name = value

        elif self.type == "Activator" and parameter == "type":
            if value != "sampling":
                self._nodenet.set_nodespace_gatetype_activator(self.parent_nodespace, value, self.uid)
            else:
                self._nodenet.set_nodespace_sampling_activator(self.parent_nodespace, self.uid)
        elif self.type == "Pipe" and parameter == "expectation":
            g_expect_array = self._partition.g_expect.get_value(borrow=True)
            g_expect_array[self._partition.allocated_node_offsets[self._id] + get_numerical_gate_type("gen")] = float(value)
            g_expect_array[self._partition.allocated_node_offsets[self._id] + get_numerical_gate_type("sur")] = float(value)
            g_expect_array[self._partition.allocated_node_offsets[self._id] + get_numerical_gate_type("por")] = float(value)
            self._partition.g_expect.set_value(g_expect_array, borrow=True)
        elif self.type == "Pipe" and parameter == "wait":
            g_wait_array = self._partition.g_wait.get_value(borrow=True)
            g_wait_array[self._partition.allocated_node_offsets[self._id] + get_numerical_gate_type("sur")] = int(value)
            g_wait_array[self._partition.allocated_node_offsets[self._id] + get_numerical_gate_type("por")] = int(value)
            self._partition.g_wait.set_value(g_wait_array, borrow=True)
        elif self.type == "Comment" and parameter == "comment":
            self.parameters[parameter] = value
        elif self.type in self._nodenet.native_modules:
            if parameter in self.nodetype.parameters:
                self.parameters[parameter] = value
            else:
                raise NameError("Parameter %s not defined for node %s" % (parameter, str(self)))

    def clear_parameter(self, parameter):
        if self.type in self._nodenet.native_modules and parameter in self.parameters:
            del self.parameters[parameter]

    def clone_parameters(self):
        parameters = {}
        if self.type == "Sensor":
            sensor_element = self._partition.allocated_node_offsets[self._id] + GEN
            datasource_index = np.where(self._partition.sensor_indices == sensor_element)[0]
            if len(datasource_index) == 0:
                parameters['datasource'] = None
            else:
                parameters['datasource'] = self._nodenet.get_datasources()[datasource_index[0]]
        elif self.type == "Actuator":
            actuator_element = self._partition.allocated_node_offsets[self._id] + GEN
            datatarget_index = np.where(self._partition.actuator_indices == actuator_element)[0]
            if len(datatarget_index) == 0:
                parameters['datatarget'] = None
            else:
                parameters['datatarget'] = self._nodenet.get_datatargets()[datatarget_index[0]]
        elif self.type == "Activator":
            activator_type = None
            if self._id in self._partition.allocated_nodespaces_por_activators:
                activator_type = "por"
            elif self._id in self._partition.allocated_nodespaces_ret_activators:
                activator_type = "ret"
            elif self._id in self._partition.allocated_nodespaces_sub_activators:
                activator_type = "sub"
            elif self._id in self._partition.allocated_nodespaces_sur_activators:
                activator_type = "sur"
            elif self._id in self._partition.allocated_nodespaces_cat_activators:
                activator_type = "cat"
            elif self._id in self._partition.allocated_nodespaces_exp_activators:
                activator_type = "exp"
            elif self._id in self._partition.allocated_nodespaces_sampling_activators:
                activator_type = "sampling"
            parameters['type'] = activator_type
        elif self.type == "Pipe":
            g_expect_array = self._partition.g_expect.get_value(borrow=True)
            value = g_expect_array[self._partition.allocated_node_offsets[self._id] + get_numerical_gate_type("sur")].item()
            parameters['expectation'] = value
            g_wait_array = self._partition.g_wait.get_value(borrow=True)
            parameters['wait'] = g_wait_array[self._partition.allocated_node_offsets[self._id] + get_numerical_gate_type("sur")].item()
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

    def _pluck_apart_state(self, state, numpy_elements):
        if isinstance(state, dict):
            result = dict()
            for key, value in state.items():
                result[key] = self._pluck_apart_state(value, numpy_elements)
        elif isinstance(state, list):
            result = []
            for value in state:
                result.append(self._pluck_apart_state(value, numpy_elements))
        elif isinstance(state, tuple):
            raise ValueError("Tuples in node states are not supported")
        elif isinstance(state, np.ndarray):
            result = "__numpyelement__" + str(id(state))
            numpy_elements[result] = state
        else:
            return state

        return result

    def _put_together_state(self, state, numpy_elements):
        if isinstance(state, dict):
            result = dict()
            for key, value in state.items():
                result[key] = self._put_together_state(value, numpy_elements)
        elif isinstance(state, list):
            result = []
            for value in state:
                result.append(self._put_together_state(value, numpy_elements))
        elif isinstance(state, str) and state.startswith("__numpyelement__"):
            result = numpy_elements[state]
        else:
            return state

        return result

    def get_persistable_state(self):
        """
        Returns a tuple of dicts, the first one containing json-serializable state information
        and the second one containing numpy elements that should be persisted into an npz.
        The json-seriazable dict will contain special values that act as keys for the second dict.
        This allows to save nested numpy state.
        set_persistable_state knows how to unserialize from the returned tuple.
        """
        numpy_elements = dict()
        json_state = self._pluck_apart_state(self._state, numpy_elements)

        return json_state, numpy_elements

    def set_persistable_state(self, json_state, numpy_elements):
        """
        Sets this node's state from a tuple created with get_persistable_state,
        essentially nesting numpy objects back into the state dict where it belongs
        """
        self._state = self._put_together_state(json_state, numpy_elements)

    def node_function(self):
        try:
            params = self.clone_parameters()
            self.nodetype.nodefunction(netapi=self._nodenet.netapi, node=self, **params)
        except Exception:
            self._nodenet.is_active = False
            if self.nodetype is not None and self.nodetype.nodefunction is None:
                self.logger.warning("No nodefunction found for nodetype %s. Node function definition is: %s" % (self.nodetype.name, self.nodetype.nodefunction_definition))
            else:
                raise

    def get_slot_activations(self, slot_type=None):
        """ Returns a numpy array of the slot activations of a highdimensional
        native module. You can optional give a high-level gatetype to recieve
        only activations of an highdimensional slot type """
        if self.is_highdimensional:
            if self.slot_fat_snapshot is None:
                self.take_slot_activation_snapshot()
            if slot_type:
                offset = self.nodetype.slotindexes[slot_type]
                length = self.nodetype.dimensionality['slots'].get(slot_type, 1)
                if length == 1:
                    return self.slot_fat_snapshot[offset]
                else:
                    return self.slot_fat_snapshot[offset:offset + length]
            else:
                return self.slot_fat_snapshot
        else:
            if slot_type is None:
                return self.slot_activation_snapshot
            else:
                return self.slot_activation_snapshot[slot_type]

    def set_gate_activations(self, new_activations):
        start = self._partition.allocated_node_offsets[node_from_id(self.uid)]
        end = start + len(self._nodetype.gatetypes)
        a_array = self._partition.a.get_value(borrow=True)
        a_array[start:end] = new_activations
        self._partition.a.set_value(a_array, borrow=True)

    def get_gate_activations(self):
        start = self._partition.allocated_node_offsets[node_from_id(self.uid)]
        end = start + len(self._nodetype.gatetypes)
        a_array = self._partition.a.get_value(borrow=True)
        return a_array[start:end]

    def save_data(self, data):
        np.savez(self.datafile, data=data)

    def load_data(self):
        if os.path.isfile(self.datafile):
            return np.load(self.datafile)['data']


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
        w_matrix = self.__partition.w.get_value(borrow=True)
        gatecolumn = w_matrix[:, self.__partition.allocated_node_offsets[node_from_id(self.__node.uid)] + self.__numerictype]
        return len(np.nonzero(gatecolumn)[0]) == 0

    @property
    def activation(self):
        return float(self.__partition.a.get_value(borrow=True)[self.__partition.allocated_node_offsets[node_from_id(self.__node.uid)] + self.__numerictype])

    @activation.setter
    def activation(self, value):
        a_array = self.__partition.a.get_value(borrow=True)
        a_array[self.__partition.allocated_node_offsets[node_from_id(self.__node.uid)] + self.__numerictype] = value
        self.__partition.a.set_value(a_array, borrow=True)

    def __init__(self, type, node, nodenet, partition):
        self.__type = type
        self.__node = node
        self.__nodenet = nodenet
        self.__partition = partition
        self.__numerictype = get_numerical_gate_type(type, node.nodetype)
        self.__linkcache = None

    def get_links(self):
        if self.__linkcache is None:
            self.__linkcache = []
            w_matrix = self.__partition.w.get_value(borrow=True)
            gatecolumn = w_matrix[:, self.__partition.allocated_node_offsets[node_from_id(self.__node.uid)] + self.__numerictype]
            links_indices = np.nonzero(gatecolumn)[0]
            for index in links_indices:
                target_id = self.__partition.allocated_elements_to_nodes[index]
                target_type = self.__partition.allocated_nodes[target_id]
                target_nodetype = self.__nodenet.get_nodetype(get_string_node_type(target_type, self.__nodenet.native_modules))
                target_slot_numerical = index - self.__partition.allocated_node_offsets[target_id]
                target_slot_type = get_string_slot_type(target_slot_numerical, target_nodetype)
                link = TheanoLink(self.__nodenet, self.__node.uid, self.__type, node_to_id(target_id, self.__partition.pid), target_slot_type)
                self.__linkcache.append(link)

            element = self.__partition.allocated_node_offsets[node_from_id(self.__node.uid)] + self.__numerictype
            # does any of the inlinks in any partition orginate from me?
            for partition_to_spid, to_partition in self.__nodenet.partitions.items():
                if self.__partition.spid in to_partition.inlinks:
                    inlinks = to_partition.inlinks[self.__partition.spid]
                    from_elements = inlinks[0].get_value(borrow=True)
                    to_elements = inlinks[1].get_value(borrow=True)
                    if element in from_elements:
                        element_index = np.where(from_elements == element)[0][0]
                        inlink_type = inlinks[4]
                        if inlink_type == "dense":
                            weights = inlinks[2].get_value(borrow=True)
                            gatecolumn = weights[:, element_index]
                            links_indices = np.nonzero(gatecolumn)[0]
                        elif inlink_type == "identity":
                            links_indices = [element_index]

                        for link_index in links_indices:
                            target_id = to_partition.allocated_elements_to_nodes[to_elements[link_index]]
                            target_type = to_partition.allocated_nodes[target_id]
                            target_slot_numerical = to_elements[link_index] - to_partition.allocated_node_offsets[target_id]
                            target_nodetype = self.__nodenet.get_nodetype(get_string_node_type(target_type, self.__nodenet.native_modules))
                            target_slot_type = get_string_slot_type(target_slot_numerical, target_nodetype)
                            link = TheanoLink(self.__nodenet, self.__node.uid, self.__type, node_to_id(target_id, to_partition.pid), target_slot_type)
                            self.__linkcache.append(link)

        return self.__linkcache

    def invalidate_caches(self):
        self.__linkcache = None

    def gate_function(self, input_activation):
        # in the theano implementation, this will only be called for native module gates, and simply write
        # the value back to the activation vector for the theano math to take over
        self.activation = input_activation


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
        w_matrix = self.__partition.w.get_value(borrow=True)
        slotrow = w_matrix[self.__partition.allocated_node_offsets[node_from_id(self.__node.uid)] + self.__numerictype]
        if self.__partition.sparse:
            return len(np.nonzero(slotrow)[1]) == 0
        else:
            return len(np.nonzero(slotrow)[0]) == 0

    @property
    def activation(self):
        return self.__node.get_slot_activations(self.__type)

    def __init__(self, type, node, nodenet, partition):
        self.__type = type
        self.__node = node
        self.__nodenet = nodenet
        self.__partition = partition
        self.__numerictype = get_numerical_slot_type(type, node.nodetype)
        self.__linkcache = None

    def get_activation(self):
        return self.activation

    def get_links(self):
        if self.__linkcache is None:
            self.__linkcache = []
            w_matrix = self.__partition.w.get_value(borrow=True)
            slotrow = w_matrix[self.__partition.allocated_node_offsets[node_from_id(self.__node.uid)] + self.__numerictype]
            if self.__partition.sparse:
                links_indices = np.nonzero(slotrow)[1]
            else:
                links_indices = np.nonzero(slotrow)[0]
            for index in links_indices:
                source_id = self.__partition.allocated_elements_to_nodes[index]
                source_type = self.__partition.allocated_nodes[source_id]
                source_gate_numerical = index - self.__partition.allocated_node_offsets[source_id]
                source_nodetype = self.__nodenet.get_nodetype(get_string_node_type(source_type, self.__nodenet.native_modules))
                source_gate_type = get_string_gate_type(source_gate_numerical, source_nodetype)
                link = TheanoLink(self.__nodenet, node_to_id(source_id, self.__partition.pid), source_gate_type, self.__node.uid, self.__type)
                self.__linkcache.append(link)

            element = self.__partition.allocated_node_offsets[node_from_id(self.__node.uid)] + self.__numerictype
            for partition_from_spid, inlinks in self.__partition.inlinks.items():
                from_elements = inlinks[0].get_value(borrow=True)
                to_elements = inlinks[1].get_value(borrow=True)
                if element in to_elements:
                    element_index = np.where(to_elements == element)[0][0]
                    inlink_type = inlinks[4]
                    from_partition = self.__nodenet.partitions[partition_from_spid]
                    if inlink_type == "dense":
                        weights = inlinks[2].get_value(borrow=True)
                        slotrow = weights[element_index]
                        links_indices = np.nonzero(slotrow)[0]
                    elif inlink_type == "identity":
                        links_indices = [element_index]

                    for link_index in links_indices:
                        source_id = from_partition.allocated_elements_to_nodes[from_elements[link_index]]
                        source_type = from_partition.allocated_nodes[source_id]
                        source_gate_numerical = from_elements[link_index] - from_partition.allocated_node_offsets[source_id]
                        source_nodetype = self.__nodenet.get_nodetype(get_string_node_type(source_type, self.__nodenet.native_modules))
                        source_gate_type = get_string_gate_type(source_gate_numerical, source_nodetype)
                        link = TheanoLink(self.__nodenet, node_to_id(source_id, from_partition.pid), source_gate_type, self.__node.uid, self.__type)
                        self.__linkcache.append(link)

        return self.__linkcache

    def invalidate_caches(self):
        self.__linkcache = None
