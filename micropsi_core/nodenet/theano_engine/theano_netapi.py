__author__ = 'rvuine'

from micropsi_core.nodenet.netapi import NetAPI

class TheanoNetAPI(NetAPI):
    """
    Theano / numpy extension of the NatAPI, giving native modules access to bulk operations and efficient
    data structures for machine learning purposes.
    """

    def __init__(self, nodenet):
        super(TheanoNetAPI, self).__init__(nodenet)

    def tag_nodes(self, nodespace=None, node_name_prefix=None):
        """
        Will tag the given set of nodes.
        Tags can be used in bulk operations.
        Tagged nodes will have stable sorting accross all bulk operations.
        """
        pass

    def untag_nodes(self, tag):
        """
        Deletes the given tag
        """
        pass

    def get_activations(self, tag):
        """
        Returns an array of activations for the given tag.
        For multi-gate nodes, the activations of the gen gates will be returned.
        """
        pass

    def get_thetas(self, tag):
        """
        Returns an array of theta values for the given tag.
        For multi-gate nodes, the thetas of the gen gates will be returned
        """
        pass

    def set_thetas(self, tag, new_thetas):
        """
        Bulk-sets thetas for the given tag.
        For multi-gate nodes, the thetas of the gen gates will be set
        new_thetas dimensionality has to match the tag length
        """
        pass

    def get_link_weights(self, tag_from, tag_to):
        """
        Returns the weights of links between two tags as a matrix.
        Rows are tag_to slots, columns are tag_from gates.
        Non-existing links will be returned as 0-entries in the matrix.
        """
        pass

    def set_link_weights(self, tag_from, tag_to, new_w):
        """
        Sets the weights of links between two tags from the given matrix new_w.
        Rows are tag_to slots, columns are tag_from gates.
        Note that setting matrix entries to non-0 values will implicitly create links.
        """
        pass