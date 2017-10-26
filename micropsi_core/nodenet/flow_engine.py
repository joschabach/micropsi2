
import os
import io
import networkx as nx

from abc import ABCMeta, abstractmethod

from micropsi_core.tools import OrderedSet
from micropsi_core.nodenet.node import FlowNodetype


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
            else:
                self._delete_flow_module(node_uid)
        self.verify_flow_consistency()
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
        self.flow_module_instances[node.uid] = node
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

    def generate_worldadapter_flow_instances(self):
        """ Generates flow module instances for the existing autogenerated worldadapter-flowmodule-types """
        for idx, key in enumerate(['datasources', 'datatargets']):
            if key in self.native_module_definitions:
                uid = self.create_node(key, None, [(idx + 2) * 100, 100], name=key)
                self.worldadapter_flow_nodes[key] = uid

    @abstractmethod
    def update_flow_graphs(self, node_uids=None):
        pass  # pragma: no cover

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

    def verify_flow_consistency(self):
        toposort = nx.topological_sort(self.flowgraph)
        for uid in toposort:
            node = self.flow_module_instances.get(uid)
            if node is not None:
                del_uids = []
                input_uids = []
                for in_name in node.inputs:
                    if node.inputmap[in_name]:
                        source_uid, source_name = node.inputmap[in_name]
                        source = self.flow_module_instances[source_uid]
                        if source_name not in source.outputs:
                            self.logger.warning("Removing invalid flow %s:%s -> %s:%s" % (source, source_name, node, in_name))
                            node.inputmap[in_name] = tuple()
                            del_uids.append(source_uid)
                        else:
                            input_uids.append(source_uid)
                for del_uid in del_uids:
                    if del_uid not in input_uids:
                        self.flowgraph.remove_edge(del_uid, node.uid)
                del_uids = []
                output_uids = []
                for out_name in node.outputs:
                    if node.outputmap[out_name]:
                        for target_uid, target_name in node.outputmap[out_name].copy():
                            target = self.flow_module_instances[target_uid]
                            if target_name not in target.inputs:
                                self.logger.warning("Removing invalid flow: %s:%s -> %s:%s" % (node, out_name, target, target_name))
                                node.outputmap[out_name].remove((target_uid, target_name))
                                del_uids.append(target_uid)
                            else:
                                output_uids.append(target_uid)
                for del_uid in del_uids:
                    if del_uid not in output_uids:
                        self.flowgraph.remove_edge(node.uid, del_uid)
            else:
                self.logger.warning("Removing invalid flownode: %s" % uid)
                self._delete_flow_module(uid)
