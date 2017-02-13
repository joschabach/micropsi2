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


@pytest.mark.engine("theano_engine")
def test_add_gate_activation_recorder_operation(test_nodenet):
    nodenet = runtime.nodenets[test_nodenet]
    netapi = nodenet.netapi
    nodes = []
    for i in range(3):
        nodes.append(netapi.create_node("Neuron", None, "node%d" % i))
    res, data = runtime.run_operation(test_nodenet, 'add_gate_activation_recorder', {
        'gate': 'gen',
        'interval': 1,
        'name': 'gate_activation_recorder',
    }, [n.uid for n in nodes])
    runtime.step_nodenet(test_nodenet)
    runtime.get_recorder(test_nodenet, data['uid']).values['activations'].shape == (3)


@pytest.mark.engine("theano_engine")
def test_add_node_activation_recorder_operation(test_nodenet):
    nodenet = runtime.nodenets[test_nodenet]
    netapi = nodenet.netapi
    nodes = []
    for i in range(3):
        nodes.append(netapi.create_node("Pipe", None, "node%d" % i))
    res, data = runtime.run_operation(test_nodenet, 'add_node_activation_recorder', {
        'interval': 1,
        'name': 'node_activation_recorder',
    }, [n.uid for n in nodes])
    runtime.step_nodenet(test_nodenet)
    runtime.get_recorder(test_nodenet, data['uid']).values['activations'].shape == (7, 3)


@pytest.mark.engine("theano_engine")
def test_add_linkweight_recorder_operation(test_nodenet):
    nodenet = runtime.nodenets[test_nodenet]
    netapi = nodenet.netapi
    nodes1 = []
    nodes2 = []
    for i in range(3):
        n1 = netapi.create_node("Neuron", None, "node1%d" % i)
        n2 = netapi.create_node("Neuron", None, "node2%d" % i)
        n1.position = [i * 20, 20]
        n2.position = [i * 20, 40]
        nodes1.append(n1)
        nodes2.append(n2)
    for i in range(3):
        for j in range(3):
            netapi.link(nodes1[i], 'gen', nodes2[j], 'gen')

    res, data = runtime.run_operation(test_nodenet, 'add_linkweight_recorder', {
        'direction': 'down',
        'from_gate': 'gen',
        'to_slot': 'gen',
        'interval': 1,
        'name': 'linkweight_recorder'
    }, [n.uid for n in nodes1] + [n.uid for n in nodes2])
    runtime.step_nodenet(test_nodenet)
    runtime.get_recorder(test_nodenet, data['uid']).values['linkweights'].shape == (3, 3)
