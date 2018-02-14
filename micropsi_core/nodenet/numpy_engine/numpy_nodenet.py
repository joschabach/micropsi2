

import networkx as nx

from micropsi_core import tools
from micropsi_core.nodenet.node import FlowNodetype
from micropsi_core.nodenet.flow_engine import FlowEngine
from micropsi_core.nodenet.flow_netapi import FlowNetAPI
from micropsi_core.nodenet.dict_engine.dict_nodenet import DictNodenet
from micropsi_core.nodenet.numpy_engine.numpy_flowmodule import NumpyFlowModule
from micropsi_core.nodenet.numpy_engine.numpy_stepoperators import CalculateNumpyFlowmodules


class NumpyNodenet(FlowEngine, DictNodenet):

    @property
    def engine(self):
        return "numpy_engine"

    @property
    def worldadapter_instance(self):
        return self._worldadapter_instance

    @worldadapter_instance.setter
    def worldadapter_instance(self, _worldadapter_instance):
        typechange = True
        if self._worldadapter_instance and self.worldadapter == _worldadapter_instance.__class__.__name__ and \
                _worldadapter_instance.device_map == self._worldadapter_instance.device_map:
            typechange = False
        super(NumpyNodenet, self.__class__).worldadapter_instance.fset(self, _worldadapter_instance)
        if typechange:
            flow_io_types = self.generate_worldadapter_flow_types(delete_existing=typechange)
            self.native_module_definitions.update(flow_io_types)
            for key in flow_io_types:
                self.native_modules[key] = FlowNodetype(nodenet=self, **flow_io_types[key])
            self.generate_worldadapter_flow_instances()

    def _create_netapi(self):
        self.netapi = FlowNetAPI(self)

    def initialize_stepoperators(self):
        super().initialize_stepoperators()
        self.stepoperators.append(CalculateNumpyFlowmodules(self))
        self.stepoperators.sort(key=lambda op: op.priority)

    def merge_data(self, nodenet_data, keep_uids=False, uidmap={}, **kwargs):
        flow_data = {}
        for uid in list(nodenet_data.get('nodes', {}).keys()):
            data = nodenet_data['nodes'][uid]
            if data['type'] in self.native_modules and isinstance(self.native_modules[data['type']], FlowNodetype):
                del nodenet_data['nodes'][uid]
                flow_data[uid] = data

        nodespaces_to_merge = set(nodenet_data.get('nodespaces', {}).keys())
        for nodespace in nodespaces_to_merge:
            self.initialize_nodespace(nodespace, nodenet_data['nodespaces'])
        del nodenet_data['nodespaces']

        for uid in flow_data:
            if not keep_uids:
                newuid = tools.generate_uid()
            else:
                newuid = uid
            flow_data[uid]['uid'] = newuid
            uidmap[uid] = newuid
            self._nodes[newuid] = NumpyFlowModule(self, **flow_data[uid])
            self.flow_module_instances[newuid] = self._nodes[uid]
            self.native_module_instances[newuid] = self._nodes[uid]
        super().merge_data(nodenet_data, keep_uids=keep_uids, uidmap=uidmap, **kwargs)

    def create_node(self, nodetype, nodespace_uid, position, name=None, uid=None, parameters=None, gate_configuration=None):
        if nodetype in self.native_modules and type(self.native_modules[nodetype]) == FlowNodetype:
            nodespace_uid = self.get_nodespace(nodespace_uid).uid
            node = NumpyFlowModule(
                self,
                parent_nodespace=nodespace_uid,
                position=position,
                name=name,
                type=nodetype,
                uid=uid,
                parameters=parameters,
                gate_configuration=gate_configuration)
            self._create_flow_module(node)
            return node.uid
        else:
            return super().create_node(nodetype, nodespace_uid, position, name, uid, parameters, gate_configuration)

    def update_flow_graphs(self, node_uids=None):
        if self.is_flowbuilder_active:
            return
        self.flow_toposort = nx.topological_sort(self.flowgraph)
        self.flow_graphs = []
        endpoints = []
        for uid in self.flow_toposort:
            node = self.flow_module_instances.get(uid)
            if node is not None:
                if node.is_output_node():
                    endpoints.append(uid)
            node.ensure_initialized()

        for enduid in endpoints:
            ancestors = nx.ancestors(self.flowgraph, enduid)
            node = self.flow_module_instances[enduid]
            if ancestors or node.inputs == []:
                path = [uid for uid in self.flow_toposort if uid in ancestors] + [enduid]
                if path:
                    self.flow_graphs.append(path)

    def reload_native_modules(self, native_modules):
        wa_flows = self.worldadapter_flow_nodes  # save uids, because clear() deletes that info
        states_to_restore = {}
        for uid, node in self.native_module_instances.items():
            json_state, numpy_state = node.get_persistable_state()
            if numpy_state:
                states_to_restore[uid] = [json_state, numpy_state]
        super().reload_native_modules(native_modules)  # dict_nodenet reloads with clear() and merge()
        self.worldadapter_flow_nodes = wa_flows
        for uid in states_to_restore:
            self.native_module_instances[uid].set_persistable_state(*states_to_restore[uid])
        self.verify_flow_consistency()
        self.update_flow_graphs()
