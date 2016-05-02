
from micropsi_core.nodenet.operations import selectioninfo


@selectioninfo(mincount=2)
def add_activation_recorder(netapi, selection, gate='gen', interval=1, name='activation_recoder'):
    """Adds an activation recorder to the selected nodes"""
    firstnode = netapi.get_node(selection[0])
    nodespace = netapi.get_nodespace(firstnode.parent_nodespace)
    group_config = {
        'nodespace_uid': nodespace.uid,
        'node_uids': selection,
        'gatetype': gate}
    netapi.add_activation_recorder(group_config, name=name, interval=int(interval))


@selectioninfo(mincount=2)
def add_linkweight_recorder(netapi, selection, direction='down', from_gate='gen', to_slot='gen', interval=1, name='linkweight_recoder'):
    """ Attempts to detect two layers of nodes (y-coordinate) and adds a linkweight-monitor"""
    nodes = [netapi.get_node(uid) for uid in selection]
    nodespace = netapi.get_nodespace(nodes[0].parent_nodespace)
    groups = {}
    for n in nodes:
        if n.position[1] in groups:
            groups[n.position[1]].append(n)
        else:
            groups[n.position[1]] = [n]
    if len(groups.keys()) != 2:
        raise RuntimeError("Could not determine 2 node-layers")

    grouplist = list(groups.values())
    if direction == 'up':
        grouplist.reverse()

    from_group_config = {
        'nodespace_uid': nodespace.uid,
        'node_uids': [n.uid for n in grouplist[0]],
        'gatetype': from_gate}
    to_group_config = {
        'nodespace_uid': nodespace.uid,
        'node_uids': [n.uid for n in grouplist[1]],
        'gatetype': to_slot}
    netapi.add_linkweight_recorder(from_group_config, to_group_config, name=name, interval=int(interval))
