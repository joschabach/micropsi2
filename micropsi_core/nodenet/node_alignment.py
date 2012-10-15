#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""
Auto-align the net entities in a given nodespace
"""

__author__ = 'joscha'
__date__ = '15.10.12'

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
        print i
        nodenet.nodespaces[id].position = (
            BORDER + (i%PREFERRED_WIDTH+1)*GRID - GRID/2,
            BORDER + int(i/PREFERRED_WIDTH+1)*GRID - GRID/2,
            )

    start_position = (BORDER + GRID/2, BORDER + (1.5+int(len(nodenet.nodespaces)/PREFERRED_WIDTH))*GRID)

    class Cell(object):
        def __init__(self, node):
            self.nodes = [node]


    print unsorted_nodes
    print "ok"
    return True
