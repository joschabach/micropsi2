__author__ = 'rvuine'

from micropsi_core.nodenet.netapi import NetAPI

class TheanoNetAPI(NetAPI):
    """
    Theano / numpy extension of the NatAPI, giving native modules access to bulk operations and efficient
    data structures for machine learning purposes.
    """

    def __init__(self, nodenet):
        super(TheanoNetAPI, self).__init__(nodenet)

    def group_nodes(self, nodespace=None, node_name_prefix=None):
        """
        Will group the given set of nodes.
        Groups can be used in bulk operations.
        Grouped nodes will have stable sorting accross all bulk operations.
        """
        pass

    def group_nodes(self, group):
        """
        Deletes the given group (not the nodes, just the group assignment)
        """
        pass

    def get_activations(self, group):
        """
        Returns an array of activations for the given group.
        For multi-gate nodes, the activations of the gen gates will be returned.
        """
        pass

    def get_thetas(self, group):
        """
        Returns an array of theta values for the given group.
        For multi-gate nodes, the thetas of the gen gates will be returned
        """
        pass

    def set_thetas(self, group, new_thetas):
        """
        Bulk-sets thetas for the given group.
        For multi-gate nodes, the thetas of the gen gates will be set
        new_thetas dimensionality has to match the group length
        """
        pass

    def get_link_weights(self, group_from, group_to):
        """
        Returns the weights of links between two groups as a matrix.
        Rows are group_to slots, columns are group_from gates.
        Non-existing links will be returned as 0-entries in the matrix.
        """
        pass

    def set_link_weights(self, group_from, group_to, new_w):
        """
        Sets the weights of links between two groups from the given matrix new_w.
        Rows are group_to slots, columns are group_from gates.
        Note that setting matrix entries to non-0 values will implicitly create links.
        """
        pass