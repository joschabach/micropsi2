
import os
import io
import numpy as np
import networkx as nx

from abc import ABCMeta, abstractmethod

from micropsi_core.tools import OrderedSet
from micropsi_core.nodenet.node import FlowNodetype
from micropsi_core.nodenet.flowmodule import FlowModule


class FlowEngine(metaclass=ABCMeta):

    """ Abstract base class for a flow-engine that implements
    flow module behaviour """

    @property
    def metadata(self):
        data = super(FlowEngine, self.__class__).metadata.fget(self)
        data.update({'worldadapter_flow_nodes': self.worldadapter_flow_nodes})
        return data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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

    def save(self, base_path=None, zipfile=None):
        super().save(base_path, zipfile)
        if base_path is None:
            base_path = self.persistency_path
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

    def load(self):
        super().load()
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
                    data.close()
            else:
                self._delete_flow_module(node_uid)

        self.update_flow_graphs()

    def _load_nodetypes(self, nodetype_data):
        newnative_modules = {}
        nodetype_data.update(self.generate_worldadapter_flow_types())
        for key, data in nodetype_data.items():
            if data.get('engine', self.engine) == self.engine:
                if data.get('flow_module'):
                    try:
                        newnative_modules[key] = FlowNodetype(nodenet=self, **data)
                    except Exception as err:
                        self.logger.error("Can not instantiate node type %s: %s: %s" % (key, err.__class__.__name__, str(err)))
                        post_mortem()
                else:
                    result = newnative_modules.update(super()._load_nodetypes({key: data}))
                    if result:
                        newnative_modules.update(result)
        return newnative_modules

    def initialize_nodenet(self, initfrom):
        invalid_uids = super().initialize_nodenet(initfrom)
        self.worldadapter_flow_nodes = initfrom.get('worldadapter_flow_nodes', {})
        return invalid_uids

    def create_node(self, nodetype, nodespace_uid, position, name=None, uid=None, parameters=None, gate_configuration=None):
        uid = super().create_node(nodetype, nodespace_uid, position, name, uid, parameters, gate_configuration)
        if nodetype in self.native_modules and type(self.native_modules[nodetype]) == FlowNodetype:
            self._create_flow_module(self.get_node(uid))
        return uid

    def get_node(self, uid):
        if uid in self.flow_module_instances:
            return self.flow_module_instances[uid]
        else:
            return super().get_node(uid)

    def delete_node(self, uid):
        if uid in self.flow_module_instances:
            self._delete_flow_module(uid)
        super().delete_node(uid)
        self.update_flow_graphs()

    def _create_flow_module(self, node):
        self.flowgraph.add_node(node.uid, implementation=node.nodetype.implementation)

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

    def create_link(self, source_node_uid, gate_type, target_node_uid, slot_type, weight=1):
        result = super().create_link(source_node_uid, gate_type, target_node_uid, slot_type, weight)
        if target_node_uid in self.flow_module_instances:
            self.update_flow_graphs()
        return result

    def delete_link(self, source_node_uid, gate_type, target_node_uid, slot_type):
        result = super().delete_link(source_node_uid, gate_type, target_node_uid, slot_type)
        if target_node_uid in self.flow_module_instances:
            self.update_flow_graphs()
        return result

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

    @abstractmethod
    def generate_worldadapter_flow_instances(self):
        """ Generates flow module instances for the existing autogenerated worldadapter-flowmodule-types """
        pass  # pragma: no cover

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
                path = [uid for uid in toposort if uid in ancestors] + [enduid]
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
                if len(paths) == 0 or paths[-1]['implementation'] != node.implementation:
                    paths.append({'implementation': node.implementation, 'members': [node], 'hash': node.uid})
                else:
                    paths[-1]['members'].append(node)
                    paths[-1]['hash'] += node.uid
        return paths

    @abstractmethod
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
            if true, return a callable that expects a parameter "thetas" that will be used instead of existing thetas. defaults to False

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
        pass  # pragma: no cover

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

    @abstractmethod
    def set_theta(self, node_uid, name, val):
        pass  # pragma: no cover

    @abstractmethod
    def get_theta(self, node_uid, name):
        pass  # pragma: no cover

    @abstractmethod
    def collect_thetas(self, node_uids):
        pass  # pragma: no cover
