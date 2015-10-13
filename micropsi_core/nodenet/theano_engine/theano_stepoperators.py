
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
        if self.worldadapter is None:
            return

        datasource_to_value_map = {}
        for datasource in self.worldadapter.get_available_datasources():
            datasource_to_value_map[datasource] = self.worldadapter.get_datasource(datasource)

        datatarget_to_value_map = {}
        for datatarget in self.worldadapter.get_available_datatargets():
            datatarget_to_value_map[datatarget] = self.worldadapter.get_datatarget_feedback(datatarget)

        self.nodenet.set_sensors_and_actuator_feedback_to_values(datasource_to_value_map, datatarget_to_value_map)

    def write_actuators(self):
        if self.worldadapter is None:
            return

        values_to_write = self.nodenet.read_actuators()
        for datatarget in values_to_write:
            self.worldadapter.add_to_datatarget(datatarget, values_to_write[datatarget])

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
        self.count_success_and_failure(nodenet)
