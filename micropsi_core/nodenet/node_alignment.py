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

    unaligned_nodespaces = sorted(nodenet.nodespaces[nodespace].netentities["nodespaces"], key=lambda i:nodenet.nodespaces[i].index)
    unaligned_nodes = sorted(nodenet.nodespaces[nodespace].netentities["nodes"], key = lambda i: nodenet.nodes[i].index)

    BORDER = 50
    GRID = 150
    PREFERRED_WIDTH = 8

    # position nodespaces

    for i, id in enumerate(unaligned_nodespaces):
        nodenet.nodespaces[id].position = (
            BORDER + (i%PREFERRED_WIDTH+1)*GRID - GRID/2,
            BORDER + int(i/PREFERRED_WIDTH+1)*GRID - GRID/2,
            )

    start_position = (BORDER + GRID/2, BORDER + (1.5+int(len(nodenet.nodespaces)/PREFERRED_WIDTH))*GRID)

    # simplify linkage
    print "starting alignment"
    structure = unify_links(nodenet, unaligned_nodes)
    print "nodes unified"
    horizontal_groups = group_horizontal_links(structure)
    print "horizontal grouping done"
    print horizontal_groups

    # arrange nodes in a grid
        # arrange node tree



    print "ok"
    return True

def unify_links(nodenet, nodes):
    """create a proxy representation of the node space to simplify bi-directional links."""

    structure = OrderedDict([(i, {}) for i in nodes])
    for node_id in nodes:
        node = nodenet.nodes[node_id]
        for gate_type in node.gates:
            direction = {"sub": "s", "ret": "e", "cat": "sw", "sym":"se"}.get(gate_type)
            if direction:
                # inverse link, will be represented as inverted forward link
                links = node.gates[gate_type].outgoing
                for link in links:
                    target_node_id = nodenet.links[link].target_node.uid
                    if target_node_id in structure:
                        if not direction in structure[target_node_id]: structure[target_node_id][direction]=[]
                        if not node_id in structure[target_node_id][direction]:
                            structure[target_node_id][direction].append(node_id)
            else:
                direction = {"sur": "n", "por": "e", "exp": "sw", "ref":"se", "gen": "b"}.get(gate_type, "o")
                if direction:
                    # forward link, "o" is for unknown gate types
                    links = node.gates[gate_type].outgoing
                    for link in links:
                        target_node_id = nodenet.links[link].target_node.uid
                        if target_node_id in structure:
                            if not direction in structure[node_id]: structure[node_id][direction]=[]
                            structure[node_id][direction].append(target_node_id)
    # finally, let us sort all nodes in the direction groups
    for node_id in structure:
        for direction in structure[node_id]:
            structure[node_id][direction].sort(key = lambda i: nodenet.nodes[i].index)

    return structure

def group_horizontal_links(structure):
    """group direct horizontal links (por)"""
    h_groups = []
    ungrouped_nodes = structure.keys()
    while ungrouped_nodes:
        current_node_id = ungrouped_nodes[0]
        h_groups.append(add_nodes_horizontally(current_node_id, structure, ungrouped_nodes))
    return h_groups

def add_nodes_horizontally(current_node_id, structure, ungrouped_nodes):
    """recursive helper function for adding horizontally linked nodes to a group"""
    current_node = structure[current_node_id]
    del ungrouped_nodes[current_node_id]
    current_group = {"groups": [current_node_id], "n":current_node.get("n", [None])[0], "type": "h"}
    subgroup = {"groups":[], "type": "v"}
    for node in current_node("e"):  # handle branching horizontal links with vertical sub-groups
        subgroup["groups"].append(add_nodes_horizontally(node, structure, ungrouped_nodes))
    # inherit parenthood if no parent is known
    current_group["n"] = current_group["n"] or subgroup["n"]
    if len(subgroup["groups"]) == 1:
        # only one element in sub-group means that there are no branches and we can extract the element directly
        current_group["groups"].append(subgroup["groups"][0])
    else:
        current_group["groups"].append(subgroup)
    return current_group


