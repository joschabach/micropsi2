import pytest
from micropsi_core import runtime


def test_user_operation(test_nodenet, resourcepath):
    import os
    os.makedirs(os.path.join(resourcepath, 'operations', 'foobar'))
    with open(os.path.join(resourcepath, 'operations', 'foobar', 'somoperation.py'), 'w+') as fp:
        fp.write("""
def delete_nodes(netapi, selection):
    for uid in selection:
        netapi.delete_node(netapi.get_node(uid))

delete_nodes.selectioninfo = {
    'nodetypes': [],
    'mincount': 1,
    'maxcount': -1
}""")
    runtime.reload_code()
    ops = runtime.get_available_operations()
    assert ops['delete_nodes']['category'] == 'foobar'
    res, uid = runtime.add_node(test_nodenet, "Neuron", [10, 10], None)
    runtime.run_operation(test_nodenet, "delete_nodes", {}, [uid])
    assert uid not in runtime.nodenets[test_nodenet].get_node_uids()


def test_autoalign_operation(test_nodenet):
    ops = runtime.get_available_operations()
    for selectioninfo in ops['autoalign']['selection']:
        if selectioninfo['nodetypes'] == ['Nodespace']:
            assert selectioninfo['mincount'] == 1
            assert selectioninfo['maxcount'] == -1
        else:
            assert selectioninfo['mincount'] == 2
            assert selectioninfo['maxcount'] == -1
            assert selectioninfo['nodetypes'] == []
    assert ops['autoalign']['category'] == 'layout'
    assert ops['autoalign']['parameters'] == []

    api = runtime.nodenets[test_nodenet].netapi
    ns1 = api.create_nodespace(None, "foo")
    p1 = api.create_node("Pipe", None, "p1")
    p2 = api.create_node("Pipe", None, "p2")
    p3 = api.create_node("Pipe", None, "p3")
    api.link_with_reciprocal(p1, p2, 'subsur')
    api.link_with_reciprocal(p1, p3, 'subsur')
    api.link_with_reciprocal(p2, p3, 'porret')
    runtime.save_nodenet(test_nodenet)
    runtime.run_operation(test_nodenet, "autoalign", {}, [p1.uid, p2.uid, p3.uid, ns1])
    assert p1.position[0] == p2.position[0]
    assert p1.position[1] < p2.position[1]
    assert p2.position[1] == p3.position[1]
    runtime.revert_nodenet(test_nodenet)
    runtime.run_operation(test_nodenet, "autoalign", {}, [api.get_nodespace(None).uid])
    assert p1.position[0] == p2.position[0]
    assert p1.position[1] < p2.position[1]
    assert p2.position[1] == p3.position[1]
    result, data = runtime.run_operation(test_nodenet, "autoalign", {}, [p1.uid])
    assert 'error' in data
