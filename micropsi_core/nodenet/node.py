# -*- coding: utf-8 -*-

"""
Node definition

Gate definition
Slot definition
Nodetype definition

default Nodetypes

"""

from abc import ABCMeta, abstractmethod

import micropsi_core.tools

__author__ = 'joscha'
__date__ = '09.05.12'


class Node(metaclass=ABCMeta):
    """
    Abstract base class for node implementations.
    """

    @property
    @abstractmethod
    def uid(self):
        """
        The uid of this node
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def index(self):
        """
        The index property of this node. Index properties are used for persistent sorting information.
        """
        pass  # pragma: no cover

    @index.setter
    @abstractmethod
    def index(self, index):
        """
        Sets the index property of this node. Index properties are used for persistent sorting information.
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def position(self):
        """
        This node's 3D coordinates within its nodespace
        """
        # todo: persistent 3D coordinates are likely to be made non-persistent or stored elsewhere
        pass  # pragma: no cover

    @position.setter
    @abstractmethod
    def position(self, position):
        """
        This node's 3D coordinates within its nodespace
        """
        # todo: persistent 3D coordinates are likely to be made non-persistent or stored elsewhere
        pass  # pragma: no cover

    @property
    @abstractmethod
    def name(self):
        """
        This node's human readable name for display purposes. Returns the UID if no human readable name has been set.
        """
        pass  # pragma: no cover

    @name.setter
    @abstractmethod
    def name(self, name):
        """
        Sets this node's human readable name for display purposes.
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def parent_nodespace(self):
        """
        The UID of this node's parent nodespace
        """
        pass  # pragma: no cover

    @parent_nodespace.setter
    @abstractmethod
    def parent_nodespace(self, uid):
        """
        Sets this node's parent nodespace by UID, effectively moving from its old parent space to the new one
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def activation(self):
        """
        This node's activation property as calculated once per step by its node function
        """
        pass  # pragma: no cover

    @activation.setter
    @abstractmethod
    def activation(self, activation):
        """
        Sets this node's activation property, overriding what has been calculated by the node function
        """
        pass  # pragma: no cover

    @property
    def type(self):
        """
        The node's type (as a string)
        """
        return self._nodetype_name

    @property
    def nodetype(self):
        """
        The Nodetype instance for this node
        """
        return self._nodetype

    def __init__(self, nodenet, nodetype_name, nodetype):
        """
        Constructor needs the string name of this node's type, and a Nodetype instance
        """
        self._nodenet = nodenet
        self._nodetype_name = nodetype_name
        self._nodetype = nodetype
        self.logger = nodetype.logger
        self.on_start = lambda x: None
        self.on_stop = lambda x: None

    def get_data(self, complete=False, include_links=True):
        """
        Return this node's json data for the frontend
        """
        data = {
            "name": self.name,
            "position": self.position,
            "parent_nodespace": self.parent_nodespace,
            "type": self.type,
            "parameters": self.clone_parameters(),
            "state": self.get_persistable_state()[0],
            "activation": self.activation,
            "gate_activations": self.construct_gates_dict(),
            "gate_configuration": self.get_gate_configuration()
        }
        data["uid"] = self.uid
        if complete:
            data['index'] = self.index
        if include_links:
            data['links'] = self.construct_links_dict()
        return data

    def construct_links_dict(self):
        """
        Return a dict of links originating at this node
        """
        links = {}
        for key in self.get_gate_types():
            gatelinks = self.get_gate(key).get_links()
            if gatelinks:
                links[key] = [l.get_data() for l in gatelinks]
        return links

    def get_user_prompt(self, key):
        if key not in self._nodetype.user_prompts:
            raise KeyError("Nodetype %s does not define a user_prompt named %s" % (self._nodetype.name, key))
        return self._nodetype.user_prompts[key]

    @abstractmethod
    def get_gate(self, type):
        """
        Returns this node's gate of the given type, or None if no such gate exists
        """
        pass  # pragma: no cover

    @abstractmethod
    def set_gate_configuration(self, gate_type, gatefunction, gatefunction_parameters={}):
        """
        Configures the given gate to use the gatefunction of the given name, with the given parameters
        if gatefunction_name is None, the default "identity" gatefunction is set for the gate
        """
        pass

    @abstractmethod
    def get_gate_configuration(self, gate_type=None):
        """
        Returns a dict specifying the gatefunction and parameters configured for the given gate,
        or all gates if None
        """
        pass

    @abstractmethod
    def get_slot(self, type):
        """
        Returns the slot of the given type or none if no such slot exists
        """
        pass  # pragma: no cover

    @abstractmethod
    def get_parameter(self, parameter):
        """
        Returns the value of a node parameter of None if the parameter is not set.
        Parameters are used to change what a node does and do typically not change between net steps.
        An example is the "type" parameter of directional activators that configures the activator to control
        the gates of type "type"
        """
        pass  # pragma: no cover

    @abstractmethod
    def set_parameter(self, parameter, value):
        """
        Changes the value of the given parameter.
        Parameters are used to change what a node does and do typically not change between net steps.
        An example is the "type" parameter of directional activators that configures the activator to control
        the gates of type "type"
        """
        pass  # pragma: no cover

    @abstractmethod
    def clear_parameter(self, parameter):
        """
        Unsets/clears the given parameter.
        """
        pass  # pragma: no cover

    @abstractmethod
    def clone_parameters(self):
        """
        Returns a copy of this node's parameter set.
        Write access to this dict will not affect the node.
        Parameters are used to change what a node does and do typically not change between net steps.
        An example is the "type" parameter of directional activators that configures the activator to control
        the gates of type "type"
        """
        pass  # pragma: no cover

    def get_state(self, state):
        """
        Returns the value of the given state.
        Node state is runtime-information that can change between net steps.
        A typical use is native modules "attaching" a bit of information to a node for later retrieval.
        Node states are not formally required by the node net specification. They exist for convenience reasons only.
        """
        return self._state.get(state)

    def set_state(self, state, value):
        """
        Sets the value of a given state.
        Node state is runtime-information that can change between net steps.
        A typical use is native modules "attaching" a bit of information to a node for later retrieval.
        Node states are not formally required by the node net specification. They exist for convenience reasons only.
        """
        try:
            import numpy as np
            if isinstance(value, np.floating):
                value = float(value)
        except ImportError:
            pass
        self._state[state] = value

    def clone_state(self):
        """
        Returns a copy of the node's state.
        Write access to this dict will not affect the node.
        Node state is runtime-information that can change between net steps.
        A typical use is native modules "attaching" a bit of information to a node for later retrieval.
        Node states are not formally required by the node net specification. They exist for convenience reasons only.
        """
        return self._state.copy()

    def _pluck_apart_state(self, state, numpy_elements):
        try:
            import numpy as np
        except ImportError:
            return state
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

    @abstractmethod
    def node_function(self):
        """
        The node function of the node, called after activation has been propagated to the node's slots.
        This method is expected to set the node's activation(s) and all of the gates' activations by calling the
        gate_function of all gates.
        Implementations can either directly implement this method based on the type of the node, or implement some
        sort of indirection mechanism that selects the code to be executed.
        For native modules (nodes with non-standard node_functions) that can be reloaded at runtime, this is a must.
        """
        pass  # pragma: no cover

    @abstractmethod
    def unlink_completely(self):
        """
        Deletes all links originating or ending at this node
        """
        pass  # pragma: no cover

    @abstractmethod
    def unlink(self, gate_name=None, target_node_uid=None, slot_name=None):
        """
        Remove links originating from this node.
        All parameters are optional and can be used to limit the links to be removed.
        Parameters:
            gate_name: Only delete links originating at the given gate at this node
            target_node_uid: Only delete links ending at the node with the given uid
            slot_name: Only delete links ending in the given slot atthe target node
        """
        pass  # pragma: no cover

    def get_gate_types(self):
        """
        Returns the types of gates existing in this node
        """
        return list(self.nodetype.gatetypes)

    def get_slot_types(self):
        """
        Returns the types of slots existing in this node
        """
        return list(self.nodetype.slottypes)

    def get_associated_links(self):
        """
        Return a list of all links originating or terminating at this node
        """
        links = []
        for key in self.get_gate_types():
            links.extend(self.get_gate(key).get_links())
        for key in self.get_slot_types():
            links.extend(self.get_slot(key).get_links())
        return links

    def get_associated_node_uids(self):
        """
        Return a list of all node_uids that are linked to this node
        """
        nodes = []
        for link in self.get_associated_links():
            if link.source_node.uid != self.uid:
                nodes.append(link.source_node.uid)
            if link.target_node.uid != self.uid:
                nodes.append(link.target_node.uid)
        return nodes

    def construct_gates_dict(self):
        """
        Return a dict mapping gate-names to gate-activations
        """
        data = {}
        for gate_name in self.get_gate_types():
            data[gate_name] = self.get_gate(gate_name).activation
        return data

    def __repr__(self):
        return "<%s \"%s\" (%s)>" % (self.nodetype.name, self.name, self.uid)


class Gate(metaclass=ABCMeta):
    """
    Activation outlet of nodes, where links (connected to slots on the other side) originate.
    Gate activations are set by the node's node_function through calling gate_function for all of their gates.
    """

    @property
    @abstractmethod
    def type(self):
        """
        Returns the type of the gate (as a string)
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def node(self):
        """
        Returns the Node object that this gate belongs to
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def empty(self):
        """
        Returns true if the gate has no links
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def activation(self):
        """
        Returns the gate's activation
        """
        pass  # pragma: no cover

    @abstractmethod
    def get_links(self):
        """
        Returns a list of Link objects originating from this gate
        """
        pass  # pragma: no cover

    @abstractmethod
    def gate_function(self, input_activation):
        """
        This function sets the activation of the gate.
        This only needs to be implemented if the reference implementation for the node functions from
        nodefunctions.py is being used.

        Alternative implementations are free to calculate gate activation values in node functions directly and
        can pass on the implementation of this method.

        The default gate function should be linear (input * amplification) if over the threshold parameter, plus
        band-passed by the min and max parameters.

        Implementations should allow to define alternative gate functions on a per-nodespace basis, i.e. all
        gates of nodes in a given nodespace should use the same gate function.
        """
        pass  # pragma: no cover

    def __repr__(self):
        return "<Gate %s of node %s>" % (self.type, self.node)


class Slot(metaclass=ABCMeta):
    """
    Activation intake for nodes. Nodes may have many slots, in which links terminate.
    Slot activations are set by the node net's activation propagation logic. They are immediately read (in the same
    net step by node functions.)
    """

    @property
    @abstractmethod
    def type(self):
        """
        Returns the type of the slot (as a string)
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def node(self):
        """
        Returns the Node object that this slot belongs to
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def empty(self):
        """
        Returns true if the slot has no links
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def activation(self):
        """
        Returns the activation in this slot
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def get_activation(self):
        """
        Returns the activation in this slot.
        """
        pass  # pragma: no cover

    @abstractmethod
    def get_links(self):
        """
        Returns a list of Link objects terminating at this slot
        """
        pass  # pragma: no cover

    def __repr__(self):
        return "<Slot %s of node %s>" % (self.type, self.node)


class Nodetype(object):
    """Every node has a type, which is defined by its slot types, gate types, its node function and a list of
    node parameteres."""

    @property
    def parameters(self):
        return self._parameters

    @parameters.setter
    def parameters(self, parameters):
        self._parameters = parameters
        self.nodefunction = self._nodefunction_definition  # update nodefunction

    @property
    def nodefunction_definition(self):
        return self._nodefunction_definition

    @nodefunction_definition.setter
    def nodefunction_definition(self, nodefunction_definition):
        self._nodefunction_definition = nodefunction_definition
        args = ','.join(self.parameters).strip(',')
        try:
            self.nodefunction = micropsi_core.tools.create_function(nodefunction_definition,
                parameters="nodenet, node, " + args)
        except SyntaxError as err:
            self.logger.warning("Syntax error while compiling node function: %s", str(err))
            raise err

    @property
    def nodefunction_name(self):
        return self._nodefunction_name

    def __init__(self, name, nodenet, slottypes=None, gatetypes=None, parameters=None,
                 nodefunction_definition=None, nodefunction_name=None, parameter_values=None,
                 symbol=None, shape=None, engine=None, parameter_defaults=None, path='', category='', user_prompts={}, **_):
        """Initializes or creates a nodetype.

        Arguments:
            name: a unique identifier for this nodetype
            nodenet: the nodenet that this nodetype is part of

        If a nodetype with the same name is already defined in the nodenet, it is overwritten. Parameters that
        are not given here will be taken from the original definition. Thus, you may use this initializer to
        set up the nodetypes after loading new nodenet state (by using it without parameters).
        """
        self._parameters = []
        self._nodefunction_definition = None
        self._nodefunction_name = None
        self.line_number = -1

        self.name = name

        self.slottypes = slottypes or []
        self.gatetypes = gatetypes or []

        self.path = path
        self.category = category
        self.shape = shape
        self.symbol = symbol
        self.logger = nodenet.logger

        self.parameters = parameters or []
        self.parameter_values = parameter_values or {}
        self.parameter_defaults = parameter_defaults or {}

        self.user_prompts = {}
        for key, val in user_prompts.items():
            self.user_prompts[key] = val.copy()

        if nodefunction_definition:
            self.nodefunction_definition = nodefunction_definition
        elif nodefunction_name:
            self._nodefunction_name = nodefunction_name
        else:
            self.nodefunction = None
        self.load_functions()

    def load_functions(self):
        """ Loads nodefunctions and user_prompt callbacks"""
        import os
        from importlib.machinery import SourceFileLoader
        import inspect
        try:
            if self.path and self._nodefunction_name or self.user_prompts.keys():
                modulename = "nodetypes." + self.category.replace('/', '.') + os.path.basename(self.path)[:-3]
                module = SourceFileLoader(modulename, self.path).load_module()
                if self._nodefunction_name:
                    self.nodefunction = getattr(module, self._nodefunction_name)
                    self.line_number = inspect.getsourcelines(self.nodefunction)[1]
                for key, data in self.user_prompts.items():
                    if hasattr(module, data['callback']):
                        self.user_prompts[key]['callback'] = getattr(module, data['callback'])
                    else:
                        self.logger.warning("Callback '%s' for user_prompt %s of nodetype %s not defined" % (data['callback'], key, self.name))
            elif self._nodefunction_name:
                from micropsi_core.nodenet import nodefunctions
                if hasattr(nodefunctions, self._nodefunction_name):
                    self.nodefunction = getattr(nodefunctions, self._nodefunction_name)
                else:
                    self.logger.warning("Can not find definition of nodefunction %s" % self._nodefunction_name)
        except (ImportError, AttributeError) as err:
            self.logger.warning("Import error while importing node definition file of nodetype %s: %s" % (self.name, err))
            raise err

    def get_gate_dimensionality(self, gate):
        return 1

    def get_slot_dimensionality(self, slot):
        return 1

    def get_data(self):
        data = {
            'name': self.name,
            'parameters': self.parameters,
            'parameter_values': self.parameter_values,
            'parameter_defaults': self.parameter_defaults,
            'symbol': self.symbol,
            'shape': self.shape,
            'nodefunction_definition': self.nodefunction_definition,
            'nodefunction_name': self.nodefunction_name,
            'path': self.path,
            'category': self.category,
            'line_number': self.line_number,
            'gatetypes': self.gatetypes,
            'slottypes': self.slottypes
        }
        return data


class FlowNodetype(Nodetype):
    def __init__(self, name, nodenet, slottypes=None, gatetypes=None, parameters=None,
                 nodefunction_definition=None, nodefunction_name=None, parameter_values=None,
                 symbol=None, shape=None, engine=None, parameter_defaults=None, path='', category='',
                 flow_module=True, inputs=None, outputs=None, implementation=None, is_autogenerated=False, **_):
        super().__init__(name, nodenet, slottypes=slottypes, gatetypes=gatetypes, parameters=parameters,
                 nodefunction_definition=nodefunction_definition, nodefunction_name=nodefunction_name, parameter_values=parameter_values,
                 symbol=symbol, shape=shape, engine=engine, parameter_defaults=parameter_defaults, path=path, category=category)
        if is_autogenerated:
            self.slottypes = []
            self.gatetypes = []
        else:
            self.slottypes = ['sub']
            self.gatetypes = ['sur']
        self.is_autogenerated = is_autogenerated
        self.is_flow_module = True
        self.implementation = implementation
        self.inputs = inputs
        self.outputs = outputs

    def get_data(self):
        data = super().get_data()
        data.update({
            'inputs': self.inputs,
            'outputs': self.outputs,
            'implementation': self.implementation,
            'is_autogenerated': self.is_autogenerated
        })
        return data


class HighdimensionalNodetype(Nodetype):
    def __init__(self, name, nodenet, slottypes=None, gatetypes=None, parameters=None,
                 nodefunction_definition=None, nodefunction_name=None, parameter_values=None,
                 symbol=None, shape=None, engine=None, parameter_defaults=None, path='', category='', dimensionality={}, **_):
        super().__init__(name, nodenet, slottypes=slottypes, gatetypes=gatetypes, parameters=parameters,
                 nodefunction_definition=nodefunction_definition, nodefunction_name=nodefunction_name, parameter_values=parameter_values,
                 symbol=symbol, shape=shape, engine=engine, parameter_defaults=parameter_defaults, path=path, category=category)

        self.is_highdimensional = bool(dimensionality)
        if nodenet.engine == "dict_engine" and self.is_highdimensional:
            nodenet.logger.warning("Dict engine does not support high dimensional native_modules")
            self.is_highdimensional = False
            self.dimensionality = {}

        self.gategroups = [("%s0" % g) if dimensionality['gates'].get(g, 1) > 1 else g for g in gatetypes]
        self.slotgroups = [("%s0" % s) if dimensionality['slots'].get(s, 1) > 1 else s for s in slottypes]
        self.dimensionality = dimensionality
        gates = []
        slots = []
        index = 0
        self.slotindexes = {}
        self.gateindexes = {}
        for g in self.gatetypes:
            self.gateindexes[g] = index
            if dimensionality['gates'].get(g, 1) > 1:
                group = ["%s%d" % (g, i) for i in range(dimensionality['gates'][g])]
                gates.extend(group)
                index += dimensionality['gates'][g]
            else:
                gates.append(g)
                index += 1

        index = 0
        for s in self.slottypes:
            self.slotindexes[s] = index
            if dimensionality['slots'].get(s, 1) > 1:
                group = ["%s%d" % (s, i) for i in range(dimensionality['slots'][s])]
                slots.extend(group)
                index += dimensionality['slots'][s]
            else:
                slots.append(s)
                index += 1
        self.gatetypes = gates
        self.slottypes = slots

    def get_gate_dimensionality(self, gate):
        return self.dimensionality.get('gates', {}).get(gate, 1)

    def get_slot_dimensionality(self, slot):
        return self.dimensionality.get('slots', {}).get(slot, 1)

    def get_data(self):
        data = super().get_data()
        data['gatetypes'] = self.gategroups
        data['slottypes'] = self.slotgroups
        data['is_highdimensional'] = True
        data['dimensionality'] = {
            'gates': dict(("%s0" % g, self.dimensionality['gates'][g]) for g in self.dimensionality['gates']),
            'slots': dict(("%s0" % s, self.dimensionality['slots'][s]) for s in self.dimensionality['slots']),
        }
        return data
