
import pytest
from micropsi_core import runtime as micropsi


def prepare(netapi, partition_options={}):
    partition_options.update({'new_partition': True})
    nodespace = netapi.create_nodespace(None, name="partition", options=partition_options)
    source = netapi.create_node('Register', None, "Source")
    register = netapi.create_node('Register', nodespace.uid, "Register")
    netapi.link(source, 'gen', register, 'gen')
    netapi.link(source, 'gen', source, 'gen')
    source.activation = 1
    return nodespace, source, register


@pytest.mark.engine("theano_engine")
def test_partition_creation(test_nodenet):
    nodenet = micropsi.get_nodenet(test_nodenet)
    netapi = nodenet.netapi
    netapi.create_nodespace(None, name="partition", options={'new_partition': True})
    assert len(nodenet.partitions.keys()) == 2


@pytest.mark.engine("theano_engine")
def test_cross_partition_links(test_nodenet):
    nodenet = micropsi.get_nodenet(test_nodenet)
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
def test_partition_persistence(test_nodenet):
    nodenet = micropsi.get_nodenet(test_nodenet)
    netapi = nodenet.netapi
    nodespace, source, register = prepare(netapi)
    micropsi.save_nodenet(test_nodenet)
    micropsi.revert_nodenet(test_nodenet)
    nodenet.step()
    assert register.activation == 1


@pytest.mark.engine("theano_engine")
def test_delete_node_deletes_inlinks(test_nodenet):
    nodenet = micropsi.get_nodenet(test_nodenet)
    netapi = nodenet.netapi
    nodespace, source, register = prepare(netapi)
    target = netapi.create_node("Register", None, "target")
    netapi.link(register, 'gen', target, 'gen')
    netapi.delete_node(register)
    links = netapi.get_node(source.uid).get_gate('gen').get_links()
    assert len(links) == 1
    assert links[0].target_node.uid == source.uid
    assert target.get_slot('gen').empty
    assert nodespace.partition.inlinks == {}
    assert len(nodenet.rootpartition.inlinks[nodespace.partition.spid][1].get_value()) == 0


@pytest.mark.engine("theano_engine")
def test_delete_node_modifies_inlinks(test_nodenet):
    nodenet = micropsi.get_nodenet(test_nodenet)
    netapi = nodenet.netapi
    nodespace, source, register = prepare(netapi)
    target = netapi.create_node("Register", None, "target")

    register2 = netapi.create_node("Register", nodespace.uid, "reg2")
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
def test_grow_partitions(test_nodenet):
    nodenet = micropsi.get_nodenet(test_nodenet)
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
    micropsi.step_nodenet(test_nodenet)
    micropsi.save_nodenet(test_nodenet)
    micropsi.revert_nodenet(test_nodenet)
    micropsi.step_nodenet(test_nodenet)


@pytest.mark.engine("theano_engine")
def test_announce_nodes(test_nodenet):
    nodenet = micropsi.get_nodenet(test_nodenet)
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
def test_delete_partition(test_nodenet):
    nodenet = micropsi.get_nodenet(test_nodenet)
    netapi = nodenet.netapi
    nodespace, source, register = prepare(netapi)
    netapi.delete_nodespace(nodespace)
    links = source.get_gate('gen').get_links()
    assert len(links) == 1
    assert links[0].target_node == source


@pytest.mark.engine("theano_engine")
def test_delete_partition_unlinks_native_module(test_nodenet, resourcepath):
    nodenet = micropsi.get_nodenet(test_nodenet)
    netapi = nodenet.netapi
    nodespace, source, register = prepare(netapi)
    import os
    nodetype_file = os.path.join(resourcepath, 'Test', 'nodetypes.json')
    nodefunc_file = os.path.join(resourcepath, 'Test', 'nodefunctions.py')
    with open(nodetype_file, 'w') as fp:
        fp.write("""{"Testnode": {
            "name": "Testnode",
            "slottypes": ["gen", "foo", "bar"],
            "nodefunction_name": "testnodefunc",
            "gatetypes": ["gen", "foo", "bar"]}}""")
    with open(nodefunc_file, 'w') as fp:
        fp.write("def testnodefunc(netapi, node=None, **prams):\r\n    return 17")
    micropsi.reload_native_modules()
    testnode = netapi.create_node("Testnode", None, "test")
    netapi.link(testnode, 'foo', register, 'gen')
    netapi.link(register, 'gen', testnode, 'bar')
    netapi.delete_nodespace(nodespace)
    data = testnode.get_data(include_links=True)
    assert data['links'] == {}


@pytest.mark.engine("theano_engine")
def test_delete_nodespace_unlinks_native_module(test_nodenet, resourcepath):
    nodenet = micropsi.get_nodenet(test_nodenet)
    netapi = nodenet.netapi
    nodespace = netapi.create_nodespace(None, "foo")
    foopipe = netapi.create_node("Pipe", nodespace.uid, 'foopipe')
    import os
    nodetype_file = os.path.join(resourcepath, 'Test', 'nodetypes.json')
    nodefunc_file = os.path.join(resourcepath, 'Test', 'nodefunctions.py')
    with open(nodetype_file, 'w') as fp:
        fp.write("""{"Testnode": {
            "name": "Testnode",
            "slottypes": ["gen", "foo", "bar"],
            "nodefunction_name": "testnodefunc",
            "gatetypes": ["gen", "foo", "bar"]}}""")
    with open(nodefunc_file, 'w') as fp:
        fp.write("def testnodefunc(netapi, node=None, **prams):\r\n    return 17")
    micropsi.reload_native_modules()
    testnode = netapi.create_node("Testnode", None, "test")
    netapi.link(testnode, 'foo', foopipe, 'sub')
    netapi.link(foopipe, 'sur', testnode, 'bar')
    micropsi.save_nodenet(test_nodenet)
    # I don't understand why, but this is necessary.
    micropsi.revert_nodenet(test_nodenet)
    netapi.delete_nodespace(nodespace)
    data = netapi.get_node(testnode.uid).get_data(include_links=True)
    assert data['links'] == {}


@pytest.mark.engine("theano_engine")
def test_delete_subnodespace_removes_x_partition_links(test_nodenet, resourcepath):
    nodenet = micropsi.get_nodenet(test_nodenet)
    netapi = nodenet.netapi
    nodespace = netapi.create_nodespace(None, "partition", options={'new_partition': True})
    subnodespace = netapi.create_nodespace(nodespace.uid, "foo")
    r1 = netapi.create_node("Register", None)
    r2 = netapi.create_node("Register", subnodespace.uid)
    r3 = netapi.create_node("Register", None)
    netapi.link(r1, 'gen', r2, 'gen')
    netapi.link(r2, 'gen', r3, 'gen')
    netapi.delete_nodespace(subnodespace)
    data = netapi.get_node(r1.uid).get_data({'include_links': True})
    assert data['links'] == {}
    for key in nodenet.rootpartition.inlinks:
        for i in range(3):
            assert len(nodenet.rootpartition.inlinks[key][i].get_value()) == 0


@pytest.mark.engine("theano_engine")
def test_sensor_actuator_indices(test_nodenet):
    nodenet = micropsi.get_nodenet(test_nodenet)
    netapi = nodenet.netapi
    result, world_uid = micropsi.new_world('default', 'World')
    micropsi.set_nodenet_properties(test_nodenet, worldadapter='Default', world_uid=world_uid)
    sensor = netapi.create_node("Sensor", None, "static_sensor")
    sensor.set_parameter("datasource", "static_on")
    actor = netapi.create_node("Actor", None, "echo_actor")
    actor.set_parameter("datatarget", "echo")
    register = netapi.create_node("Register", None, "source")
    register.activation = 0.8
    netapi.link(register, 'gen', register, 'gen', weight=0.5)
    netapi.link(register, 'gen', actor, 'gen')
    assert sensor.activation == 0
    assert actor.get_gate('gen').activation == 0
    micropsi.step_nodenet(test_nodenet)
    micropsi.step_nodenet(test_nodenet)
    assert sensor.activation == 1
    assert round(actor.get_gate('gen').activation, 3) == 0.8
    netapi.delete_node(sensor)
    netapi.delete_node(actor)
    assert set(nodenet.rootpartition.actuator_indices) == {-1}
    assert set(nodenet.rootpartition.sensor_indices) == {-1}


def test_partition_get_node_data(test_nodenet):
    nodenet = micropsi.get_nodenet(test_nodenet)
    netapi = nodenet.netapi
    nodespace, source, register = prepare(netapi)

    nodes = []
    for i in range(10):
        n = netapi.create_node("Pipe", nodespace.uid if i > 4 else None, "node %d" % i)
        nodes.append(n)

    for i in range(4):
        netapi.link(nodes[i], 'gen', nodes[5], 'gen', weight=((i + 2) / 10))
    netapi.link(nodes[9], 'gen', nodes[4], 'gen', 0.375)

    third_ns = netapi.create_nodespace(None, "third")
    third = netapi.create_node("Register", third_ns.uid, "third")
    netapi.link(nodes[4], 'gen', third, 'gen')

    node_data = nodenet.get_nodes(nodespace_uids=[None])['nodes']
    assert set(node_data.keys()) == set([n.uid for n in nodes[:5]] + [source.uid, register.uid, third.uid] + [nodes[9].uid, nodes[5].uid])

    node_data = nodenet.get_nodes()['nodes']
    n1, n3, n4, n9 = nodes[1], nodes[3], nodes[4], nodes[9]
    assert round(node_data[n1.uid]['links']['gen'][0]['weight'], 3) == 0.3
    assert round(node_data[n3.uid]['links']['gen'][0]['weight'], 3) == 0.5
    assert round(node_data[n9.uid]['links']['gen'][0]['weight'], 3) == 0.375
    # assert node_data[n4.uid]['links'] == {}

    node_data = nodenet.get_nodes(nodespace_uids=[nodespace.uid])['nodes']
    assert len(node_data.keys()) == 12
    assert node_data[n4.uid]['links'] == {}
    assert third.uid not in node_data
