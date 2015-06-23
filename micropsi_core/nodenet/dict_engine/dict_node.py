# -*- coding: utf-8 -*-

"""
Node definition

Gate definition
Slot definition
Nodetype definition

default Nodetypes

"""

import logging
import copy

from micropsi_core.nodenet.node import Node, Gate, Nodetype, Slot
from .dict_link import DictLink
from micropsi_core.nodenet.dict_engine.dict_netentity import NetEntity
import micropsi_core.nodenet.gatefunctions as gatefunctions

__author__ = 'joscha'
__date__ = '09.05.12'


emptySheafElement = dict(uid="default", name="default", activation=0)


class DictNode(NetEntity, Node):
    """A net entity with slots and gates and a node function.

    Node functions are called alternating with the link functions. They process the information in the slots
    and usually call all the gate functions to transmit the activation towards the links.

    Attributes:
        activation: a numeric value (usually between -1 and 1) to indicate its activation. Activation is determined
            by the node function, usually depending on the value of the slots.
        slots: a list of slots (activation inlets)
        gates: a list of gates (activation outlets)
        node_function: a function to be executed whenever the node receives activation
    """

    @property
    def activation(self):
        return self.sheaves['default']['activation']

    @property
    def activations(self):
        return dict((k, v['activation']) for k, v in self.sheaves.items())

    @activation.setter
    def activation(self, activation):
        self.set_sheaf_activation(activation)

    def set_sheaf_activation(self, activation, sheaf="default"):
        sheaves_to_calculate = self.get_sheaves_to_calculate()
        if sheaf not in sheaves_to_calculate:
            raise "Sheaf " + sheaf + " can not be set as it hasn't been propagated to any slot"

        if activation is None:
            activation = 0

        self.sheaves[sheaf]['activation'] = float(activation)
        if 'gen' in self.nodetype.gatetypes:
            self.set_gate_activation('gen', activation, sheaf)

    def __init__(self, nodenet, parent_nodespace, position, state=None, activation=0,
                 name="", type="Concept", uid=None, index=None, parameters=None, gate_parameters=None, gate_activations=None, gate_functions=None, **_):
        if not gate_parameters:
            gate_parameters = {}

        if nodenet.is_node(uid):
            raise KeyError("Node with uid %s already exists" % uid)

        Node.__init__(self, type, nodenet.get_nodetype(type))

        NetEntity.__init__(self, nodenet, parent_nodespace, position,
            name=name, entitytype="nodes", uid=uid, index=index)

        self.__non_default_gate_parameters = {}

        self.__state = {}

        self.__gates = {}
        self.__slots = {}
        self.__gatefunctions = {}
        if gate_functions is None:
            gate_functions = {}
        self.__parameters = dict((key, self.nodetype.parameter_defaults.get(key)) for key in self.nodetype.parameters)
        if parameters is not None:
            for key in parameters:
                if parameters[key] is not None:
                    self.set_parameter(key, parameters[key])

        for gate_name in gate_parameters:
            for key in gate_parameters[gate_name]:
                if gate_parameters[gate_name][key] != self.nodetype.gate_defaults[gate_name].get(key, None):
                    if gate_name not in self.__non_default_gate_parameters:
                        self.__non_default_gate_parameters[gate_name] = {}
                    self.__non_default_gate_parameters[gate_name][key] = gate_parameters[gate_name][key]

        gate_parameters = copy.deepcopy(self.nodetype.gate_defaults)
        for gate_name in gate_parameters:
            if gate_name in self.__non_default_gate_parameters:
                gate_parameters[gate_name].update(self.__non_default_gate_parameters[gate_name])

        gate_parameters_for_validation = copy.deepcopy(gate_parameters)
        for gate_name in gate_parameters_for_validation:
            for key in gate_parameters_for_validation[gate_name]:
                if key in self.nodetype.gate_defaults:
                    try:
                        gate_parameters[gate_name][key] = float(gate_parameters[gate_name][key])
                    except:
                        logging.getLogger('nodenet').warn('Invalid gate parameter value for gate %s, param %s, node %s' % (gate_name, key, self.uid))
                        gate_parameters[gate_name][key] = self.nodetype.gate_defaults[gate_name].get(key, 0)
                else:
                    gate_parameters[gate_name][key] = float(gate_parameters[gate_name][key])

        for gate in self.nodetype.gatetypes:
            if gate not in gate_functions:
                self.__gatefunctions[gate] = gatefunctions.identity
            else:
                self.__gatefunctions[gate] = getattr(gatefunctions, gate_functions[gate])
            if gate_activations is None or gate not in gate_activations:
                sheaves_to_use = None
            else:
                sheaves_to_use = gate_activations[gate]
            self.__gates[gate] = DictGate(gate, self, sheaves=sheaves_to_use, parameters=gate_parameters.get(gate))
        for slot in self.nodetype.slottypes:
            self.__slots[slot] = DictSlot(slot, self)
        if state:
            self.__state = state
        nodenet._register_node(self)
        self.sheaves = {"default": emptySheafElement.copy()}
        self.activation = activation

    def node_function(self):
        """Called whenever the node is activated or active.

        In different node types, different node functions may be used, i.e. override this one.
        Generally, a node function must process the slot activations and call each gate function with
        the result of the slot activations.

        Metaphorically speaking, the node function is the soma of a MicroPsi neuron. It reacts to
        incoming activations in an arbitrarily specific way, and may then excite the outgoing dendrites (gates),
        which transmit activation to other neurons with adaptive synaptic strengths (link weights).
        """

        # call nodefunction of my node type
        if self.nodetype and self.nodetype.nodefunction is not None:

            sheaves_to_calculate = self.get_sheaves_to_calculate()

            # find node activation to carry over
            node_activation_to_carry_over = {}
            for id in self.sheaves:
                if id in sheaves_to_calculate:
                    node_activation_to_carry_over[id] = self.sheaves[id]

            # clear activation states
            for gatename in self.get_gate_types():
                gate = self.get_gate(gatename)
                gate.sheaves = {}
            self.sheaves = {}

            # calculate activation states for all open sheaves
            for sheaf_id in sheaves_to_calculate:

                # prepare sheaves
                for gatename in self.get_gate_types():
                    gate = self.get_gate(gatename)
                    gate.sheaves[sheaf_id] = sheaves_to_calculate[sheaf_id].copy()
                if sheaf_id in node_activation_to_carry_over:
                    self.sheaves[sheaf_id] = node_activation_to_carry_over[sheaf_id].copy()
                    self.set_sheaf_activation(node_activation_to_carry_over[sheaf_id]['activation'], sheaf_id)
                else:
                    self.sheaves[sheaf_id] = sheaves_to_calculate[sheaf_id].copy()
                    self.set_sheaf_activation(0, sheaf_id)

            # and actually calculate new values for them
            for sheaf_id in sheaves_to_calculate:

                try:
                    self.nodetype.nodefunction(netapi=self.nodenet.netapi, node=self, sheaf=sheaf_id, **self.__parameters)
                except Exception:
                    self.nodenet.is_active = False
                    self.activation = -1
                    raise
        else:
            # default node function (only using the "default" sheaf)
            if len(self.get_slot_types()):
                self.activation = sum([self.get_slot(slot).activation for slot in self.get_slot_types()])
                if len(self.get_gate_types()):
                    for gatetype in self.get_gate_types():
                        self.get_gate(gatetype).gate_function(self.activation)

    def get_gate(self, gatename):
        try:
            return self.__gates[gatename]
        except KeyError:
            return None

    def get_slot(self, slotname):
        try:
            return self.__slots[slotname]
        except KeyError:
            return None

    def set_gate_activation(self, gatetype, activation, sheaf="default"):
        """ sets the activation of the given gate"""
        activation = float(activation)
        gate = self.get_gate(gatetype)
        if gate is not None:
            gate.sheaves[sheaf]['activation'] = activation

    def get_sheaves_to_calculate(self):
        sheaves_to_calculate = {}
        for slotname in self.get_slot_types():
            for uid in self.get_slot(slotname).sheaves:
                sheaves_to_calculate[uid] = self.get_slot(slotname).sheaves[uid].copy()
                sheaves_to_calculate[uid]['activation'] = 0
        if 'default' not in sheaves_to_calculate:
            sheaves_to_calculate['default'] = emptySheafElement.copy()
        return sheaves_to_calculate

    def get_gate_parameters(self):
        """Looks into the gates and returns gate parameters if these are defined"""
        gate_parameters = {}
        for gatetype in self.get_gate_types():
            if self.get_gate(gatetype).parameters:
                gate_parameters[gatetype] = self.get_gate(gatetype).parameters
        if len(gate_parameters):
            return gate_parameters
        else:
            return None

    def clone_non_default_gate_parameters(self, gate_type=None):
        if gate_type is None:
            return self.__non_default_gate_parameters.copy()
        if gate_type not in self.__non_default_gate_parameters:
            return None
        return {
            gate_type: self.__non_default_gate_parameters[gate_type].copy()
        }

    def set_gate_parameter(self, gate_type, parameter, value):
        if self.__non_default_gate_parameters is None:
            self.__non_default_gate_parameters = {}
        if parameter in self.nodetype.gate_defaults[gate_type]:
            if value is None:
                value = self.nodetype.gate_defaults[gate_type][parameter]
            else:
                value = float(value)
            if value != self.nodetype.gate_defaults[gate_type][parameter]:
                if gate_type not in self.__non_default_gate_parameters:
                    self.__non_default_gate_parameters[gate_type] = {}
                self.__non_default_gate_parameters[gate_type][parameter] = value
            elif parameter in self.__non_default_gate_parameters.get(gate_type, {}):
                del self.__non_default_gate_parameters[gate_type][parameter]
        self.get_gate(gate_type).parameters[parameter] = value

    def get_gatefunction(self, gate_type):
        if self.get_gate(gate_type):
            return self.__gatefunctions[gate_type]
        raise KeyError("Wrong Gatetype")

    def get_gatefunction_name(self, gate_type):
        if self.get_gate(gate_type):
            return self.__gatefunctions[gate_type].__name__
        raise KeyError("Wrong Gatetype")

    def set_gatefunction_name(self, gate_type, gatefunction):
        if self.get_gate(gate_type):
            if gatefunction is None:
                self.__gatefunctions[gate_type] = gatefunctions.identity
            elif hasattr(gatefunctions, gatefunction):
                self.__gatefunctions[gate_type] = getattr(gatefunctions, gatefunction)
            else:
                raise NameError("Unknown Gatefunction")
        else:
            raise KeyError("Wrong Gatetype")

    def get_gatefunction_names(self):
        ret = {}
        for key in self.__gatefunctions:
            ret[key] = self.__gatefunctions[key].__name__
        return ret

    def reset_slots(self):
        for slottype in self.get_slot_types():
            self.get_slot(slottype).sheaves = {"default": emptySheafElement.copy()}

    def get_parameter(self, parameter):
        if parameter in self.__parameters:
            return self.__parameters[parameter]
        else:
            return None

    def clear_parameter(self, parameter):
        if parameter in self.__parameters:
            if parameter not in self.nodetype.parameters:
                del self.__parameters[parameter]
            else:
                self.__parameters[parameter] = None

    def set_parameter(self, parameter, value):
        if (value == '' or value is None):
            if parameter in self.nodetype.parameter_defaults:
                value = self.nodetype.parameter_defaults[parameter]
            else:
                value = None
        self.__parameters[parameter] = value

    def clone_parameters(self):
        return self.__parameters.copy()

    def clone_sheaves(self):
        return self.sheaves.copy()

    def get_state(self, state_element):
        if state_element in self.__state:
            return self.__state[state_element]
        else:
            return None

    def set_state(self, state_element, value):
        self.__state[state_element] = value

    def clone_state(self):
        return self.__state.copy()

    def link(self, gate_name, target_node_uid, slot_name, weight=1, certainty=1):
        """Ensures a link exists with the given parameters and returns it
           Only one link between a node/gate and a node/slot can exist, its parameters will be updated with the
           given parameters if a link existed prior to the call of this method
           Will return None if no such link can be created.
        """

        if not self.nodenet.is_node(target_node_uid):
            return None

        target = self.nodenet.get_node(target_node_uid)

        if slot_name not in target.get_slot_types():
            raise ValueError("Node %s has no slot %s" % (target_node_uid, slot_name))

        gate = self.get_gate(gate_name)
        if gate is None:
            raise ValueError("Node %s has no slot %s" % (self.uid, gate_name))
        link = None
        for candidate in gate.get_links():
            if candidate.target_node.uid == target.uid and candidate.target_slot == slot_name:
                link = candidate
                break
        if link is None:
            link = DictLink(self, gate_name, target, slot_name)

        link._set_weight(weight, certainty)
        return link

    def unlink_completely(self):
        """Deletes all links originating from this node or ending at this node"""
        links_to_delete = set()
        for gate_name_candidate in self.get_gate_types():
            for link_candidate in self.get_gate(gate_name_candidate).get_links():
                links_to_delete.add(link_candidate)
        for slot_name_candidate in self.get_slot_types():
            for link_candidate in self.get_slot(slot_name_candidate).get_links():
                links_to_delete.add(link_candidate)
        for link in links_to_delete:
            link.remove()

    def unlink(self, gate_name=None, target_node_uid=None, slot_name=None):
        links_to_delete = set()
        for gate_name_candidate in self.get_gate_types():
            if gate_name is None or gate_name == gate_name_candidate:
                for link_candidate in self.get_gate(gate_name_candidate).get_links():
                    if target_node_uid is None or target_node_uid == link_candidate.target_node.uid:
                        if slot_name is None or slot_name == link_candidate.target_slot.type:
                            links_to_delete.add(link_candidate)
        for link in links_to_delete:
            link.remove()


class DictGate(Gate):
    """The activation outlet of a node. Nodes may have many gates, from which links originate.

    Attributes:
        type: a string that determines the type of the gate
        node: the parent node of the gate
        sheaves: a dict of sheaves this gate initially has to support
        parameters: a dictionary of values used by the gate function
    """

    @property
    def type(self):
        return self.__type

    @property
    def node(self):
        return self.__node

    @property
    def empty(self):
        return len(self.__outgoing) == 0

    @property
    def activation(self):
        return self.sheaves['default']['activation']

    @property
    def activations(self):
        return dict((k, v['activation']) for k, v in self.sheaves.items())

    def __init__(self, type, node, sheaves=None, parameters=None):
        """create a gate.

        Parameters:
            type: a string that refers to a node type
            node: the parent node
            parameters: an optional dictionary of parameters for the gate function
        """
        self.__type = type
        self.__node = node
        if sheaves is None:
            self.sheaves = {"default": emptySheafElement.copy()}
        else:
            self.sheaves = {}
            for key in sheaves:
                self.sheaves[key] = dict(uid=sheaves[key]['uid'], name=sheaves[key]['name'], activation=sheaves[key]['activation'])
        self.__outgoing = {}
        self.parameters = parameters.copy()
        self.monitor = None

    def get_links(self):
        return list(self.__outgoing.values())

    def get_parameter(self, parameter_name):
        return self.parameters[parameter_name]

    def _register_outgoing(self, link):
        self.__outgoing[link.uid] = link

    def _unregister_outgoing(self, link):
        del self.__outgoing[link.uid]

    def clone_sheaves(self):
        return self.sheaves.copy()

    def gate_function(self, input_activation, sheaf="default"):
        """This function sets the activation of the gate.

        The gate function should be called by the node function, and can be replaced by different functions
        if necessary. This default gives a linear function (input * amplification), cut off below a threshold.
        You might want to replace it with a radial basis function, for instance.
        """
        if input_activation is None:
            input_activation = 0

        # check if the current node space has an activator that would prevent the activity of this gate
        nodespace = self.node.nodenet.get_nodespace(self.node.parent_nodespace)
        if nodespace.has_activator(self.type):
            gate_factor = nodespace.get_activator_value(self.type)
        else:
            gate_factor = 1.0
        if gate_factor == 0.0:
            self.sheaves[sheaf]['activation'] = 0
            return 0  # if the gate is closed, we don't need to execute the gate function

        gatefunction = self.__node.get_gatefunction(self.__type)

        if gatefunction:
            activation = gatefunction(input_activation, self.parameters.get('rho', 0), self.parameters.get('theta', 0))
        else:
            activation = input_activation

        if activation * gate_factor < self.parameters['threshold']:
            activation = 0
        else:
            activation = activation * self.parameters["amplification"] * gate_factor

        activation = min(self.parameters["maximum"], max(self.parameters["minimum"], activation))

        self.sheaves[sheaf]['activation'] = activation

        return activation

    def open_sheaf(self, input_activation, sheaf="default"):
        """This function opens a new sheaf and calls the gate function for the newly opened sheaf
        """
        if sheaf is "default":
            sheaf_uid_prefix = "default" + "-"
            sheaf_name_prefix = ""
        else:
            sheaf_uid_prefix = sheaf + "-"
            sheaf_name_prefix = self.sheaves[sheaf]['name'] + "-"

        new_sheaf = dict(uid=sheaf_uid_prefix + self.node.uid, name=sheaf_name_prefix + self.node.name, activation=0)
        self.sheaves[new_sheaf['uid']] = new_sheaf

        self.gate_function(input_activation, new_sheaf['uid'])


class DictSlot(Slot):
    """The entrance of activation into a node. Nodes may have many slots, in which links terminate.

    Attributes:
        type: a string that determines the type of the slot
        node: the parent node of the slot
        activation: a numerical value which is the sum of all incoming activations
        current_step: the simulation step when the slot last received activation
        incoming: a dictionary of incoming links together with the respective activation received by them
    """

    @property
    def type(self):
        return self.__type

    @property
    def node(self):
        return self.__node

    @property
    def empty(self):
        return len(self.__incoming) == 0

    @property
    def activation(self):
        return self.sheaves['default']['activation']

    @property
    def activations(self):
        return dict((k, v['activation']) for k, v in self.sheaves.items())

    def __init__(self, type, node):
        """create a slot.

        Parameters:
            type: a string that refers to the slot type
            node: the parent node
        """
        self.__type = type
        self.__node = node
        self.__incoming = {}
        self.sheaves = {"default": emptySheafElement.copy()}

    def get_activation(self, sheaf="default"):
        if len(self.__incoming) == 0:
            return 0
        if sheaf not in self.sheaves:
            return 0
        return self.sheaves[sheaf]['activation']

    def get_links(self):
        return list(self.__incoming.values())

    def _register_incoming(self, link):
        self.__incoming[link.uid] = link

    def _unregister_incoming(self, link):
        del self.__incoming[link.uid]
