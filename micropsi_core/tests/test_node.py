#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""
Tests for node, nodefunction and the like
"""

from micropsi_core.nodenet.node import Nodetype
from micropsi_core.nodenet.nodefunctions import register, concept
from micropsi_core import runtime as micropsi
import pytest


@pytest.mark.engine("theano_engine")
def test_nodetype_function_definition_overwrites_default_function_name_theano(fixed_nodenet):
    nodenet = micropsi.get_nodenet(fixed_nodenet)
    nodetype = nodenet.get_standard_nodetype_definitions()['Register'].copy()
    foo = Nodetype(nodenet=nodenet, **nodetype)
    assert foo.nodefunction == register
    nodetype['nodefunction_definition'] = 'return 17'
    foo = Nodetype(nodenet=nodenet, **nodetype)
    assert foo.nodefunction != register
    assert foo.nodefunction(nodenet, None) == 17


@pytest.mark.engine("dict_engine")
def test_nodetype_function_definition_overwrites_default_function_name(fixed_nodenet):
    nodenet = micropsi.get_nodenet(fixed_nodenet)
    nodetype = nodenet.get_standard_nodetype_definitions()['Concept'].copy()
    foo = Nodetype(nodenet=nodenet, **nodetype)
    assert foo.nodefunction == concept
    nodetype['nodefunction_definition'] = 'return 17'
    foo = Nodetype(nodenet=nodenet, **nodetype)
    assert foo.nodefunction != concept
    assert foo.nodefunction(nodenet, None) == 17


def test_node_states(test_nodenet, node):
    nodenet = micropsi.get_nodenet(test_nodenet)
    node = nodenet.get_node(node)
    assert node.get_state('foobar') is None
    node.set_state('foobar', 'bazbaz')
    assert node.get_state('foobar') == 'bazbaz'
    node.set_state('foobar', 42)
    assert node.get_state('foobar') == 42
