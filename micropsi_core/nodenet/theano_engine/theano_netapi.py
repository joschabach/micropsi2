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

    def group_nodes_by_names(self, nodespace=None, node_name_prefix=None):
        """
        Will group the given set of nodes.
        Groups can be used in bulk operations.
        Grouped nodes will have stable sorting accross all bulk operations.
        """
        self.__nodenet.group_nodes_by_names(nodespace, node_name_prefix)

    def group_nodes_by_ids(self, node_ids, group_name):
        """
        Will group the given set of nodes.
        Groups can be used in bulk operations.
        Grouped nodes will have stable sorting accross all bulk operations.
        """
        self.__nodenet.group_nodes_by_ids(node_ids, group_name)

    def ungroup_nodes(self, group):
        """
        Deletes the given group (not the nodes, just the group assignment)
        """
        self.__nodenet.ungroup_nodes(group)

    def get_activations(self, group):
        """
        Returns an array of activations for the given group.
        For multi-gate nodes, the activations of the gen gates will be returned.
        """
        return self.__nodenet.get_activations(group)

    def get_thetas(self, group):
        """
        Returns an array of theta values for the given group.
        For multi-gate nodes, the thetas of the gen gates will be returned
        """
        return self.__nodenet.get_thetas(group)

    def set_thetas(self, group, new_thetas):
        """
        Bulk-sets thetas for the given group.
        For multi-gate nodes, the thetas of the gen gates will be set
        new_thetas dimensionality has to match the group length
        """
        self.__nodenet.set_thetas(group, new_thetas)

    def get_link_weights(self, group_from, group_to):
        """
        Returns the weights of links between two groups as a matrix.
        Rows are group_to slots, columns are group_from gates.
        Non-existing links will be returned as 0-entries in the matrix.
        """
        return self.__nodenet.get_link_weights(group_from, group_to)

    def set_link_weights(self, group_from, group_to, new_w):
        """
        Sets the weights of links between two groups from the given matrix new_w.
        Rows are group_to slots, columns are group_from gates.
        Note that setting matrix entries to non-0 values will implicitly create links.
        """
        self.__nodenet.set_link_weights(group_from, group_to, new_w)

    def get_selectors(self, group):
        """
        Returns The indices for the elements for the given group, as an ndarray of ints.
        These indices are valid in a, w, and theta.
        """
        return self.__nodenet.nodegroups[group]

    def get_a(self):
        """
        Returns the theano shared variable with the activation vector
        """
        return self.__nodenet.a

    def get_w(self):
        """
        Returns the theano shared variable with the link weights
        Caution: Changing non-zero values to zero or zero-values to non-zero will lead to inconsistencies.
        """
        return self.__nodenet.w

    def get_theta(self):
        """
        Returns the theano shared variable with the "theta" parameter values
        """
        return self.__nodenet.g_theta