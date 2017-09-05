# -*- coding: utf-8 -*-

"""
Node definition

Gate definition
Slot definition
Nodetype definition

default Nodetypes

"""

from micropsi_core.nodenet.node import Node, Gate, Slot
from .dict_link import DictLink
from micropsi_core.nodenet.dict_engine.dict_netentity import NetEntity
import micropsi_core.nodenet.gatefunctions as gatefunctions

__author__ = 'joscha'
__date__ = '09.05.12'


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
    def position(self):
        return self.__position

    @position.setter
    def position(self, position):
        position = list(position)
        position = (position + [0] * 3)[:3]
        self.__position = position
        self.last_changed = self.nodenet.current_step

    @property
    def activation(self):
        return self.__activation

    @activation.setter
    def activation(self, activation):
        #activation_to_set = float(activation)
        #gengate = self.get_gate('gen')
        #if gengate is not None:
        #    activation_to_set = gengate.gate_function(float(activation))
        #self.__activation = activation_to_set
        self.__activation = float(activation)
        gengate = self.get_gate('gen')
        if gengate is not None:
            gengate.activation = float(activation)

    def __init__(self, nodenet, parent_nodespace, position, state=None, activation=0,
                 name="", type="Concept", uid=None, index=None, parameters=None, gate_activations=None, gate_configuration=None, **_):

        if nodenet.is_node(uid):
            raise KeyError("Node with uid %s already exists" % uid)

        Node.__init__(self, nodenet, type, nodenet.get_nodetype(type))

        NetEntity.__init__(self, nodenet, parent_nodespace,
            name=name, entitytype="nodes", uid=uid, index=index)

        self.position = position

        self.__state = {}
        self.__activation = 0

        self.__gates = {}
        self.__slots = {}
        self._gate_configuration = gate_configuration or {}

        self.__parameters = dict((key, self.nodetype.parameter_defaults.get(key)) for key in self.nodetype.parameters)
        if parameters is not None:
            for key in parameters:
                if parameters[key] is not None and key in self.nodetype.parameters:
                    self.set_parameter(key, parameters[key])

        for gate in self.nodetype.gatetypes:
            self.__gates[gate] = DictGate(gate, self)
        for slot in self.nodetype.slottypes:
            self.__slots[slot] = DictSlot(slot, self)
        if state:
            self.__state = state
        nodenet._register_node(self)
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

            # clear activation states
            for gatename in self.get_gate_types():
                gate = self.get_gate(gatename)
                gate.__activation = 0

            #call node function
            try:
                params = self.clone_parameters()
                self.nodetype.nodefunction(netapi=self.nodenet.netapi, node=self, **params)
            except Exception:
                self.nodenet.is_active = False
                self.activation = -1
                raise
        else:
            # default node function
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

    def set_gate_activation(self, gatetype, activation):
        """ sets the activation of the given gate"""
        if gatetype == 'gen':
            self.activation = float(activation)
        gate = self.get_gate(gatetype)
        if gate is not None:
            gate.activation = activation

    def set_gate_configuration(self, gate_type, gatefunction, gatefunction_parameters={}):
        gatefuncs = self.nodenet.get_available_gatefunctions()
        if gatefunction == 'identity' or gatefunction is None:
            self._gate_configuration.pop(gate_type, None)
        elif gatefunction in gatefuncs:
            for param, default in gatefuncs[gatefunction].items():
                if param not in gatefunction_parameters:
                    gatefunction_parameters[param] = default
            self._gate_configuration[gate_type] = {
                'gatefunction': gatefunction,
                'gatefunction_parameters': gatefunction_parameters
            }
        else:
            raise NameError("Unknown Gatefunction")

    def get_gate_configuration(self, gate_type=None):
        if gate_type is None:
            return self._gate_configuration
        elif self.get_gate(gate_type):
            if gate_type in self._gate_configuration:
                return self._gate_configuration[gate_type]
            else:
                return {
                    'gatefunction': 'identity',
                    'gatefunction_parameters': {}
                }
        else:
            raise KeyError("Wrong Gatetype")

    def reset_slots(self):
        for slottype in self.get_slot_types():
            self.get_slot(slottype).reset()

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
        if parameter in self.nodetype.parameters:
            self.__parameters[parameter] = value
        else:
            raise NameError("Parameter %s not defined for node %s" % (parameter, str(self)))

    def clone_parameters(self):
        return self.__parameters.copy()

    def get_state(self, state_element):
        if state_element in self.__state:
            return self.__state[state_element]
        else:
            return None

    def set_state(self, state_element, value):
        self.__state[state_element] = value

    def clone_state(self):
        return self.__state.copy()

    def link(self, gate_name, target_node_uid, slot_name, weight=1):
        """Ensures a link exists with the given weight and returns it
           Only one link between a node/gate and a node/slot can exist, its weight will be updated with the
           given value if a link existed prior to the call of this method
           Will return None if no such link can be created.
        """

        if not self.nodenet.is_node(target_node_uid):
            return None

        target = self.nodenet.get_node(target_node_uid)

        self.last_changed = self.nodenet.current_step
        target.last_changed = self.nodenet.current_step
        self.nodenet.get_nodespace(self.parent_nodespace).contents_last_changed = self.nodenet.current_step
        self.nodenet.get_nodespace(target.parent_nodespace).contents_last_changed = self.nodenet.current_step

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

        link._set_weight(weight)
        return link

    def unlink_completely(self):
        """Deletes all links originating from this node or ending at this node"""
        self.last_changed = self.nodenet.current_step
        self.nodenet.get_nodespace(self.parent_nodespace).contents_last_changed = self.nodenet.current_step

        links_to_delete = set()
        for gate_name_candidate in self.get_gate_types():
            for link_candidate in self.get_gate(gate_name_candidate).get_links():
                links_to_delete.add(link_candidate)
        for slot_name_candidate in self.get_slot_types():
            for link_candidate in self.get_slot(slot_name_candidate).get_links():
                links_to_delete.add(link_candidate)
        for link in links_to_delete:
            link.target_node.last_changed = self.nodenet.current_step
            self.nodenet.get_nodespace(link.target_node.parent_nodespace).contents_last_changed = self.nodenet.current_step
            link.remove()

    def unlink(self, gate_name=None, target_node_uid=None, slot_name=None):
        self.last_changed = self.nodenet.current_step
        self.nodenet.get_nodespace(self.parent_nodespace).contents_last_changed = self.nodenet.current_step

        links_to_delete = set()
        for gate_name_candidate in self.get_gate_types():
            if gate_name is None or gate_name == gate_name_candidate:
                for link_candidate in self.get_gate(gate_name_candidate).get_links():
                    if target_node_uid is None or target_node_uid == link_candidate.target_node.uid:
                        if slot_name is None or slot_name == link_candidate.target_slot.type:
                            links_to_delete.add(link_candidate)
        for link in links_to_delete:
            link.target_node.last_changed = self.nodenet.current_step
            self.nodenet.get_nodespace(link.target_node.parent_nodespace).contents_last_changed = self.nodenet.current_step
            link.remove()


class DictGate(Gate):
    """The activation outlet of a node. Nodes may have many gates, from which links originate.

    Attributes:
        type: a string that determines the type of the gate
        node: the parent node of the gate
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
        return self.__activation

    @activation.setter
    def activation(self, activation):
        self.__activation = activation

    def __init__(self, type, node):
        """create a gate.

        Parameters:
            type: a string that refers to a node type
            node: the parent node
        """
        self.__type = type
        self.__node = node
        self.__activation = 0
        self.__outgoing = {}
        self.monitor = None

    def get_links(self):
        return list(self.__outgoing.values())

    def get_parameter(self, parameter_name):
        return self.parameters[parameter_name]

    def _register_outgoing(self, link):
        self.__outgoing[link.signature] = link

    def _unregister_outgoing(self, link):
        del self.__outgoing[link.signature]

    def gate_function(self, input_activation):
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
            self.__activation = 0.0
            return 0  # if the gate is closed, we don't need to execute the gate function

        config = self.__node.get_gate_configuration(self.__type)

        gatefunction = getattr(gatefunctions, config['gatefunction'])

        self.__activation = gate_factor * gatefunction(input_activation, **config['gatefunction_parameters'])

        return self.__activation


class DictSlot(Slot):
    """The entrance of activation into a node. Nodes may have many slots, in which links terminate.

    Attributes:
        type: a string that determines the type of the slot
        node: the parent node of the slot
        activation: a numerical value which is the sum of all incoming activations
        current_step: the calculation step when the slot last received activation
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
        return self.__activation

    def __init__(self, type, node):
        """create a slot.

        Parameters:
            type: a string that refers to the slot type
            node: the parent node
        """
        self.__type = type
        self.__node = node
        self.__incoming = {}
        self.__activation = 0

    def add_activation(self, activation):
        self.__activation += activation

    def reset(self):
        self.__activation = 0

    def get_activation(self):
        if len(self.__incoming) == 0:
            return 0
        return self.__activation

    def get_links(self):
        return list(self.__incoming.values())

    def _register_incoming(self, link):
        self.__incoming[link.signature] = link

    def _unregister_incoming(self, link):
        del self.__incoming[link.signature]
