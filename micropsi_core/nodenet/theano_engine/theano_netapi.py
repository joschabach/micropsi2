__author__ = 'rvuine'

from micropsi_core.nodenet.netapi import NetAPI


class TheanoNetAPI(NetAPI):
    """
    Theano / numpy extension of the NetAPI, giving native modules access to bulk operations and efficient
    data structures for machine learning purposes.
    """

    def __init__(self, nodenet):
        super(TheanoNetAPI, self).__init__(nodenet)
        self.__nodenet = nodenet

    @property
    def floatX(self):
        return self.__nodenet.numpyfloatX

    def announce_nodes(self, nodespace_uid, numer_of_nodes, average_element_per_node):
        self.__nodenet.announce_nodes(nodespace_uid, numer_of_nodes, average_element_per_node)

    def decay_por_links(self, nodespace_uid):
        """ Decays all por-links in the given nodespace """
        #    por_cols = T.lvector("por_cols")
        #    por_rows = T.lvector("por_rows")
        #    new_w = T.set_subtensor(nodenet.w[por_rows, por_cols], nodenet.w[por_rows, por_cols] - 0.0001)
        #    self.decay = theano.function([por_cols, por_rows], None, updates={nodenet.w: new_w}, accept_inplace=True)
        import numpy as np
        from .theano_definitions import node_from_id, PIPE, POR
        nodespace_uid = self.get_nodespace(nodespace_uid).uid
        porretdecay = self.__nodenet.get_modulator('base_porret_decay_factor')
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

    def add_gate_activation_recorder(self, group_definition, name, interval=1):
        """ Adds an activation recorder to a group of nodes."""
        return self.__nodenet.add_gate_activation_recorder(group_definition, name, interval)

    def add_node_activation_recorder(self, group_definition, name, interval=1):
        """ Adds an activation recorder to a group of nodes."""
        return self.__nodenet.add_node_activation_recorder(group_definition, name, interval)

    def add_linkweight_recorder(self, from_group_definition, to_group_definition, name, interval=1):
        """ Adds a linkweight recorder to links between to groups."""
        return self.__nodenet.add_linkweight_recorder(from_group_definition, to_group_definition, name, interval)

    def get_recorder(self, uid):
        """Returns the recorder with the given uid"""
        return self.__nodenet.get_recorder(uid)

    def remove_recorder(self, uid):
        """Removes the recorder with the given uid"""
        return self.__nodenet.remove_recorder(uid)

    def group_node_gates(self, node_uid, gate_prefix, group_name=None):
        self.__nodenet.group_highdimensional_elements(node_uid, gate=gate_prefix, group_name=group_name)

    def group_node_slots(self, node_uid, slot_prefix, group_name=None):
        self.__nodenet.group_highdimensional_elements(node_uid, slot=slot_prefix, group_name=group_name)

    def connect_flow_modules(self, source_node, source_output, target_node, target_input):
        """ Link two flow_modules """
        return self.__nodenet.connect_flow_modules(source_node.uid, source_output, target_node.uid, target_input)

    def connect_flow_module_to_worldadapter(self, flow_module, gateslot):
        """ Link a flow_module to a worldadapter.
        Depending on whether you give an input or output name, it links to either
        datasources or datatargets """
        return self.__nodenet.connect_flow_module_to_worldadapter(flow_module.uid, gateslot)

    def disconnect_flow_modules(self, source_node, source_output, target_node, target_input):
        """ Removes the link between the given flow_modules """
        return self.__nodenet.disconnect_flow_modules(source_node.uid, source_output, target_node.uid, target_input)

    def disconnect_flow_module_from_worldadapter(self, flow_module, gateslot):
        """ Unlinks the given connection betwenn the given flow_module and the worldadapter """
        return self.__nodenet.disconnect_flow_module_from_worldadapter(flow_module.uid, gateslot)

    def compile_flow_subgraph(self, nodes, with_shared_variables=False):
        """ Returns one callable for the given flow_modules """
        func, dangling_inputs, dangling_outputs = self.__nodenet.compile_flow_subgraph([n.uid for n in nodes], with_shared_variables=with_shared_variables, partial=True)
        return func

    def collect_shared_variables(self, nodes):
        """ Returns a list of shared variabels, sorted by node first, alphabetically second """
        return self.__nodenet.collect_shared_variables([n.uid for n in nodes])
