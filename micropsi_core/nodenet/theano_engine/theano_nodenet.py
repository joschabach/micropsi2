# -*- coding: utf-8 -*-

"""
Nodenet definition
"""
import json
import io
import os
import copy
import math

import theano
from theano import tensor as T
import numpy as np
import scipy

import pdb

from micropsi_core.tools import post_mortem
from micropsi_core.nodenet import monitor
from micropsi_core.nodenet.nodenet import Nodenet, NODENET_VERSION
from micropsi_core.nodenet.node import Nodetype, HighdimensionalNodetype
from micropsi_core.nodenet.stepoperators import DoernerianEmotionalModulators
from micropsi_core.nodenet.theano_engine.theano_flowengine import TheanoFlowEngine
from micropsi_core.nodenet.theano_engine.theano_node import *
from micropsi_core.nodenet.theano_engine.theano_definitions import *
from micropsi_core.nodenet.theano_engine.theano_stepoperators import *
from micropsi_core.nodenet.theano_engine.theano_nodespace import *
from micropsi_core.nodenet.theano_engine.theano_netapi import TheanoNetAPI
from micropsi_core.nodenet.theano_engine.theano_partition import TheanoPartition

from configuration import config as settings


STANDARD_NODETYPES = {
    "Comment": {
        "name": "Comment",
        "symbol": "#",
        'parameters': ['comment'],
        "shape": "Rectangle"
    },
    "Neuron": {
        "name": "Neuron",
        "slottypes": ["gen"],
        "nodefunction_name": "neuron",
        "gatetypes": ["gen"]
    },
    "Sensor": {
        "name": "Sensor",
        "parameters": ["datasource"],
        "nodefunction_name": "sensor",
        "gatetypes": ["gen"]
    },
    "Actuator": {
        "name": "Actuator",
        "parameters": ["datatarget"],
        "nodefunction_name": "actuator",
        "slottypes": ["gen"],
        "gatetypes": ["gen"]
    },
    "Pipe": {
        "name": "Pipe",
        "slottypes": ["gen", "por", "ret", "sub", "sur", "cat", "exp"],
        "nodefunction_name": "pipe",
        "gatetypes": ["gen", "por", "ret", "sub", "sur", "cat", "exp"],
        "parameters": ["expectation", "wait"],
        "parameter_defaults": {
            "expectation": 1,
            "wait": 10
        },
        'symbol': 'πp'
    },
    "Activator": {
        "name": "Activator",
        "slottypes": ["gen"],
        "parameters": ["type"],
        "parameter_values": {"type": ["por", "ret", "sub", "sur", "cat", "exp", "sampling"]},
        "nodefunction_name": "activator"
    },
    "LSTM": {
        "name": "LSTM",
        "slottypes": ["gen", "por", "gin", "gou", "gfg"],
        "gatetypes": ["gen", "por", "gin", "gou", "gfg"],
        "nodefunction_name": "lstm",
        "symbol": "◷"
    }
}


class TheanoNodenetCore(Nodenet):
    """
        theano runtime engine implementation
    """

    @property
    def engine(self):
        return "theano_engine"

    @property
    def worldadapter_instance(self):
        return self._worldadapter_instance

    @worldadapter_instance.setter
    def worldadapter_instance(self, _worldadapter_instance):
        if self._worldadapter_instance != _worldadapter_instance:
            self._worldadapter_instance = _worldadapter_instance
            self._rebuild_sensor_actuator_indices()
        if self._worldadapter_instance:
            self._worldadapter_instance.nodenet = self

    @property
    def current_step(self):
        return self._step

    def __init__(self, persistency_path, name="", worldadapter="Default", world=None, owner="", uid=None, native_modules={}, use_modulators=True, worldadapter_instance=None, version=None):

        # map of string uids to positions. Not all nodes necessarily have an entry.
        self.positions = {}

        # map of string uids to names. Not all nodes neccessarily have an entry.
        self.names = {}

        # map of data sources to string node IDs
        self.sensormap = {}

        # map of data targets to string node IDs
        self.actuatormap = {}

        super().__init__(persistency_path, name, worldadapter, world, owner, uid, native_modules=native_modules, use_modulators=use_modulators, worldadapter_instance=worldadapter_instance, version=version)

        self.nodetypes = {}
        for type, data in STANDARD_NODETYPES.items():
            self.nodetypes[type] = Nodetype(nodenet=self, **data)

        self.numpyfloatX = getattr(np, T.config.floatX)

        self.byte_per_float = 8

        device = T.config.device
        self.logger.info("Theano configured to use %s", device)
        if device.startswith("gpu"):
            if T.config.floatX != "float32":
                self.logger.warning("Precision set to %s, but attempting to use gpu.", precision)

        self.partitions = {}
        self.last_allocated_partition = 0

        average_elements_per_node_assumption = 6
        configured_elements_per_node_assumption = settings['theano']['elements_per_node_assumption']
        try:
            average_elements_per_node_assumption = int(configured_elements_per_node_assumption)
        except:  # pragma: no cover
            self.logger.warning("Unsupported elements_per_node_assumption value from configuration: %s, falling back to 4", configured_elements_per_node_assumption)

        initial_number_of_nodes = 2000
        configured_initial_number_of_nodes = settings['theano']['initial_number_of_nodes']
        try:
            initial_number_of_nodes = int(configured_initial_number_of_nodes)
        except:  # pragma: no cover
            self.logger.warning("Unsupported initial_number_of_nodes value from configuration: %s, falling back to 2000", configured_initial_number_of_nodes)

        sparse = True
        configuredsparse = settings['theano']['sparse_weight_matrix']
        if configuredsparse == "True":
            sparse = True
        elif configuredsparse == "False":
            sparse = False
        else:  # pragma: no cover
            self.logger.warning("Unsupported sparse_weight_matrix value from configuration: %s, falling back to True", configuredsparse)
            sparse = True

        rootpartition = TheanoPartition(self,
                                        self.last_allocated_partition,
                                        sparse=sparse,
                                        initial_number_of_nodes=initial_number_of_nodes,
                                        average_elements_per_node_assumption=average_elements_per_node_assumption)
        self.partitions[rootpartition.spid] = rootpartition
        self.rootpartition = rootpartition
        self.partitionmap = {}
        self.inverted_partitionmap = {}
        self._rebuild_sensor_actuator_indices(rootpartition)

        self.proxycache = {}

        self.stepoperators = []
        self.initialize_stepoperators()

        self.native_module_definitions = {}
        for key in native_modules:
            if native_modules[key].get('engine', self.engine) == self.engine:
                self.native_module_definitions[key] = native_modules[key]

        self.create_nodespace(None, "Root", nodespace_to_id(1, rootpartition.pid))

        self.initialize_nodenet({})

    def _create_netapi(self):
        self.netapi = TheanoNetAPI(self)

    def on_start(self):
        self.is_active = True
        for partition in self.partitions.values():
            for uid, node in partition.native_module_instances.items():
                node.on_start(node)

    def on_stop(self):
        self.is_active = False
        for partition in self.partitions.values():
            for uid, node in partition.native_module_instances.items():
                node.on_stop(node)

    def get_data(self, complete=False, include_links=True):
        data = super().get_data(complete=complete, include_links=include_links)
        data['nodes'] = self.construct_nodes_dict(complete=complete, include_links=include_links)
        data['nodespaces'] = self.construct_nodespaces_dict(None, transitive=True)
        data['version'] = self._version
        data['modulators'] = self.construct_modulators_dict()
        return data

    def export_json(self):
        data = self.get_data(complete=True, include_links=False)
        data['links'] = self.construct_links_list()
        return data

    def get_nodes(self, nodespace_uids=[], include_links=True, links_to_nodespaces=[]):
        """
        Returns a dict with contents for the given nodespaces
        """
        data = {}
        data['nodes'] = {}
        data['nodespaces'] = {}

        if nodespace_uids == []:
            nodespace_uids = False
        else:
            nodespace_uids = [self.get_nodespace(uid).uid for uid in nodespace_uids]

        if nodespace_uids:
            nodespaces_by_partition = {}
            for nodespace_uid in nodespace_uids:
                spid = self.get_partition(nodespace_uid).spid
                data['nodespaces'].update(self.construct_nodespaces_dict(nodespace_uid))
                if spid not in nodespaces_by_partition:
                    nodespaces_by_partition[spid] = []
                nodespaces_by_partition[spid].append(nodespace_from_id(nodespace_uid))

            linked_nodespaces_by_partition = dict((spid, []) for spid in self.partitions)
            if links_to_nodespaces:
                # group by partition:
                for uid in links_to_nodespaces:
                    spid = self.get_partition(uid).spid
                    linked_nodespaces_by_partition[spid].append(nodespace_from_id(uid))

            for spid in nodespaces_by_partition:
                nodes, links, _ = self.partitions[spid].get_node_data(nodespaces_by_partition=nodespaces_by_partition, include_links=include_links, linked_nodespaces_by_partition=linked_nodespaces_by_partition)
                data['nodes'].update(nodes)
                data['links'] = links

        else:
            data['nodespaces'] = self.construct_nodespaces_dict(None, transitive=True)
            for partition in self.partitions.values():
                nodes, _, _ = partition.get_node_data(nodespaces_by_partition=None, include_links=include_links)
                data['nodes'].update(nodes)

        return data

    def get_links_for_nodes(self, node_uids):

        nodes = {}
        links = []

        def linkid(linkdict):
            return "%s:%s:%s:%s" % (linkdict['source_node_uid'], linkdict['source_gate_name'], linkdict['target_slot_name'], linkdict['target_node_uid'])

        innerlinks = {}
        for uid in node_uids:
            nid = node_from_id(uid)
            partition = self.get_partition(uid)

            ntype = partition.allocated_nodes[nid]
            nofel = get_elements_per_type(ntype, self.native_modules)
            offset = partition.allocated_node_offsets[nid]

            elrange = np.asarray(range(offset, offset + nofel))
            weights = None

            num_nodetype = partition.allocated_nodes[nid]
            str_nodetype = get_string_node_type(num_nodetype, self.native_modules)
            obj_nodetype = self.get_nodetype(str_nodetype)

            # inner partition links:
            w_matrix = partition.w.get_value(borrow=True)

            node_ids = []
            for i, el in enumerate(elrange):
                from_els = np.nonzero(w_matrix[el, :])[1]
                to_els = np.nonzero(w_matrix[:, el])[0]
                if len(from_els):
                    slot_numerical = el - partition.allocated_node_offsets[nid]
                    slot_type = get_string_slot_type(slot_numerical, obj_nodetype)
                    if type(obj_nodetype) == HighdimensionalNodetype:
                        if slot_type.rstrip('0123456789') in obj_nodetype.dimensionality['slots']:
                            slot_type = slot_type.rstrip('0123456789') + '0'
                    from_nids = partition.allocated_elements_to_nodes[from_els]
                    node_ids.extend(from_nids)

                    for j, from_el in enumerate(from_els):
                        source_uid = node_to_id(from_nids[j], partition.pid)
                        from_nodetype = partition.allocated_nodes[from_nids[j]]
                        from_obj_nodetype = self.get_nodetype(get_string_node_type(from_nodetype, self.native_modules))
                        gate_numerical = from_el - partition.allocated_node_offsets[from_nids[j]]
                        gate_type = get_string_gate_type(gate_numerical, from_obj_nodetype)
                        if type(from_obj_nodetype) == HighdimensionalNodetype:
                            if gate_type.rstrip('0123456789') in from_obj_nodetype.dimensionality['gates']:
                                gate_type = gate_type.rstrip('0123456789') + '0'
                        ldict = {
                            'source_node_uid': source_uid,
                            'source_gate_name': gate_type,
                            'target_node_uid': uid,
                            'target_slot_name': slot_type,
                            'weight': float(w_matrix[el, from_el])
                        }
                        innerlinks[linkid(ldict)] = ldict

                if len(to_els):
                    gate_numerical = el - partition.allocated_node_offsets[nid]
                    gate_type = get_string_gate_type(gate_numerical, obj_nodetype)
                    if type(obj_nodetype) == HighdimensionalNodetype:
                        if gate_type.rstrip('0123456789') in obj_nodetype.dimensionality['gates']:
                            gate_type = gate_type.rstrip('0123456789') + '0'
                    to_nids = partition.allocated_elements_to_nodes[to_els]
                    node_ids.extend(to_nids)
                    for j, to_el in enumerate(to_els):
                        target_uid = node_to_id(to_nids[j], partition.pid)
                        to_nodetype = partition.allocated_nodes[to_nids[j]]
                        to_obj_nodetype = self.get_nodetype(get_string_node_type(to_nodetype, self.native_modules))
                        slot_numerical = to_el - partition.allocated_node_offsets[to_nids[j]]
                        slot_type = get_string_slot_type(slot_numerical, to_obj_nodetype)
                        if type(to_obj_nodetype) == HighdimensionalNodetype:
                            if slot_type.rstrip('0123456789') in to_obj_nodetype.dimensionality['slots']:
                                slot_type = slot_type.rstrip('0123456789') + '0'
                        ldict = {
                            'source_node_uid': uid,
                            'source_gate_name': gate_type,
                            'target_node_uid': target_uid,
                            'target_slot_name': slot_type,
                            'weight': float(w_matrix[to_el, el])
                        }
                        innerlinks[linkid(ldict)] = ldict

            links = list(innerlinks.values())
            nodes.update(partition.get_node_data(ids=[x for x in node_ids if x != nid], include_links=False)[0])

            # search links originating from this node
            for to_partition in self.partitions.values():
                if partition.spid in to_partition.inlinks:
                    inlinks = to_partition.inlinks[partition.spid]
                    from_elements = inlinks[0].get_value(borrow=True)
                    node_gates = np.intersect1d(elrange, from_elements)
                    if len(node_gates):
                        to_elements = inlinks[1].get_value(borrow=True)
                        if inlinks[4] == 'identity':
                            slots = np.arange(len(from_elements))
                            gates = np.arange(len(from_elements))
                            weights = 1
                        elif inlinks[4] == 'dense':
                            weights = inlinks[2].get_value(borrow=True)
                            slots, gates = np.nonzero(weights)
                        node_ids = set()
                        for index, gate_index in enumerate(gates):
                            if from_elements[gate_index] not in elrange:
                                continue
                            gate_numerical = from_elements[gate_index] - partition.allocated_node_offsets[nid]
                            gate_type = get_string_gate_type(gate_numerical, obj_nodetype)
                            slot_index = slots[index]
                            target_nid = to_partition.allocated_elements_to_nodes[to_elements[slot_index]]
                            node_ids.add(target_nid)
                            to_nodetype = to_partition.allocated_nodes[target_nid]
                            to_obj_nodetype = self.get_nodetype(get_string_node_type(to_nodetype, self.native_modules))
                            slot_numerical = to_elements[slot_index] - to_partition.allocated_node_offsets[target_nid]
                            slot_type = get_string_slot_type(slot_numerical, to_obj_nodetype)
                            if type(to_obj_nodetype) == HighdimensionalNodetype:
                                if slot_type.rstrip('0123456789') in to_obj_nodetype.dimensionality['slots']:
                                    slot_type = slot_type.rstrip('0123456789') + '0'
                            if type(obj_nodetype) == HighdimensionalNodetype:
                                if gate_type.rstrip('0123456789') in obj_nodetype.dimensionality['gates']:
                                    gate_type = gate_type.rstrip('0123456789') + '0'

                            links.append({
                                'source_node_uid': uid,
                                'source_gate_name': gate_type,
                                'target_node_uid': node_to_id(target_nid, to_partition.pid),
                                'target_slot_name': slot_type,
                                'weight': 1 if np.isscalar(weights) else float(weights[slot_index, gate_index])
                            })
                        nodes.update(to_partition.get_node_data(ids=list(node_ids), include_links=False)[0])

            # search for links terminating at this node
            for from_spid in partition.inlinks:
                inlinks = partition.inlinks[from_spid]
                from_partition = self.partitions[from_spid]
                to_elements = inlinks[1].get_value(borrow=True)
                node_slots = np.intersect1d(elrange, to_elements)
                if len(node_slots):
                    from_elements = inlinks[0].get_value(borrow=True)
                    if inlinks[4] == 'identity':
                        slots = np.arange(len(from_elements))
                        gates = np.arange(len(from_elements))
                        weights = 1
                    elif inlinks[4] == 'dense':
                        weights = inlinks[2].get_value(borrow=True)
                        slots, gates = np.nonzero(weights)
                    node_ids = set()
                    for index, slot_index in enumerate(slots):
                        if to_elements[slot_index] not in elrange:
                            continue
                        slot_numerical = to_elements[slot_index] - partition.allocated_node_offsets[nid]
                        slot_type = get_string_slot_type(slot_numerical, obj_nodetype)
                        gate_index = gates[index]
                        source_nid = from_partition.allocated_elements_to_nodes[from_elements[gate_index]]
                        node_ids.add(source_nid)
                        from_nodetype = from_partition.allocated_nodes[source_nid]
                        from_obj_nodetype = self.get_nodetype(get_string_node_type(from_nodetype, self.native_modules))
                        gate_numerical = from_elements[gate_index] - from_partition.allocated_node_offsets[source_nid]
                        gate_type = get_string_gate_type(gate_numerical, from_obj_nodetype)
                        if type(from_obj_nodetype) == HighdimensionalNodetype:
                            if gate_type.rstrip('0123456789') in from_obj_nodetype.dimensionality['gates']:
                                gate_type = gate_type.rstrip('0123456789') + '0'
                        if type(obj_nodetype) == HighdimensionalNodetype:
                            if slot_type.rstrip('0123456789') in obj_nodetype.dimensionality['slots']:
                                slot_type = slot_type.rstrip('0123456789') + '0'

                        links.append({
                            'source_node_uid': node_to_id(source_nid, from_partition.pid),
                            'source_gate_name': gate_type,
                            'target_node_uid': uid,
                            'target_slot_name': slot_type,
                            'weight': 1 if np.isscalar(weights) and weights == 1 else float(weights[slot_index, gate_index])
                        })

                    nodes.update(from_partition.get_node_data(ids=list(node_ids), include_links=False)[0])

        return links, nodes

    def initialize_stepoperators(self):
        self.stepoperators = [
            TheanoPropagate(),
            TheanoCalculate(self)]
        if self.use_modulators:
            self.stepoperators.append(DoernerianEmotionalModulators())
        self.stepoperators.sort(key=lambda op: op.priority)

    def save(self, base_path=None, zipfile=None):
        if base_path is None:
            base_path = self.persistency_path

        # write json metadata, which will be used by runtime to manage the net
        metadata = self.metadata
        metadata['positions'] = self.positions
        metadata['names'] = self.names
        metadata['actuatormap'] = self.actuatormap
        metadata['sensormap'] = self.sensormap
        metadata['nodes'] = self.construct_native_modules_and_comments_dict()
        metadata['monitors'] = self.construct_monitors_dict()
        metadata['modulators'] = self.construct_modulators_dict()
        metadata['partition_parents'] = self.inverted_partitionmap

        if zipfile:
            zipfile.writestr('nodenet.json', json.dumps(metadata))
        else:
            with open(os.path.join(base_path, 'nodenet.json'), 'w+', encoding="utf-8") as fp:
                fp.write(json.dumps(metadata, indent=4))

        # write numpy states of native modules
        numpy_states = self.construct_native_modules_numpy_state_dict()
        for node_uid, states in numpy_states.items():
            if len(states) > 0:
                filename = "%s_numpystate.npz" % node_uid
                if zipfile:
                    stream = io.BytesIO()
                    np.savez(stream, **states)
                    stream.seek(0)
                    zipfile.writestr(filename, stream.getvalue())
                else:
                    np.savez(os.path.join(base_path, filename), **states)

        for partition in self.partitions.values():
            # save partitions
            partition.save(base_path=base_path, zipfile=zipfile)

    def load(self):
        """Load the node net from a file"""

        if self._version != NODENET_VERSION:
            self.logger.error("Wrong version of nodenet data in nodenet %s, cannot load." % self.uid)
            return False

        # try to access file
        filename = os.path.join(self.persistency_path, 'nodenet.json')
        with self.netlock:
            initfrom = {}
            if os.path.isfile(filename):
                try:
                    self.logger.info("Loading nodenet %s metadata from file %s", self.name, filename)
                    with open(filename, encoding="utf-8") as file:
                        initfrom.update(json.load(file))
                except ValueError:  # pragma: no cover
                    self.logger.warning("Could not read nodenet metadata from file %s", filename)
                    return False
                except IOError:  # pragma: no cover
                    self.logger.warning("Could not open nodenet metadata file %s", filename)
                    return False

            # determine whether we have a complete json dump, or our theano npz partition files:
            nodes_data = initfrom.get('nodes', {})

            # pop the monitors:
            monitors = initfrom.pop('monitors', {})

            # initialize
            invalid_uids = self.initialize_nodenet(initfrom)

            for uid in invalid_uids:
                del nodes_data[uid]

            for partition in self.partitions.values():
                partition.load_data(nodes_data, invalid_uids=invalid_uids)

            for partition in self.partitions.values():
                partition.load_inlinks()

            # reloading native modules ensures the types in allocated_nodes are up to date
            # (numerical native module types are runtime dependent and may differ from when allocated_nodes
            # was saved).
            self.reload_native_modules(self.native_module_definitions)

            # recover numpy states for native modules
            for partition in self.partitions.values():
                nodeids = np.where((partition.allocated_nodes > MAX_STD_NODETYPE) | (partition.allocated_nodes == COMMENT))[0]
                for node_id in nodeids:
                    node_uid = node_to_id(node_id, partition.pid)
                    file = os.path.join(self.persistency_path, '%s_numpystate.npz' % node_uid)
                    if os.path.isfile(file):
                        node = self.get_node(node_uid)
                        numpy_states = np.load(file)
                        node.set_persistable_state(node._state, numpy_states)
                        numpy_states.close()

            for monitorid in monitors:
                data = monitors[monitorid]
                if hasattr(monitor, data['classname']):
                    mon = getattr(monitor, data['classname'])(self, **data)
                    self._monitors[mon.uid] = mon
                else:
                    self.logger.warning('unknown classname for monitor: %s (uid:%s) ' % (data['classname'], monitorid))

            # re-initialize step operators for theano recompile to new shared variables
            self.initialize_stepoperators()

            self._rebuild_sensor_actuator_indices()

            return True

    def initialize_nodenet(self, initfrom):

        self._modulators.update(initfrom.get("modulators", {}))

        if initfrom.get('runner_condition'):
            self.set_runner_condition(initfrom['runner_condition'])

        self._nodespace_ui_properties = initfrom.get('nodespace_ui_properties', {})

        invalid_uids = []
        if len(initfrom) != 0:
            # now merge in all init data (from the persisted file typically)
            invalid_uids = self.merge_data(initfrom, keep_uids=True, native_module_instances_only=True)
            if 'names' in initfrom:
                self.names = initfrom['names']
            if 'positions' in initfrom:
                self.positions = initfrom['positions']
            if 'actuatormap' in initfrom:
                self.actuatormap = initfrom['actuatormap']
            if 'sensormap' in initfrom:
                self.sensormap = initfrom['sensormap']
            if 'current_step' in initfrom:
                self._step = initfrom['current_step']
        return invalid_uids

    def merge_data(self, nodenet_data, keep_uids=False, native_module_instances_only=False):
        """merges the nodenet state with the current node net, might have to give new UIDs to some entities"""
        uidmap = {}
        invalid_nodes = {}

        # for dict_engine compatibility
        uidmap["Root"] = self.rootpartition.rootnodespace_uid

        # re-use the root nodespace
        uidmap[self.rootpartition.rootnodespace_uid] = self.rootpartition.rootnodespace_uid

        # make sure we have the partition NoNs large enough to store the native modules:
        indexes = [n['index'] for n in nodenet_data.get('nodes', {}).values()]
        node_maxindex = max(indexes) if indexes else 10
        if self.rootpartition.NoN <= node_maxindex:
            self.rootpartition.grow_number_of_nodes((node_maxindex - self.rootpartition.NoN) + 1)

        # instantiate partitions
        partitions_to_instantiate = nodenet_data.get('partition_parents', {})
        largest_pid = 0
        for partition_spid, parent_uid in partitions_to_instantiate.items():
            pid = int(partition_spid)
            if pid > largest_pid:
                largest_pid = pid
            self.create_partition(pid,
                                  parent_uid,
                                  sparse=True,
                                  initial_number_of_nodes=round(node_maxindex * 1.2 + 1),
                                  average_elements_per_node_assumption=7,
                                  initial_number_of_nodespaces=round(len(set(nodenet_data.get('nodespaces', {}).keys())) * 1.2) + 1)
        self.last_allocated_partition = largest_pid

        # merge in spaces, make sure that parent nodespaces exist before children are initialized
        nodespaces_to_merge = set(nodenet_data.get('nodespaces', {}).keys())
        for nodespace in nodespaces_to_merge:
            self.merge_nodespace_data(nodespace, nodenet_data['nodespaces'], uidmap, keep_uids)

        # make sure rootpartition has enough NoN, NoE
        if native_module_instances_only:
            non = noe = 0
            for uid in nodenet_data.get('nodes', {}):
                non += 1
                try:
                    noe += get_elements_per_type(get_numerical_node_type(nodenet_data['nodes'][uid]['type'], self.native_modules), self.native_modules)
                except ValueError:
                    pass  # Unknown nodetype
            if non > self.rootpartition.NoN or noe > self.rootpartition.NoE:
                self.rootpartition.announce_nodes(non, math.ceil(noe / non))

        # merge in nodes
        for uid in nodenet_data.get('nodes', {}):
            data = nodenet_data['nodes'][uid]
            parent_uid = data['parent_nodespace']
            id_to_pass = uid
            if not keep_uids:
                parent_uid = uidmap[data['parent_nodespace']]
                id_to_pass = None
            if data['type'] not in self.nodetypes and data['type'] not in self.native_modules:
                self.logger.error("Invalid nodetype %s for node %s" % (data['type'], uid))
                invalid_nodes[uid] = data
                continue
            if native_module_instances_only:
                if not data.get('flow_module'):
                    if data['type'] in self.native_module_definitions and not self.native_module_definitions[data['type']].get('flow_module'):
                        node = TheanoNode(self, self.get_partition(uid), parent_uid, uid, get_numerical_node_type(data['type'], nativemodules=self.native_modules), state=data.get('state', {}), parameters=data.get('parameters'))
                    else:
                        invalid_nodes[uid] = data
                        continue
                    self.proxycache[node.uid] = node
                    new_uid = node.uid
                else:
                    continue
            else:
                new_uid = self.create_node(
                    data['type'],
                    parent_uid,
                    data['position'],
                    name=data['name'],
                    uid=id_to_pass,
                    parameters=data.get('parameters'),
                    gate_configuration=data.get('gate_configuration'))
            uidmap[uid] = new_uid
            node_proxy = self.get_node(new_uid)
            for gatetype in data.get('gate_activations', {}):
                if gatetype in node_proxy.nodetype.gatetypes:
                    node_proxy.get_gate(gatetype).activation = data['gate_activations'][gatetype]
            state = data.get('state', {})
            if state is not None:
                for key, value in state.items():
                    node_proxy.set_state(key, value)

        # merge in links
        links = nodenet_data.get('links', [])
        for link in links:
            if link['source_node_uid'] in invalid_nodes or link['target_node_uid'] in invalid_nodes:
                continue
            self.create_link(
                uidmap[link['source_node_uid']],
                link['source_gate_name'],
                uidmap[link['target_node_uid']],
                link['target_slot_name'],
                link['weight']
            )

        for monitorid in nodenet_data.get('monitors', {}):
            data = nodenet_data['monitors'][monitorid]
            if 'node_uid' in data:
                old_node_uid = data['node_uid']
                if old_node_uid in uidmap:
                    data['node_uid'] = uidmap[old_node_uid]
            if 'classname' in data:
                if hasattr(monitor, data['classname']):
                    mon = getattr(monitor, data['classname'])(self, **data)
                    self._monitors[mon.uid] = mon
                else:
                    self.logger.warning('unknown classname for monitor: %s (uid:%s) ' % (data['classname'], monitorid))
            else:
                # Compatibility mode
                mon = monitor.NodeMonitor(self, name=data['node_name'], **data)
                self._monitors[mon.uid] = mon

        return invalid_nodes.keys()

    def merge_nodespace_data(self, nodespace_uid, data, uidmap, keep_uids=False):
        """
        merges the given nodespace with the given nodespace data dict
        This will make sure all parent nodespaces for the given nodespace exist (and create the parents
        if necessary)
        """
        if keep_uids:
            partition = self.get_partition(nodespace_uid)
            id = nodespace_from_id(nodespace_uid)
            if partition.allocated_nodespaces[id] == 0:
                # move up the nodespace tree until we find an existing parent or hit root
                if id != 1:
                    parent_id = nodespace_from_id(data[nodespace_uid].get('parent_nodespace'))
                    if partition.allocated_nodespaces[parent_id] == 0:
                        self.merge_nodespace_data(nodespace_to_id(parent_id, partition.pid), data, uidmap, keep_uids)
                self.create_nodespace(
                    data[nodespace_uid].get('parent_nodespace'),
                    name=data[nodespace_uid].get('name', 'Root'),
                    uid=nodespace_uid
                )
        else:
            if nodespace_uid not in uidmap:
                parent_uid = data[nodespace_uid].get('parent_nodespace')
                if parent_uid not in uidmap:
                    self.merge_nodespace_data(parent_uid, data, uidmap, keep_uids)
                newuid = self.create_nodespace(
                    uidmap[data[nodespace_uid].get('parent_nodespace')],
                    data[nodespace_uid].get('position'),
                    name=data[nodespace_uid].get('name', 'Root'),
                    uid=None
                )
                uidmap[nodespace_uid] = newuid

    def step(self):
        with self.netlock:
            self._step += 1

            for operator in self.stepoperators:
                operator.execute(self, None, self.netapi)

        steps = sorted(list(self.deleted_items.keys()))
        if steps:
            for i in steps:
                if i >= self.current_step - 100:
                    break
                else:
                    del self.deleted_items[i]
        self.user_prompt_response = {}

    def get_partition(self, uid):
        if uid is None:
            return self.rootpartition
        return self.partitions.get(uid[1:4], None)

    def get_node(self, uid):
        partition = self.get_partition(uid)
        if partition is None:
            raise KeyError("No node with id %s exists" % uid)
        if uid in partition.native_module_instances:
            return partition.native_module_instances[uid]
        elif uid in partition.comment_instances:
            return partition.comment_instances[uid]
        elif uid in self.proxycache:
            return self.proxycache[uid]
        elif self.is_node(uid):
            return self._create_node_proxy(partition, uid)
        else:
            raise KeyError("No node with id %s exists" % uid)

    def _create_node_proxy(self, partition, uid):
        id = node_from_id(uid)
        parent_id = partition.allocated_node_parents[id]
        node = TheanoNode(self, partition, nodespace_to_id(parent_id, partition.pid), uid, partition.allocated_nodes[id])
        self.proxycache[node.uid] = node
        return node

    def get_node_uids(self, group_nodespace_uid=None, group=None):
        if group is not None:
            if group_nodespace_uid is None:
                group_nodespace_uid = self.get_nodespace(None).uid
            partition = self.get_partition(group_nodespace_uid)
            return [node_to_id(nid, partition.pid) for nid in partition.allocated_elements_to_nodes[partition.nodegroups[group_nodespace_uid][group]]]
        else:
            uids = []
            for partition in self.partitions.values():
                uids.extend([node_to_id(id, partition.pid) for id in np.nonzero(partition.allocated_nodes)[0]])
            return uids

    def is_node(self, uid):
        if uid is None or uid[0] != 'n':
            return False
        partition = self.get_partition(uid)
        if partition is None:
            return False
        numid = node_from_id(uid)
        return numid < partition.NoN and partition.allocated_nodes[numid] != 0

    def announce_nodes(self, nodespace_uid, number_of_nodes, average_elements_per_node):
        partition = self.get_partition(nodespace_uid)
        partition.announce_nodes(number_of_nodes, average_elements_per_node)

    def create_node(self, nodetype, nodespace_uid, position, name=None, uid=None, parameters=None, gate_configuration=None):
        nodespace_uid = self.get_nodespace(nodespace_uid).uid
        partition = self.get_partition(nodespace_uid)
        nodespace_id = nodespace_from_id(nodespace_uid)

        id_to_pass = None
        if uid is not None:
            id_to_pass = node_from_id(uid)

        id = partition.create_node(nodetype, nodespace_id, id_to_pass, parameters, gate_configuration)
        uid = node_to_id(id, partition.pid)

        if position is not None:
            position = (position + [0] * 3)[:3]
            self.positions[uid] = position

        if parameters is None:
            parameters = {}

        if nodetype == "Sensor":
            if 'datasource' in parameters:
                self.get_node(uid).set_parameter("datasource", parameters['datasource'])
                if name is None or name == "" or name == uid:
                    name = parameters['datasource']
        elif nodetype == "Actuator":
            if 'datatarget' in parameters:
                self.get_node(uid).set_parameter("datatarget", parameters['datatarget'])
                if name is None or name == "" or name == uid:
                    name = parameters['datatarget']
        elif nodetype in self.native_modules:
            if name is None or name == "" or name == uid:
                name = nodetype

        if name is not None and name != "" and name != uid:
            self.names[uid] = name

        return uid

    def delete_node(self, uid):
        partition = self.get_partition(uid)
        node_id = node_from_id(uid)

        associated_ids = partition.get_associated_node_ids(node_id)

        nodetype = partition.allocated_nodes[node_id]

        associated_uids = []

        # find this node in links coming in from other partitions, and nullify the inter-partition-weight matrix
        for partition_from_spid, inlinks in partition.inlinks.copy().items():
            for numeric_slot in range(0, get_slots_per_type(nodetype, self.native_modules)):
                element = partition.allocated_node_offsets[node_id] + numeric_slot
                from_elements = inlinks[0].get_value(borrow=True)
                to_elements = inlinks[1].get_value(borrow=True)

                if element in to_elements:
                    inlink_type = inlinks[4]
                    if inlink_type == "dense":
                        weights = inlinks[2].get_value(borrow=True)
                        from_partition = self.partitions[partition_from_spid]
                        element_index = np.where(to_elements == element)[0][0]
                        slotrow = weights[element_index]
                        links_indices = np.nonzero(slotrow)[0]
                        for link_index in links_indices:
                            source_id = from_partition.allocated_elements_to_nodes[from_elements[link_index]]
                            associated_uids.append(node_to_id(source_id, from_partition.pid))
                        # set all weights for this element to 0
                        new_weights = np.delete(weights, element_index, 0)
                        if len(new_weights) == 0:
                            # if this was the last link, remove whole inlinks information for this partition pair
                            del partition.inlinks[partition_from_spid]
                            break

                        # find empty columns (elements linking only to this element)
                        zero_columns = np.where(~new_weights.any(axis=0))[0]
                        # remove empty columns from weight matrix:
                        new_weights = np.delete(new_weights, zero_columns, 1)
                        # save new weight matrix
                        partition.inlinks[partition_from_spid][2].set_value(new_weights)
                    elif inlink_type == "identity":
                        element_index = np.where(to_elements == element)[0][0]
                        zero_columns = element_index

                    # remove this element
                    partition.inlinks[partition_from_spid][1].set_value(np.delete(to_elements, element_index))
                    # remove from_elements
                    partition.inlinks[partition_from_spid][0].set_value(np.delete(from_elements, zero_columns))

        # find this node in links going out to other partitions, and nullify the inter-partition-weight matrix
        for partition_to_spid, to_partition in self.partitions.items():
            if partition.spid in to_partition.inlinks:
                for numeric_gate in range(0, get_gates_per_type(nodetype, self.native_modules)):
                    element = partition.allocated_node_offsets[node_id] + numeric_gate
                    inlinks = to_partition.inlinks[partition.spid]
                    from_elements = inlinks[0].get_value(borrow=True)
                    to_elements = inlinks[1].get_value(borrow=True)

                    if element in from_elements:
                        inlink_type = inlinks[4]
                        if inlink_type == "dense":
                            weights = inlinks[2].get_value(borrow=True)
                            element_index = np.where(from_elements == element)[0][0]
                            gatecolumn = weights[:, element_index]
                            links_indices = np.nonzero(gatecolumn)[0]
                            for link_index in links_indices:
                                target_id = to_partition.allocated_elements_to_nodes[to_elements[link_index]]
                                associated_uids.append(node_to_id(target_id, to_partition.pid))
                            # set all weights for this element to 0
                            new_weights = np.delete(weights, element_index, 1)
                            if len(new_weights) == 0:
                                # if this was the last link, remove whole inlinks information for target partition
                                del to_partition.inlinks[partition.spid]
                                break

                            # find empty rows (elements linked only by this node)
                            zero_rows = np.where(~new_weights.any(axis=1))[0]
                            # remove empty rows from weight matrix
                            new_weights = np.delete(new_weights, zero_rows, 0)
                            # save new weights
                            to_partition.inlinks[partition.spid][2].set_value(new_weights)

                        elif inlink_type == "identity":
                            element_index = np.where(from_elements == element)[0][0]
                            zero_columns = element_index

                        # remove this element
                        to_partition.inlinks[partition.spid][0].set_value(np.delete(from_elements, element_index))
                        # remove to_elements
                        to_partition.inlinks[partition.spid][1].set_value(np.delete(to_elements, zero_rows))

        partition.delete_node(node_id)

        # remove sensor association if there should be one
        if uid in self.sensormap.values():
            self.sensormap = {k: v for k, v in self.sensormap.items() if v != uid}

        # remove actuator association if there should be one
        if uid in self.actuatormap.values():
            self.actuatormap = {k: v for k, v in self.actuatormap.items() if v != uid}

        self.clear_supplements(uid)

        for id_to_clear in associated_ids:
            associated_uids.append(node_to_id(id_to_clear, partition.pid))

        for uid_to_clear in associated_uids:
            partition = self.get_partition(uid_to_clear)
            if uid_to_clear in partition.native_module_instances:
                proxy = partition.native_module_instances[uid_to_clear]
                for g in proxy.get_gate_types():
                    proxy.get_gate(g).invalidate_caches()
                for s in proxy.get_slot_types():
                    proxy.get_slot(s).invalidate_caches()
            if uid_to_clear in self.proxycache:
                del self.proxycache[uid_to_clear]

    def set_nodespace_gatetype_activator(self, nodespace_uid, gate_type, activator_uid):
        partition = self.get_partition(nodespace_uid)
        activator_id = 0
        if activator_uid is not None and len(activator_uid) > 0:
            activator_id = node_from_id(activator_uid)
        nodespace_id = nodespace_from_id(nodespace_uid)
        partition.set_nodespace_gatetype_activator(nodespace_id, gate_type, activator_id)

    def set_nodespace_sampling_activator(self, nodespace_uid, activator_uid):
        partition = self.get_partition(nodespace_uid)
        activator_id = 0
        if activator_uid is not None and len(activator_uid) > 0:
            activator_id = node_from_id(activator_uid)
        nodespace_id = nodespace_from_id(nodespace_uid)
        partition.set_nodespace_sampling_activator(nodespace_id, activator_id)

    def get_nodespace(self, uid):
        if uid is None:
            uid = nodespace_to_id(1, self.rootpartition.pid)

        if not self.is_nodespace(uid):
            raise KeyError("No nodespace with id %s exists", uid)

        partition = self.get_partition(uid)

        if uid in self.proxycache:
            return self.proxycache[uid]
        else:
            nodespace = TheanoNodespace(self, partition, uid)
            self.proxycache[uid] = nodespace
            return nodespace

    def get_nodespace_uids(self):
        ids = []
        for partition in self.partitions.values():
            ids.extend([nodespace_to_id(id, partition.pid) for id in np.nonzero(partition.allocated_nodespaces)[0]])
            ids.append(nodespace_to_id(1, partition.pid))
        return ids

    def is_nodespace(self, uid):
        return uid in self.get_nodespace_uids()

    def set_node_positions(self, positions):
        for uid in positions:
            pos = (positions[uid] + [0] * 3)[:3]
            self.positions[uid] = pos
            if uid in self.proxycache:
                self.proxycache[uid].position = pos

    def create_partition(self, pid, parent_uid, sparse, initial_number_of_nodes, average_elements_per_node_assumption, initial_number_of_nodespaces):

        if parent_uid is None:
            parent_uid = self.get_nodespace(None).uid
        if pid > 999:
            raise NotImplementedError("Only partition IDs < 1000 are supported right now")
        partition = TheanoPartition(self,
                                    pid,
                                    sparse=sparse,
                                    initial_number_of_nodes=initial_number_of_nodes,
                                    average_elements_per_node_assumption=average_elements_per_node_assumption,
                                    initial_number_of_nodespaces=initial_number_of_nodespaces)
        self.partitions[partition.spid] = partition
        if parent_uid not in self.partitionmap:
            self.partitionmap[parent_uid] = []
        self.partitionmap[parent_uid].append(partition)
        self.inverted_partitionmap[partition.spid] = parent_uid
        self._rebuild_sensor_actuator_indices(partition)
        return partition.spid

    def delete_partition(self, pid):
        spid = "%03i" % pid
        partitionrootspace = "s%s1" %spid
        partition = self.partitions[spid]
        for subspace_uid in self.get_nodespace(partitionrootspace).get_known_ids('nodespaces'):
            self.delete_nodespace(subspace_uid)

        parent_uid = self.inverted_partitionmap[spid]
        if parent_uid in self.partitionmap and partition in self.partitionmap[parent_uid]:
            self.partitionmap[parent_uid].remove(partition)
        if spid in self.inverted_partitionmap:
            del self.inverted_partitionmap[spid]
        if spid in self.partitions:
            del self.partitions[spid]
        for otherpartition in self.partitions.values():
            if spid in otherpartition.inlinks:
                del otherpartition.inlinks[spid]
                for uid, node in otherpartition.native_module_instances.items():
                    for g in node.get_gate_types():
                        node.get_gate(g).invalidate_caches()
                    for s in node.get_slot_types():
                        node.get_slot(s).invalidate_caches()

    def create_nodespace(self, parent_uid, name="", uid=None, options=None):
        if options is None:
            options = {}
        new_partition = options.get('new_partition', False)

        partition = self.get_partition(parent_uid)

        parent_id = 0
        if parent_uid is not None:
            parent_id = nodespace_from_id(parent_uid)
        elif uid != self.rootpartition.rootnodespace_uid:
            parent_id = 1

        id_to_pass = None
        if uid is not None:
            id_to_pass = nodespace_from_id(uid)

        if new_partition and parent_id != 0:

            initial_number_of_nodespaces = 10
            if "initial_number_of_nodespaces" in options:
                initial_number_of_nodespaces = int(options["initial_number_of_nodespaces"])

            average_elements_per_node_assumption = 4
            if "average_elements_per_node_assumption" in options:
                average_elements_per_node_assumption = int(options["average_elements_per_node_assumption"])
            else:
                configured_elements_per_node_assumption = settings['theano']['elements_per_node_assumption']
                try:
                    average_elements_per_node_assumption = int(configured_elements_per_node_assumption)
                except:
                    self.logger.warning("Unsupported elements_per_node_assumption value from configuration: %s, falling back to 4", configured_elements_per_node_assumption)  # pragma: no cover

            initial_number_of_nodes = 2000
            if "initial_number_of_nodes" in options:
                initial_number_of_nodes = int(options["initial_number_of_nodes"])
            else:
                configured_initial_number_of_nodes = settings['theano']['initial_number_of_nodes']
                try:
                    initial_number_of_nodes = int(configured_initial_number_of_nodes)
                except:
                    self.logger.warning("Unsupported initial_number_of_nodes value from configuration: %s, falling back to 2000", configured_initial_number_of_nodes)  # pragma: no cover

            sparse = True
            if "sparse" in options:
                sparse = options["sparse"]
            else:
                configuredsparse = settings['theano']['sparse_weight_matrix']
                if configuredsparse == "True":
                    sparse = True
                elif configuredsparse == "False":
                    sparse = False
                else:
                    self.logger.warning("Unsupported sparse_weight_matrix value from configuration: %s, falling back to True", configuredsparse)  # pragma: no cover
                    sparse = True

            self.last_allocated_partition += 1
            spid = self.create_partition(
                self.last_allocated_partition,
                parent_uid,
                sparse=sparse,
                initial_number_of_nodes=initial_number_of_nodes,
                average_elements_per_node_assumption=average_elements_per_node_assumption,
                initial_number_of_nodespaces=initial_number_of_nodespaces)
            partition = self.partitions[spid]
            id = partition.create_nodespace(0, id_to_pass)
            uid = nodespace_to_id(id, partition.pid)
        else:
            id = partition.create_nodespace(parent_id, id_to_pass)
            uid = nodespace_to_id(id, partition.pid)

        if name is not None and len(name) > 0 and name != uid:
            self.names[uid] = name

        return uid

    def delete_nodespace(self, nodespace_uid):
        if nodespace_uid is None or nodespace_uid == self.get_nodespace(None).uid:
            raise ValueError("The root nodespace cannot be deleted.")
        self._nodespace_ui_properties.pop(nodespace_uid, None)
        partition = self.get_partition(nodespace_uid)
        nodespace_id = nodespace_from_id(nodespace_uid)
        if nodespace_id == 1 and partition.pid != self.rootpartition.pid:
            self.delete_partition(partition.pid)
        else:
            partition.delete_nodespace(nodespace_id)

    def clear_supplements(self, uid):
        # clear from proxycache
        if uid in self.proxycache:
            del self.proxycache[uid]

        # clear from name and positions dicts
        if uid in self.names:
            del self.names[uid]
        if uid in self.positions:
            del self.positions[uid]

    def get_sensors(self, nodespace=None, datasource=None):
        sensors = {}
        sensorlist = []
        if datasource is None:
            sensorlist = self.sensormap.values()
        elif datasource in self.sensormap:
            sensorlist.append(self.sensormap[datasource])
        for uid in sensorlist:
            if nodespace is None or self.get_partition(uid).allocated_node_parents[node_from_id(uid)] == nodespace_from_id(nodespace):
                sensors[uid] = self.get_node(uid)
        return sensors

    def get_actuators(self, nodespace=None, datatarget=None):
        actuators = {}
        actuatorlist = []
        if datatarget is None:
            actuatorlist = self.actuatormap.values()
        elif datatarget in self.actuatormap:
            actuatorlist.append(self.actuatormap[datatarget])
        for uid in actuatorlist:
            if nodespace is None or self.get_partition(uid).allocated_node_parents[node_from_id(uid)] == nodespace_from_id(nodespace):
                actuators[uid] = self.get_node(uid)
        return actuators

    def create_link(self, source_node_uid, gate_type, target_node_uid, slot_type, weight=1):
        result = self.set_link_weight(source_node_uid, gate_type, target_node_uid, slot_type, weight)
        return result

    def set_link_weight(self, source_node_uid, gate_type, target_node_uid, slot_type, weight=1):

        source_partition = self.get_partition(source_node_uid)
        target_partition = self.get_partition(target_node_uid)

        source_node_id = node_from_id(source_node_uid)
        target_node_id = node_from_id(target_node_uid)

        if target_partition != source_partition:

            source_nodetype = None
            target_nodetype = None
            if source_partition.allocated_nodes[source_node_id] > MAX_STD_NODETYPE:
                source_nodetype = self.get_nodetype(get_string_node_type(source_partition.allocated_nodes[source_node_id], self.native_modules))
            if target_partition.allocated_nodes[target_node_id] > MAX_STD_NODETYPE:
                target_nodetype = self.get_nodetype(get_string_node_type(target_partition.allocated_nodes[target_node_id], self.native_modules))

            ngt = get_numerical_gate_type(gate_type, source_nodetype)
            nst = get_numerical_slot_type(slot_type, target_nodetype)

            if ngt > get_gates_per_type(source_partition.allocated_nodes[source_node_id], self.native_modules):
                raise ValueError("Node %s does not have a gate of type %s" % (source_node_uid, gate_type))

            if nst > get_slots_per_type(target_partition.allocated_nodes[target_node_id], self.native_modules):
                raise ValueError("Node %s does not have a slot of type %s" % (target_node_uid, slot_type))

            elements_from_indices = np.asarray([source_partition.allocated_node_offsets[source_node_id] + ngt], dtype=np.int32)
            elements_to_indices = np.asarray([target_partition.allocated_node_offsets[target_node_id] + nst], dtype=np.int32)
            new_w = np.eye(1, dtype=T.config.floatX)
            new_w[0, 0] = weight

            target_partition.set_inlink_weights(source_partition.spid, elements_from_indices, elements_to_indices, new_w)
        else:
            source_partition.set_link_weight(source_node_id, gate_type, target_node_id, slot_type, weight)

        if source_node_uid in self.proxycache:
            self.proxycache[source_node_uid].get_gate(gate_type).invalidate_caches()
        if target_node_uid in self.proxycache:
            self.proxycache[target_node_uid].get_slot(slot_type).invalidate_caches()
        for partition in self.partitions.values():
            if source_node_uid in partition.native_module_instances:
                partition.native_module_instances[source_node_uid].get_gate(gate_type).invalidate_caches()
            if target_node_uid in partition.native_module_instances:
                partition.native_module_instances[target_node_uid].get_slot(slot_type).invalidate_caches()

        return True

    def delete_link(self, source_node_uid, gate_type, target_node_uid, slot_type):
        result = self.set_link_weight(source_node_uid, gate_type, target_node_uid, slot_type, 0)
        return result

    def _load_nodetypes(self, nodetype_data):
        newnative_modules = {}
        for key, data in nodetype_data.items():
            if data.get('engine', self.engine) == self.engine:
                try:
                    if data.get('dimensionality'):
                        newnative_modules[key] = HighdimensionalNodetype(nodenet=self, **data)
                    else:
                        newnative_modules[key] = Nodetype(nodenet=self, **data)
                except Exception as err:
                    self.logger.error("Can not instantiate node type %s: %s: %s" % (key, err.__class__.__name__, str(err)))
                    post_mortem()
        return newnative_modules

    def reload_native_modules(self, native_modules):

        # check which instances need to be recreated because of gate/slot changes and keep their .data
        instances_to_recreate = {}
        instances_to_delete = {}

        # create the new nodetypes
        self.native_module_definitions = {}
        newnative_modules = self._load_nodetypes(native_modules)
        self.native_module_definitions = dict((uid, native_modules[uid]) for uid in newnative_modules)

        for partition in self.partitions.values():
            for uid, instance in partition.native_module_instances.items():
                if instance.type not in newnative_modules:
                    self.logger.warning("No more definition available for node type %s, deleting instance %s" %
                                (instance.type, uid))
                    instances_to_delete[uid] = instance
                    continue

                numeric_id = node_from_id(uid)

                # else:
                number_of_elements = len(np.where(partition.allocated_elements_to_nodes == numeric_id)[0])
                new_number_of_elements = max(len(newnative_modules[instance.type].slottypes), len(newnative_modules[instance.type].gatetypes))
                if number_of_elements != new_number_of_elements:
                    self.logger.warning("Number of elements changed for node type %s from %d to %d, recreating instance %s" %
                                    (instance.type, number_of_elements, new_number_of_elements, uid))
                    instances_to_recreate[uid] = instance.get_data(complete=True, include_links=False)

            # actually remove the instances
            for uid in instances_to_delete.keys():
                self.delete_node(uid)
            for uid in instances_to_recreate.keys():
                self.delete_node(uid)

            self.native_modules = newnative_modules

            # update the living instances that have the same slot/gate numbers
            new_native_module_instances = {}
            for uid in list(partition.native_module_instances.keys()):
                instance = partition.native_module_instances[uid]
                if not isinstance(instance._nodetype, type(self.native_modules[instance.type])):
                    self.logger.warning("Nature of nodetype changed for node %s. Deleting" % instance)
                    self.delete_node(uid)
                    continue
                parameters = instance.clone_parameters()
                state = instance.clone_state()
                position = instance.position
                name = instance.name
                partition = self.get_partition(uid)
                new_instance = TheanoNode(self, partition, instance.parent_nodespace, uid, partition.allocated_nodes[node_from_id(uid)])

                new_native_module_instances[uid] = new_instance
                new_instance.position = position
                new_instance.name = name
                for key, value in parameters.items():
                    try:
                        new_instance.set_parameter(key, value)
                    except NameError:
                        pass  # parameter not defined anymore
                for key, value in state.items():
                    new_instance.set_state(key, value)

            partition.native_module_instances = new_native_module_instances

        self.update_numeric_native_module_types()

        # recreate the deleted ones. Gate configurations and links will not be transferred.
        for uid, data in instances_to_recreate.items():
            new_uid = self.create_node(
                data['type'],
                data['parent_nodespace'],
                data['position'],
                name=data['name'],
                uid=uid,
                parameters=data['parameters'])

    def update_numeric_native_module_types(self):
        """
        update native modules numeric types if the types have been updated
        either due to reload_native_modules, or due to changing the worldadapter
        """
        for key, partition in self.partitions.items():
            native_module_ids = np.where(partition.allocated_nodes > MAX_STD_NODETYPE)[0]
            for id in native_module_ids:
                instance = self.get_node(node_to_id(id, partition.pid))
                partition.allocated_nodes[id] = get_numerical_node_type(instance.type, self.native_modules)

    def get_activation_data(self, nodespace_uids=[], rounded=1):
        if rounded is not None:
            mult = math.pow(10, rounded)
        activations = {}
        if nodespace_uids == []:
            for partition in self.partitions.values():
                ids = np.nonzero(partition.allocated_nodes)[0]
                for id in ids:
                    elements = get_elements_per_type(partition.allocated_nodes[id], self.native_modules)
                    offset = partition.allocated_node_offsets[id]
                    if rounded is None:
                        act = [n.item() for n in partition.a.get_value()[offset:offset+elements]]
                        if set(act) != {0}:
                            activations[node_to_id(id, partition.pid)] = act
                    else:
                        act = [n.item() / mult for n in np.rint(partition.a.get_value()[offset:offset+elements]*mult)]
                        if set(act) != {0}:
                            activations[node_to_id(id, partition.pid)] = act
        else:
            for nsuid in nodespace_uids:
                nodespace = self.get_nodespace(nsuid)
                partition = self.get_nodespace(nodespace.uid).partition
                nodespace_id = nodespace_from_id(nodespace.uid)
                ids = np.where(partition.allocated_node_parents == nodespace_id)[0]
                for id in ids:
                    elements = get_elements_per_type(partition.allocated_nodes[id], self.native_modules)
                    offset = partition.allocated_node_offsets[id]
                    if rounded is None:
                        act = [n.item() for n in partition.a.get_value()[offset:offset+elements]]
                        if set(act) != {0}:
                            activations[node_to_id(id, partition.pid)] = act
                    else:
                        act = [n.item() / mult for n in np.rint(partition.a.get_value()[offset:offset+elements]*mult)]
                        if set(act) != {0}:
                            activations[node_to_id(id, partition.pid)] = act
        return activations

    def get_nodetype(self, type):
        if type in self.nodetypes:
            return self.nodetypes[type]
        else:
            return self.native_modules.get(type)

    def construct_links_list(self, nodespace_uid=None):
        data = []

        for partition in self.partitions.values():
            if nodespace_uid is not None:
                nspartition = self.get_partition(nodespace_uid)
                if nspartition != partition:
                    continue

            w_matrix = partition.w.get_value(borrow=True)
            link_to_indices, link_from_indices = np.nonzero(w_matrix)

            for i, link_from_index in enumerate(link_from_indices):
                link_to_index = link_to_indices[i]

                source_id = partition.allocated_elements_to_nodes[link_from_index]
                source_type = partition.allocated_nodes[source_id]

                if nodespace_uid is not None:
                    nid = nodespace_from_id(nodespace_uid)
                    if partition.allocated_node_parents[source_id] != nid:
                        continue

                target_id = partition.allocated_elements_to_nodes[link_to_index]
                target_type = partition.allocated_nodes[target_id]

                target_slot_numerical = link_to_index - partition.allocated_node_offsets[target_id]
                target_slot_type = get_string_slot_type(target_slot_numerical, self.get_nodetype(get_string_node_type(target_type, self.native_modules)))

                source_gate_numerical = link_from_index - partition.allocated_node_offsets[source_id]
                source_gate_type = get_string_gate_type(source_gate_numerical, self.get_nodetype(get_string_node_type(source_type, self.native_modules)))

                weight = w_matrix[link_to_index, link_from_index].item()

                data.append({
                    "weight": weight,
                    "target_slot_name": target_slot_type,
                    "target_node_uid": node_to_id(target_id, partition.pid),
                    "source_gate_name": source_gate_type,
                    "source_node_uid": node_to_id(source_id, partition.pid)
                })

            # find links going out to other partitions
            for partition_to_spid, to_partition in self.partitions.items():
                if partition.spid in to_partition.inlinks:
                    inlinks = to_partition.inlinks[partition.spid]
                    from_elements = inlinks[0].get_value(borrow=True)
                    to_elements = inlinks[1].get_value(borrow=True)

                    inlink_type = inlinks[4]
                    if inlink_type == "dense":
                        weights = inlinks[2].get_value(borrow=True)
                        for i, element in enumerate(to_elements):
                            slotrow = weights[i]
                            links_indices = np.nonzero(slotrow)[0]
                            for link_index in links_indices:
                                source_id = partition.allocated_elements_to_nodes[from_elements[link_index]]
                                source_type = partition.allocated_nodes[source_id]
                                source_gate_numerical = from_elements[link_index] - partition.allocated_node_offsets[source_id]
                                source_gate_type = get_string_gate_type(source_gate_numerical, self.get_nodetype(get_string_node_type(source_type, self.native_modules)))

                                target_id = to_partition.allocated_elements_to_nodes[element]
                                target_type = to_partition.allocated_nodes[target_id]
                                target_slot_numerical = element - to_partition.allocated_node_offsets[target_id]
                                target_slot_type = get_string_slot_type(target_slot_numerical, self.get_nodetype(get_string_node_type(target_type, self.native_modules)))

                                data.append({
                                    "weight": float(weights[i, link_index]),
                                    "target_slot_name": target_slot_type,
                                    "target_node_uid": node_to_id(target_id, to_partition.pid),
                                    "source_gate_name": source_gate_type,
                                    "source_node_uid": node_to_id(source_id, partition.pid)
                                })
                    elif inlink_type == "identity":
                        for i, element in enumerate(to_elements):
                            source_id = partition.allocated_elements_to_nodes[from_elements[i]]
                            source_type = partition.allocated_nodes[source_id]
                            source_gate_numerical = from_elements[link_index] - partition.allocated_node_offsets[source_id]
                            source_gate_type = get_string_gate_type(source_gate_numerical, self.get_nodetype(get_string_node_type(source_type, self.native_modules)))

                            target_id = to_partition.allocated_elements_to_nodes[element]
                            target_type = to_partition.allocated_nodes[target_id]
                            target_slot_numerical = element - to_partition.allocated_node_offsets[target_id]
                            target_slot_type = get_string_slot_type(target_slot_numerical, self.get_nodetype(get_string_node_type(target_type, self.native_modules)))

                            data.append({
                                "weight": 1.,
                                "target_slot_name": target_slot_type,
                                "target_node_uid": node_to_id(target_id, to_partition.pid),
                                "source_gate_name": source_gate_type,
                                "source_node_uid": node_to_id(source_id, partition.pid)
                            })

        return data

    def construct_native_modules_and_comments_dict(self):
        data = {}
        i = 0
        for partition in self.partitions.values():
            nodeids = np.where((partition.allocated_nodes > MAX_STD_NODETYPE) | (partition.allocated_nodes == COMMENT))[0]
            for node_id in nodeids:
                i += 1
                node_uid = node_to_id(node_id, partition.pid)
                data[node_uid] = self.get_node(node_uid).get_data(complete=True)
        return data

    def construct_native_modules_numpy_state_dict(self):
        numpy_states = {}
        i = 0
        for partition in self.partitions.values():
            nodeids = np.where((partition.allocated_nodes > MAX_STD_NODETYPE) | (partition.allocated_nodes == COMMENT))[0]
            for node_id in nodeids:
                node_uid = node_to_id(node_id, partition.pid)
                numpy_states[node_uid] = self.get_node(node_uid).get_persistable_state()[1]
        return numpy_states

    def construct_nodes_dict(self, nodespace_uid=None, complete=False, include_links=True):
        data = {}
        for partition in self.partitions.values():
            if nodespace_uid is not None:
                nodespace_partition = self.get_partition(nodespace_uid)
                if nodespace_partition != partition:
                    continue

            nodeids = np.nonzero(partition.allocated_nodes)[0]
            if nodespace_uid is not None:
                parent_id = nodespace_from_id(nodespace_uid)
                nodeids = np.where(partition.allocated_node_parents == parent_id)[0]
            for node_id in nodeids:
                node_uid = node_to_id(node_id, partition.pid)
                data[node_uid] = self.get_node(node_uid).get_data(complete=complete, include_links=include_links)
        return data

    def construct_nodespaces_dict(self, nodespace_uid, transitive=False):
        data = {}
        if nodespace_uid is None:
            nodespace_uid = self.get_nodespace(None).uid

        if transitive:
            for partition in self.partitions.values():
                nodespace_id = nodespace_from_id(nodespace_uid)
                nodespace_ids = np.nonzero(partition.allocated_nodespaces)[0]
                nodespace_ids = np.append(nodespace_ids, 1)
                for candidate_id in nodespace_ids:
                    is_in_hierarchy = False
                    if candidate_id == nodespace_id:
                        is_in_hierarchy = True
                    else:
                        parent_id = partition.allocated_nodespaces[candidate_id]
                        while parent_id > 0 and parent_id != nodespace_id:
                            parent_id = partition.allocated_nodespaces[parent_id]
                        if parent_id == nodespace_id:
                            is_in_hierarchy = True

                    if is_in_hierarchy:
                        data[nodespace_to_id(candidate_id, partition.pid)] = self.get_nodespace(nodespace_to_id(candidate_id, partition.pid)).get_data()

            if nodespace_uid in self.partitionmap:
                for partition in self.partitionmap[nodespace_uid]:
                    partition_root_uid = partition.rootnodespace_uid
                    data[partition_root_uid] = self.get_nodespace(partition_root_uid).get_data()

        else:
            for uid in self.get_nodespace(nodespace_uid).get_known_ids('nodespaces'):
                data[uid] = self.get_nodespace(uid).get_data()

        return data

    def construct_modulators_dict(self):
        return self._modulators.copy()

    def get_standard_nodetype_definitions(self):
        """
        Returns the standard node types supported by this nodenet
        """
        return copy.deepcopy(STANDARD_NODETYPES)

    def set_sensors_and_actuator_feedback_values(self):
        """
        Sets the values for sensors and actuator_feedback from the worldadapter
        """
        # convert from python types:
        sensor_values = np.array([])
        actuator_feedback_values = np.array([])
        if self._worldadapter_instance:
            sensor_values = np.concatenate((sensor_values, np.asarray(self._worldadapter_instance.get_datasource_values())))
            actuator_feedback_values = np.concatenate((actuator_feedback_values, np.asarray(self._worldadapter_instance.get_datatarget_feedback_values())))
        if self.use_modulators:
            # include modulators
            readables = [0 for _ in DoernerianEmotionalModulators.readable_modulators]
            for idx, key in enumerate(sorted(DoernerianEmotionalModulators.readable_modulators)):
                readables[idx] = self.get_modulator(key)
            sensor_values = np.concatenate((sensor_values, np.asarray(readables)))
            writeables = [0 for _ in DoernerianEmotionalModulators.writeable_modulators]
            for idx, key in enumerate(sorted(DoernerianEmotionalModulators.writeable_modulators)):
                writeables[idx] = 1
            actuator_feedback_values = np.concatenate((actuator_feedback_values, np.asarray(writeables)))

        for partition in self.partitions.values():
            a_array = partition.a.get_value(borrow=True)
            valid = np.where(partition.sensor_indices >= 0)[0]
            a_array[partition.sensor_indices[valid]] = sensor_values[valid]
            valid = np.where(partition.actuator_indices >= 0)[0]
            a_array[partition.actuator_indices[valid]] = actuator_feedback_values[valid]
            partition.a.set_value(a_array, borrow=True)

    def set_actuator_values(self):
        """
        Writes the values from the actuators to datatargets and modulators
        """
        actuator_values_to_write = np.zeros(self.rootpartition.actuator_indices.shape)
        for partition in self.partitions.values():
            a_array = partition.a.get_value(borrow=True)
            valid = np.where(partition.actuator_indices >= 0)
            actuator_values_to_write[valid] += a_array[partition.actuator_indices[valid]]
        if self.use_modulators:
            writeables = sorted(DoernerianEmotionalModulators.writeable_modulators)
            # remove modulators from actuator values
            modulator_values = actuator_values_to_write[-len(writeables):]
            actuator_values_to_write = actuator_values_to_write[:-len(writeables)]
            for idx, key in enumerate(writeables):
                if key in self.actuatormap:
                    self.set_modulator(key, modulator_values[idx])
        if self._worldadapter_instance:
            self._worldadapter_instance.add_datatarget_values(actuator_values_to_write)

    def _rebuild_sensor_actuator_indices(self, partition=None):
        """
        Rebuilds the actuator and sensor indices of the given partition or all partitions if None
        """
        if partition is not None:
            partitions = [partition]
        else:
            partitions = self.partitions.values()
        for partition in partitions:
            partition.sensor_indices = np.empty(len(self.get_datasources()), np.int32)
            partition.sensor_indices.fill(-1)
            partition.actuator_indices = np.empty(len(self.get_datatargets()), np.int32)
            partition.actuator_indices.fill(-1)
            for datatarget, node_id in self.actuatormap.items():
                if not isinstance(node_id, str):
                    node_id = node_id[0]
                if self.get_partition(node_id) == partition:
                    self.get_node(node_id).set_parameter("datatarget", datatarget)

            for datasource, node_id in self.sensormap.items():
                if not isinstance(node_id, str):
                    node_id = node_id[0]
                if self.get_partition(node_id) == partition:
                    self.get_node(node_id).set_parameter("datasource", datasource)

    def group_nodes_by_names(self, nodespace_uid, node_name_prefix=None, gatetype="gen", sortby='id', group_name=None):
        if nodespace_uid is None:
            nodespace_uid = self.get_nodespace(None).uid

        partition = self.get_partition(nodespace_uid)

        if group_name is None:
            group_name = node_name_prefix

        ids = []
        for uid, name in self.names.items():
            parentpartition = self.get_partition(uid)
            if parentpartition == partition and self.is_node(uid) and name.startswith(node_name_prefix) and \
                    (parentpartition.allocated_node_parents[node_from_id(uid)] == nodespace_from_id(nodespace_uid)):
                ids.append(uid)
        self.group_nodes_by_ids(nodespace_uid, ids, group_name, gatetype, sortby)

    def group_nodes_by_ids(self, nodespace_uid, node_uids, group_name, gatetype="gen", sortby=None):
        if nodespace_uid is None:
            nodespace_uid = self.get_nodespace(None).uid
        partition = self.get_partition(nodespace_uid)

        ids = [node_from_id(uid) for uid in node_uids]
        if sortby == 'id':
            ids = sorted(ids)
        elif sortby == 'name':
            ids = sorted(ids, key=lambda id: self.names[node_to_id(id, partition.pid)])

        partition.group_nodes_by_ids(nodespace_uid, ids, group_name, gatetype)

    def group_highdimensional_elements(self, node_uid, gate=None, slot=None, group_name=None):
        partition = self.get_partition(node_uid)
        partition.group_highdimensional_elements(node_uid, gate=gate, slot=slot, group_name=group_name)

    def ungroup_nodes(self, nodespace_uid, group):
        if nodespace_uid is None:
            nodespace_uid = self.get_nodespace(None).uid
        partition = self.get_partition(nodespace_uid)
        partition.ungroup_nodes(nodespace_uid, group)

    def get_activations(self, nodespace_uid, group):
        if nodespace_uid is None:
            nodespace_uid = self.get_nodespace(None).uid
        partition = self.get_partition(nodespace_uid)
        return partition.get_activations(nodespace_uid, group)

    def set_activations(self, nodespace_uid, group, new_activations):
        if nodespace_uid is None:
            nodespace_uid = self.get_nodespace(None).uid
        partition = self.get_partition(nodespace_uid)
        partition.set_activations(nodespace_uid, group, new_activations)

    def get_gate_configurations(self, nodespace_uid, group, gatefunction_parameter=None):
        if nodespace_uid is None:
            nodespace_uid = self.get_nodespace(None).uid
        partition = self.get_partition(nodespace_uid)
        return partition.get_gate_configurations(nodespace_uid, group, gatefunction_parameter)

    def set_gate_configurations(self, nodespace_uid, group, gatefunction, gatefunction_parameter=None, parameter_values=None):
        if nodespace_uid is None:
            nodespace_uid = self.get_nodespace(None).uid
        partition = self.get_partition(nodespace_uid)
        partition.set_gate_configurations(nodespace_uid, group, gatefunction, gatefunction_parameter, parameter_values)

    def get_link_weights(self, nodespace_from_uid, group_from, nodespace_to_uid, group_to):
        if nodespace_from_uid is None:
            nodespace_from_uid = self.get_nodespace(None).uid
        if nodespace_to_uid is None:
            nodespace_to_uid = self.get_nodespace(None).uid
        partition_from = self.get_partition(nodespace_from_uid)
        partition_to = self.get_partition(nodespace_to_uid)

        if partition_to != partition_from:
            if nodespace_from_uid not in partition_from.nodegroups or group_from not in partition_from.nodegroups[nodespace_from_uid]:
                raise ValueError("Group %s does not exist in nodespace %s." % (group_from, nodespace_from_uid))
            if nodespace_to_uid not in partition_to.nodegroups or group_to not in partition_to.nodegroups[nodespace_to_uid]:
                raise ValueError("Group %s does not exist in nodespace %s." % (group_to, nodespace_to_uid))

            from_els = partition_from.nodegroups[nodespace_from_uid][group_from]
            to_els = partition_to.nodegroups[nodespace_to_uid][group_to]
            zero_weights = np.zeros((len(to_els), len(from_els)))

            if partition_from.spid not in partition_to.inlinks:
                return zero_weights

            inlinks = partition_to.inlinks[partition_from.spid]
            from_indices = inlinks[0].get_value(borrow=True)
            to_indices = inlinks[1].get_value(borrow=True)

            if len(np.union1d(from_indices, from_els)) > len(from_indices) or len(np.union1d(to_indices, to_els)) > len(to_indices):
                self.set_link_weights(nodespace_from_uid, group_from, nodespace_to_uid, group_to, zero_weights)
                inlinks = partition_to.inlinks[partition_from.spid]
                from_indices = inlinks[0].get_value(borrow=True)
                to_indices = inlinks[1].get_value(borrow=True)

            search_from = np.searchsorted(from_indices, from_els)
            search_to = np.searchsorted(to_indices, to_els)
            cols, rows = np.meshgrid(search_from, search_to)
            return inlinks[2].get_value(borrow=True)[rows, cols]
        else:
            return partition_from.get_link_weights(nodespace_from_uid, group_from, nodespace_to_uid, group_to)

    def set_link_weights(self, nodespace_from_uid, group_from, nodespace_to_uid, group_to, new_w):
        if nodespace_from_uid is None:
            nodespace_from_uid = self.get_nodespace(None).uid
        if nodespace_to_uid is None:
            nodespace_to_uid = self.get_nodespace(None).uid

        partition_from = self.get_partition(nodespace_from_uid)
        partition_to = self.get_partition(nodespace_to_uid)

        if partition_to != partition_from:
            if nodespace_from_uid not in partition_from.nodegroups or group_from not in partition_from.nodegroups[nodespace_from_uid]:
                raise ValueError("Group %s does not exist in nodespace %s." % (group_from, nodespace_from_uid))
            if nodespace_to_uid not in partition_to.nodegroups or group_to not in partition_to.nodegroups[nodespace_to_uid]:
                raise ValueError("Group %s does not exist in nodespace %s." % (group_to, nodespace_to_uid))

            elements_from_indices = np.array(partition_from.nodegroups[nodespace_from_uid][group_from], dtype='int32')
            elements_to_indices = np.array(partition_to.nodegroups[nodespace_to_uid][group_to], dtype='int32')

            partition_to.set_inlink_weights(partition_from.spid, elements_from_indices, elements_to_indices, new_w)
        else:
            partition_from.set_link_weights(nodespace_from_uid, group_from, nodespace_to_uid, group_to, new_w)

        self.proxycache.clear()

    def get_available_gatefunctions(self):
        return {
            "identity": {},
            "absolute": {},
            "sigmoid": {'bias': 0},
            "elu": {'bias': 0},
            "relu": {'bias': 0},
            "one_over_x": {},
            "threshold": {
                "minimum": 0,
                "maximum": 1,
                "amplification": 1,
                "threshold": 0
            }
        }

    def add_slot_monitor(self, node_uid, slot, **_):
        raise RuntimeError("Theano engine does not support slot monitors")

    def has_nodespace_changes(self, nodespace_uids=[], since_step=0):
        if nodespace_uids == []:
            nodespace_uids = self.get_nodespace_uids()

        for nodespace_uid in nodespace_uids:
            nodespace = self.get_nodespace(nodespace_uid)
            partition = self.get_partition(nodespace.uid)
            if partition.has_nodespace_changes(nodespace.uid, since_step):
                return True
        return False

    def get_nodespace_changes(self, nodespace_uids=[], since_step=0, include_links=True):
        result = {
            'nodes_dirty': {},
            'nodespaces_dirty': {},
            'nodes_deleted': [],
            'nodespaces_deleted': []
        }

        if nodespace_uids == []:
            nodespace_uids = self.get_nodespace_uids()

        nodespaces_by_partition = {}
        for nodespace_uid in nodespace_uids:
            spid = self.get_partition(nodespace_uid).spid
            if spid not in nodespaces_by_partition:
                nodespaces_by_partition[spid] = []
            nodespace_uid = self.get_nodespace(nodespace_uid).uid  # b/c of None == Root
            nodespaces_by_partition[spid].append(nodespace_from_id(nodespace_uid))

        for nsuid in nodespace_uids:
            nodespace = self.get_nodespace(nsuid)
            partition = self.get_partition(nodespace.uid)
            for i in range(since_step, self.current_step + 1):
                if i in self.deleted_items:
                    result['nodespaces_deleted'].extend(self.deleted_items[i].get('nodespaces_deleted', []))
                    result['nodes_deleted'].extend(self.deleted_items[i].get('nodes_deleted', []))
            changed_nodes, changed_nodespaces = partition.get_nodespace_changes(nodespace.uid, since_step)
            nodes, _, _ = partition.get_node_data(ids=changed_nodes, nodespaces_by_partition=nodespaces_by_partition, include_links=include_links)
            result['nodes_dirty'].update(nodes)
            for uid in changed_nodespaces:
                uid = nodespace_to_id(uid, partition.pid)
                result['nodespaces_dirty'][uid] = self.get_nodespace(uid).get_data()
        return result

    def get_dashboard(self):
        data = super().get_dashboard()
        data['count_nodes'] = 0
        data['count_links'] = -1
        data['count_positive_nodes'] = 0
        data['count_negative_nodes'] = 0
        data['modulators'] = self.construct_modulators_dict()
        data['nodetypes'] = {'NativeModules': 0}
        data['concepts'] = {
            'checking': 0,
            'verified': 0,
            'failed': 0,
            'off': 0
        }
        data['schemas'] = {
            'checking': 0,
            'verified': 0,
            'failed': 0,
            'off': 0,
            'total': 0
        }
        for uid, partition in self.partitions.items():
            node_ids = np.nonzero(partition.allocated_nodes)[0]
            data['count_nodes'] += len(node_ids)
            for id in node_ids:
                if partition.allocated_nodes[id] <= MAX_STD_NODETYPE:
                    nodetype = get_string_node_type(partition.allocated_nodes[id])
                    if nodetype not in data['nodetypes']:
                        data['nodetypes'][nodetype] = 1
                    else:
                        data['nodetypes'][nodetype] += 1
                else:
                    data['nodetypes']['NativeModules'] += 1
                act = float(partition.a.get_value(borrow=True)[partition.allocated_node_offsets[id] + GEN])
                if act > 0:
                    data['count_positive_nodes'] += 1
                elif act < 0:
                    data['count_negative_nodes'] += 1
                if partition.allocated_nodes[id] == PIPE:
                    node = self.get_node(node_to_id(id, partition.pid))
                    if node.get_gate('gen').activation == 0 and node.get_gate('sub').activation > 0 and len(node.get_gate('sub').get_links()):
                        data['concepts']['checking'] += 1
                        if node.get_gate('sur').get_links() == []:
                            data['schemas']['checking'] += 1
                    elif node.get_gate('sub').activation > 0 and node.activation > 0.5:
                        data['concepts']['verified'] += 1
                        if node.get_gate('sur').get_links() == []:
                            data['schemas']['verified'] += 1
                    elif node.activation < 0:
                        data['concepts']['failed'] += 1
                        if node.get_gate('sur').get_links() == []:
                            data['schemas']['failed'] += 1
                    else:
                        data['concepts']['off'] += 1
                        if node.get_gate('sur').get_links() == []:
                            data['schemas']['off'] += 1
        data['schemas']['total'] = sum(data['schemas'].values())
        data['concepts']['total'] = sum(data['concepts'].values())
        return data


class TheanoNodenet(TheanoFlowEngine, TheanoNodenetCore):
    pass
