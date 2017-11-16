

from micropsi_core.nodenet.stepoperators import CalculateFlowmodules


class CalculateNumpyFlowmodules(CalculateFlowmodules):

    def execute(self, nodenet, nodes, netapi):

        if not nodenet.flow_module_instances:
            return
        for uid, item in nodenet.flow_module_instances.items():
            item.is_part_of_active_graph = False
        flowio = {}

        if nodenet.worldadapter_instance:
            if 'datasources' in nodenet.worldadapter_flow_nodes:
                sourcenode = nodenet.get_node(nodenet.worldadapter_flow_nodes['datasources'])
                sourcenode.is_part_of_active_graph = True
                flowio[sourcenode.uid] = {}
                for key in sourcenode.outputs:
                    flowio[sourcenode.uid][key] = self.value_guard(nodenet.worldadapter_instance.get_flow_datasource(key), nodenet.worldadapter, key)
                    for target_uid, target_name in sourcenode.outputmap[key]:
                        datatarget_uid = nodenet.worldadapter_flow_nodes.get('datatargets')
                        if target_uid == datatarget_uid:
                            nodenet.flow_module_instances[datatarget_uid].is_part_of_active_graph = True
                            nodenet.worldadapter_instance.add_to_flow_datatarget(target_name, flowio[sourcenode.uid][key])

        flow_nodes_to_calculate = set()
        for graph in nodenet.flow_graphs:
            if nodenet.get_node(graph[-1]).is_requested():
                [flow_nodes_to_calculate.add(uid) for uid in graph]

        for uid in nodenet.flow_toposort:
            if uid in flow_nodes_to_calculate:
                skip = False
                inputs = {}
                node = nodenet.get_node(uid)
                for in_name in node.inputs:
                    if not node.inputmap[in_name]:
                        raise RuntimeError("Missing Flow-input %s of node %s" % (in_name, str(node)))
                    source_uid, source_name = node.inputmap[in_name]
                    if flowio[source_uid][source_name] is None:
                        # netapi.logger.debug("Skipping graph bc. empty inputs")
                        skip = True
                        break
                    else:
                        inputs["%s_%s" % (node.uid, in_name)] = flowio[source_uid][source_name]
                if skip:
                    flowio[node.uid] = {}
                    for out_name in node.outputs:
                        flowio[node.uid][out_name] = None
                    continue
                func = node.build()
                inputlist = [inputs["%s_%s" % (node.uid, name)] for name in node.inputs]
                result = func(*inputlist, netapi=nodenet.netapi, node=node, parameters=node.clone_parameters())
                if len(node.outputs) == 1 and not isinstance(result, list):
                    result = [result]
                node.is_part_of_active_graph = True
                for index, out_name in enumerate(node.outputs):
                    if node.uid not in flowio:
                        flowio[node.uid] = {}
                    if 'datatargets' in nodenet.worldadapter_flow_nodes:
                        targetnode = nodenet.get_node(nodenet.worldadapter_flow_nodes['datatargets'])
                        for uid, name in node.outputmap[out_name]:
                            if uid == targetnode.uid and node.uid != nodenet.worldadapter_flow_nodes.get('datasources', False):
                                targetnode.is_part_of_active_graph = True
                                nodenet.worldadapter_instance.add_to_flow_datatarget(name, result[index])
                    flowio[node.uid][out_name] = self.value_guard(result[index], func, out_name) if result is not None else None
