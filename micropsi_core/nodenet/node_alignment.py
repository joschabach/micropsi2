#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""
Auto-align the net entities in a given nodespace
"""

__author__ = 'joscha'
__date__ = '15.10.12'

from collections import OrderedDict

def align(nodenet, nodespace):
    """aligns the entities in the given nodenet.
        Arguments:
            nodenet: current node net
            nodespace: the nodespace in which the entities are to be aligned
        Returns:
            True on success, False otherwise
    """
    if not nodespace in nodenet.nodespaces: return False

    unsorted_nodespaces = sorted(nodenet.nodespaces[nodespace].netentities["nodespaces"], key=lambda i:nodenet.nodespaces[i].index)
    unsorted_nodes = sorted(nodenet.nodespaces[nodespace].netentities["nodes"], key = lambda i: nodenet.nodes[i].index)

    BORDER = 50
    GRID = 150
    PREFERRED_WIDTH = 8

    # position nodespaces

    for i, id in enumerate(unsorted_nodespaces):
        nodenet.nodespaces[id].position = (
            BORDER + (i%PREFERRED_WIDTH+1)*GRID - GRID/2,
            BORDER + int(i/PREFERRED_WIDTH+1)*GRID - GRID/2,
            )

    start_position = (BORDER + GRID/2, BORDER + (1.5+int(len(nodenet.nodespaces)/PREFERRED_WIDTH))*GRID)

    while unsorted_nodes:

        region = { "head_node": unsorted_nodes.pop(0) }

        # build a tree of nodes

        # check downward links
        set_regions(region, nodenet, unsorted_nodes[:], ordering = OrderedDict([("sub", "s")]))

        # check backward links

        # check undirected links

        # arrange node tree



    print "ok"
    return True

def set_regions(region, nodenet, unsorted_nodes, ordering):
    """Helper function that sorts connected nodes recursively into regions, according to their link type"""

    current_node = nodenet.nodes[region["head_node"]]
    for gate_type in ordering:
        if gate_type in current_node.gates:
            links = current_node.gates[gate_type].outgoing
            for link in links:
                target_node = nodenet.links[link].target_node
                if target_node in unsorted_nodes:
                    del unsorted_nodes[target_node]
                    direction = ordering[gate_type]
                    if not direction in region: region[direction]=[]
                    print target_node," is in field ", direction, " of node ", current_node
                    region[direction].append(set_regions({"head_node": target_node}, nodenet, unsorted_nodes, ordering))
    return region