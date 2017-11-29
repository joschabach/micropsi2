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
GRID = 170.0
PREFERRED_WIDTH = 8.0
FLOWGRID = 270.0


def align(nodenet, nodespace, entity_uids=False):
    """aligns the entities in the given nodenet.
        Arguments:
            nodenet: current node net
            nodespace: the nodespace in which the entities are to be aligned
            entity_uids: optional list of entity uids that should be aligned. If set, other entities remain untouched
        Returns:
            True on success, False otherwise
    """
    nodespace = nodenet.get_nodespace(nodespace).uid

    # treat flowmodules seperately
    flownodes = []
    if hasattr(nodenet, "flow_module_instances"):
        flownodes = nodenet.flow_module_instances.keys()

    unaligned_nodespaces = sorted(nodenet.get_nodespace(nodespace).get_known_ids('nodespaces'),
        key=lambda i: nodenet.get_nodespace(i).index)
    unaligned_nodes = [x for x in sorted(nodenet.get_nodespace(nodespace).get_known_ids('nodes'),
        key=lambda i: nodenet.get_node(i).index) if x not in flownodes]

    if entity_uids:
        unaligned_nodespaces = [id for id in unaligned_nodespaces if id in entity_uids]
        unaligned_nodes = [id for id in unaligned_nodes if id in entity_uids]
        sensors = []
        actuators = []
        activators = []
        if unaligned_nodes or unaligned_nodespaces:
            ymin = min(nodenet.get_node(n).position[1] for n in unaligned_nodes + unaligned_nodespaces)
            xmin = min(nodenet.get_node(n).position[0] for n in unaligned_nodes + unaligned_nodespaces)
            start_position = (xmin, ymin, 0)
        else:
            start_position = (BORDER + GRID / 2, BORDER, 0)

    else:
        sensors = [s for s in unaligned_nodes if nodenet.get_node(s).type == "Sensor"]
        actuators = [a for a in unaligned_nodes if nodenet.get_node(a).type == "Actuator"]
        activators = [a for a in unaligned_nodes if nodenet.get_node(a).type == "Activator"]
        unaligned_nodes = [n for n in unaligned_nodes if not nodenet.get_node(n).type in ("Sensor", "Actuator", "Activator")]

        start_position = (BORDER + GRID / 2, BORDER + (0.5 + math.ceil(len(unaligned_nodespaces) / PREFERRED_WIDTH)) * GRID, 0)

    # position nodespaces

    for i, id in enumerate(unaligned_nodespaces):
        nodenet.get_nodespace(id).position = calculate_grid_position(i)

    # simplify linkage
    group = unify_links(nodenet, unaligned_nodes)
    # connect all nodes that have por- and ret-links
    por_groups = group_horizontal_links(group)
    # connect native modules
    # group_other_links(por_groups)
    # group nodes that share a sur-linked parent below that parent
    group_with_same_parent(por_groups)
    # put sensors and actuators below
    sensor_group = HorizontalGroup([DisplayNode(i) for i in sensors] + [DisplayNode(i) for i in actuators])
    actviator_group = HorizontalGroup([DisplayNode(i) for i in activators])
    por_groups.append(sensor_group)
    por_groups.append(actviator_group)

    if len(flownodes):
        flow_groups = align_flow_nodes(nodenet, entity_uids)
        for g in flow_groups:
            por_groups.append(g)

    # calculate actual coordinates by traversing the group structure
    por_groups.arrange(nodenet, start_position)

    return True


INVERSE_DIRECTIONS = {"s": "n", "w": "e", "nw": "se", "ne": "sw",
                      "n": "s", "e": "w", "se": "nw", "sw": "ne",
                      "o": "O", "O": "o", "b": "a", "a": "b"}


class DisplayNode(object):
    def __init__(self, uid, directions=None, parent=None):
        self.uid = uid
        self.directions = directions or {}
        self.parent = parent
        self.stackable = False

    def __repr__(self):
        params = "%s" % str(self.uid)
        if self.directions:
            params += ", dirs: "
            for i in self.directions:
                params += "[%s]: " % i
                for j in self.directions[i]:
                    params += "%s, " % str(j.uid)
        return '%s(%s)' % ("Node", params)

    def __repr__2(self):
        params = "'%s'" % self.uid
        if self.directions:
            params += ", directions=%r" % self.directions
        if self.parent:
            params += ", parent=%r" % self.parent
        return '%s(%s)' % (self.__class__.__name__, params)

    def width(self):
        return 1

    def height(self):
        return 1

    def arrange(self, nodenet, starting_point=[0, 0, 0]):
        if self.uid is not None:
            nodenet.get_node(self.uid).position = starting_point


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
        node = nodenet.get_node(node_id)
        vertical_only = True
        for gate_type in node.get_gate_types():
            direction = {"sub": "s", "ret": "w", "cat": "ne", "sym": "nw",
                         "sur": "n", "por": "e", "exp": "sw", "ref": "se", "gen": "n"}.get(gate_type, "o")
            if direction:
                # "o" is for unknown gate types
                for link in node.get_gate(gate_type).get_links():
                    target_node_id = link.target_node.uid
                    if target_node_id in node_index:
                        # otherwise, the link points outside the current nodespace and will be ignored here
                        if direction not in node_index[node_id].directions:
                            node_index[node_id].directions[direction] = OrderedSet()
                        node_index[node_id].directions[direction].add(node_index[target_node_id])
                        inverse = INVERSE_DIRECTIONS[direction]
                        if inverse not in node_index[target_node_id].directions:
                            node_index[target_node_id].directions[inverse] = OrderedSet()
                        node_index[target_node_id].directions[inverse].add(node_index[node_id])
            if direction != 'n' and direction != 's':
                vertical_only = False
        node_index[node_id].stackable = vertical_only

    # finally, let us sort all node_id_list in the direction groups
    for node_id in node_index:
        for direction in node_index[node_id].directions:
            node_index[node_id].directions[direction] = list(node_index[node_id].directions[direction])
            node_index[node_id].directions[direction].sort(key=lambda i: nodenet.get_node(i.uid).index)

    return UnorderedGroup(node_index.values())


def group_horizontal_links(all_nodes):
    """group direct horizontal links (por)"""
    h_groups = UnorderedGroup()
    excluded_nodes = OrderedSet()
    for i in all_nodes:
        if not i.directions.get("w"):  # find leftmost nodes
            excluded_nodes.add(i)
            if i.directions.get("e"):
                h_group = HorizontalGroup([i])
                _add_nodes_horizontally(i, h_group, excluded_nodes)
                if len(h_group) > 1:
                    h_groups.append(h_group)
                else:
                    h_groups.append(i)
            else:
                h_groups.append(i)
        # now handle circles (we find them by identifying left-over nodes that still have "e" links)
    for i in all_nodes:
        if i not in excluded_nodes:
            excluded_nodes.add(i)
            if i.directions.get("e"):
                h_group = HorizontalGroup([i])
                _add_nodes_horizontally(i, h_group, excluded_nodes)
                if len(h_group) > 1:
                    h_groups.append(h_group)
                else:
                    h_groups.append(i)
            else:
                h_groups.append(i)
    _fix_link_inheritance(h_groups, OrderedSet())
    return h_groups


def _add_nodes_horizontally(display_node, h_group, excluded_nodes):
    """recursive helper function for adding horizontally linked nodes to a group"""

    while True:
        successor_nodes = [node for node in display_node.directions.get("e", []) if node not in excluded_nodes]

        if len(successor_nodes) == 1:
            display_node = successor_nodes[0]
            excluded_nodes.add(display_node)
            h_group.append(display_node)
            if not display_node.directions.get("e"):
                break
        else:
            break


def group_other_links(all_groups):
    """group other horizontal links (native modules)"""
    excluded_nodes = OrderedSet()
    _group_other_links(all_groups, excluded_nodes, "O")
    _group_other_links(all_groups, excluded_nodes, "o")
    _fix_link_inheritance(all_groups, OrderedSet())
    return all_groups


def _group_other_links(groups, excluded_nodes, direction):
    for i in groups:
        if i.directions.get(direction):  # inverse non-standard links
            predecessors = []
            for node in i.directions[direction]:
                if node not in excluded_nodes and not node.directions.get("w") and not node.directions.get("e"):
                    # this node is not part of another group at this point
                    excluded_nodes.add(node)
                    predecessors.append(node.parent)
            if len(predecessors) == 1:
                i.insert(0, predecessors[0])
            if len(predecessors) > 1:
                i.insert(0, VerticalGroup(predecessors[0]))


def group_with_same_parent(all_groups):
    """group horizontal groups that share the same super-node"""
    # find groups with same super-node
    candidates = OrderedDict()
    for g in all_groups:
        if "n" in g.directions:
            super_node = list(g.directions["n"])[0]  # there can be multiple super-nodes, but we only take the 1st
            if super_node not in candidates:
                candidates[super_node] = []
            candidates[super_node].append(g)
    # build vertical groups
    for super_node in candidates:
        h_group = HorizontalGroup()
        for g in candidates[super_node]:
            all_groups.remove(g)
            if isinstance(g, HorizontalGroup):
                for e in g:
                    h_group.append(e)
            else:
                h_group.append(g)

        parent_group = super_node.parent
        v_group = VerticalGroup([super_node, h_group])
        parent_group[parent_group.index(super_node)] = v_group
        for clist in candidates.values():
            if super_node in clist:
                clist[clist.index(super_node)] = v_group

    # _fix_link_inheritance(all_groups, OrderedSet())
    return all_groups


def _fix_link_inheritance(group, excluded_nodes):
    """recursive helper function to mark for a group and every sub-group into which directions it is linked.
    The function adds the links as .directions to the group and its sub-groups, and carries a set of
    excluded_nodes to remember which links should not be inherited upwards"""

    from copy import deepcopy
    if hasattr(group, "uid"):
        excluded_nodes.add(group)
    else:
        for i in group:
            locally_excluded_nodes = OrderedSet()
            _fix_link_inheritance(i, locally_excluded_nodes)
            for d in i.directions:
                if d not in group.directions:
                    group.directions[d] = OrderedSet()
                for node in i.directions[d]:
                    group.directions[d].add(node)
            for i in locally_excluded_nodes:
                excluded_nodes.add(i)
        # now delete all links to excluded nodes
        dirs_copy = group.directions.copy()
        for d in dirs_copy:
            for node in deepcopy(dirs_copy[d]):
                if node in excluded_nodes:
                    group.directions[d].remove(node)
            if not group.directions[d]:
                del group.directions[d]


def align_flow_nodes(nodenet, entity_uids):
    toposort = nodenet.flow_toposort
    startnode = None
    i = 0
    while True:
        n = nodenet.get_node(toposort[i])
        if n.inputmap == {}:
            startnode = n
            break
        i += 1
    if startnode is not None:
        hopmap = OrderedDict()
        hopmap[startnode.uid] = 0
        for uid in toposort:
            if uid not in hopmap:
                node = nodenet.get_node(uid)
                hop = 0
                for key in node.inputmap:
                    if node.inputmap[key]:
                        source_uid = node.inputmap[key][0]
                        hop = max(hopmap[source_uid] + 1, hop)
                hopmap[uid] = hop
        buckets = {}
        highest = 1
        farthest = 1
        for uid in hopmap:
            if not entity_uids or uid in entity_uids:
                hops = hopmap[uid]
                if hops not in buckets:
                    buckets[hops] = []
                buckets[hops].append(uid)
                highest = max(len(buckets[hops]), highest)
                farthest = max(hops, farthest)
        flow_groups = [[]] * highest
        nodes = hopmap
        for i in range(highest):
            flow_groups[i] = HorizontalGroup([DisplayNode(None)] * (farthest + 1), hspace=FLOWGRID)
            for j, nodes in buckets.items():
                if len(nodes) == highest - i:
                    flow_groups[i][j] = DisplayNode(buckets[j].pop())
        return flow_groups
    else:
        return [HorizontalGroup([DisplayNode(i) for i in toposort], hspace=FLOWGRID)]


class UnorderedGroup(list):

    @property
    def stackable(self):
        for i in self:
            if not i.stackable:
                return False
        return True

    def __init__(self, elements=None, parent=None, hspace=GRID, vspace=GRID):
        self.directions = {}
        self.parent = parent
        self.hspace = hspace
        self.vspace = vspace
        if elements:
            list.__init__(self, elements)
            for i in elements:
                i.parent = self

    def __repr__(self):
        sig = "Group"
        if self.__class__.__name__ == "HorizontalGroup":
            sig = "HGroup"
        if self.__class__.__name__ == "VerticalGroup":
            sig = "VGroup"

        params = ""
        if self.directions:
            params += "dirs: "
            for i in self.directions:
                params += "[%s]: " % i
                for j in self.directions[i]:
                    params += "%s, " % str(j.uid)

        if len(self):
            params += "%r, " % list(self)
        return '%s(%s)' % (sig, params)

    def __repr2__(self):
        params = ""
        if len(self):
            params += "%r" % list(self)
        # if self.parent:
        #    params += ", parent=%r" % self.parent
        if self.directions:
            params += ", directions=%r" % self.directions
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

    def append(self, element):
        element.parent = self
        list.append(self, element)

    def arrange(self, nodenet, start_position=[0, 0, 0]):
        # arrange elements of unordered group below each other
        x, y, z = start_position
        for i in self:
            i.arrange(nodenet, [x, y, z])
            y += i.height() * self.vspace


class HorizontalGroup(UnorderedGroup):

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

    def arrange(self, nodenet, start_position=[0, 0, 0]):
        x, y, z = start_position
        for i in self:
            i.arrange(nodenet, [x, y, z])
            xshift = 1 if self.stackable else i.width()
            x += xshift * self.hspace


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

    def arrange(self, nodenet, start_position=[0, 0, 0]):
        x, y, z = start_position
        for i in self:
            i.arrange(nodenet, [x, y, z])
            y += i.height() * self.vspace


def calculate_grid_position(index, start_position=[0, 0, 0]):
    """Determines the position of an item in a simple grid, based on default values defined here"""
    return (
        BORDER + (index % PREFERRED_WIDTH + 1) * GRID - GRID / 2,
        BORDER + int(index / PREFERRED_WIDTH + 1) * GRID - GRID / 2,
    )
