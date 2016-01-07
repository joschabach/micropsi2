# -*- coding: utf-8 -*-

"""
Nodenet definition
"""
import json
import os
import copy
import math

from theano import tensor as T
import numpy as np
import scipy

from micropsi_core.nodenet import monitor
from micropsi_core.nodenet.nodenet import Nodenet
from micropsi_core.nodenet.node import Nodetype
from micropsi_core.nodenet.stepoperators import DoernerianEmotionalModulators
from micropsi_core.nodenet.theano_engine.theano_node import *
from micropsi_core.nodenet.theano_engine.theano_definitions import *
from micropsi_core.nodenet.theano_engine.theano_stepoperators import *
from micropsi_core.nodenet.theano_engine.theano_nodespace import *
from micropsi_core.nodenet.theano_engine.theano_netapi import TheanoNetAPI
from micropsi_core.nodenet.theano_engine.theano_partition import TheanoPartition

from configuration import config as settings


STANDARD_NODETYPES = {
    "Nodespace": {
        "name": "Nodespace"
    },
    "Comment": {
        "name": "Comment",
        "symbol": "#",
        'parameters': ['comment'],
        "shape": "Rectangle"
    },
    "Register": {
        "name": "Register",
        "slottypes": ["gen"],
        "nodefunction_name": "register",
        "gatetypes": ["gen"]
    },
    "Sensor": {
        "name": "Sensor",
        "parameters": ["datasource"],
        "nodefunction_name": "sensor",
        "gatetypes": ["gen"]
    },
    "Actor": {
        "name": "Actor",
        "parameters": ["datatarget"],
        "nodefunction_name": "actor",
        "slottypes": ["gen"],
        "gatetypes": ["gen"]
    },
    "Pipe": {
        "name": "Pipe",
        "slottypes": ["gen", "por", "ret", "sub", "sur", "cat", "exp"],
        "nodefunction_name": "pipe",
        "gatetypes": ["gen", "por", "ret", "sub", "sur", "cat", "exp"],
        "gate_defaults": {
            "gen": {
                "minimum": -1,
                "maximum": 1,
                "threshold": -1,
                "spreadsheaves": 0
            },
            "por": {
                "minimum": -1,
                "maximum": 1,
                "threshold": -1,
                "spreadsheaves": 0
            },
            "ret": {
                "minimum": -1,
                "maximum": 1,
                "threshold": -1,
                "spreadsheaves": 0
            },
            "sub": {
                "minimum": -1,
                "maximum": 1,
                "threshold": -1,
                "spreadsheaves": True
            },
            "sur": {
                "minimum": -1,
                "maximum": 1,
                "threshold": -1,
                "spreadsheaves": 0
            },
            "cat": {
                "minimum": -1,
                "maximum": 1,
                "threshold": -1,
                "spreadsheaves": 1
            },
            "exp": {
                "minimum": -1,
                "maximum": 1,
                "threshold": -1,
                "spreadsheaves": 0
            }
        },
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
        "symbol": "◷",
        "gate_defaults": {
            "gen": {
                "minimum": -1000,
                "maximum": 1000,
                "threshold": -1000
            },
            "por": {
                "minimum": -1000,
                "maximum": 1000,
                "threshold": -1000
            },
            "gin": {
                "minimum": -1000,
                "maximum": 1000,
                "threshold": -1000
            },
            "gou": {
                "minimum": -1000,
                "maximum": 1000,
                "threshold": -1000
            },
            "gfg": {
                "minimum": -1000,
                "maximum": 1000,
                "threshold": -1000
            }
        }
    }
}

NODENET_VERSION = 1


class TheanoNodenet(Nodenet):
    """
        theano runtime engine implementation
    """

    @property
    def engine(self):
        return "theano_engine"

    @property
    def current_step(self):
        return self._step

    def __init__(self, name="", worldadapter="Default", world=None, owner="", uid=None, native_modules={}):

        # map of string uids to positions. Not all nodes necessarily have an entry.
        self.positions = {}

        # map of string uids to names. Not all nodes neccessarily have an entry.
        self.names = {}

        # map of data sources to string node IDs
        self.sensormap = {}

        # map of string node IDs to data sources
        self.inverted_sensor_map = {}

        # map of data targets to string node IDs
        self.actuatormap = {}

        # map of string node IDs to data targets
        self.inverted_actuator_map = {}

        super(TheanoNodenet, self).__init__(name, worldadapter, world, owner, uid)

        precision = settings['theano']['precision']
        if precision == "32":
            T.config.floatX = "float32"
            self.scipyfloatX = scipy.float32
            self.numpyfloatX = np.float32
            self.byte_per_float = 4
        elif precision == "64":
            T.config.floatX = "float64"
            self.scipyfloatX = scipy.float64
            self.numpyfloatX = np.float64
            self.byte_per_float = 8
        else:
            self.logger.warn("Unsupported precision value from configuration: %s, falling back to float64", precision)
            T.config.floatX = "float64"
            self.scipyfloatX = scipy.float64
            self.numpyfloatX = np.float64
            self.byte_per_float = 8

        device = T.config.device
        self.logger.info("Theano configured to use %s", device)
        if device.startswith("gpu"):
            self.logger.info("Using CUDA with cuda_root=%s and theano_flags=%s", os.environ["CUDA_ROOT"], os.environ["THEANO_FLAGS"])
            if T.config.floatX != "float32":
                self.logger.warn("Precision set to %s, but attempting to use gpu.", precision)

        self.netapi = TheanoNetAPI(self)

        self.partitions = {}
        self.last_allocated_partition = 0

        average_elements_per_node_assumption = 6
        configured_elements_per_node_assumption = settings['theano']['elements_per_node_assumption']
        try:
            average_elements_per_node_assumption = int(configured_elements_per_node_assumption)
        except:
            self.logger.warn("Unsupported elements_per_node_assumption value from configuration: %s, falling back to 4", configured_elements_per_node_assumption)

        initial_number_of_nodes = 2000
        configured_initial_number_of_nodes = settings['theano']['initial_number_of_nodes']
        try:
            initial_number_of_nodes = int(configured_initial_number_of_nodes)
        except:
            self.logger.warn("Unsupported initial_number_of_nodes value from configuration: %s, falling back to 2000", configured_initial_number_of_nodes)

        sparse = True
        configuredsparse = settings['theano']['sparse_weight_matrix']
        if configuredsparse == "True":
            sparse = True
        elif configuredsparse == "False":
            sparse = False
        else:
            self.logger.warn("Unsupported sparse_weight_matrix value from configuration: %s, falling back to True", configuredsparse)
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

        self._version = NODENET_VERSION  # used to check compatibility of the node net data
        self._step = 0
        self._modulators = {}
        self._modulators['por_ret_decay'] = 0.

        self.proxycache = {}

        self.stepoperators = []
        self.initialize_stepoperators()

        self._nodetypes = {}
        for type, data in STANDARD_NODETYPES.items():
            self._nodetypes[type] = Nodetype(nodenet=self, **data)

        self.native_module_definitions = native_modules
        self.native_modules = {}
        for type, data in self.native_module_definitions.items():
            self.native_modules[type] = Nodetype(nodenet=self, **data)

        self.create_nodespace(None, None, "Root", nodespace_to_id(1, rootpartition.pid))

        self.initialize_nodenet({})

    def get_data(self, complete=False, include_links=True):
        data = super().get_data(complete=complete, include_links=include_links)
        data['nodes'] = self.construct_nodes_dict(complete=complete, include_links=include_links)
        # for uid in data['nodes']:
        #    data['nodes'][uid]['gate_parameters'] = self.get_node(uid).clone_non_default_gate_parameters()
        data['nodespaces'] = self.construct_nodespaces_dict(None)
        data['version'] = self._version
        data['modulators'] = self.construct_modulators_dict()
        return data

    def export_json(self):
        data = self.get_data(complete=True, include_links=False)
        data['links'] = self.construct_links_list()
        return data

    def initialize_stepoperators(self):
        self.stepoperators = [
            TheanoPropagate(),
            TheanoCalculate(self),
            DoernerianEmotionalModulators()]
        self.stepoperators.sort(key=lambda op: op.priority)

    def save(self, filename):

        # write json metadata, which will be used by runtime to manage the net
        with open(filename, 'w+') as fp:
            metadata = self.metadata
            metadata['positions'] = self.positions
            metadata['names'] = self.names
            metadata['actuatormap'] = self.actuatormap
            metadata['sensormap'] = self.sensormap
            metadata['nodes'] = self.construct_native_modules_and_comments_dict()
            metadata['monitors'] = self.construct_monitors_dict()
            metadata['modulators'] = self.construct_modulators_dict()
            metadata['partition_parents'] = self.inverted_partitionmap
            fp.write(json.dumps(metadata, sort_keys=True, indent=4))

        for partition in self.partitions.values():
            # write bulk data to our own numpy-based file format
            datafilename = os.path.join(os.path.dirname(filename), self.uid + "-data-" + partition.spid)
            partition.save(datafilename)

    def load(self, filename):
        """Load the node net from a file"""
        # try to access file

        with self.netlock:
            initfrom = {}
            datafile = None
            if os.path.isfile(filename):
                try:
                    self.logger.info("Loading nodenet %s metadata from file %s", self.name, filename)
                    with open(filename) as file:
                        initfrom.update(json.load(file))
                except ValueError:
                    self.logger.warn("Could not read nodenet metadata from file %s", filename)
                    return False
                except IOError:
                    self.logger.warn("Could not open nodenet metadata file %s", filename)
                    return False

            # initialize with metadata
            self.initialize_nodenet(initfrom)

            nodes_data = {}
            if 'nodes' in initfrom:
                nodes_data = initfrom['nodes']

            for partition in self.partitions.values():
                datafilename = os.path.join(os.path.dirname(filename), self.uid + "-data-" + partition.spid + ".npz")
                partition.load_data(datafilename, nodes_data)

            for partition in self.partitions.values():
                datafilename = os.path.join(os.path.dirname(filename), self.uid + "-data-" + partition.spid + ".npz")
                partition.load_inlinks(datafilename)

            # reloading native modules ensures the types in allocated_nodes are up to date
            # (numerical native module types are runtime dependent and may differ from when allocated_nodes
            # was saved).
            self.reload_native_modules(self.native_module_definitions)

            for sensor, id_list in self.sensormap.items():
                for id in id_list:
                    self.inverted_sensor_map[id] = sensor
            for actuator, id_list in self.actuatormap.items():
                for id in id_list:
                    self.inverted_actuator_map[id] = actuator

            # re-initialize step operators for theano recompile to new shared variables
            self.initialize_stepoperators()

            return True

    def remove(self, filename):
        neighbors = os.listdir(os.path.dirname(filename))
        for neighbor in neighbors:
            if neighbor.startswith(self.uid):
                os.remove(os.path.join(os.path.dirname(filename), neighbor))

    def initialize_nodenet(self, initfrom):

        self._modulators.update(initfrom.get("modulators", {}))

        if initfrom.get('runner_condition'):
            self.set_runner_condition(initfrom['runner_condition'])

        if len(initfrom) != 0:
            # now merge in all init data (from the persisted file typically)
            self.merge_data(initfrom, keep_uids=True)
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

    def merge_data(self, nodenet_data, keep_uids=False):
        """merges the nodenet state with the current node net, might have to give new UIDs to some entities"""

        uidmap = {}
        invalid_nodes = []

        # for dict_engine compatibility
        uidmap["Root"] = self.rootpartition.rootnodespace_uid

        # re-use the root nodespace
        uidmap[self.rootpartition.rootnodespace_uid] = self.rootpartition.rootnodespace_uid

        # instantiate partitions
        partitions_to_instantiate = nodenet_data.get('partition_parents', {})
        largest_pid = 0
        for partition_spid, parent_uid in partitions_to_instantiate.items():
            pid = int(partition_spid)
            if pid > largest_pid:
                largest_pid = pid
            self.create_partition(pid,
                                  parent_uid,
                                  True,
                                  round(len(nodenet_data.get('nodes', {}).keys()) * 1.2),
                                  7,
                                  round(len(set(nodenet_data.get('nodespaces', {}).keys())) * 1.2))
        self.last_allocated_partition = largest_pid

        # merge in spaces, make sure that parent nodespaces exist before children are initialized
        nodespaces_to_merge = set(nodenet_data.get('nodespaces', {}).keys())
        for nodespace in nodespaces_to_merge:
            self.merge_nodespace_data(nodespace, nodenet_data['nodespaces'], uidmap, keep_uids)

        # merge in nodes
        for uid in nodenet_data.get('nodes', {}):
            data = nodenet_data['nodes'][uid]
            parent_uid = data['parent_nodespace']
            if not keep_uids:
                parent_uid = uidmap[data['parent_nodespace']]
            if data['type'] not in self._nodetypes and data['type'] not in self.native_modules:
                self.logger.warn("Invalid nodetype %s for node %s" % (data['type'], uid))
                data['parameters'] = {
                    'comment': 'There was a %s node here' % data['type']
                }
                data['type'] = 'Comment'
                del data['gate_parameters']
                invalid_nodes.append(uid)
            new_uid = self.create_node(
                data['type'],
                parent_uid,
                data['position'],
                name=data['name'],
                uid=uid,
                parameters=data.get('parameters'),
                gate_parameters=data.get('gate_parameters'),
                gate_functions=data.get('gate_functions'))
            uidmap[uid] = new_uid
            node_proxy = self.get_node(new_uid)
            for gatetype in data.get('gate_activations', {}):   # todo: implement sheaves
                if gatetype in node_proxy.nodetype.gatetypes:
                    node_proxy.get_gate(gatetype).activation = data['gate_activations'][gatetype]['default']['activation']
            state = data.get('state', {})
            if state is not None:
                for key, value in state.items():
                    node_proxy.set_state(key, value)

        # merge in links
        links = nodenet_data.get('links', [])
        if isinstance(links, dict):
            # compatibility
            links = links.values()
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
                    self.logger.warn('unknown classname for monitor: %s (uid:%s) ' % (data['classname'], monitorid))
            else:
                # Compatibility mode
                mon = monitor.NodeMonitor(self, name=data['node_name'], **data)
                self._monitors[mon.uid] = mon

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
                    data[nodespace_uid].get('position'),
                    name=data[nodespace_uid].get('name', 'Root'),
                    uid=nodespace_uid
                )
        else:
            if not nodespace_uid in uidmap:
                parent_uid = data[nodespace_uid].get('parent_nodespace')
                if not parent_uid in uidmap:
                    self.merge_nodespace_data(parent_uid, data, uidmap, keep_uids)
                newuid = self.create_nodespace(
                    uidmap[data[nodespace_uid].get('parent_nodespace')],
                    data[nodespace_uid].get('position'),
                    name=data[nodespace_uid].get('name', 'Root'),
                    uid=None
                )
                uidmap[nodespace_uid] = newuid

    def step(self):
        if self.worldadapter_instance is not None:
            self.worldadapter_instance.snapshot()

        with self.netlock:
            self._step += 1

            for operator in self.stepoperators:
                operator.execute(self, None, self.netapi)

    def get_partition(self, uid):
        if uid is None:
            return self.rootpartition
        return self.partitions.get(uid[1:4], None)

    def get_node(self, uid):
        partition = self.get_partition(uid)
        if partition is None:
            raise KeyError("No node with id %s exists", uid)
        if uid in partition.native_module_instances:
            return partition.native_module_instances[uid]
        elif uid in partition.comment_instances:
            return partition.comment_instances[uid]
        elif uid in self.proxycache:
            return self.proxycache[uid]
        elif self.is_node(uid):
            id = node_from_id(uid)
            parent_id = partition.allocated_node_parents[id]
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

    def create_node(self, nodetype, nodespace_uid, position, name=None, uid=None, parameters=None, gate_parameters=None, gate_functions=None):
        nodespace_uid = self.get_nodespace(nodespace_uid).uid
        partition = self.get_partition(nodespace_uid)
        nodespace_id = nodespace_from_id(nodespace_uid)

        id_to_pass = None
        if uid is not None:
            id_to_pass = node_from_id(uid)

        id = partition.create_node(nodetype, nodespace_id, id_to_pass, parameters, gate_parameters, gate_functions)
        uid = node_to_id(id, partition.pid)

        if position is not None:
            self.positions[uid] = position
        if name is not None and name != "" and name != uid:
            self.names[uid] = name

        if parameters is None:
            parameters = {}

        if nodetype == "Sensor":
            if 'datasource' in parameters:
                datasource = parameters['datasource']
                if datasource is not None:
                    connectedsensors = self.sensormap.get(datasource, [])
                    connectedsensors.append(uid)
                    self.sensormap[datasource] = connectedsensors
                    self.inverted_sensor_map[uid] = datasource
        elif nodetype == "Actor":
            if 'datatarget' in parameters:
                datatarget = parameters['datatarget']
                if datatarget is not None:
                    connectedactuators = self.actuatormap.get(datatarget, [])
                    connectedactuators.append(uid)
                    self.actuatormap[datatarget] = connectedactuators
                    self.inverted_actuator_map[uid] = datatarget

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
                weights = inlinks[2].get_value(borrow=True)
                if element in to_elements:
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
                    weights = inlinks[2].get_value(borrow=True)
                    if element in from_elements:
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
                        # remove this element
                        to_partition.inlinks[partition.spid][0].set_value(np.delete(from_elements, element_index))
                        # remove to_elements
                        to_partition.inlinks[partition.spid][1].set_value(np.delete(to_elements, zero_rows))

        partition.delete_node(node_id)

        # remove sensor association if there should be one
        if uid in self.inverted_sensor_map:
            sensor = self.inverted_sensor_map[uid]
            del self.inverted_sensor_map[uid]
            if sensor in self.sensormap:
                self.sensormap[sensor].remove(uid)
                if len(self.sensormap[sensor]) == 0:
                    del self.sensormap[sensor]

        # remove actuator association if there should be one
        if uid in self.inverted_actuator_map:
            actuator = self.inverted_actuator_map[uid]
            del self.inverted_actuator_map[uid]
            if actuator in self.actuatormap:
                self.actuatormap[actuator].remove(uid)
                if len(self.actuatormap[actuator]) == 0:
                    del self.actuatormap[actuator]

        self.clear_supplements(uid)

        for id_to_clear in associated_ids:
            associated_uids.append(node_to_id(id_to_clear, partition.pid))

        for uid_to_clear in associated_uids:
            if uid_to_clear in self.proxycache:
                del self.proxycache[uid_to_clear]

    def set_node_gate_parameter(self, uid, gate_type, parameter, value):
        partition = self.get_partition(uid)
        id = node_from_id(uid)
        partition.set_node_gate_parameter(id, gate_type, parameter, value)

    def set_node_gatefunction_name(self, uid, gate_type, gatefunction_name):
        partition = self.get_partition(uid)
        id = node_from_id(uid)
        partition.set_node_gatefunction_name(id, gate_type, gatefunction_name)

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

    def create_nodespace(self, parent_uid, position, name="", uid=None, options=None):
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
                    self.logger.warn("Unsupported elements_per_node_assumption value from configuration: %s, falling back to 4", configured_elements_per_node_assumption)

            initial_number_of_nodes = 2000
            if "initial_number_of_nodes" in options:
                initial_number_of_nodes = int(options["initial_number_of_nodes"])
            else:
                configured_initial_number_of_nodes = settings['theano']['initial_number_of_nodes']
                try:
                    initial_number_of_nodes = int(configured_initial_number_of_nodes)
                except:
                    self.logger.warn("Unsupported initial_number_of_nodes value from configuration: %s, falling back to 2000", configured_initial_number_of_nodes)

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
                    self.logger.warn("Unsupported sparse_weight_matrix value from configuration: %s, falling back to True", configuredsparse)
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
        if position is not None:
            self.positions[uid] = position

        return uid

    def delete_nodespace(self, nodespace_uid):
        if nodespace_uid is None or nodespace_uid == self.get_nodespace(None).uid:
            raise ValueError("The root nodespace cannot be deleted.")

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
            for ds_sensors in self.sensormap.values():
                sensorlist.extend(ds_sensors)
        elif datasource in self.sensormap:
            sensorlist = self.sensormap[datasource]
        for uid in sensorlist:
            if nodespace is None or self.get_partition(uid).allocated_node_parents[node_from_id(uid)] == nodespace_from_id(nodespace):
                sensors[uid] = self.get_node(uid)
        return sensors

    def get_actors(self, nodespace=None, datatarget=None):
        actuators = {}
        actuatorlist = []
        if datatarget is None:
            for dt_actuators in self.actuatormap.values():
                actuatorlist.extend(dt_actuators)
        elif datatarget in self.actuatormap:
            actuatorlist = self.actuatormap[datatarget]
        for uid in actuatorlist:
            if nodespace is None or self.get_partition(uid).allocated_node_parents[node_from_id(uid)] == nodespace_from_id(nodespace):
                actuators[uid] = self.get_node(uid)
        return actuators

    def create_link(self, source_node_uid, gate_type, target_node_uid, slot_type, weight=1, certainty=1):
        return self.set_link_weight(source_node_uid, gate_type, target_node_uid, slot_type, weight)

    def set_link_weight(self, source_node_uid, gate_type, target_node_uid, slot_type, weight=1, certainty=1):

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
        return self.set_link_weight(source_node_uid, gate_type, target_node_uid, slot_type, 0)

    def reload_native_modules(self, native_modules):

        self.native_module_definitions = native_modules

        # check which instances need to be recreated because of gate/slot changes and keep their .data
        instances_to_recreate = {}
        instances_to_delete = {}
        for partition in self.partitions.values():
            for uid, instance in partition.native_module_instances.items():
                if instance.type not in native_modules:
                    self.logger.warn("No more definition available for node type %s, deleting instance %s" %
                                    (instance.type, uid))
                    instances_to_delete[uid] = instance
                    continue

                numeric_id = node_from_id(uid)
                number_of_elements = len(np.where(partition.allocated_elements_to_nodes == numeric_id)[0])
                new_numer_of_elements = max(len(native_modules[instance.type]['slottypes']), len(native_modules[instance.type]['gatetypes']))
                if number_of_elements != new_numer_of_elements:
                    self.logger.warn("Number of elements changed for node type %s from %d to %d, recreating instance %s" %
                                    (instance.type, number_of_elements, new_numer_of_elements, uid))
                    instances_to_recreate[uid] = instance.get_data(complete=True, include_links=False)

            # actually remove the instances
            for uid in instances_to_delete.keys():
                self.delete_node(uid)
            for uid in instances_to_recreate.keys():
                self.delete_node(uid)

            # update the node functions of all Nodetypes
            self.native_modules = {}
            for type, data in native_modules.items():
                self.native_modules[type] = Nodetype(nodenet=self, **native_modules[type])

            # update the living instances that have the same slot/gate numbers
            new_instances = {}
            for id, instance in partition.native_module_instances.items():
                parameters = instance.clone_parameters()
                state = instance.clone_state()
                position = instance.position
                name = instance.name
                partition = self.get_partition(id)
                new_native_module_instance = TheanoNode(self, partition, instance.parent_nodespace, id, partition.allocated_nodes[node_from_id(id)])
                new_native_module_instance.position = position
                new_native_module_instance.name = name
                for key, value in parameters.items():
                    new_native_module_instance.set_parameter(key, value)
                for key, value in state.items():
                    new_native_module_instance.set_state(key, value)
                new_instances[id] = new_native_module_instance
            partition.native_module_instances = new_instances

            # recreate the deleted ones. Gate configurations and links will not be transferred.
            for uid, data in instances_to_recreate.items():
                new_uid = self.create_node(
                    data['type'],
                    data['parent_nodespace'],
                    data['position'],
                    name=data['name'],
                    uid=uid,
                    parameters=data['parameters'])

            # update native modules numeric types, as these may have been set with a different native module
            # node types list
            native_module_ids = np.where(partition.allocated_nodes > MAX_STD_NODETYPE)[0]
            for id in native_module_ids:
                instance = self.get_node(node_to_id(id, partition.pid))
                partition.allocated_nodes[id] = get_numerical_node_type(instance.type, self.native_modules)

    def get_nodespace_data(self, nodespace_uid, include_links=True):
        partition = self.get_partition(nodespace_uid)
        data = {
            'nodes': self.construct_nodes_dict(nodespace_uid, 1000, include_links=include_links),
            'nodespaces': self.construct_nodespaces_dict(nodespace_uid),
            'monitors': self.construct_monitors_dict(),
            'modulators': self.construct_modulators_dict()
        }
        if include_links:
            followupnodes = []
            for uid in data['nodes']:
                followupnodes.extend(self.get_node(uid).get_associated_node_uids())

            for uid in followupnodes:
                followup_partition = self.get_partition(uid)
                if followup_partition.pid != partition.pid or (partition.allocated_node_parents[node_from_id(uid)] != nodespace_from_id(nodespace_uid)):
                    data['nodes'][uid] = self.get_node(uid).get_data(complete=False, include_links=include_links)

        return data

    def get_activation_data(self, nodespace_uid=None, rounded=1):
        if rounded is not None:
            mult = math.pow(10, rounded)
        activations = {}
        if nodespace_uid is None:
            for partition in self.partitions.values():
                ids = np.nonzero(partition.allocated_nodes)[0]
                for id in ids:
                    elements = get_elements_per_type(partition.allocated_nodes[id])
                    offset = partition.allocated_node_offsets[id]
                    if rounded is None:
                        activations[node_to_id(id, partition.pid)] = [n.item() for n in partition.a.get_value()[offset:offset+elements]]
                    else:
                        activations[node_to_id(id, partition.pid)] = [n.item() / mult for n in np.rint(partition.a.get_value()[offset:offset+elements]*mult)]
        else:
            partition = self.get_nodespace(nodespace_uid).partition
            nodespace_id = nodespace_from_id(nodespace_uid)
            ids = np.where(partition.allocated_node_parents == nodespace_id)
            for id in ids:
                elements = get_elements_per_type(partition.allocated_nodes[id])
                offset = partition.allocated_node_offsets[id]
                if rounded is None:
                    activations[node_to_id(id, partition.pid)] = [n.item() for n in partition.a.get_value()[offset:offset+elements]]
                else:
                    activations[node_to_id(id, partition.pid)] = [n.item() / mult for n in np.rint(partition.a.get_value()[offset:offset+elements]*mult)]
        return activations

    def get_modulator(self, modulator):
        return self._modulators.get(modulator, 1)

    def change_modulator(self, modulator, diff):
        self._modulators[modulator] = self._modulators.get(modulator, 0) + diff

    def set_modulator(self, modulator, value):
        self._modulators[modulator] = value

    def get_nodetype(self, type):
        if type in self._nodetypes:
            return self._nodetypes[type]
        else:
            return self.native_modules.get(type)

    def construct_links_list(self, nodespace_uid=None):
        data = []

        for partition in self.partitions.values():
            if nodespace_uid is not None:
                nspartition = self.get_partition(nodespace_uid)
                if nspartition != partition:
                    continue
                parent = nodespace_from_id(nodespace_uid)
                node_ids = np.where(partition.allocated_node_parents == parent)[0]
            else:
                node_ids = np.nonzero(partition.allocated_nodes)[0]
            w_matrix = partition.w.get_value(borrow=True)
            for node_id in node_ids:

                source_type = partition.allocated_nodes[node_id]
                for gate_type in range(get_gates_per_type(source_type, self.native_modules)):
                    gatecolumn = w_matrix[:, partition.allocated_node_offsets[node_id] + gate_type]
                    links_indices = np.nonzero(gatecolumn)[0]
                    for index in links_indices:
                        target_id = partition.allocated_elements_to_nodes[index]
                        target_type = partition.allocated_nodes[target_id]
                        target_slot_numerical = index - partition.allocated_node_offsets[target_id]
                        target_slot_type = get_string_slot_type(target_slot_numerical, self.get_nodetype(get_string_node_type(target_type, self.native_modules)))
                        source_gate_type = get_string_gate_type(gate_type, self.get_nodetype(get_string_node_type(source_type, self.native_modules)))
                        if partition.sparse:               # sparse matrices return matrices of dimension (1,1) as values
                            weight = float(gatecolumn[index].data)
                        else:
                            weight = gatecolumn[index].item()

                        data.append({
                            "weight": weight,
                            "certainty": 1,
                            "target_slot_name": target_slot_type,
                            "target_node_uid": node_to_id(target_id, partition.pid),
                            "source_gate_name": source_gate_type,
                            "source_node_uid": node_to_id(node_id, partition.pid)
                        })

            # find links going out to other partitions
            for partition_to_spid, to_partition in self.partitions.items():
                if partition.spid in to_partition.inlinks:
                    inlinks = to_partition.inlinks[partition.spid]
                    from_elements = inlinks[0].get_value(borrow=True)
                    to_elements = inlinks[1].get_value(borrow=True)
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
                                "certainty": 1,
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

    def construct_nodes_dict(self, nodespace_uid=None, max_nodes=-1, complete=False, include_links=True):
        data = {}
        i = 0
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
                i += 1
                node_uid = node_to_id(node_id, partition.pid)
                data[node_uid] = self.get_node(node_uid).get_data(complete=complete, include_links=include_links)
                if max_nodes > 0 and i > max_nodes:
                    break
        return data

    def construct_nodespaces_dict(self, nodespace_uid):
        data = {}
        if nodespace_uid is None:
            nodespace_uid = self.get_nodespace(None).uid

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

        return data

    def construct_modulators_dict(self):
        return self._modulators.copy()

    def get_standard_nodetype_definitions(self):
        """
        Returns the standard node types supported by this nodenet
        """
        return copy.deepcopy(STANDARD_NODETYPES)

    def set_sensors_and_actuator_feedback_to_values(self, datasource_to_value_map, datatarget_to_value_map):
        """
        Sets the sensors for the given data sources to the given values
        """

        for partition in self.partitions.values():
            a_array = partition.a.get_value(borrow=True)

            for datasource in datasource_to_value_map:
                value = datasource_to_value_map.get(datasource)
                sensor_uids = self.sensormap.get(datasource, [])

                for sensor_uid in sensor_uids:
                    if self.get_partition(sensor_uid).pid == partition.pid:
                        a_array[partition.allocated_node_offsets[node_from_id(sensor_uid)] + GEN] = value

            for datatarget in datatarget_to_value_map:
                value = datatarget_to_value_map.get(datatarget)
                actuator_uids = self.actuatormap.get(datatarget, [])

                for actuator_uid in actuator_uids:
                    if self.get_partition(actuator_uid).pid == partition.pid:
                        a_array[partition.allocated_node_offsets[node_from_id(actuator_uid)] + GEN] = value

            partition.a.set_value(a_array, borrow=True)

    def read_actuators(self):
        """
        Returns a map of datatargets to values for writing back to the world adapter
        """

        actuator_values_to_write = {}

        for partition in self.partitions.values():
            a_array = partition.a.get_value(borrow=True)

            for datatarget in self.actuatormap:
                if datatarget not in actuator_values_to_write:
                    actuator_values_to_write[datatarget] = 0
                actuator_node_activations = 0
                for actuator_uid in self.actuatormap[datatarget]:
                    if self.get_partition(actuator_uid).pid == partition.pid:
                        actuator_node_activations += a_array[partition.allocated_node_offsets[node_from_id(actuator_uid)] + GEN]

                actuator_values_to_write[datatarget] += actuator_node_activations

            partition.a.set_value(a_array, borrow=True)

        return actuator_values_to_write

    def group_nodes_by_names(self, nodespace_uid, node_name_prefix=None, gatetype="gen", sortby='id', group_name=None):
        if nodespace_uid is None:
            nodespace_uid = self.get_nodespace(None).uid

        if group_name is None:
            group_name = node_name_prefix

        ids = []
        for uid, name in self.names.items():
            partition = self.get_partition(uid)
            if self.is_node(uid) and name.startswith(node_name_prefix) and \
                    (partition.allocated_node_parents[node_from_id(uid)] == nodespace_from_id(nodespace_uid)):
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

    def ungroup_nodes(self, nodespace_uid, group):
        if nodespace_uid is None:
            nodespace_uid = self.get_nodespace(None).uid
        partition = self.get_partition(nodespace_uid)
        partition.ungroup_nodes(nodespace_uid, group)

    def dump_group(self, nodespace_uid, group):
        if nodespace_uid is None:
            nodespace_uid = self.get_nodespace(None).uid
        partition = self.get_partition(nodespace_uid)

        ids = partition.nodegroups[nodespace_uid][group]
        for element in ids:
            nid = partition.allocated_elements_to_nodes[element]
            uid = node_to_id(nid, partition.pid)
            node = self.get_node(uid)
            print("%s %s" % (node.uid, node.name))

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

    def get_thetas(self, nodespace_uid, group):
        if nodespace_uid is None:
            nodespace_uid = self.get_nodespace(None).uid
        partition = self.get_partition(nodespace_uid)
        return partition.get_thetas(nodespace_uid, group)

    def set_thetas(self, nodespace_uid, group, new_thetas):
        if nodespace_uid is None:
            nodespace_uid = self.get_nodespace(None).uid
        partition = self.get_partition(nodespace_uid)
        partition.set_thetas(nodespace_uid, group, new_thetas)

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

            inlinks = partition_to.inlinks[partition_from.spid]
            indices_from = np.searchsorted(inlinks[0].get_value(borrow=True), partition_from.nodegroups[nodespace_from_uid][group_from])
            indices_to = np.searchsorted(inlinks[1].get_value(borrow=True), partition_to.nodegroups[nodespace_to_uid][group_to])
            cols, rows = np.meshgrid(indices_from, indices_to)
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

            elements_from_indices = partition_from.nodegroups[nodespace_from_uid][group_from]
            elements_to_indices = partition_to.nodegroups[nodespace_to_uid][group_to]

            partition_to.set_inlink_weights(partition_from.spid, elements_from_indices, elements_to_indices, new_w)
        else:
            partition_from.set_link_weights(nodespace_from_uid, group_from, nodespace_to_uid, group_to, new_w)

        uids_to_invalidate = self.get_node_uids(nodespace_from_uid, group_from)
        uids_to_invalidate.extend(self.get_node_uids(nodespace_to_uid, group_to))

        for uid in uids_to_invalidate:
            if uid in self.proxycache:
                del self.proxycache[uid]

    def get_available_gatefunctions(self):
        return ["identity", "absolute", "sigmoid", "tanh", "rect", "one_over_x"]

    def add_slot_monitor(self, node_uid, slot, **_):
        raise RuntimeError("Theano engine does not support slot monitors")

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
