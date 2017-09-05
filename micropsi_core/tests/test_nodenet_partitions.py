
import pytest


def prepare(netapi, partition_options={}):
    partition_options.update({'new_partition': True})
    nodespace = netapi.create_nodespace(None, name="partition", options=partition_options)
    source = netapi.create_node('Neuron', None, "Source")
    register = netapi.create_node('Neuron', nodespace.uid, "Neuron")
    netapi.link(source, 'gen', register, 'gen')
    netapi.link(source, 'gen', source, 'gen')
    source.activation = 1
    return nodespace, source, register


@pytest.mark.engine("theano_engine")
def test_partition_creation(runtime, test_nodenet):
    nodenet = runtime.get_nodenet(test_nodenet)
    netapi = nodenet.netapi
    netapi.create_nodespace(None, name="partition", options={'new_partition': True})
    assert len(nodenet.partitions.keys()) == 2


@pytest.mark.engine("theano_engine")
def test_cross_partition_links(runtime, test_nodenet):
    nodenet = runtime.get_nodenet(test_nodenet)
    netapi = nodenet.netapi
    nodespace, source, register = prepare(netapi)
    nodenet.step()
    assert register.activation == 1
    # change link weight
    netapi.link(source, 'gen', register, 'gen', weight=0.7)

    assert register.uid in netapi.get_node(source.uid).get_associated_node_uids()
    assert source.uid in netapi.get_node(register.uid).get_associated_node_uids()

    link = register.get_slot('gen').get_links()[0]
    assert round(link.weight, 3) == 0.7
    nodenet.step()
    assert round(register.activation, 3) == 0.7
    netapi.unlink(source, 'gen', register, 'gen')
    assert len(source.get_gate('gen').get_links()) == 1
    assert netapi.get_node(register.uid).get_gate('gen').empty
    assert netapi.get_node(register.uid).get_slot('gen').empty
    nodenet.step()
    assert register.activation == 0


@pytest.mark.engine("theano_engine")
def test_partition_persistence(runtime, test_nodenet):
    nodenet = runtime.get_nodenet(test_nodenet)
    netapi = nodenet.netapi
    nodespace, source, register = prepare(netapi)
    runtime.save_nodenet(test_nodenet)
    runtime.revert_nodenet(test_nodenet)
    nodenet.step()
    assert register.activation == 1


@pytest.mark.engine("theano_engine")
def test_delete_node_deletes_inlinks(runtime, test_nodenet):
    nodenet = runtime.get_nodenet(test_nodenet)
    netapi = nodenet.netapi
    nodespace, source, register = prepare(netapi)
    target = netapi.create_node("Neuron", None, "target")
    netapi.link(register, 'gen', target, 'gen')
    netapi.delete_node(register)
    links = netapi.get_node(source.uid).get_gate('gen').get_links()
    assert len(links) == 1
    assert links[0].target_node.uid == source.uid
    assert target.get_slot('gen').empty
    assert nodespace.partition.inlinks == {}
    assert len(nodenet.rootpartition.inlinks[nodespace.partition.spid][1].get_value()) == 0


@pytest.mark.engine("theano_engine")
def test_delete_node_modifies_inlinks(runtime, test_nodenet):
    nodenet = runtime.get_nodenet(test_nodenet)
    netapi = nodenet.netapi
    nodespace, source, register = prepare(netapi)
    target = netapi.create_node("Neuron", None, "target")

    register2 = netapi.create_node("Neuron", nodespace.uid, "reg2")
    netapi.link(register, 'gen', target, 'gen')
    netapi.link(register2, 'gen', target, 'gen')
    netapi.link(source, 'gen', register2, 'gen')

    netapi.delete_node(register)
    assert len(source.get_gate('gen').get_links()) == 2
    assert len(target.get_slot('gen').get_links()) == 1

    assert list(nodespace.partition.inlinks.keys()) == [nodenet.rootpartition.spid]
    assert list(nodenet.rootpartition.inlinks.keys()) == [nodespace.partition.spid]
    assert len(nodespace.partition.inlinks[nodenet.rootpartition.spid][1].get_value()) == 1
    assert len(nodenet.rootpartition.inlinks[nodespace.partition.spid][1].get_value()) == 1


@pytest.mark.engine("theano_engine")
def test_grow_partitions(runtime, test_nodenet):
    nodenet = runtime.get_nodenet(test_nodenet)
    netapi = nodenet.netapi
    nodespace = netapi.create_nodespace(None, name="partition", options={
        "new_partition": True,
        "initial_number_of_nodes": 2,
        "average_elements_per_node_assumption": 4,
        "initial_number_of_nodespaces": 1
    })

    for i in range(20):
        netapi.create_node("Pipe", nodespace.uid, "N %d" % i)

    partition = nodespace.partition

    # growby (NoN // 2): 2,3,4,6,9,13,19,28
    assert len(partition.allocated_nodes) == 28
    assert partition.NoE > 28 * 4

    for i in range(2):
        netapi.create_nodespace(nodespace.uid, name="NS %d" % i)

    assert len(partition.allocated_nodespaces) == 4

    # step, save, and load the net to make sure all data structures have been grown properly
    runtime.step_nodenet(test_nodenet)
    runtime.save_nodenet(test_nodenet)
    runtime.revert_nodenet(test_nodenet)
    runtime.step_nodenet(test_nodenet)


@pytest.mark.engine("theano_engine")
def test_announce_nodes(runtime, test_nodenet):
    nodenet = runtime.get_nodenet(test_nodenet)
    netapi = nodenet.netapi
    nodespace = netapi.create_nodespace(None, name="partition", options={
        "new_partition": True,
        "initial_number_of_nodes": 2,
        "average_elements_per_node_assumption": 4,
        "initial_number_of_nodespaces": 1
    })

    # announce 20 pipe nodes
    netapi.announce_nodes(nodespace.uid, 20, 8)

    partition = nodespace.partition

    # 18 nodes needed
    assert partition.NoN == 26  # growby: 18 + 18//3
    # 152 elements needed
    assert partition.NoE == 210  # growby: 152 + 152//3

    for i in range(20):
        netapi.create_node("Pipe", nodespace.uid, "N %d" % i)

    # assert that we did not grow again
    assert partition.NoN == 26
    assert partition.NoE == 210


@pytest.mark.engine("theano_engine")
def test_delete_partition(runtime, test_nodenet):
    nodenet = runtime.get_nodenet(test_nodenet)
    netapi = nodenet.netapi
    nodespace, source, register = prepare(netapi)
    netapi.delete_nodespace(nodespace)
    links = source.get_gate('gen').get_links()
    assert len(links) == 1
    assert links[0].target_node == source


@pytest.mark.engine("theano_engine")
def test_delete_partition_unlinks_native_module(runtime, test_nodenet, resourcepath):
    nodenet = runtime.get_nodenet(test_nodenet)
    netapi = nodenet.netapi
    nodespace, source, register = prepare(netapi)
    import os
    with open(os.path.join(resourcepath, 'nodetypes', 'Test', 'Testnode.py'), 'w') as fp:
        fp.write("""nodetype_definition = {
    "name": "Testnode",
    "slottypes": ["gen", "foo", "bar"],
    "nodefunction_name": "testnodefunc",
    "gatetypes": ["gen", "foo", "bar"]}

def testnodefunc(netapi, node=None, **prams):\r\n    return 17
""")
    runtime.reload_code()
    testnode = netapi.create_node("Testnode", None, "test")
    netapi.link(testnode, 'foo', register, 'gen')
    netapi.link(register, 'gen', testnode, 'bar')
    netapi.delete_nodespace(nodespace)
    data = testnode.get_data(include_links=True)
    assert data['links'] == {}


@pytest.mark.engine("theano_engine")
def test_delete_nodespace_unlinks_native_module(runtime, test_nodenet, resourcepath):
    nodenet = runtime.get_nodenet(test_nodenet)
    netapi = nodenet.netapi
    nodespace = netapi.create_nodespace(None, "foo")
    foopipe = netapi.create_node("Pipe", nodespace.uid, 'foopipe')
    import os
    with open(os.path.join(resourcepath, 'nodetypes', 'Test', 'foo.py'), 'w') as fp:
        fp.write("""nodetype_definition = {
    "name": "Testnode",
    "slottypes": ["gen", "foo", "bar"],
    "nodefunction_name": "testnodefunc",
    "gatetypes": ["gen", "foo", "bar"]
}
def testnodefunc(netapi, node=None, **prams):\r\n    return 17
""")
    runtime.reload_code()
    testnode = netapi.create_node("Testnode", None, "test")
    netapi.link(testnode, 'foo', foopipe, 'sub')
    netapi.link(foopipe, 'sur', testnode, 'bar')
    runtime.save_nodenet(test_nodenet)
    # I don't understand why, but this is necessary.
    runtime.revert_nodenet(test_nodenet)
    netapi.delete_nodespace(nodespace)
    data = netapi.get_node(testnode.uid).get_data(include_links=True)
    assert data['links'] == {}


@pytest.mark.engine("theano_engine")
def test_delete_subnodespace_removes_x_partition_links(runtime, test_nodenet):
    nodenet = runtime.get_nodenet(test_nodenet)
    netapi = nodenet.netapi
    nodespace = netapi.create_nodespace(None, "partition", options={'new_partition': True})
    subnodespace = netapi.create_nodespace(nodespace.uid, "foo")
    r1 = netapi.create_node("Neuron", None)
    r2 = netapi.create_node("Neuron", subnodespace.uid)
    r3 = netapi.create_node("Neuron", None)
    netapi.link(r1, 'gen', r2, 'gen')
    netapi.link(r2, 'gen', r3, 'gen')
    netapi.delete_nodespace(subnodespace)
    data = netapi.get_node(r1.uid).get_data({'include_links': True})
    assert data['links'] == {}
    for key in nodenet.rootpartition.inlinks:
        for i in range(3):
            assert len(nodenet.rootpartition.inlinks[key][i].get_value()) == 0


@pytest.mark.engine("theano_engine")
def test_sensor_actuator_indices(runtime, test_nodenet):
    nodenet = runtime.get_nodenet(test_nodenet)
    netapi = nodenet.netapi
    result, world_uid = runtime.new_world('default', 'DefaultWorld')
    runtime.set_nodenet_properties(test_nodenet, worldadapter='Default', world_uid=world_uid)
    sensor = netapi.create_node("Sensor", None, "static_sensor")
    sensor.set_parameter("datasource", "static_on")
    actuator = netapi.create_node("Actuator", None, "echo_actuator")
    actuator.set_parameter("datatarget", "echo")
    register = netapi.create_node("Neuron", None, "source")
    register.activation = 0.8
    netapi.link(register, 'gen', register, 'gen', weight=0.5)
    netapi.link(register, 'gen', actuator, 'gen')
    assert sensor.activation == 0
    assert actuator.get_gate('gen').activation == 0
    runtime.step_nodenet(test_nodenet)
    runtime.step_nodenet(test_nodenet)
    assert sensor.activation == 1
    assert round(actuator.get_gate('gen').activation, 3) == 0.8
    netapi.delete_node(sensor)
    netapi.delete_node(actuator)
    assert set(nodenet.rootpartition.actuator_indices) == {-1}
    assert set(nodenet.rootpartition.sensor_indices) == {-1}


@pytest.mark.engine("theano_engine")
def test_partition_get_node_data(runtime, test_nodenet):
    nodenet = runtime.get_nodenet(test_nodenet)
    netapi = nodenet.netapi
    nodespace, source, register = prepare(netapi)
    root_ns = netapi.get_nodespace(None).uid

    nodes = []
    # 10 nodes, first five in root, other five in new nodespace
    for i in range(10):
        n = netapi.create_node("Pipe", nodespace.uid if i > 4 else None, "node %d" % i)
        nodes.append(n)

    # 4 links from root to new nodespace
    for i in range(4):
        netapi.link(nodes[i], 'gen', nodes[5], 'gen', weight=((i + 2) / 10))

    # 1 link back
    netapi.link(nodes[9], 'gen', nodes[4], 'gen', 0.375)

    # 3rd nodespace, with a node linked from root
    third_ns = netapi.create_nodespace(None, "third")
    third = netapi.create_node("Neuron", third_ns.uid, "third")
    netapi.link(nodes[4], 'gen', third, 'gen')

    n1, n3, n4, n5, n9 = nodes[1], nodes[3], nodes[4], nodes[5], nodes[9]

    # assert outlinks/inlinks in get_node
    _, data = runtime.get_node(test_nodenet, n1.uid)
    assert data['outlinks'] == 1
    assert data['inlinks'] == 0
    _, data = runtime.get_node(test_nodenet, n4.uid)
    assert data['outlinks'] == 1
    assert data['inlinks'] == 1

    node_data = nodenet.get_nodes(nodespace_uids=[None])['nodes']
    assert set(node_data.keys()) == set([n.uid for n in nodes[:5]] + [source.uid])
    assert node_data[n1.uid]['outlinks'] == 1
    assert node_data[n4.uid]['outlinks'] == 1
    assert node_data[n4.uid]['links'] == {}

    node_data = nodenet.get_nodes()['nodes']
    assert round(node_data[n1.uid]['links']['gen'][0]['weight'], 3) == 0.3
    assert round(node_data[n3.uid]['links']['gen'][0]['weight'], 3) == 0.5
    assert round(node_data[n9.uid]['links']['gen'][0]['weight'], 3) == 0.375

    node_data = nodenet.get_nodes(nodespace_uids=[nodespace.uid])['nodes']
    assert len(node_data.keys()) == 6
    assert third.uid not in node_data
    assert node_data[n5.uid]['inlinks'] == 4
    assert node_data[n5.uid]['links'] == {}
    assert node_data[n9.uid]['outlinks'] == 1
    assert node_data[n9.uid]['links'] == {}

    data = nodenet.get_nodes(nodespace_uids=[nodespace.uid], links_to_nodespaces=[root_ns])
    assert 'links' in data
    source_uids = [l['source_node_uid'] for l in data['links']]
    # source->register + our 4 links:
    assert set(source_uids) == set(['n0001', 'n0002', 'n0003', 'n0004', 'n0005'])
    assert data['nodes'][n9.uid]['links']['gen'][0]['target_node_uid'] == n4.uid


@pytest.mark.engine("theano_engine")
def test_get_links_for_nodes_partitions(runtime, test_nodenet):

    def linkid(linkdict):
        return "%s:%s:%s:%s" % (linkdict['source_node_uid'], linkdict['source_gate_name'], linkdict['target_slot_name'], linkdict['target_node_uid'])

    nodenet = runtime.get_nodenet(test_nodenet)
    netapi = nodenet.netapi
    nodespace, source, register = prepare(netapi)

    root_ns = netapi.get_nodespace(None).uid
    p0 = netapi.create_node("Pipe", root_ns, "rootpipe")
    p1 = netapi.create_node("Pipe", nodespace.uid, "partitionpipe")
    netapi.link_with_reciprocal(p0, p1, 'catexp')

    links, nodes = nodenet.get_links_for_nodes([p1.uid])
    assert p0.uid in nodes
    assert len(links) == 2
    assert set([linkid(l) for l in links]) == set(["%s:%s:%s:%s" % (p0.uid, 'cat', 'cat', p1.uid), "%s:%s:%s:%s" % (p1.uid, 'exp', 'exp', p0.uid)])


def prepare_linkweight_tests(netapi):
    nodespace = netapi.create_nodespace(None, name="partition", options={'new_partition': True})
    rootpipes = []
    partitionpipes = []
    for i in range(3):
        rootpipes.append(netapi.create_node("Pipe", None, "rootpipe%d" % i))
    for i in range(5):
        partitionpipes.append(netapi.create_node("Pipe", nodespace.uid, "partitionpipe%d" % i))
    netapi.group_nodes_by_names(None, "rootpipe", sortby="name")
    netapi.group_nodes_by_names(nodespace.uid, "partitionpipe", sortby="name")
    return nodespace, rootpipes, partitionpipes


@pytest.mark.engine("theano_engine")
def test_set_link_weights_across_unlinked_partitions(runtime, test_nodenet):
    # first case: unlinked partitions:
    import numpy as np
    nodenet = runtime.get_nodenet(test_nodenet)
    netapi = nodenet.netapi
    nodespace, rootpipes, partitionpipes = prepare_linkweight_tests(netapi)
    weights = netapi.get_link_weights(None, "rootpipe", nodespace.uid, "partitionpipe")
    assert np.all(weights == np.zeros((5, 3)))
    weights[0, 0] = 0.3
    weights[1, 1] = 0.5
    netapi.set_link_weights(None, "rootpipe", nodespace.uid, "partitionpipe", weights)
    data = nodenet.get_nodes()
    l0 = data['nodes'][rootpipes[0].uid]['links']['gen'][0]
    l1 = data['nodes'][rootpipes[1].uid]['links']['gen'][0]
    assert round(l0['weight'], 3) == 0.3
    assert l0['target_node_uid'] == partitionpipes[0].uid
    assert round(l1['weight'], 3) == 0.5
    assert l1['target_node_uid'] == partitionpipes[1].uid


@pytest.mark.engine("theano_engine")
def test_set_link_weights_across_already_linked_partitions(runtime, test_nodenet):
    # second case: already linked partitions:
    import numpy as np
    nodenet = runtime.get_nodenet(test_nodenet)
    netapi = nodenet.netapi
    nodespace, rootpipes, partitionpipes = prepare_linkweight_tests(netapi)
    netapi.link_with_reciprocal(rootpipes[0], partitionpipes[0], 'subsur')
    weights = netapi.get_link_weights(None, "rootpipe", nodespace.uid, "partitionpipe")
    assert np.all(weights == np.zeros((5, 3)))
    weights[0, 0] = 0.3
    weights[1, 1] = 0.5
    netapi.set_link_weights(None, "rootpipe", nodespace.uid, "partitionpipe", weights)
    data = nodenet.get_nodes()
    l0 = data['nodes'][rootpipes[0].uid]['links']['gen'][0]
    l1 = data['nodes'][rootpipes[1].uid]['links']['gen'][0]
    assert round(l0['weight'], 3) == 0.3
    assert l0['target_node_uid'] == partitionpipes[0].uid
    assert round(l1['weight'], 3) == 0.5
    assert l1['target_node_uid'] == partitionpipes[1].uid
