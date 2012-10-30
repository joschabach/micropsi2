#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""
Auto-align the net entities in a given nodespace
"""

__author__ = 'joscha'
__date__ = '15.10.12'

from collections import OrderedDict
from micropsi_core.tools import OrderedSet
import math


BORDER = 50.0
GRID = 150.0
PREFERRED_WIDTH = 8.0


def align(nodenet, nodespace):
    """aligns the entities in the given nodenet.
        Arguments:
            nodenet: current node net
            nodespace: the nodespace in which the entities are to be aligned
        Returns:
            True on success, False otherwise
    """
    if not nodespace in nodenet.nodespaces: return False

    unaligned_nodespaces = sorted(nodenet.nodespaces[nodespace].netentities.get("nodespaces", {}),
        key=lambda i:nodenet.nodespaces[i].index)
    unaligned_nodes = sorted(nodenet.nodespaces[nodespace].netentities["nodes"],
        key = lambda i: nodenet.nodes[i].index)



    # position nodespaces

    for i, id in enumerate(unaligned_nodespaces):
        nodenet.nodespaces[id].position = (
            BORDER + (i%PREFERRED_WIDTH+1)*GRID - GRID/2,
            BORDER + int(i/PREFERRED_WIDTH+1)*GRID - GRID/2,
            )

    start_position = (BORDER + GRID/2, BORDER + (0.5+math.ceil(len(unaligned_nodespaces)/PREFERRED_WIDTH))*GRID)

    # simplify linkage
    print "starting alignment"
    group = unify_links(nodenet, unaligned_nodes)
    print "nodes unified"

    por_groups = group_horizontal_links(group)
    por_groups.arrange(nodenet, start_position)
    # horizontal_groups = group_horizontal_links(structure)
    print "horizontal grouping done"
    # print horizontal_groups

    # arrange nodes in a grid
        # arrange node tree



    print "ok"
    return True

INVERSE_DIRECTIONS = { "s": "n", "w": "e", "nw": "se", "ne": "sw",
                       "n": "s", "e": "w", "se": "nw", "sw": "ne",
                       "o": "O", "O": "o", "b": "a", "a": "b" }

class DisplayNode(object):
    def __init__(self, uid, directions = None, parent = None):
        self.uid = uid
        self.directions = directions or {}
        self.parent = parent

    def __repr__(self):
        params = "'%s'" % self.uid
        if self.directions:
            params += ", directions=%r" % self.directions
        #if self.parent:
        #    params += ", parent=%r" % self.parent
        return '%s(%s)' % (self.__class__.__name__, params)

    def width(self):
        return 1

    def height(self):
        return 1

    def arrange(self, nodenet, starting_point = (0,0)):
        nodenet.nodes[self.uid].position = starting_point


def unify_links(nodenet, node_id_list):
    """create a proxy representation of the node space to simplify bi-directional links.
    This structure is an ordered set of proxy nodes (DisplayNode) with directions.
    Each direction is marked by its key (such as "n"), and followed by a list of nodes
    that are linked in that direction. The nodes are sorted by their index (as marked in
    the node net).

    Arguments:
        nodenet: the nodenet that we are working on
        node_id_list: a list of node ids to be processed
    """

    node_index = OrderedDict([(i, DisplayNode(i)) for i in node_id_list])

    for node_id in node_id_list:
        node = nodenet.nodes[node_id]
        for gate_type in node.gates:
            direction = {"sub": "s", "ret": "w", "cat": "ne", "sym":"nw",
                         "sur": "n", "por": "e", "exp": "sw", "ref":"se", "gen": "b"}.get(gate_type, "o")
            if direction:
                # "o" is for unknown gate types
                link_ids = node.gates[gate_type].outgoing
                for link_id in link_ids:
                    target_node_id = nodenet.links[link_id].target_node.uid
                    if target_node_id in node_index:
                        # otherwise, the link points outside the current nodespace and will be ignored here
                        if not direction in node_index[node_id].directions:
                            node_index[node_id].directions[direction]=OrderedSet()
                        node_index[node_id].directions[direction].add(node_index[target_node_id])
                        inverse = INVERSE_DIRECTIONS[direction]
                        if not inverse in node_index[target_node_id].directions:
                            node_index[target_node_id].directions[inverse]=OrderedSet()
                        node_index[target_node_id].directions[inverse].add(node_index[node_id])

    # finally, let us sort all node_id_list in the direction groups
    for node_id in node_index:
        for direction in node_index[node_id].directions:
            node_index[node_id].directions[direction] = list(node_index[node_id].directions[direction])
            node_index[node_id].directions[direction].sort(key = lambda i: nodenet.nodes[i.uid].index)

    return UnorderedGroup(node_index.values())


def group_horizontal_links(all_nodes):
    """group direct horizontal links (por)"""
    h_groups = UnorderedGroup()
    excluded_nodes = OrderedSet()
    for i in all_nodes:
        if not i.directions.get("w"): # find leftmost nodes
            excluded_nodes.add(i)
            if i.directions.get("e"):
                h_group = HorizontalGroup([i])
                add_nodes_horizontally(i, h_group, excluded_nodes)
                if len(h_group) > 1:
                    h_groups.append(h_group)
                else:
                    h_groups.append(i)
            else:
                h_groups.append(i)
    # now handle circles
    for i in all_nodes:
        if not i in excluded_nodes:
            excluded_nodes.add(i)
            if i.directions.get("e"):
                h_group = HorizontalGroup([i])
                add_nodes_horizontally(i, h_group, excluded_nodes)
                if len(h_group) > 1:
                    h_groups.append(h_group)
                else:
                    h_groups.append(i)
            else:
                h_groups.append(i)
    return h_groups

def add_nodes_horizontally(display_node, h_group, excluded_nodes):
    """recursive helper function for adding horizontally linked nodes to a group"""

    successor_nodes = [ node for node in display_node.directions.get("e", []) if node not in excluded_nodes ]

    if len(successor_nodes) > 1:
        # let us group these guys vertically
        v_group = VerticalGroup()
        for node in successor_nodes:
            excluded_nodes.add(node)
            if node.directions.get("e"):
                local_h_group = HorizontalGroup([node])
                add_nodes_horizontally(node, local_h_group, excluded_nodes)
                v_group.append(local_h_group)
            else:
                v_group.append(node)
        h_group.append(v_group)

    else:
        if len(successor_nodes) == 1:
            node = successor_nodes[0]
            excluded_nodes.add(node)
            h_group.append(node)
            if node.directions.get("e"):
                add_nodes_horizontally(node, h_group, excluded_nodes)


class UnorderedGroup(list):

    def __init__(self, elements = None, parent = None):
        self.directions = {}
        self.parent = parent
        if elements:
            list.__init__(self, elements)
            for i in elements:
                i.parent = self

    def __repr__(self):
        params = ""
        if len(self):
            params += "%r" % list(self)
        # if self.parent:
        #    params += ", parent=%r" % self.parent
        return '%s(%s)' % (self.__class__.__name__, params)

    def width(self):
        width = 0
        for i in self:
            width = max(width, i.width())
        return width

    def height(self):
        height = 0
        for i in self:
            height += i.height()
        return height

    def arrange(self, nodenet, start_position = (0, 0)):
        # arrange elements of unordered group below each other
        x, y = start_position
        for i in self:
            i.arrange(nodenet, (x, y))
            y += i.height()*GRID

class HorizontalGroup(UnorderedGroup):
    def __init__(self, elements = None, parent = None):
        UnorderedGroup.__init__(self, elements, parent)
        if elements:
            for i in elements:
                if i.directions.get("n"):
                    self.directions["n"] = i.directions["n"][0]
                    break

    def width(self):
        width = 0
        for i in self:
            width += i.width()
        return width

    def height(self):
        height = 0
        for i in self:
            height = max(i.height(), height)
        return height

    def arrange(self, nodenet, start_position = (0,0)):
        x, y = start_position
        for i in self:
            i.arrange(nodenet, (x, y))
            x += i.width()*GRID

class VerticalGroup(UnorderedGroup):

    def width(self):
        width = 0
        for i in self:
            width = max(width, i.width())
        return width

    def height(self):
        height = 0
        for i in self:
            height += i.height()
        return height

    def arrange(self, nodenet, start_position = (0,0)):
        x, y = start_position
        for i in self:
            i.arrange(nodenet, (x, y))
            y += i.height()*GRID
