# -*- coding: utf-8 -*-
"""
Nodespace definition
"""

from .netentity import NetEntity
import micropsi_core.tools
import warnings

__author__ = 'joscha'
__date__ = '09.05.12'


class Nodespace(NetEntity):
    """A container for net entities.

    One nodespace is marked as root, all others are contained in
    exactly one other nodespace.

    Attributes:
        activators: a dictionary of activators that control the spread of activation, via activator nodes
        netentities: a dictionary containing all the contained nodes and nodespaces, to speed up drawing
    """

    def __init__(self, nodenet, parent_nodespace, position, name="", uid=None,
                 index=None, gatefunctions=None):
        """create a node space at a given position and within a given node space"""
        self.activators = {}
        self.netentities = {}
        NetEntity.__init__(self, nodenet, parent_nodespace, position, name, "nodespaces", uid, index)
        nodenet.nodespaces[self.uid] = self
        if not gatefunctions:
            gatefunctions = dict()
        self.gatefunctions = {}
        for nodetype in gatefunctions:
            for gatetype in gatefunctions[nodetype]:
                self.set_gate_function(nodetype, gatetype, gatefunctions[nodetype][gatetype])

    def get_contents(self):
        """returns a dictionary with all contained net entities, related links and dependent nodes"""
        return self.netentities

    def get_activator_value(self, type):
        """returns the value of the activator of the given type, or 1, if none exists"""
        pass

    def get_data_targets(self):
        """Returns a dictionary of available data targets to associate actors with.

        Data targets are either handed down by the node net manager (to operate on the environment), or
        by the node space itself, to perform directional activation."""
        pass

    def get_data_sources(self):
        """Returns a dictionary of available data sources to associate sensors with.

        Data sources are either handed down by the node net manager (to read from the environment), or
        by the node space itself, to obtain information about its contents."""
        pass

    def set_gate_function(self, nodetype, gatetype, gatefunction, parameters=None):
        """Sets the gatefunction for a given node- and gatetype within this nodespace"""
        if gatefunction:
            if 'gatefunctions' not in self.data:
                self.data['gatefunctions'] = {}
            if nodetype not in self.data['gatefunctions']:
                self.data['gatefunctions'][nodetype] = {}
            self.data['gatefunctions'][nodetype][gatetype] = gatefunction
            if nodetype not in self.gatefunctions:
                self.gatefunctions[nodetype] = {}
            try:
                import math
                self.gatefunctions[nodetype][gatetype] = micropsi_core.tools.create_function(gatefunction, parameters="x, r, t", additional_symbols={'math': math})
            except SyntaxError as err:
                warnings.warn("Syntax error while compiling gate function: %s, %s" % (gatefunction, str(err)))
                raise err
        else:
            if nodetype in self.gatefunctions and gatetype in self.gatefunctions[nodetype]:
                del self.gatefunctions[nodetype][gatetype]
            if nodetype in self.data['gatefunctions'] and gatetype in self.data['gatefunctions'][nodetype]:
                del self.data['gatefunctions'][nodetype][gatetype]

    def get_gatefunction(self, nodetype, gatetype):
        """Retrieve a bytecode-compiled gatefunction for a given node- and gatetype"""
        if nodetype in self.gatefunctions and gatetype in self.gatefunctions[nodetype]:
            return self.gatefunctions[nodetype][gatetype]
