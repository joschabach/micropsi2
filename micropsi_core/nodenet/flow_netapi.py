
from contextlib import contextmanager
from micropsi_core.nodenet.netapi import NetAPI


class FlowNetAPI(NetAPI):
    """
    Flow-extension to netapi. Intended to work with flow-engine type nodenets
    """

    @property
    def floatX(self):
        """ configured numpy float datatype (either numpy.float32 or numpy.float64"""
        return self._nodenet.numpyfloatX

    @property
    @contextmanager
    def flowbuilder(self):
        """ Contextmanager to prevent the nodenet from compiling flow-graphs. Will compile when the context is left:
        Usage:
        with netapi.flowbuilder:
            # create & connect flow modules
        nodenet.step() """
        self._nodenet.is_flowbuilder_active = True
        yield
        self._nodenet.is_flowbuilder_active = False
        self._nodenet.update_flow_graphs()

    def flow(self, source_node, source_output, target_node, target_input):
        """ Create flow between flowmodules. Use "worldadapter" and "datasources"/"datatargets" to create flow
        to the worldadapter """
        source = source_node if source_node == 'worldadapter' else source_node.uid
        target = target_node if target_node == 'worldadapter' else target_node.uid
        return self._nodenet.flow(source, source_output, target, target_input)

    def unflow(self, source_node, source_output, target_node, target_input):
        """ Remove flow between the given flow_modules """
        source = source_node if source_node == 'worldadapter' else source_node.uid
        target = target_node if target_node == 'worldadapter' else target_node.uid
        return self._nodenet.unflow(source, source_output, target, target_input)
