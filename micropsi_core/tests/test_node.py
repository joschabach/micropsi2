#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""
Tests for node, nodefunction and the like
"""

from micropsi_core.nodenet.node import Node, Nodetype, STANDARD_NODETYPES
from micropsi_core.nodenet.nodefunctions import concept
from micropsi_core import runtime as micropsi


def test_nodetype_function_definition_overwrites_default_function_name(fixed_nodenet):
    nodenet = micropsi.get_nodenet(fixed_nodenet)
    nodetype = STANDARD_NODETYPES['Concept'].copy()
    foo = Nodetype(nodenet=nodenet, **nodetype)
    assert foo.nodefunction == concept
    nodetype['nodefunction_definition'] = 'return 17'
    foo = Nodetype(nodenet=nodenet, **nodetype)
    assert foo.nodefunction != concept
    assert foo.nodefunction(nodenet, None) == 17

