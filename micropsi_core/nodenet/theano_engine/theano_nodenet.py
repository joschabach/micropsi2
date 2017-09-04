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
import networkx as nx

try:
    import ipdb as pdb
except ImportError:
    import pdb

from micropsi_core.tools import post_mortem
from micropsi_core.tools import OrderedSet
from micropsi_core.nodenet import monitor
from micropsi_core.nodenet import recorder
from micropsi_core.nodenet.nodenet import Nodenet, NODENET_VERSION
from micropsi_core.nodenet.node import Nodetype, FlowNodetype, HighdimensionalNodetype
from micropsi_core.nodenet.stepoperators import DoernerianEmotionalModulators
from micropsi_core.nodenet.theano_engine.theano_node import *
from micropsi_core.nodenet.theano_engine.theano_definitions import *
from micropsi_core.nodenet.theano_engine.theano_stepoperators import *
from micropsi_core.nodenet.theano_engine.theano_nodespace import *
from micropsi_core.nodenet.theano_engine.theano_netapi import TheanoNetAPI
from micropsi_core.nodenet.theano_engine.theano_partition import TheanoPartition
from micropsi_core.nodenet.theano_engine.theano_flowmodule import FlowModule

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


class TheanoNodenet(Nodenet):
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
        typechange = True
        if self._worldadapter_instance and self.worldadapter == _worldadapter_instance.__class__.__name__:
            typechange = False
        if self._worldadapter_instance != _worldadapter_instance:
            self._worldadapter_instance = _worldadapter_instance
            self._rebuild_sensor_actuator_indices()

            flow_io_types = self.generate_worldadapter_flow_types(delete_existing=typechange)
            self.native_module_definitions.update(flow_io_types)
            for key in flow_io_types:
                self.native_modules[key] = FlowNodetype(nodenet=self, **flow_io_types[key])
            self.update_numeric_native_module_types()
            self.generate_worldadapter_flow_instances()
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

        precision = settings['theano']['precision']
        if precision == "32":
            T.config.floatX = "float32"
            self.theanofloatX = "float32"
            self.scipyfloatX = scipy.float32
            self.numpyfloatX = np.float32
            self.byte_per_float = 4
        elif precision == "64":
            T.config.floatX = "float64"
            self.theanofloatX = "float64"
            self.scipyfloatX = scipy.float64
            self.numpyfloatX = np.float64
            self.byte_per_float = 8
        else:
            raise RuntimeError("Unsupported float precision value")

        device = T.config.device
        self.logger.info("Theano configured to use %s", device)
        if device.startswith("gpu"):
            self.logger.info("Using CUDA with cuda_root=%s and theano_flags=%s", os.environ["CUDA_ROOT"], os.environ["THEANO_FLAGS"])
            if T.config.floatX != "float32":
                self.logger.warning("Precision set to %s, but attempting to use gpu.", precision)

        self.netapi = TheanoNetAPI(self)

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

        self._step = 0

        self.proxycache = {}

        self.stepoperators = []
        self.initialize_stepoperators()

        self.native_module_definitions = {}
        for key in native_modules:
            if native_modules[key].get('engine', self.engine) == self.engine:
                self.native_module_definitions[key] = native_modules[key]

        self.flow_module_instances = {}
        self.flow_graphs = []
        self.thetas = {}

        flow_io_types = self.generate_worldadapter_flow_types(delete_existing=True)
        self.native_module_definitions.update(flow_io_types)
        for key in flow_io_types:
            self.native_modules[key] = FlowNodetype(nodenet=self, **flow_io_types[key])

        self.flowgraph = nx.MultiDiGraph()
        self.is_flowbuilder_active = False
        self.flowfunctions = []
        self.worldadapter_flow_nodes = {}

        self.create_nodespace(None, "Root", nodespace_to_id(1, rootpartition.pid))

        self.initialize_nodenet({})

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
            TheanoCalculate(self),
            TheanoCalculateFlowmodules(self)]
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
        metadata['recorders'] = self.construct_recorders_dict()
        metadata['worldadapter_flow_nodes'] = self.worldadapter_flow_nodes
        if zipfile:
            zipfile.writestr('nodenet.json', json.dumps(metadata))
        else:
            with open(os.path.join(base_path, 'nodenet.json'), 'w+', encoding="utf-8") as fp:
                fp.write(json.dumps(metadata, sort_keys=True, indent=4))

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

        for node_uid in self.thetas:
            # save thetas
            data = {}
            filename = "%s_thetas.npz" % node_uid
            for idx, name in enumerate(self.thetas[node_uid]['names']):
                data[name] = self.thetas[node_uid]['variables'][idx].get_value()
            if zipfile:
                stream = io.BytesIO()
                np.savez(stream, **data)
                stream.seek(0)
                zipfile.writestr(filename, stream.getvalue())
            else:
                np.savez(os.path.join(base_path, filename), **data)

        # write graph data
        if zipfile:
            stream = io.BytesIO()
            nx.write_gpickle(self.flowgraph, stream)
            stream.seek(0)
            zipfile.writestr("flowgraph.pickle", stream.getvalue())
        else:
            nx.write_gpickle(self.flowgraph, os.path.join(base_path, "flowgraph.pickle"))

        for recorder_uid in self._recorders:
            self._recorders[recorder_uid].save()

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
            self.worldadapter_flow_nodes = initfrom.get('worldadapter_flow_nodes', {})
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

            for monitorid in monitors:
                data = monitors[monitorid]
                if hasattr(monitor, data['classname']):
                    mon = getattr(monitor, data['classname'])(self, **data)
                    self._monitors[mon.uid] = mon
                else:
                    self.logger.warning('unknown classname for monitor: %s (uid:%s) ' % (data['classname'], monitorid))

            for recorder_uid in initfrom.get('recorders', {}):
                data = initfrom['recorders'][recorder_uid]
                self._recorders[recorder_uid] = getattr(recorder, data['classname'])(self, **data)

            flowfile = os.path.join(self.persistency_path, 'flowgraph.pickle')

            if os.path.isfile(flowfile):
                self.flowgraph = nx.read_gpickle(flowfile)

            for node_uid in nx.topological_sort(self.flowgraph):
                if node_uid in self.flow_module_instances:
                    self.flow_module_instances[node_uid].ensure_initialized()
                    theta_file = os.path.join(self.persistency_path, "%s_thetas.npz" % node_uid)
                    if os.path.isfile(theta_file):
                        data = np.load(theta_file)
                        for key in data:
                            self.set_theta(node_uid, key, data[key])
                else:
                    self._delete_flow_module(node_uid)

            self.update_flow_graphs()

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
                if data.get('flow_module'):
                    if self.native_module_definitions[data['type']].get('flow_module'):
                        node = FlowModule(
                            self,
                            self.get_partition(uid),
                            data['parent_nodespace'],
                            data['uid'],
                            get_numerical_node_type(data['type'], nativemodules=self.native_modules),
                            parameters=data.get('parameters', {}),
                            inputmap=data.get('inputmap', {}),
                            outputmap=data.get('outputmap', {}),
                            is_copy_of=data.get('is_copy_of'))
                        self.flow_module_instances[node.uid] = node
                    else:
                        invalid_nodes[uid] = data
                        continue
                else:
                    if not self.native_module_definitions[data['type']].get('flow_module'):
                        node = TheanoNode(self, self.get_partition(uid), parent_uid, uid, get_numerical_node_type(data['type'], nativemodules=self.native_modules), parameters=data.get('parameters'))
                    else:
                        invalid_nodes[uid] = data
                        continue
                self.proxycache[node.uid] = node
                new_uid = node.uid
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

        for uid in invalid_nodes:
            if invalid_nodes[uid].get('flow_module'):
                self._delete_flow_module(uid)
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
            raise KeyError("No node with id %s exists", uid)
        if uid in partition.native_module_instances:
            if uid in self.flow_module_instances:
                return self.flow_module_instances[uid]
            else:
                return partition.native_module_instances[uid]
        elif uid in partition.comment_instances:
            return partition.comment_instances[uid]
        elif uid in self.proxycache:
            return self.proxycache[uid]
        elif self.is_node(uid):
            id = node_from_id(uid)
            parent_id = partition.allocated_node_parents[id]
            nodetype = get_string_node_type(partition.allocated_nodes[id], self.native_modules)
            if type(self.get_nodetype(nodetype)) == FlowNodetype:
                node = FlowModule(self, partition, nodespace_to_id(parent_id, partition.pid), uid, partition.allocated_nodes[id])
                self.flow_module_instances[uid] = node
            else:
                node = TheanoNode(self, partition, nodespace_to_id(parent_id, partition.pid), uid, partition.allocated_nodes[id])
            self.proxycache[node.uid] = node
            return node
        else:
            raise KeyError("No node with id %s exists", uid)

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

    def _create_flow_module(self, node):
        self.flowgraph.add_node(node.uid, implementation=node.nodetype.implementation)

    def flow(self, source_uid, source_output, target_uid, target_input):
        if source_uid == "worldadapter":
            source_uid = self.worldadapter_flow_nodes['datasources']
        if target_uid == "worldadapter":
            target_uid = self.worldadapter_flow_nodes['datatargets']
        self.flowgraph.add_edge(source_uid, target_uid, key="%s_%s" % (source_output, target_input))
        self.flow_module_instances[target_uid].set_input(target_input, source_uid, source_output)
        self.flow_module_instances[source_uid].set_output(source_output, target_uid, target_input)
        self.update_flow_graphs()

    def unflow(self, source_uid, source_output, target_uid, target_input):
        if source_uid == "worldadapter":
            source_uid = self.worldadapter_flow_nodes['datasources']
        if target_uid == "worldadapter":
            target_uid = self.worldadapter_flow_nodes['datatargets']
        self.flowgraph.remove_edge(source_uid, target_uid, key="%s_%s" % (source_output, target_input))
        self.flow_module_instances[target_uid].unset_input(target_input)
        self.flow_module_instances[source_uid].unset_output(source_output, target_uid, target_input)
        self.update_flow_graphs()

    def _delete_flow_module(self, delete_uid):
        if delete_uid in self.flowgraph.nodes():
            self.flowgraph.remove_node(delete_uid)
        for uid, module in self.flow_module_instances.items():
            for name in module.inputmap:
                if module.inputmap[name]:
                    source_uid, source_name = module.inputmap[name]
                    if source_uid == delete_uid:
                        module.unset_input(name)
            for name in module.outputmap:
                for target_uid, target_name in module.outputmap[name].copy():
                    if target_uid == delete_uid:
                        module.unset_output(name, delete_uid, target_name)
        if delete_uid in self.flow_module_instances:
            del self.flow_module_instances[delete_uid]
        self.update_flow_graphs()

    def update_flow_graphs(self, node_uids=None):
        if self.is_flowbuilder_active:
            return
        self.flowfunctions = []
        startpoints = []
        endpoints = []
        pythonnodes = set()

        toposort = nx.topological_sort(self.flowgraph)
        self.flow_toposort = toposort
        for uid in toposort:
            node = self.flow_module_instances.get(uid)
            if node is not None:
                if node.implementation == 'python':
                    pythonnodes.add(uid)
                if node.is_input_node():
                    startpoints.append(uid)
                if node.is_output_node():
                    endpoints.append(uid)

        graphs = []
        for enduid in endpoints:
            ancestors = nx.ancestors(self.flowgraph, enduid)
            node = self.flow_module_instances[enduid]
            if ancestors or node.inputs == []:
                fullpath = [uid for uid in toposort if uid in ancestors] + [enduid]
                path = []
                for uid in reversed(fullpath):
                    if uid in endpoints and uid != enduid:
                        continue
                    path.insert(0, uid)
                if path:
                    graphs.append(path)

        # worldadapter_names = []
        # if self.worldadapter_instance is not None:
        #     worldadapter_names += self.worldadapter_instance.get_available_flow_datasources() + self.worldadapter_instance.get_available_flow_datatargets()

        flowfunctions = {}
        floworder = OrderedSet()
        for idx, graph in enumerate(graphs):
            # split graph in parts:
            # node_uids = [uid for uid in graph if uid not in worldadapter_names]
            node_uids = [uid for uid in graph]
            nodes = [self.get_node(uid) for uid in node_uids]
            paths = self.split_flow_graph_into_implementation_paths(nodes)
            for p in paths:
                floworder.add(p['hash'])
                if p['hash'] not in flowfunctions:
                    func, dang_in, dang_out = self.compile_flow_subgraph([n.uid for n in p['members']], use_unique_input_names=True)
                    if func:
                        flowfunctions[p['hash']] = {'callable': func, 'members': p['members'], 'endnodes': set([nodes[-1]]), 'inputs': dang_in, 'outputs': dang_out}
                else:
                    flowfunctions[p['hash']]['endnodes'].add(nodes[-1])
        for funcid in floworder:
            self.flowfunctions.append(flowfunctions[funcid])

        self.logger.debug("Compiled %d flowfunctions" % len(self.flowfunctions))

    def split_flow_graph_into_implementation_paths(self, nodes):
        paths = []
        for node in nodes:
            if node.implementation == 'python':
                paths.append({'implementation': 'python', 'members': [node], 'hash': node.uid})
            else:
                if len(paths) == 0 or paths[-1]['implementation'] == 'python':
                    paths.append({'implementation': 'theano', 'members': [node], 'hash': node.uid})
                else:
                    paths[-1]['members'].append(node)
                    paths[-1]['hash'] += node.uid

        return paths

    def compile_flow_subgraph(self, node_uids, requested_outputs=None, use_different_thetas=False, use_unique_input_names=False):
        """ Compile and return one callable for the given flow_module_uids.
        If use_different_thetas is True, the callable expects an argument names "thetas".
        Thetas are expected to be sorted in the same way collect_thetas() would return them.

        Parameters
        ----------
        node_uids : list
            the uids of the members of this graph

        requested_outputs : list, optional
            list of tuples (node_uid, out_name) to filter the callable's return-values. defaults to None, returning all outputs

        use_different_thetas : boolean, optional
            if true, return a callable that excepts a parameter "thetas" that will be used instead of existing thetas. defaults to False

        use_unique_input_names : boolen, optional
            if true, the returned callable expects input-kwargs to be prefixe by node_uid: "UID_NAME". defaults to False, using only the name of the input

        Returns
        -------
        callable : function
            the compiled function for this subgraph

        dangling_inputs : list
            list of tuples (node_uid, input) that the callable expectes as inputs

        dangling_outputs : list
            list of tuples (node_uid, input) that the callable will return as output

        """
        subgraph = [self.get_node(uid) for uid in self.flow_toposort if uid in node_uids]

        # split the nodes into symbolic/non-symbolic paths
        paths = self.split_flow_graph_into_implementation_paths(subgraph)

        dangling_inputs = []
        dangling_outputs = []

        thunks = []

        for path_idx, path in enumerate(paths):
            thunk = {
                'implementation': path['implementation'],
                'function': None,
                'node': None,
                'outputs': [],
                'input_sources': [],
                'dangling_outputs': [],
                'list_outputs': [],
                'members': path['members']
            }
            member_uids = [n.uid for n in path['members']]
            outexpressions = {}
            inputs = []
            outputs = []
            skip = False

            # index for outputs of this thunk, considering unpacked list outputs
            thunk_flattened_output_index = 0

            for node in path['members']:
                buildargs = []
                # collect the inputs for this Flowmodule:
                for in_idx, in_name in enumerate(node.inputs):
                    if not node.inputmap[in_name] or node.inputmap[in_name][0] not in member_uids:
                        # this input is not satisfied from within this path
                        in_expr = create_tensor(node.definition['inputdims'][in_idx], self.theanofloatX, name="%s_%s" % (node.uid, in_name))
                        inputs.append(in_expr)
                        if not node.inputmap[in_name] or node.inputmap[in_name][0] not in node_uids:
                            # it's not even satisfied by another path within the subgraph,
                            # and needs to be provided as input to the emerging callable
                            if use_unique_input_names:
                                thunk['input_sources'].append(('kwargs', -1, "%s_%s" % (node.uid, in_name)))
                            else:
                                thunk['input_sources'].append(('kwargs', -1, in_name))
                            dangling_inputs.append((node.uid, in_name))
                        else:
                            # this input will be satisfied by another path within the subgraph
                            source_uid, source_name = node.inputmap[in_name]
                            for idx, p in enumerate(paths):
                                if self.get_node(source_uid) in p['members']:
                                    # record which thunk, and which index of its output-array satisfies this input
                                    thunk['input_sources'].append(('path', idx, thunks[idx]['outputs'].index((source_uid, source_name))))
                        buildargs.append(in_expr)
                    else:
                        # this input is satisfied within this path
                        source_uid, source_name = node.inputmap[in_name]
                        buildargs.append(outexpressions[source_uid][self.get_node(source_uid).outputs.index(source_name)])

                # build the outexpression
                try:
                    if len(node.outputs) <= 1:
                        original_outex = [node.build(*buildargs)]
                    elif node.implementation == 'python':
                        func = node.build(*buildargs)
                        original_outex = [func] * len(node.outputs)
                    else:
                        original_outex = node.build(*buildargs)
                except Exception as err:
                    import traceback as tb
                    frame = [f[0] for f in tb.walk_tb(err.__traceback__) if f[0].f_code.co_filename == node.definition.get('path', '')]
                    lineno = "<unknown>" if len(frame) == 0 else str(frame[0].f_lineno)
                    self.logger.error("Error in Flowmodule %s at line %s:  %s: %s" % (str(node), lineno, err.__class__.__name__, str(err)))
                    post_mortem()
                    skip = True
                    break

                outexpressions[node.uid] = original_outex
                flattened_outex = []
                outputlengths = []
                flattened_markers = []
                # check if this node has a list as one of its return values:
                for idx, ex in enumerate(original_outex):
                    if type(ex) == list:
                        # if so, flatten the outputs, and mark the offset and length of the flattened output
                        # so that we can later reconstruct the nested output-structure
                        flattened_markers.append((len(outputs) + idx, len(ex)))
                        outputlengths.append(len(ex))
                        for item in ex:
                            flattened_outex.append(item)
                    else:
                        flattened_outex.append(ex)
                        outputlengths.append(1)

                # offset for indexing the flattened_outexpression by output_index
                node_flattened_output_offset = 0

                # go thorugh the nodes outputs, and see how they will be used:
                for out_idx, out_name in enumerate(node.outputs):
                    dangling = ['external']
                    if node.outputmap[out_name]:
                        # if this output is used, we have to see where every connection goes
                        # iterate through every connection, and note if it's used path-internally,
                        # subgraph-internally, or will produce an output of the emerging callable
                        dangling = []
                        for pair in node.outputmap[out_name]:
                            if pair[0] in member_uids:
                                # path-internally satisfied
                                dangling.append(False)
                            elif pair[0] in node_uids:
                                # internal dangling aka subgraph-internally satisfied
                                dangling.append("internal")
                            else:
                                # externally dangling aka this will be a final output
                                dangling.append("external")
                    # now, handle internally or externally dangling outputs if there are any:
                    if set(dangling) != {False}:
                        thunk['outputs'].append((node.uid, out_name))
                        if outputlengths[out_idx] > 1:
                            # if this is output should produce a list, note this, for later de-flattenation
                            # and append the flattened output to the output-collection
                            thunk['list_outputs'].append((thunk_flattened_output_index, outputlengths[out_idx]))
                            for i in range(outputlengths[out_idx]):
                                outputs.append(flattened_outex[out_idx + node_flattened_output_offset + i])
                            node_flattened_output_offset += outputlengths[out_idx] - 1
                        else:
                            outputs.append(flattened_outex[out_idx + node_flattened_output_offset])
                        if "external" in dangling:
                            # this output will be a final one:
                            if requested_outputs is None or (node.uid, out_name) in requested_outputs:
                                dangling_outputs.append((node.uid, out_name))
                                thunk['dangling_outputs'].append(thunk_flattened_output_index)
                        thunk_flattened_output_index += outputlengths[out_idx]

            if skip:
                # thunk borked, skip
                continue

            # now, set the function of this thunk. Either compile a theano function
            # or assign the python function.
            if not use_different_thetas:
                if thunk['implementation'] == 'theano':
                    thunk['function'] = theano.function(inputs=inputs, outputs=outputs)
                else:
                    thunk['node'] = path['members'][0]
                    thunk['function'] = outexpressions[thunk['node'].uid][0]

            else:
                sharedvars = self.collect_thetas(node_uids)
                dummies = [create_tensor(var.ndim, self.theanofloatX, name="Theta_%s" % var.name) for var in sharedvars]
                if thunk['implementation'] == 'theano':
                    givens = list(zip(sharedvars, dummies))
                    thunk['function'] = theano.function(inputs=inputs + dummies, outputs=outputs, givens=givens)
                else:
                    thunk['node'] = path['members'][0]
                    thunk['function'] = outexpressions[thunk['node'].uid][0]

            thunks.append(thunk)

        if not use_unique_input_names:
            # check for name collisions
            for thunk in thunks:
                if len(set(thunk['input_sources'])) != (len(thunk['input_sources'])):
                    raise RuntimeError("""
                        Name Collision in inputs detected!
                        This graph can only be compiled as callable if you use unique_input_names.
                        set use_unique_input_names to True, and give the inputs as "UID_NAME"
                        where uid is the uid of the node getting this input, and name is the input name of this node""")

        def compiled(thetas=None, **kwargs):
            """ Compiled callable for this subgraph """
            all_outputs = []  # outputs for use within this thunk
            final_outputs = []  # final, external dangling outputs
            for idx, thunk in enumerate(thunks):
                funcargs = []
                # get the inputs: Either from the kwargs, or from the already existing outputs
                for source, pidx, item in thunk['input_sources']:
                    if source == 'kwargs':
                        funcargs.append(kwargs[item])
                    elif source == 'path':
                        funcargs.append(all_outputs[pidx][item])
                if thunk['implementation'] == 'python':
                    params = thunk['node'].clone_parameters()
                    out = thunk['function'](*funcargs, netapi=self.netapi, node=thunk['node'], parameters=params)
                    if len(thunk['node'].outputs) <= 1:
                        out = [out]
                    else:
                        if type(out) != tuple:
                            raise RuntimeError("""Output mismatch!
                                Node %s returned only one output instead of %d.""" % (str(thunk['node']), len(thunk['node'].outputs)))
                        elif len(out) != len(thunk['node'].outputs):
                            raise RuntimeError("""Output mismatch!
                                Node %s returned %d outputs instead of %d.""" % (str(thunk['node']), len(out), len(thunk['node'].outputs)))
                else:
                    if thetas:
                        funcargs += thetas
                    out = thunk['function'](*funcargs)
                if thunk['list_outputs']:
                    # if we have list_outputs, we need to nest the output of this thunk again
                    # to recreate the nested structure from a flat list of outputs
                    new_out = []
                    out_iter = iter(out)
                    try:
                        for out_index in range(len(out)):
                            for offset, length in thunk['list_outputs']:
                                if offset == out_index:
                                    sublist = []
                                    for i in range(length):
                                        sublist.append(next(out_iter))
                                    new_out.append(sublist)
                                else:
                                    new_out.append(next(out_iter))
                    except StopIteration:
                        # iterator finished, we handled all items.
                        pass
                    out = new_out
                if out:
                    all_outputs.append(out)
                    for idx in thunk['dangling_outputs']:
                        if requested_outputs is None or thunk['outputs'][idx] in requested_outputs:
                            final_outputs.append(out[idx])
            return final_outputs

        compiled.__doc__ = """Compiled subgraph of nodes %s
            Inputs: %s
            Outputs: %s
        """ % (str(subgraph), str([("%s of %s" % x[::-1]) for x in dangling_inputs]), str([("%s of %s" % x[::-1]) for x in dangling_outputs]))

        return compiled, dangling_inputs, dangling_outputs

    def shadow_flowgraph(self, flow_modules):
        """ Creates shallow copies of the given flow_modules, copying instances and internal connections.
        Shallow copies will always have the parameters and shared variables of their originals
        """
        copies = []
        copymap = {}
        for node in flow_modules:
            copy_uid = self.create_node(
                node.type,
                node.parent_nodespace,
                node.position,
                name=node.name,
                parameters=node.clone_parameters())
            copy = self.get_node(copy_uid)
            copy.is_copy_of = node.uid
            copymap[node.uid] = copy
            copies.append(copy)
        for node in flow_modules:
            for in_name in node.inputmap:
                if node.inputmap[in_name]:
                    source_uid, source_name = node.inputmap[in_name]
                    if source_uid in copymap:
                        self.flow(copymap[source_uid].uid, source_name, copymap[node.uid].uid, in_name)
        return copies

    def set_theta(self, node_uid, name, val):
        if node_uid not in self.thetas:
            self.thetas[node_uid] = {
                'names': [],
                'variables': []
            }
        if name not in self.thetas[node_uid]['names']:
            new_names = sorted(self.thetas[node_uid]['names'] + [name])
            self.thetas[node_uid]['names'] = new_names
            index = self.thetas[node_uid]['names'].index(name)
            if not isinstance(val, T.sharedvar.TensorSharedVariable):
                val = theano.shared(value=val.astype(T.config.floatX), name=name, borrow=True)
            self.thetas[node_uid]['variables'].insert(index, val)
        else:
            if not isinstance(val, T.sharedvar.TensorSharedVariable):
                val = theano.shared(value=val.astype(T.config.floatX), name=name, borrow=True)
            index = self.thetas[node_uid]['names'].index(name)
            self.thetas[node_uid]['variables'][index].set_value(val.get_value(), borrow=True)

    def get_theta(self, node_uid, name):
        data = self.thetas[node_uid]
        index = data['names'].index(name)
        return data['variables'][index]

    def collect_thetas(self, node_uids):
        shared_vars = []
        for uid in node_uids:
            node = self.get_node(uid)
            if node.is_copy_of:
                uid = node.is_copy_of
            data = self.thetas.get(uid)
            if data:
                shared_vars.extend(data['variables'])
        return shared_vars

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

        if nodetype in self.native_modules and type(self.native_modules[nodetype]) == FlowNodetype:
            self._create_flow_module(self.get_node(uid))

        if name is not None and name != "" and name != uid:
            self.names[uid] = name

        return uid

    def delete_node(self, uid):
        self.close_figures(uid)
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

        if uid in self.flow_module_instances:
            self._delete_flow_module(uid)

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
        if target_node_uid in self.flow_module_instances:
            self.update_flow_graphs()
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
        if target_node_uid in self.flow_module_instances:
            self.update_flow_graphs()
        return result

    def reload_native_modules(self, native_modules):

        # check which instances need to be recreated because of gate/slot changes and keep their .data
        instances_to_recreate = {}
        instances_to_delete = {}

        # create the new nodetypes
        self.native_module_definitions = {}
        newnative_modules = {}
        native_modules.update(self.generate_worldadapter_flow_types())
        for key, data in native_modules.items():
            if data.get('engine', self.engine) == self.engine:
                try:
                    if data.get('flow_module'):
                        newnative_modules[key] = FlowNodetype(nodenet=self, **data)
                    elif data.get('dimensionality'):
                        newnative_modules[key] = HighdimensionalNodetype(nodenet=self, **data)
                    else:
                        newnative_modules[key] = Nodetype(nodenet=self, **data)
                    self.native_module_definitions[key] = data
                except Exception as err:
                    self.logger.error("Can not instantiate node type %s: %s: %s" % (key, err.__class__.__name__, str(err)))
                    post_mortem()

        for partition in self.partitions.values():
            for uid, instance in partition.native_module_instances.items():
                if instance.type not in newnative_modules:
                    self.logger.warning("No more definition available for node type %s, deleting instance %s" %
                                (instance.type, uid))
                    instances_to_delete[uid] = instance
                    continue

                numeric_id = node_from_id(uid)
                if uid in self.flow_module_instances:
                    if newnative_modules[instance.type].inputs != instance.inputs or newnative_modules[instance.type].outputs != instance.outputs:
                        self.logger.warning("Inputs or Outputs of flow node type %s changed, recreating instance %s" %
                                        (instance.type, uid))
                        instances_to_recreate[uid] = instance.get_data(complete=True, include_links=False)

                else:
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
            for uid, instance in partition.native_module_instances.items():
                parameters = instance.clone_parameters()
                state = instance.clone_state()
                position = instance.position
                name = instance.name
                partition = self.get_partition(uid)
                self.close_figures(uid)
                if uid in self.flow_module_instances:
                    flowdata = instance.get_flow_data(complete=True)
                    new_instance = FlowModule(
                        self,
                        partition,
                        instance.parent_nodespace,
                        uid,
                        get_numerical_node_type(instance.type, self.native_modules),
                        inputmap=flowdata['inputmap'],
                        outputmap=flowdata['outputmap'],
                        parameters=parameters
                    )
                    self.flow_module_instances[uid] = new_instance
                else:
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

        for new_uid in nx.topological_sort(self.flowgraph):
            if new_uid in instances_to_recreate:
                self.get_node(new_uid).ensure_initialized()

        # recompile flow_graphs:
        self.update_flow_graphs()

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

    def generate_worldadapter_flow_types(self, delete_existing=False):
        """ returns native_module_definitions for datasources and targets from the configured worldadapter"""

        auto_nodetypes = []
        if delete_existing:
            for key in list(self.native_modules.keys()):
                if type(self.native_modules[key]) == FlowNodetype and self.native_modules[key].is_autogenerated:
                    auto_nodetypes.append(key)

            for uid in list(self.flow_module_instances.keys()):
                if self.flow_module_instances[uid].type in auto_nodetypes:
                    self.delete_node(uid)

            for key in auto_nodetypes:
                del self.native_modules[key]
                del self.native_module_definitions[key]

            self.worldadapter_flow_nodes = {}

        data = {}
        if self.worldadapter_instance and self.worldadapter_instance.generate_flow_modules:
            if self.worldadapter_instance.get_available_flow_datasources():
                data['datasources'] = {
                    'flow_module': True,
                    'implementation': 'python',
                    'name': 'datasources',
                    'outputs': self.worldadapter_instance.get_available_flow_datasources(),
                    'inputs': [],
                    'is_autogenerated': True
                }
            if self.worldadapter_instance.get_available_flow_datatargets():
                dtgroups = self.worldadapter_instance.get_available_flow_datatargets()
                dtdims = [self.worldadapter_instance.get_flow_datatarget(name).ndim for name in dtgroups]
                data['datatargets'] = {
                    'flow_module': True,
                    'implementation': 'python',
                    'name': 'datatargets',
                    'inputs': dtgroups,
                    'outputs': [],
                    'inputdims': dtdims,
                    'is_autogenerated': True
                }
        return data

    def generate_worldadapter_flow_instances(self):
        """ Generates flow module instances for the existing autogenerated worldadapter-flowmodule-types """
        for idx, key in enumerate(['datasources', 'datatargets']):
            if key in self.native_module_definitions:
                uid = self.worldadapter_flow_nodes.get(key)
                if uid and uid in self.flow_module_instances:
                    node = self.flow_module_instances[uid]
                    for out in node.outputmap:
                        if out not in self.native_module_definitions[key]['outputs']:
                            for target_uid, name in node.outputmap[out].copy():
                                self.unflow('worldadapter', out, target_uid, name)
                    for _in in node.inputmap:
                        if _in not in self.native_module_definitions[key]['inputs']:
                            for source_uid, name in node.inputmap[_in]:
                                self.unflow(source_uid, name, 'worldadapter', _in)
                    numerictype = get_numerical_node_type(key, self.native_modules)
                    self.flow_module_instances[uid] = FlowModule(self, node._partition, self.rootpartition.rootnodespace_uid, node.uid, numerictype, node.parameters, node.inputmap, node.outputmap)
                else:
                    uid = self.create_node(key, None, [(idx + 2) * 100, 100], name=key)
                    self.worldadapter_flow_nodes[key] = uid

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
                if node_uid in self.flow_module_instances:
                    data[node_uid].update(self.flow_module_instances[node_uid].get_flow_data())
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

    def group_nodes_by_ids(self, nodespace_uid, node_uids, group_name, gatetype="gen", sortby='id'):
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

    def add_gate_activation_recorder(self, group_definition, name, interval=1):
        """ Adds an activation recorder to a group of nodes."""
        rec = recorder.GateActivationRecorder(self, group_definition, name, interval=interval)
        self._recorders[rec.uid] = rec
        return rec

    def add_node_activation_recorder(self, group_definition, name, interval=1):
        """ Adds an activation recorder to a group of nodes."""
        rec = recorder.NodeActivationRecorder(self, group_definition, name, interval=interval)
        self._recorders[rec.uid] = rec
        return rec

    def add_linkweight_recorder(self, from_group_definition, to_group_definition, name, interval=1):
        """ Adds a linkweight recorder to links between to groups."""
        rec = recorder.LinkweightRecorder(self, from_group_definition, to_group_definition, name, interval=interval)
        self._recorders[rec.uid] = rec
        return rec

    def get_dashboard(self):
        data = super(TheanoNodenet, self).get_dashboard()
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
