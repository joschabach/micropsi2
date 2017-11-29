__author__ = 'rvuine'

from micropsi_core.nodenet.flow_netapi import FlowNetAPI


class TheanoNetAPI(FlowNetAPI):
    """
    Theano extension of the NetAPI, giving native modules access to bulk operations and efficient
    data structures for machine learning purposes.
    """

    def announce_nodes(self, nodespace_uid, numer_of_nodes, average_element_per_node):
        """ announce a new number of nodes and grow the internal matrices before adding the nodes """
        self._nodenet.announce_nodes(nodespace_uid, numer_of_nodes, average_element_per_node)

    def decay_por_links(self, nodespace_uid):
        """ Decays all por-links in the given nodespace """
        #    por_cols = T.lvector("por_cols")
        #    por_rows = T.lvector("por_rows")
        #    new_w = T.set_subtensor(nodenet.w[por_rows, por_cols], nodenet.w[por_rows, por_cols] - 0.0001)
        #    self.decay = theano.function([por_cols, por_rows], None, updates={nodenet.w: new_w}, accept_inplace=True)
        import numpy as np
        from .theano_definitions import node_from_id, PIPE, POR
        nodespace_uid = self.get_nodespace(nodespace_uid).uid
        porretdecay = self._nodenet.get_modulator('base_porret_decay_factor')
        ns = self.get_nodespace(nodespace_uid)
        partition = ns._partition
        if partition.has_pipes and porretdecay != 0:
            ns_id = node_from_id(nodespace_uid)
            node_ids = np.where(partition.allocated_node_parents == ns_id)[0]
            pipe_ids = np.where(partition.allocated_nodes == PIPE)[0]
            ns_pipes = np.intersect1d(node_ids, pipe_ids, assume_unique=True)
            por_cols = partition.allocated_node_offsets[ns_pipes] + POR
            w = partition.w.get_value(borrow=True)
            por_rows = np.nonzero(w[:, por_cols] > 0.)[0]
            cols, rows = np.meshgrid(por_cols, por_rows)
            w_update = w[rows, cols]
            w_update *= (1 - porretdecay)
            w[rows, cols] = w_update
            partition.w.set_value(w, borrow=True)

    def group_node_gates(self, node_uid, gate_prefix, group_name=None):
        """ Creates a group of the high-dimensional gates of the given node"""
        self._nodenet.group_highdimensional_elements(node_uid, gate=gate_prefix, group_name=group_name)

    def group_node_slots(self, node_uid, slot_prefix, group_name=None):
        """ Creates a group of the high-dimensional slots of the given node"""
        self._nodenet.group_highdimensional_elements(node_uid, slot=slot_prefix, group_name=group_name)

    def get_callable_flowgraph(self, nodes, requested_outputs=None, use_different_thetas=False, use_unique_input_names=False):
        """ Returns one callable for the given flow_modules.
        Parameters:
            use_different_thetas (default: False) - Return a callable that expects a parameter "thetas" that will be used instead of existing thetas
            use_unique_input_names (default: False) - Return a callable that expects input parameter names as "uid_name" where uid is the node_uid, and name is the input_name
            requested_outputs (default:None) - Optional list of (node_uid, outputname) tuples, so that the callable will return only the given outputs
        """
        func, dangling_inputs, dangling_outputs = self._nodenet.compile_flow_subgraph([n.uid for n in nodes], requested_outputs=requested_outputs, use_different_thetas=use_different_thetas, use_unique_input_names=use_unique_input_names)
        return func

    def collect_thetas(self, nodes):
        """ Returns a list of thetas, sorted by node first, alphabetically second """
        return self._nodenet.collect_thetas([n.uid for n in nodes])

    def shadow_flowgraph(self, flow_modules):
        """ Creates a shallow copy of the given flow_modules, copying instances and internal connections.
        Shallow copies will always have the parameters and shared variables of their originals
        """
        return self._nodenet.shadow_flowgraph(flow_modules)
