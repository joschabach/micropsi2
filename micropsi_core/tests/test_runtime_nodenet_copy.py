#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""

"""
import os
from micropsi_core.nodenet.nodenet import Nodespace, Node, Link
from micropsi_core import runtime as micropsi

__author__ = 'joscha'
__date__ = '12.11.12'

def test_copy_nodes():
    success, nodenet_uid1 = micropsi.new_nodenet("Origin_Nodenet", "Default", owner="tester")
    success, nodenet_uid2 = micropsi.new_nodenet("Target_Nodenet", "Default", owner="tester")

    # create a few nodes
    assert nodenet_uid1 not in micropsi.nodenets
    micropsi.load_nodenet(nodenet_uid1)
    assert nodenet_uid1 in micropsi.nodenets
    micropsi.load_nodenet(nodenet_uid2)
    assert nodenet_uid1 in micropsi.nodenets
    assert nodenet_uid2 in micropsi.nodenets

    micropsi.add_node(nodenet_uid1, "Nodespace", (100, 150), "Root", uid="ns1")
    micropsi.add_node(nodenet_uid1, "Nodespace", (200, 150), "Root", uid="confl")
    micropsi.add_node(nodenet_uid1, "Nodespace", (400, 150), "Root", uid="ns2")
    micropsi.add_node(nodenet_uid2, "Nodespace", (200, 150), "Root", uid="confl")

    micropsi.add_node(nodenet_uid1, "Register", (300, 140), "Root", uid="n1")
    micropsi.add_node(nodenet_uid1, "Register", (300, 240), "Root", uid="n2")
    micropsi.add_node(nodenet_uid1, "Register", (300, 340), "Root", uid="associated_node")
    micropsi.add_node(nodenet_uid1, "Register", (400, 240), "ns1", uid="n3")
    micropsi.add_node(nodenet_uid1, "Register", (400, 240), "ns2", uid="n4")
    micropsi.add_node(nodenet_uid1, "Register", (100, 240), "confl", uid="n5")
    micropsi.add_node(nodenet_uid2, "Register", (100, 140), "Root", uid="n1")
    micropsi.add_node(nodenet_uid2, "Register", (150, 240), "Root", uid="nt2")

    micropsi.add_link(nodenet_uid1, "n1", "gen", "n2", "gen", uid="l1")
    micropsi.add_link(nodenet_uid1, "n2", "gen", "n3", "gen", uid="l2")
    micropsi.add_link(nodenet_uid1, "n1", "gen", "associated_node", "gen", uid="la")
    micropsi.add_link(nodenet_uid1, "n3", "gen", "n1", "gen", uid="l3")
    micropsi.add_link(nodenet_uid1, "n4", "gen", "n1", "gen", uid="l4")
    micropsi.add_link(nodenet_uid2, "n1", "gen", "nt2", "gen", uid="l1")

    # now copy stuff between nodespaces
    micropsi.copy_nodes( ["n1", "n2", "n3", "n5", "ns1", "confl"], nodenet_uid1, nodenet_uid2)

    micropsi.save_nodenet(nodenet_uid1)
    micropsi.save_nodenet(nodenet_uid2)

    target = micropsi.get_nodespace(nodenet_uid2, "Root", -1)
    assert len(target["nodes"]) == 4 + 2
    assert len(target["nodespaces"]) == 2 + 2

    assert "n1" in target["nodes"]
    assert "n2" in target["nodes"]
    assert "n3" in target["nodes"]
    assert "associated_node" not in target["nodes"]
    assert "n4" not in target["nodes"]
    assert "n5" in target["nodes"]
    assert "nt2" in target["nodes"]

    assert "ns1" in target["nodespaces"]
    assert "ns2" not in target["nodespaces"]
    assert "confl" in target["nodespaces"]

    assert len(target["links"]) == 3 + 1
    assert "l1" in target["links"]
    assert "l2" in target["links"]
    assert "l3" in target["links"]
    assert "l4" not in target["links"]

    # we should also test for parentage and link connectivity


    # TODO now test copying within the same nodenet

    micropsi.copy_nodes( ["n1", "n2", "n3", "n5", "ns1", "confl"], nodenet_uid1, nodenet_uid1, target_nodespace_uid="ns2" )
    micropsi.save_nodenet(nodenet_uid1)
    # delete_nodenets
    micropsi.delete_nodenet(nodenet_uid1)
    micropsi.delete_nodenet(nodenet_uid2)


