# -*- coding: utf-8 -*-

"""
Nodenet definition
"""

import os
import logging

from datetime import datetime
from threading import Lock
from abc import ABCMeta, abstractmethod

import micropsi_core.tools
from .netapi import NetAPI
from . import monitor
from .node import Nodetype, FlowNodetype, HighdimensionalNodetype
from micropsi_core.nodenet.stepoperators import DoernerianEmotionalModulators
from micropsi_core.nodenet.statuslogger import StatusLogger

__author__ = 'joscha'
__date__ = '09.05.12'


NODENET_VERSION = 2


class NodenetLockException(Exception):
    pass


class Nodenet(metaclass=ABCMeta):

    """
    Nodenet is the abstract base class for all node net implementations and defines the interface towards
    runtime.py, which is where JSON API and tests access node nets.

    This abstract Nodenet class defines handling of node net uid, name, world and worldadapter connections,
    but makes no assumptions on persistency (filesystem, database, memory-only) or implementation.
    """

    @property
    @abstractmethod
    def engine(self):
        """
        Returns the type of node net engine this nodenet is implemented with
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def current_step(self):
        """
        Returns the current net step, an integer
        """
        pass  # pragma: no cover

    @property
    def metadata(self):
        """
        Returns a dict representing the node net meta data.
        """
        data = {
            'uid': self.uid,
            'engine': self.engine,
            'owner': self.owner,
            'name': self.name,
            'is_active': self.is_active,
            'current_step': self.current_step,
            'world': self._world_uid,
            'worldadapter': self._worldadapter_uid,
            'version': self._version,
            'runner_condition': self._runner_condition,
            'use_modulators': self.use_modulators,
            'nodespace_ui_properties': self._nodespace_ui_properties,
            'worldadapter_config': {} if not self.worldadapter_instance else self.worldadapter_instance.config,
            'device_map': {} if not self.worldadapter_instance else self.worldadapter_instance.device_map
        }
        return data

    @property
    def uid(self):
        """
        Returns the uid of the node net
        """
        return self._uid

    @property
    def name(self):
        """
        Returns the name of the node net for display purposes
        """
        if self._name is not None:
            return self._name
        else:
            return self.uid

    @name.setter
    def name(self, name):
        """
        Sets the name of the node net to the given string
        """
        self._name = name

    @property
    def world(self):
        """
        Returns the currently connected world_uid
        """
        return self._world_uid

    @world.setter
    def world(self, world_uid):
        """
        Sets the world_uid of this nodenet
        """
        self._world_uid = world_uid

    @property
    def worldadapter(self):
        """
        Returns the uid of the currently connected world adapter
        """
        return self._worldadapter_uid

    @worldadapter.setter
    def worldadapter(self, worldadapter_uid):
        """
        Sets the worldadapter uid of this nodenet
        """
        self._worldadapter_uid = worldadapter_uid

    @property
    def worldadapter_instance(self):
        """
        Returns the instance of the currently connected world adapter
        """
        return self._worldadapter_instance

    @worldadapter_instance.setter
    def worldadapter_instance(self, _worldadapter_instance):
        """
        Connects the node net to the given worldadapter instance, or disconnects if None is given
        """
        self._worldadapter_instance = _worldadapter_instance
        if self._worldadapter_instance:
            self._worldadapter_instance.nodenet = self

    @property
    def statuslogger(self):
        return self._statuslogger

    def __init__(self, persistency_path, name="", worldadapter="Default", world=None, owner="", uid=None, native_modules={}, use_modulators=True, worldadapter_instance=None, version=None):
        """
        Constructor for the abstract base class, must be called by implementations
        """
        self._uid = uid or micropsi_core.tools.generate_uid()
        self.persistency_path = persistency_path
        self._name = name
        self._world_uid = world
        self._worldadapter_uid = worldadapter if world else None
        self._worldadapter_instance = worldadapter_instance
        if self._worldadapter_instance:
            self._worldadapter_instance.nodenet = self
        self.is_active = False
        self.frequency = 0.0
        self.use_modulators = use_modulators

        self._version = version or NODENET_VERSION  # used to check compatibility of the node net data
        self._uid = uid
        self._runner_condition = None

        self.runner_config = {}
        self.owner = owner
        self._step = 0
        self._monitors = {}
        self._adhoc_monitors = {}
        self._nodespace_ui_properties = {}

        self.netlock = Lock()

        self.logger = logging.getLogger('agent.%s' % self.uid)
        self.logger.info("Setting up nodenet %s with engine %s", self.name, self.engine)

        self.user_prompt = None
        self.user_prompt_response = {}

        self._statuslogger = StatusLogger("agent.%s.status" % self.uid)
        self._create_netapi()

        self.deleted_items = {}
        self.stepping_rate = []
        self.dashboard_values = {}

        self.native_modules = self._load_nodetypes(native_modules)
        self.native_module_instances = {}
        self.native_module_definitions = dict((uid, native_modules[uid]) for uid in self.native_modules)

        self._modulators = {}
        if use_modulators:
            for modulator in DoernerianEmotionalModulators.writeable_modulators + DoernerianEmotionalModulators.readable_modulators:
                self._modulators[modulator] = 1

        if not os.path.isdir(self.persistency_path):
            os.mkdir(self.persistency_path)

        self.initialize_stepoperators()

    def _create_netapi(self):
        self.netapi = NetAPI(self)

    @abstractmethod
    def initialize_stepoperators(self):
        """
        Instantiate Stepoperators
        """
        pass  # pragma: no cover

    def get_data(self, complete=False, include_links=True):
        """
        Returns a dict representing the whole node net.
        Concrete implementations may call this (super) method and then add the following fields if they want to
        use JSON persistency:

        links
        nodes
        nodespaces
        version
        """
        data = self.metadata
        data.update({
            'nodes': {},
            'nodespaces': {},
            'monitors': self.construct_monitors_dict(),
            'modulators': {},
        })
        return data

    def on_start(self):
        self.is_active = True
        for uid, node in self.native_module_instances.items():
            node.on_start(node)

    def on_stop(self):
        self.is_active = False
        for uid, node in self.native_module_instances.items():
            node.on_stop(node)

    def set_user_prompt(self, node, key, message, parameters={}):
        if self.user_prompt is not None:
            raise RuntimeError("Currently only one user prompt per nodenet step supported. node %s already registered one" % str(self.user_prompt['node']))
        else:
            self.user_prompt = {
                'node': node,
                'key': key,
                'msg': message,
                'parameters': parameters
            }
            self.is_active = False

    def consume_user_prompt(self):
        data = self.user_prompt
        if data:
            data['node'] = data['node'].get_data()
        self.user_prompt = None
        return data

    def set_user_prompt_response(self, node_uid, key, parameters):
        node = self.get_node(node_uid)
        node.get_user_prompt(key)['callback'](self.netapi, node, parameters)

    @abstractmethod
    def get_nodes(self, nodespaces=[], node_uids=[], include_links=True, links_to_nodespaces=[]):
        """
        Returns a dict with contents for the given nodespaces
        """
        pass  # pragma: no cover

    @abstractmethod
    def get_links_for_nodes(self, node_uids):
        """
        Returns a tuple consisting of links from/to the given node
        and the nodes that are connected via these links
        """
        pass  # pragma: no cover

    @abstractmethod
    def save(self, base_path=None, zipfile=None):
        """
        Saves the nodenet to persistency.
        Arguments:
            base_path (String) - Save files to a non-standard directory
            zipfile (ZipFile object) - Save the nodenet to a zipfile instead
        """
        pass  # pragma: no cover

    @abstractmethod
    def load(self):
        """
        Loads the node net from the given main metadata json file.
        """
        pass  # pragma: no cover

    def timed_step(self, runner_config={}):
        start = datetime.now()
        self.runner_config = runner_config
        self.step()
        elapsed = datetime.now() - start
        self.stepping_rate.append(elapsed.seconds + ((elapsed.microseconds // 1000) / 1000))
        self.stepping_rate = self.stepping_rate[-100:]

    @abstractmethod
    def step(self):
        """
        Performs one calculation step, propagating activation accross links
        """
        pass  # pragma: no cover

    @abstractmethod
    def get_node(self, uid):
        """
        Returns the Node object with the given UID or None if no such Node object exists
        """
        pass  # pragma: no cover

    @abstractmethod
    def get_node_uids(self, group_nodespace_uid=None, group=None):
        """
        Returns a list of the UIDs of all Node objects that exist in the node net
        If group_nodespace_uid/group parameters are given, all uids of nodes in the given group will be returned
        """
        pass  # pragma: no cover

    @abstractmethod
    def is_node(self, uid):
        """
        Returns true if the given UID is the UID of an existing Node object
        """
        pass  # pragma: no cover

    @abstractmethod
    def create_node(self, nodetype, nodespace_uid, position, name="", uid=None, parameters=None, gate_configuration=None):
        """
        Creates a new node of the given node type (string), in the given nodespace, at the given
        position and returns the uid of the new node
        """
        pass  # pragma: no cover

    @abstractmethod
    def delete_node(self, uid):
        """
        Deletes the node with the given UID.
        """
        pass  # pragma: no cover

    @abstractmethod
    def get_nodespace(self, uid):
        """
        Returns the Nodespace object with the given UID or None if no such Nodespace object exists
        Passing none will return the root nodespace
        """
        pass  # pragma: no cover

    @abstractmethod
    def get_nodespace_uids(self):
        """
        Returns a list of the UIDs of all Nodespace objects that exist in the node net
        """
        pass  # pragma: no cover

    @abstractmethod
    def is_nodespace(self, uid):
        """
        Returns true if the given UID is the UID of an existing Nodespace object
        """
        pass  # pragma: no cover

    def set_nodespace_properties(self, nodespace_uid, data):
        """
        Sets a persistent property for UI purposes for the given nodespace
        """
        nodespace_uid = self.get_nodespace(nodespace_uid).uid
        if nodespace_uid not in self._nodespace_ui_properties:
            self._nodespace_ui_properties[nodespace_uid] = {}
        self._nodespace_ui_properties[nodespace_uid].update(data)

    def get_nodespace_properties(self, nodespace_uid=None):
        """
        Return the nodespace properties of all or only the given nodespace
        """
        if nodespace_uid:
            return self._nodespace_ui_properties.get(nodespace_uid, {})
        else:
            return self._nodespace_ui_properties

    @abstractmethod
    def set_node_positions(self, positions):
        """ Sets the position of nodes.
        Parameters: a hash of uids to their positions """
        pass   # pragma: no cover

    @abstractmethod
    def create_nodespace(self, parent_uid, name="", uid=None):
        """
        Creates a new nodespace within the given parent-nodespace
        """
        pass  # pragma: no cover

    @abstractmethod
    def delete_nodespace(self, nodespace_uid):
        """
        Deletes the nodespace with the given UID, and everything it contains
        """
        pass  # pragma: no cover

    @abstractmethod
    def get_sensors(self, nodespace=None, datasource=None):
        """
        Returns a dict of all sensor nodes. Optionally filtered by the given nodespace and data source
        """
        pass  # pragma: no cover

    @abstractmethod
    def get_actuators(self, nodespace=None, datatarget=None):
        """
        Returns a dict of all actuator nodes. Optionally filtered by the given nodespace and data target
        """
        pass  # pragma: no cover

    @abstractmethod
    def create_link(self, source_node_uid, gate_type, target_node_uid, slot_type, weight=1):
        """
        Creates a new link between the given node/gate and node/slot
        """
        pass  # pragma: no cover

    @abstractmethod
    def set_link_weight(self, source_node_uid, gate_type, target_node_uid, slot_type, weight=1):
        """
        Set weight of the link between the given node/gate and node/slot
        """
        pass  # pragma: no cover

    @abstractmethod
    def delete_link(self, source_node_uid, gate_type, target_node_uid, slot_type):
        """
        Deletes the link between the given node/gate and node/slot
        """
        pass  # pragma: no cover

    def _load_nodetypes(self, nodetype_data):
        """
        Creates nodetype-instances for the given nodetype data
        """
        newnative_modules = {}
        for key, data in nodetype_data.items():
            if data.get('engine', self.engine) == self.engine:
                try:
                    newnative_modules[key] = Nodetype(nodenet=self, **data)
                except Exception as err:
                    self.logger.error("Can not instantiate node type %s: %s: %s" % (key, err.__class__.__name__, str(err)))
                    tools.post_mortem()
        return newnative_modules

    @abstractmethod
    def reload_native_modules(self, native_modules):
        """
        Replaces the native module definitions in the nodenet with the native module definitions given in the
        native_modules dict.

        Format example for the definition dict:

        "native_module_id": {
            "name": "Name of the Native Module",
            "slottypes": ["trigger"],
            "nodefunction_name": "native_module_function",
            "gatetypes": ["done"]
        }

        """
        pass  # pragma: no cover

    def get_activation_data(self, nodespace_uids=[], rounded=1):
        """
        Returns a dict of uids to lists of activation values.
        Callers need to know the types of nodes that these activations belong to.
        """
        pass  # pragma: no cover

    @abstractmethod
    def merge_data(self, nodenet_data, keep_uids=False, uidmap={}):
        """
        Merges the data in nodenet_data into this nodenet.
        If keep_uids is True, the supplied UIDs will be used. This may lead to all sorts of inconsistencies,
        so only tests should use keep_uids=True
        """
        pass  # pragma: no cover

    def get_modulator(self, modulator):
        """
        Returns the numeric value of the given global modulator
        """
        return self._modulators.get(modulator, 1)

    def change_modulator(self, modulator, diff):
        """
        Changes the value of the given global modulator by the value of diff
        """
        self._modulators[modulator] = self._modulators.get(modulator, 0) + diff

    def set_modulator(self, modulator, value):
        """
        Changes the value of the given global modulator to the given value
        """
        self._modulators[modulator] = value

    @abstractmethod
    def get_standard_nodetype_definitions(self):
        """
        Returns the standard node types supported by this nodenet
        """
        pass  # pragma: no cover

    def get_native_module_definitions(self):
        """
        Returns the native modules supported by this nodenet
        """
        data = {}
        for key in self.native_modules:
            if type(self.native_modules[key]) != FlowNodetype:
                data[key] = self.native_modules[key].get_data()
        return data

    def get_flow_module_definitions(self):
        """
        Returns the flow modules supported by this nodenet
        """
        data = {}
        for key in self.native_modules:
            if type(self.native_modules[key]) == FlowNodetype:
                data[key] = self.native_modules[key].get_data()
        return data

    @abstractmethod
    def construct_native_modules_numpy_state_dict(self):
        """
        Constructs a dict numpy states of all nodes
        """
        pass

    def get_datasources(self):
        """ Returns a sorted list of available datasources, including worldadapter datasources
        and readable modulators"""
        datasources = list(self.worldadapter_instance.get_available_datasources()) if self.worldadapter_instance else []
        if self.use_modulators:
            for item in sorted(DoernerianEmotionalModulators.readable_modulators):
                datasources.append(item)
        return datasources

    def get_datatargets(self):
        """ Returns a sorted list of available datatargets, including worldadapter datatargets
        and writeable modulators"""
        datatargets = list(self.worldadapter_instance.get_available_datatargets()) if self.worldadapter_instance else []
        if self.use_modulators:
            for item in sorted(DoernerianEmotionalModulators.writeable_modulators):
                datatargets.append(item)
        return datatargets

    @abstractmethod
    def group_nodes_by_names(self, nodespace_uid, node_name_prefix=None, gatetype="gen", sortby='id', group_name=None):
        """
        Groups the given set of nodes.
        Groups can be used in bulk operations.
        Grouped nodes will have stable sorting accross all bulk operations.
        If no group name is given, the node_name_prefix will be used as group name
        """
        pass  # pragma: no cover

    @abstractmethod
    def group_nodes_by_ids(self, nodespace_uid, node_uids, group_name, gatetype="gen", sortby='id'):
        """
        Groups the given set of nodes.
        Groups can be used in bulk operations.
        Grouped nodes will have stable sorting accross all bulk operations.
        """
        pass  # pragma: no cover

    @abstractmethod
    def ungroup_nodes(self, nodespace_uid, group):
        """
        Deletes the given group (not the nodes, just the group assignment)
        """
        pass  # pragma: no cover

    @abstractmethod
    def get_activations(self, nodespace_uid, group):
        """
        Returns an array of activations for the given group.
        For multi-gate nodes, the activations of the gate specified when creating the group will be returned.
        """
        pass  # pragma: no cover

    @abstractmethod
    def set_activations(self, nodespace_uid, group, new_activations):
        """
        Sets the activation of the given elements to the given value.
        Note that this overrides the calculated activations, including all gate mechanics,
        including gate function, thresholds, min, max, amplification and directional
        activators - the values passed will be propagated in the next step.
        """
        pass  # pragma: no cover

    @abstractmethod
    def get_gate_configurations(self, nodespace_uid, group, gatefunction_parameter=None):
        """
        Returns a dictionary containing a list of gatefunction names, and a list of the values
        of the given gatefunction_parameter (if given)
        """
        pass  # pragma: no cover

    @abstractmethod
    def set_gate_configurations(self, nodespace_uid, group, gatefunction, gatefunction_parameter=None, parameter_values=None):
        """
        Bulk-sets gatefunctions and a gatefunction_parameter for the given group.
        Arguments:
            nodespace_uid (string) - id of the parent nodespace
            group (string) - name of the group
            gatefunction (string) - name of the gatefunction to set
            gatefunction_parameter (optinoal) - name of the gatefunction_paramr to set
            parameter_values (optional) - values to set for the gatefunction_parameetr
        """
        pass  # pragma: no cover

    @abstractmethod
    def get_link_weights(self, nodespace_from_uid, group_from, nodespace_to_uid, group_to):
        """
        Returns the weights of links between two groups as a matrix.
        Rows are group_to slots, columns are group_from gates.
        Non-existing links will be returned as 0-entries in the matrix.
        """
        pass  # pragma: no cover

    @abstractmethod
    def set_link_weights(self, nodespace_from_uid, group_from, nodespace_to_uid, group_to, new_w):
        """
        Sets the weights of links between two groups from the given matrix new_w.
        Rows are group_to slots, columns are group_from gates.
        Note that setting matrix entries to non-0 values will implicitly create links.
        """
        pass  # pragma: no cover

    @abstractmethod
    def get_available_gatefunctions(self):
        """
        Returns a dict of the available gatefunctions and their parameters and parameter-defaults
        """
        pass  # pragma: no cover

    @abstractmethod
    def has_nodespace_changes(self, nodespace_uids=[], since_step=0):
        """
        Returns true, if the structure of the nodespace has changed since the given step, false otherwise
        Structural changes include everything besides activation
        """
        pass  # pragma: no cover

    @abstractmethod
    def get_nodespace_changes(self, nodespace_uids=[], since_step=0, include_links=True):
        """
        Returns a dictionary of structural changes that happened in the given nodespace
        since the given step
        Expected result format is
        {
            'nodes_dirty': {},
            'nodespaces_dirty': {},
            'nodes_deleted': [],
            'nodespaces_deleted': []
        }
        where the deleted fields carry lists of uids and the dirty fields
        carry data-dicts with the new state of the entity
        """
        pass  # pragma: no cover

    def _track_deletion(self, entity_type, uid):
        """
        Track deletion of entitytype. either 'nodes' or 'nodespaces'
        """
        if self.current_step not in self.deleted_items:
            self.deleted_items[self.current_step] = {
                'nodespaces_deleted': [],
                'nodes_deleted': []
            }
        self.deleted_items[self.current_step]["%s_deleted" % entity_type].append(uid)

    def clear(self):
        self._monitors = {}

    def add_gate_monitor(self, node_uid, gate, name=None, color=None):
        """Adds a continuous monitor to the activation of a gate. The monitor will collect the activation
        value in every calculation step.
        Returns the uid of the new monitor."""
        mon = monitor.NodeMonitor(self, node_uid, 'gate', gate, name=name, color=color)
        self._monitors[mon.uid] = mon
        return mon.uid

    def add_slot_monitor(self, node_uid, slot, name=None, color=None):
        """Adds a continuous monitor to the activation of a slot. The monitor will collect the activation
        value in every calculation step.
        Returns the uid of the new monitor."""
        mon = monitor.NodeMonitor(self, node_uid, 'slot', slot, name=name, color=color)
        self._monitors[mon.uid] = mon
        return mon.uid

    def add_link_monitor(self, source_node_uid, gate_type, target_node_uid, slot_type, name=None, color=None):
        """Adds a continuous monitor to the activation of a slot. The monitor will collect the activation
        value in every calculation step.
        Returns the uid of the new monitor."""
        mon = monitor.LinkMonitor(self, source_node_uid, gate_type, target_node_uid, slot_type, name=name, color=color)
        self._monitors[mon.uid] = mon
        return mon.uid

    def add_modulator_monitor(self, modulator, name, color=None):
        """Adds a continuous monitor to a global modulator.
        The monitor will collect respective value in every calculation step.
        Returns the uid of the new monitor."""
        mon = monitor.ModulatorMonitor(self, modulator, name=name, color=color)
        self._monitors[mon.uid] = mon
        return mon.uid

    def add_custom_monitor(self, function, name, color=None):
        """Adds a continuous monitor, that evaluates the given python-code and collects the
        return-value for every calculation step.
        Returns the uid of the new monitor."""
        mon = monitor.CustomMonitor(self, function=function, name=name, color=color)
        self._monitors[mon.uid] = mon
        return mon.uid

    def add_group_monitor(self, nodespace, name, node_name_prefix='', node_uids=[], gate='gen', color=None):
        """Adds a continuous monitor, that tracks the activations of the given group
        return-value for every calculation step.
        Returns the uid of the new monitor."""
        mon = monitor.GroupMonitor(self, nodespace, name, node_name_prefix, node_uids, gate, color=color)
        self._monitors[mon.uid] = mon
        return mon.uid

    def add_adhoc_monitor(self, function, name, parameters={}):
        """Adds an ephemeral adhoc monitor to quickly plot values returned by the given function.
        If a monitor with the given name already exists, it's value-function is updated. """
        if name in self._adhoc_monitors:
            self._adhoc_monitors[name].function = function
            self._adhoc_monitors[name].parameters = parameters
        else:
            mon = monitor.AdhocMonitor(self, function, name, parameters=parameters)
            self._adhoc_monitors[name] = mon

    def get_monitor(self, uid):
        return self._monitors.get(uid)

    def update_monitors(self):
        for uid in self._monitors:
            self._monitors[uid].step(self.current_step)
        for name in self._adhoc_monitors:
            self._adhoc_monitors[name].step(self.current_step)

    def construct_monitors_dict(self, with_values=True):
        data = {}
        for monitor_uid in self._monitors:
            data[monitor_uid] = self._monitors[monitor_uid].get_data(with_values=with_values)
        return data

    def construct_adhoc_monitors_dict(self, with_values=True):
        data = {}
        for name in self._adhoc_monitors:
            data[self._adhoc_monitors[name].uid] = self._adhoc_monitors[name].get_data(with_values=with_values)
        return data

    def remove_monitor(self, monitor_uid):
        del self._monitors[monitor_uid]

    def get_dashboard(self):
        data = self.dashboard_values.copy()
        data['is_active'] = self.is_active
        data['step'] = self.current_step
        if self.stepping_rate:
            data['stepping_rate'] = sum(self.stepping_rate) / len(self.stepping_rate)
        else:
            data['stepping_rate'] = -1
        return data

    def set_runner_condition(self, condition):
        self._runner_condition = condition

    def unset_runner_condition(self):
        self._runner_condition = None

    def get_runner_condition(self):
        return self._runner_condition

    def check_stop_runner_condition(self):
        if self._runner_condition:
            if 'step' in self._runner_condition and self.current_step >= self._runner_condition['step']:
                if 'step_amount' in self._runner_condition:
                    self._runner_condition['step'] = self.current_step + self._runner_condition['step_amount']
                return True
            if 'monitor' in self._runner_condition and self.current_step > 0:
                monitor = self.get_monitor(self._runner_condition['monitor']['uid'])
                if monitor:
                    if self.current_step in monitor.values and round(monitor.values[self.current_step], 4) == round(self._runner_condition['monitor']['value'], 4):
                        return True
                else:
                    del self.self._runner_condition['monitor']
        return False
