#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""

"""
from micropsi_core import runtime as micropsi

__author__ = 'joscha'
__date__ = '12.11.12'


def test_copy_nodes(engine):
    success, nodenet_uid1 = micropsi.new_nodenet("Origin_Nodenet", engine=engine, worldadapter="Default", owner="tester")
    success, nodenet_uid2 = micropsi.new_nodenet("Target_Nodenet", engine=engine, worldadapter="Default", owner="tester")

    # create a few nodes
    assert nodenet_uid1 in micropsi.nodenets
    assert nodenet_uid2 in micropsi.nodenets

    res, ns1 = micropsi.add_node(nodenet_uid1, "Nodespace", (100, 150), None)
    res, confl = micropsi.add_node(nodenet_uid1, "Nodespace", (200, 150), None)
    res, ns2 = micropsi.add_node(nodenet_uid1, "Nodespace", (400, 150), None)
    res, confl2 = micropsi.add_node(nodenet_uid2, "Nodespace", (200, 150), None)

    res, n1 = micropsi.add_node(nodenet_uid1, "Register", (300, 140), None)
    res, n2 = micropsi.add_node(nodenet_uid1, "Register", (300, 240), None)
    res, associated_node = micropsi.add_node(nodenet_uid1, "Register", (300, 340), None)
    res, n3 = micropsi.add_node(nodenet_uid1, "Register", (400, 240), ns1)
    res, n4 = micropsi.add_node(nodenet_uid1, "Register", (400, 240), ns2)
    res, n5 = micropsi.add_node(nodenet_uid1, "Register", (100, 240), confl)
    res, nt1 = micropsi.add_node(nodenet_uid2, "Register", (300, 140), None)
    res, nt2 = micropsi.add_node(nodenet_uid2, "Register", (150, 240), None)

    micropsi.add_link(nodenet_uid1, n1, "gen", n2, "gen")
    micropsi.add_link(nodenet_uid1, n2, "gen", n3, "gen")
    micropsi.add_link(nodenet_uid1, n1, "gen", associated_node, "gen")
    micropsi.add_link(nodenet_uid1, n3, "gen", n1, "gen")
    micropsi.add_link(nodenet_uid1, n4, "gen", n1, "gen")
    micropsi.add_link(nodenet_uid2, nt1, "gen", nt2, "gen")

    # now copy stuff between nodespaces
    micropsi.copy_nodes([n1, n2, n3, n5, ns1, confl], nodenet_uid1, nodenet_uid2)

    micropsi.save_nodenet(nodenet_uid1)
    micropsi.save_nodenet(nodenet_uid2)

    target = micropsi.nodenets[nodenet_uid2].data
    assert len(target["nodes"]) == 4 + 2
    assert len(target["nodespaces"]) == 2 + 2

    assert n1 in target["nodes"]
    assert n2 in target["nodes"]
    assert n3 in target["nodes"]
    assert associated_node not in target["nodes"]
    assert n4 not in target["nodes"]
    assert n5 in target["nodes"]
    assert nt2 in target["nodes"]

    assert ns1 in target["nodespaces"]
    assert ns2 not in target["nodespaces"]
    assert confl in target["nodespaces"]

    assert len(target["links"]) == 3 + 1

    # we should also test for parentage and link connectivity

    # TODO now test copying within the same nodenet

    micropsi.copy_nodes([n1, n2, n3, n5, ns1, confl], nodenet_uid1, nodenet_uid1, target_nodespace_uid=ns2)
    micropsi.save_nodenet(nodenet_uid1)
    # delete_nodenets
    micropsi.delete_nodenet(nodenet_uid1)
    micropsi.delete_nodenet(nodenet_uid2)
