
from micropsi_core.nodenet.stepoperators import Propagate, Calculate
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


class TheanoCalculateFlowmodules(Propagate):

    @property
    def priority(self):
        return 0

    def __init__(self, nodenet):
        self.nodenet = nodenet

    def execute(self, nodenet, nodes, netapi):
        for uid, item in nodenet.flow_module_instances.items():
            item.take_slot_activation_snapshot()
        flowio = {
            'worldadapter': {
                'datasources': nodenet.worldadapter_instance.get_datasource_values(),
                'datatargets': None
            }
        }
        for flowtype, startnode, func, endnode in nodenet.flowfuncs:
            if endnode.is_requested():
                # import pdb; pdb.set_trace()
                try:
                    inputs = {}
                    for key in startnode.inputmap:
                        for source_uid, source_name in startnode.inputmap[key]:
                            inputs[key] = flowio[source_uid][source_name]

                    if flowtype == 'symbolic':
                        out = func(**inputs)
                    else:
                        out = func(netapi, startnode, **inputs)
                        if len(endnode.outputs) == 1:
                            out = [out]
                    if out is not None:
                        flowio[endnode.uid] = {}
                        for idx, name in enumerate(endnode.outputs):
                            if endnode.outputmap[name] == {('worldadapter', 'datatargets')}:
                                nodenet.worldadapter_instance.add_datatarget_values(out[idx])
                            else:
                                flowio[endnode.uid][name] = out[idx]
                except KeyError:
                    import traceback
                    print("missing in or output: ", traceback.format_exc())
