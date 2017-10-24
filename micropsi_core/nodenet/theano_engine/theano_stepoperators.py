
from micropsi_core.nodenet.stepoperators import Propagate, Calculate, CalculateFlowmodules
import numpy as np
from micropsi_core.nodenet.theano_engine.theano_node import *
from micropsi_core.nodenet.theano_engine.theano_definitions import *


class TheanoPropagate(Propagate):
    """
        theano implementation of the Propagate operator.

        Propagates activation from a across w back to a (a is the gate vector and becomes the slot vector)

        every entry in the target vector is the sum of the products of the corresponding input vector
        and the weight values, i.e. the dot product of weight matrix and activation vector

    """

    def execute(self, nodenet, nodes, netapi):
        # propagate cross-partition to the a_in vectors
        for partition in nodenet.partitions.values():
            for inlinks in partition.inlinks.values():
                inlinks[3]()                                # call the theano_function at [3]

        # then propagate internally in all partitions
        for partition in nodenet.partitions.values():
            partition.propagate()


class TheanoCalculate(Calculate):
    """
        theano implementation of the Calculate operator.

        implements node and gate functions as a theano graph.

    """

    def __init__(self, nodenet):
        self.calculate = None
        self.worldadapter = None
        self.nodenet = nodenet

    def read_sensors_and_actuator_feedback(self):
        self.nodenet.set_sensors_and_actuator_feedback_values()

    def write_actuators(self):
        self.nodenet.set_actuator_values()

    def count_success_and_failure(self, nodenet):
        nays = 0
        yays = 0
        for partition in nodenet.partitions.values():
            if partition.has_pipes:
                nays += len(np.where((partition.n_function_selector.get_value(borrow=True) == NFPG_PIPE_SUR) & (partition.a.get_value(borrow=True) <= -1))[0])
                yays += len(np.where((partition.n_function_selector.get_value(borrow=True) == NFPG_PIPE_SUR) & (partition.a.get_value(borrow=True) >= 1))[0])
        nodenet.set_modulator('base_number_of_expected_events', yays)
        nodenet.set_modulator('base_number_of_unexpected_events', nays)

    def execute(self, nodenet, nodes, netapi):
        self.worldadapter = nodenet.worldadapter_instance

        self.write_actuators()
        self.read_sensors_and_actuator_feedback()
        for partition in nodenet.partitions.values():
            partition.calculate()
        if nodenet.use_modulators:
            self.count_success_and_failure(nodenet)


class CalculateTheanoFlowmodules(CalculateFlowmodules):

    def execute(self, nodenet, nodes, netapi):
        if not nodenet.flow_module_instances:
            return
        for uid, item in nodenet.flow_module_instances.items():
            item.is_part_of_active_graph = False
            item.take_slot_activation_snapshot()
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

        for func in nodenet.flowfunctions:
            if any([node.is_requested() for node in func['endnodes']]):
                skip = False
                inputs = {}
                for node_uid, in_name in func['inputs']:
                    if not nodenet.get_node(node_uid).inputmap[in_name]:
                        raise RuntimeError("Missing Flow-input %s of node %s" % (in_name, str(nodenet.get_node(node_uid))))
                    source_uid, source_name = nodenet.get_node(node_uid).inputmap[in_name]
                    if flowio[source_uid][source_name] is None:
                        # netapi.logger.debug("Skipping graph bc. empty inputs")
                        skip = True
                        break
                    else:
                        inputs["%s_%s" % (node_uid, in_name)] = flowio[source_uid][source_name]
                if skip:
                    for node_uid, out_name in func['outputs']:
                        if node_uid not in flowio:
                            flowio[node_uid] = {}
                        flowio[node_uid][out_name] = None
                    continue
                out = func['callable'](**inputs)
                for n in func['members']:
                    n.is_part_of_active_graph = True
                for index, (node_uid, out_name) in enumerate(func['outputs']):
                    if node_uid not in flowio:
                        flowio[node_uid] = {}
                    if 'datatargets' in nodenet.worldadapter_flow_nodes:
                        targetnode = nodenet.get_node(nodenet.worldadapter_flow_nodes['datatargets'])
                        for uid, name in nodenet.get_node(node_uid).outputmap[out_name]:
                            if uid == targetnode.uid and node_uid != nodenet.worldadapter_flow_nodes.get('datasources', False):
                                targetnode.is_part_of_active_graph = True
                                nodenet.worldadapter_instance.add_to_flow_datatarget(name, out[index])
                    flowio[node_uid][out_name] = self.value_guard(out[index], func, out_name) if out is not None else None
