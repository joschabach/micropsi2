# -*- coding: utf-8 -*-

"""
Node definition

Gate definition
Slot definition
Nodetype definition

default Nodetypes

"""

import warnings
import logging

import micropsi_core.tools
from micropsi_core.nodenet.node import Node, Nodetype, Gate, Slot
from micropsi_core.nodenet.link import Link
from micropsi_core.nodenet.netentity import NetEntity

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
        if len(self.nodetype.gatetypes):
            self.set_gate_activation(self.nodetype.gatetypes[0], activation, sheaf)

    def __init__(self, nodenet, parent_nodespace, position, state=None, activation=0,
                 name="", type="Concept", uid=None, index=None, parameters=None, gate_parameters=None, gate_activations=None, **_):
        if not gate_parameters:
            gate_parameters = {}

        if nodenet.is_node(uid):
            raise KeyError("Node already exists")

        Node.__init__(self, type, nodenet.get_nodetype(type))

        NetEntity.__init__(self, nodenet, parent_nodespace, position,
            name=name, entitytype="nodes", uid=uid, index=index)

        self.__non_default_gate_parameters = {}

        self.__state = {}

        self.__gates = {}
        self.__slots = {}

        self.__parameters = dict((key, None) for key in self.nodetype.parameters)
        if parameters is not None:
            self.__parameters.update(parameters)

        for gate_name in gate_parameters:
            for key in gate_parameters[gate_name]:
                if gate_parameters[gate_name][key] != self.nodetype.gate_defaults.get(key, None):
                    if gate_name not in self.__non_default_gate_parameters:
                        self.__non_default_gate_parameters[gate_name] = {}
                    self.__non_default_gate_parameters[gate_name][key] = gate_parameters[gate_name][key]

        gate_parameters = self.nodetype.gate_defaults.copy()
        gate_parameters.update(self.__non_default_gate_parameters)
        for gate in self.nodetype.gatetypes:
            if gate_activations is None or gate not in gate_activations:
                sheaves_to_use = None
            else:
                sheaves_to_use = gate_activations[gate]
            self.__gates[gate] = Gate(gate, self, sheaves=sheaves_to_use, gate_function=None, parameters=gate_parameters.get(gate))
        for slot in self.nodetype.slottypes:
            self.__slots[slot] = Slot(slot, self)
        if state:
            self.__state = state
        nodenet._register_node(self)
        self.sheaves = {"default": emptySheafElement.copy()}

        self.activation = 0

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
        
    def clone_non_default_gate_parameters(self):
        return self.__non_default_gate_parameters.copy()

    def set_gate_parameters(self, gate_type, parameters):
        if self.__non_default_gate_parameters is None:
            self.__non_default_gate_parameters = {}
        for parameter, value in parameters.items():
            if parameter in Nodetype.GATE_DEFAULTS:
                if value is None:
                    value = Nodetype.GATE_DEFAULTS[parameter]
                else:
                    value = float(value)
                if value != Nodetype.GATE_DEFAULTS[parameter]:
                    if gate_type not in self.__non_default_gate_parameters:
                        self.__non_default_gate_parameters[gate_type] = {}
                    self.__non_default_gate_parameters[gate_type][parameter] = value
                elif parameter in self.__non_default_gate_parameters.get(gate_type, {}):
                    del self.__non_default_gate_parameters[gate_type][parameter]
            self.get_gate(gate_type).parameters[parameter] = value

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
        self.__parameters[parameter] = value

    def set_parameters(self, parameters):
        for key in parameters:
            self.set_parameter(key, parameters[key])

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
            return None

        gate = self.get_gate(gate_name)
        if gate is None:
            return None
        link = None
        for candidate in gate.get_links():
            if candidate.target_node.uid == target.uid and candidate.target_slot == slot_name:
                link = candidate
                break
        if link is None:
            link = Link(self, gate_name, target, slot_name)

        link.weight = weight
        link.certainty = certainty
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
        """Deletes all links originating from this node or ending at this node"""
        links_to_delete = set()
        for gate_name_candidate in self.get_gate_types():
            if gate_name is None or gate_name == gate_name_candidate:
                for link_candidate in self.get_gate(gate_name_candidate).get_links():
                    if target_node_uid is None or target_node_uid == link_candidate.target_node.uid:
                        if slot_name is None or slot_name == link_candidate.target_slot.type:
                            links_to_delete.add(link_candidate)
        for link in links_to_delete:
            link.remove()