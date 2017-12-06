
from contextlib import contextmanager
from micropsi_core.nodenet.netapi import NetAPI


class FlowNetAPI(NetAPI):
    """
    Flow-extension to netapi. Intended to work with flow-engine type nodenets
    """

    @property
    @contextmanager
    def flowbuilder(self):
        """ Contextmanager to prevent the nodenet from compiling flow-graphs.

        Will compile when the context is left.

        Usage:
        with netapi.flowbuilder:
            # create & connect flow modules

        nodenet.step()

        """
        self._nodenet.is_flowbuilder_active = True
        yield
        self._nodenet.is_flowbuilder_active = False
        self._nodenet.update_flow_graphs()

    def flow(self, source_node, source_output, target_node, target_input):
        """ Create a flow connection between flowmodules.

        To connect to the worldadapter (aka "datasources" and "datatargets"),
        set source_node or target_node to "worldadapter".

        Params
        ------
            source_node: node instance or string "worldadapter"
                Provide a node instance if the flow originates form another node.
                Provide "worldadapter" if the origin is one of the datasources.

            source_output: string
                name of an output field on the source node, or name of a
                datasource if source_node is "worldadapter".

            target_node: node instance or string "worldadapter"
                Provide a node if the flow should connect to another node.
                Provide "worldadapter" if it should connect to a datatarget.

            target_input: string
                name of an input field on the target node, or name of a
                datatarget if target_node is "worldadapter".

        Returns
        -------
            None

        """
        source = source_node if source_node == 'worldadapter' else source_node.uid
        target = target_node if target_node == 'worldadapter' else target_node.uid
        return self._nodenet.flow(source, source_output, target, target_input)

    def unflow(self, source_node, source_output, target_node, target_input):
        """ Remove flow between the given flow_modules

        See `netapi.flow` for docs
        """
        source = source_node if source_node == 'worldadapter' else source_node.uid
        target = target_node if target_node == 'worldadapter' else target_node.uid
        return self._nodenet.unflow(source, source_output, target, target_input)
