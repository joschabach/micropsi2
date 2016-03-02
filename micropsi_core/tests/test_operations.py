
from micropsi_core import runtime


def test_autoalign_operation(test_nodenet):
    ops = runtime.get_available_operations()
    assert ops['autoalign']['selection']['nodetypes'] == []
    assert ops['autoalign']['selection']['mincount'] == 2
    assert ops['autoalign']['selection']['maxcount'] == -1
    assert ops['autoalign']['category'] == 'layout'
    assert ops['autoalign']['parameters'] == []

    api = runtime.nodenets[test_nodenet].netapi
    p1 = api.create_node("Pipe", None, "p1")
    p2 = api.create_node("Pipe", None, "p2")
    p3 = api.create_node("Pipe", None, "p3")
    api.link_with_reciprocal(p1, p2, 'subsur')
    api.link_with_reciprocal(p1, p3, 'subsur')
    api.link_with_reciprocal(p2, p3, 'porret')
    runtime.run_operation(test_nodenet, "autoalign", {}, [p1.uid, p2.uid, p3.uid])
    assert p1.position[0] == p2.position[0]
    assert p1.position[1] < p2.position[1]
    assert p2.position[1] == p3.position[1]
