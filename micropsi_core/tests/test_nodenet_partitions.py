
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
