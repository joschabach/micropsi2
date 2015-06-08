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

    def prepare_link_creation(self):
        w_matrix = self.__nodenet.w.get_value(borrow=True)
        w_matrix = w_matrix.tolil()
        self.__nodenet.w.set_value(w_matrix, borrow=True)

    def commit_link_creation(self):
        w_matrix = self.__nodenet.w.get_value(borrow=True)
        w_matrix = w_matrix.tocsr()
        self.__nodenet.w.set_value(w_matrix, borrow=True)

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