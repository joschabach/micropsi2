#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""
Tests for node activation propagation and gate arithmetic
"""


def prepare(runtime, test_nodenet):
    nodenet = runtime.get_nodenet(test_nodenet)
    netapi = nodenet.netapi
    source = netapi.create_node("Neuron", None, "Source")
    netapi.link(source, "gen", source, "gen")
    source.activation = 1
    nodenet.step()
    return nodenet, netapi, source


def add_directional_activators(runtime, test_nodenet):
    net = runtime.get_nodenet(test_nodenet)
    netapi = net.netapi
    sub_act = netapi.create_node("Activator", None, "sub-activator")
    net.get_node(sub_act.uid).set_parameter("type", "sub")

    sur_act = netapi.create_node("Activator", None, "sur-activator")
    net.get_node(sur_act.uid).set_parameter("type", "sur")

    por_act = netapi.create_node("Activator", None, "por-activator")
    net.get_node(por_act.uid).set_parameter("type", "por")

    ret_act = netapi.create_node("Activator", None, "ret-activator")
    net.get_node(ret_act.uid).set_parameter("type", "ret")

    cat_act = netapi.create_node("Activator", None, "cat-activator")
    net.get_node(cat_act.uid).set_parameter("type", "cat")

    exp_act = netapi.create_node("Activator", None, "exp-activator")
    net.get_node(exp_act.uid).set_parameter("type", "exp")

    return sub_act, sur_act, por_act, ret_act, cat_act, exp_act


def test_node_pipe_logic_subtrigger(runtime, test_nodenet):
    # test a resting classifier, expect sub to be activated
    net, netapi, source = prepare(runtime, test_nodenet)
    n_head = netapi.create_node("Pipe", None, "Head")

    netapi.link(source, "gen", n_head, "sub", 1)
    net.step()

    assert n_head.get_gate("sub").activation == 1


def test_node_pipe_logic_classifier_two_off(runtime, test_nodenet):
    # test a resting classifier, expect no activation
    net, netapi, source = prepare(runtime, test_nodenet)
    n_head = netapi.create_node("Pipe", None, "Head")
    n_a = netapi.create_node("Pipe", None, "A")
    n_b = netapi.create_node("Pipe", None, "B")
    netapi.link_with_reciprocal(n_head, n_a, "subsur")
    netapi.link_with_reciprocal(n_head, n_b, "subsur")

    for i in range(3):
        net.step()
    assert n_head.get_gate("gen").activation == 0


def test_node_pipe_logic_classifier_two_partial(runtime, test_nodenet):
    # test partial success of a classifier (fuzzyness)
    net, netapi, source = prepare(runtime, test_nodenet)
    n_head = netapi.create_node("Pipe", None, "Head")
    n_head.set_parameter("expectation", 0)
    n_a = netapi.create_node("Pipe", None, "A")
    n_a.set_parameter("expectation", 0)
    n_b = netapi.create_node("Pipe", None, "B")
    n_b.set_parameter("expectation", 0)
    netapi.link_with_reciprocal(n_head, n_a, "subsur")
    netapi.link(n_a, "sur", n_head, "sur", 0.5)
    netapi.link_with_reciprocal(n_head, n_b, "subsur")
    netapi.link(n_b, "sur", n_head, "sur", 0.5)
    netapi.link(source, "gen", n_head, "sub", 1)

    netapi.link(source, "gen", n_a, "sur")

    for i in range(3):
        net.step()
    assert round(n_head.get_gate("gen").activation, 2) == 1 / 2

    netapi.link(source, "gen", n_b, "sur")

    for i in range(3):
        net.step()
    assert n_head.get_gate("gen").activation == 1


def test_node_pipe_logic_classifier_two_partially_failing(runtime, test_nodenet):
    # test fuzzyness with one node failing
    net, netapi, source = prepare(runtime, test_nodenet)
    n_head = netapi.create_node("Pipe", None, "Head")
    n_a = netapi.create_node("Pipe", None, "A")
    n_b = netapi.create_node("Pipe", None, "B")
    netapi.link_with_reciprocal(n_head, n_a, "subsur")
    netapi.link(n_a, "sur", n_head, "sur", 0.5)
    netapi.link_with_reciprocal(n_head, n_b, "subsur")
    netapi.link(n_b, "sur", n_head, "sur", 0.5)
    netapi.link(source, "gen", n_head, "sub", 1)

    netapi.link(source, "gen", n_a, "sur", -1)

    for i in range(3):
        net.step()
    assert round(n_head.get_gate("gen").activation, 2) == - 1 / 2

    netapi.link(source, "gen", n_b, "sur")

    for i in range(3):
        net.step()
    assert n_head.get_gate("gen").activation == 0


def test_node_pipe_logic_classifier_three_off(runtime, test_nodenet):
    # test a resting classifier, expect no activation
    net, netapi, source = prepare(runtime, test_nodenet)
    n_head = netapi.create_node("Pipe", None, "Head")
    n_a = netapi.create_node("Pipe", None, "A")
    n_b = netapi.create_node("Pipe", None, "B")
    n_c = netapi.create_node("Pipe", None, "C")
    netapi.link_with_reciprocal(n_head, n_a, "subsur")
    netapi.link_with_reciprocal(n_head, n_b, "subsur")
    netapi.link_with_reciprocal(n_head, n_c, "subsur")

    for i in range(3):
        net.step()
    assert n_head.get_gate("gen").activation == 0


def test_node_pipe_logic_classifier_three_partial(runtime, test_nodenet):
    # test partial success of a classifier (fuzzyness)
    net, netapi, source = prepare(runtime, test_nodenet)
    n_head = netapi.create_node("Pipe", None, "Head")
    n_head.set_parameter("expectation", 0)
    n_a = netapi.create_node("Pipe", None, "A")
    n_a.set_parameter("wait", 100)
    n_a.set_parameter("expectation", 0)
    n_b = netapi.create_node("Pipe", None, "B")
    n_b.set_parameter("expectation", 0)
    n_b.set_parameter("wait", 100)
    n_c = netapi.create_node("Pipe", None, "C")
    n_c.set_parameter("expectation", 0)
    n_c.set_parameter("wait", 100)
    netapi.link_with_reciprocal(n_head, n_a, "subsur")
    netapi.link(n_a, "sur", n_head, "sur", 1/3)
    netapi.link_with_reciprocal(n_head, n_b, "subsur")
    netapi.link(n_b, "sur", n_head, "sur", 1/3)
    netapi.link_with_reciprocal(n_head, n_c, "subsur")
    netapi.link(n_c, "sur", n_head, "sur", 1/3)

    netapi.link(source, "gen", n_head, "sub", 1)
    netapi.link(source, "gen", n_a, "sur")

    for i in range(3):
        net.step()
    assert round(n_head.get_gate("gen").activation, 2) == round(1 / 3, 2)

    netapi.link(source, "gen", n_c, "sur")

    for i in range(3):
        net.step()
    assert round(n_head.get_gate("gen").activation, 2) == round(2 / 3, 2)

    netapi.link(source, "gen", n_b, "sur")

    for i in range(3):
        net.step()
    assert round(n_head.get_gate("gen").activation, 2) == 1


def test_node_pipe_logic_classifier_three_partially_failing(runtime, test_nodenet):
    # test fuzzyness with one node failing
    net, netapi, source = prepare(runtime, test_nodenet)
    n_head = netapi.create_node("Pipe", None, "Head")
    n_head.set_parameter("expectation", 0)
    n_a = netapi.create_node("Pipe", None, "A")
    n_a.set_parameter("expectation", 0)
    n_b = netapi.create_node("Pipe", None, "B")
    n_b.set_parameter("expectation", 0)
    n_c = netapi.create_node("Pipe", None, "C")
    n_c.set_parameter("expectation", 0)
    netapi.link_with_reciprocal(n_head, n_a, "subsur")
    netapi.link(n_a, "sur", n_head, "sur", 1/3)
    netapi.link_with_reciprocal(n_head, n_b, "subsur")
    netapi.link(n_b, "sur", n_head, "sur", 1/3)
    netapi.link_with_reciprocal(n_head, n_c, "subsur")
    netapi.link(n_c, "sur", n_head, "sur", 1/3)

    netapi.link(source, "gen", n_head, "sub", 1)
    netapi.link(source, "gen", n_a, "sur", -1)

    for i in range(3):
        net.step()
    assert round(n_head.get_gate("gen").activation, 2) == round(- 1 / 3, 2)

    netapi.link(source, "gen", n_c, "sur")

    for i in range(3):
        net.step()
    assert round(n_head.get_gate("gen").activation, 2) == 0

    netapi.link(source, "gen", n_b, "sur")

    for i in range(3):
        net.step()
    assert round(n_head.get_gate("gen").activation, 2) == round(1 / 3, 2)


def test_node_pipe_logic_two_script(runtime, test_nodenet):
    # test whether scripts work
    net, netapi, source = prepare(runtime, test_nodenet)
    n_head = netapi.create_node("Pipe", None, "Head")
    n_a = netapi.create_node("Pipe", None, "A")
    n_a.set_parameter("wait", 100)
    n_b = netapi.create_node("Pipe", None, "B")
    n_b.set_parameter("wait", 100)
    netapi.link_with_reciprocal(n_head, n_a, "subsur")
    netapi.link_with_reciprocal(n_head, n_b, "subsur")
    netapi.link_with_reciprocal(n_a, n_b, "porret")
    netapi.link(source, "gen", n_head, "sub")
    net.step()
    net.step()

    # quiet, first node requesting
    assert round(n_head.get_gate("gen").activation, 2) == 0
    assert round(n_a.get_gate("sub").activation, 2) == 1
    assert round(n_a.get_gate("sur").activation, 2) == 0
    assert round(n_b.get_gate("sub").activation, 2) == 0
    assert round(n_b.get_gate("sur").activation, 2) == 0

    # reply: good!
    netapi.link(source, "gen", n_a, "sur")
    net.step()
    assert round(n_a.get_gate("sub").activation, 2) == 1
    assert round(n_a.get_gate("sur").activation, 2) == 0
    assert round(n_b.get_gate("sub").activation, 2) == 0
    assert round(n_b.get_gate("sur").activation, 2) == 0

    # second node now requesting
    net.step()
    assert round(n_a.get_gate("sub").activation, 2) == 1
    assert round(n_a.get_gate("sur").activation, 2) == 0
    assert round(n_b.get_gate("sub").activation, 2) == 1
    assert round(n_b.get_gate("sur").activation, 2) == 0

    # second node good, third requesting
    netapi.link(source, "gen", n_b, "sur")
    net.step()
    net.step()
    assert round(n_a.get_gate("sub").activation, 2) == 1
    assert round(n_a.get_gate("sur").activation, 2) == 0
    assert round(n_b.get_gate("sub").activation, 2) == 1
    assert round(n_b.get_gate("sur").activation, 2) == 1

    # overall script good
    net.step()
    assert round(n_head.get_gate("gen").activation, 2) == 1


def test_node_pipe_logic_three_script(runtime, test_nodenet):
    # test whether scripts work
    net, netapi, source = prepare(runtime, test_nodenet)
    n_head = netapi.create_node("Pipe", None, "Head")
    n_a = netapi.create_node("Pipe", None, "A")
    n_a.set_parameter("wait", 100)
    n_b = netapi.create_node("Pipe", None, "B")
    n_b.set_parameter("wait", 100)
    n_c = netapi.create_node("Pipe", None, "C")
    n_c.set_parameter("wait", 100)
    netapi.link_with_reciprocal(n_head, n_a, "subsur")
    netapi.link_with_reciprocal(n_head, n_b, "subsur")
    netapi.link_with_reciprocal(n_head, n_c, "subsur")
    netapi.link_with_reciprocal(n_a, n_b, "porret")
    netapi.link_with_reciprocal(n_b, n_c, "porret")
    netapi.link(source, "gen", n_head, "sub")
    net.step()
    net.step()

    # quiet, first node requesting
    assert round(n_head.get_gate("gen").activation, 2) == 0
    assert round(n_a.get_gate("sub").activation, 2) == 1
    assert round(n_a.get_gate("sur").activation, 2) == 0
    assert round(n_b.get_gate("sub").activation, 2) == 0
    assert round(n_b.get_gate("sur").activation, 2) == 0
    assert round(n_c.get_gate("sub").activation, 2) == 0
    assert round(n_c.get_gate("sur").activation, 2) == 0

    # reply: good!
    netapi.link(source, "gen", n_a, "sur")
    net.step()
    assert round(n_a.get_gate("sub").activation, 2) == 1
    assert round(n_a.get_gate("sur").activation, 2) == 0
    assert round(n_b.get_gate("sub").activation, 2) == 0
    assert round(n_b.get_gate("sur").activation, 2) == 0
    assert round(n_c.get_gate("sub").activation, 2) == 0
    assert round(n_c.get_gate("sur").activation, 2) == 0

    # second node now requesting
    net.step()
    assert round(n_a.get_gate("sub").activation, 2) == 1
    assert round(n_a.get_gate("sur").activation, 2) == 0
    assert round(n_b.get_gate("sub").activation, 2) == 1
    assert round(n_b.get_gate("sur").activation, 2) == 0
    assert round(n_c.get_gate("sub").activation, 2) == 0
    assert round(n_c.get_gate("sur").activation, 2) == 0

    # second node good, third requesting
    netapi.link(source, "gen", n_b, "sur")
    net.step()
    net.step()
    assert round(n_a.get_gate("sub").activation, 2) == 1
    assert round(n_a.get_gate("sur").activation, 2) == 0
    assert round(n_b.get_gate("sub").activation, 2) == 1
    assert round(n_b.get_gate("sur").activation, 2) == 0
    assert round(n_c.get_gate("sub").activation, 2) == 1
    assert round(n_c.get_gate("sur").activation, 2) == 0

    # third node good
    netapi.link(source, "gen", n_c, "sur")
    net.step()
    net.step()
    assert round(n_a.get_gate("sub").activation, 2) == 1
    assert round(n_a.get_gate("sur").activation, 2) == 0
    assert round(n_b.get_gate("sub").activation, 2) == 1
    assert round(n_b.get_gate("sur").activation, 2) == 0
    assert round(n_c.get_gate("sub").activation, 2) == 1
    assert round(n_c.get_gate("sur").activation, 2) == 1

    # overall script good
    net.step()
    assert n_head.get_gate("gen").activation == 1

    # now let the second one fail
    # whole script fails, third one muted
    netapi.link(source, "gen", n_b, "sur", -1)
    net.step()
    net.step()
    net.step()     # extra steps because we're coming from a stable "all good state"
    net.step()
    assert round(n_a.get_gate("sub").activation, 2) == 1
    assert round(n_a.get_gate("sur").activation, 2) == 0
    assert round(n_b.get_gate("sub").activation, 2) == 1
    assert round(n_b.get_gate("sur").activation, 2) == -1
    assert round(n_c.get_gate("sub").activation, 2) == 0
    assert round(n_c.get_gate("sur").activation, 2) == 0

    net.step()
    assert n_head.get_gate("gen").activation == -1


def test_node_pipe_logic_alternatives(runtime, test_nodenet):
    # create a script with alternatives, let one fail, one one succeed
    net, netapi, source = prepare(runtime, test_nodenet)
    n_head = netapi.create_node("Pipe", None, "Head")
    n_a = netapi.create_node("Pipe", None, "A")
    n_a.set_parameter("wait", 100)
    n_b = netapi.create_node("Pipe", None, "B")
    n_b.set_parameter("wait", 100)
    n_c = netapi.create_node("Pipe", None, "C")
    n_c.set_parameter("wait", 100)
    n_b_a1 = netapi.create_node("Pipe", None, "B-A1")
    n_b_a1.set_parameter("wait", 100)
    n_b_a2 = netapi.create_node("Pipe", None, "B-A1")
    n_b_a2.set_parameter("wait", 100)
    netapi.link_with_reciprocal(n_head, n_a, "subsur")
    netapi.link_with_reciprocal(n_head, n_b, "subsur")
    netapi.link_with_reciprocal(n_head, n_c, "subsur")
    netapi.link_with_reciprocal(n_b, n_b_a1, "subsur")
    netapi.link_with_reciprocal(n_b, n_b_a2, "subsur")
    netapi.link_with_reciprocal(n_a, n_b, "porret")
    netapi.link_with_reciprocal(n_b, n_c, "porret")
    netapi.link_with_reciprocal(n_b_a1, n_b_a2, "porret")

    # alternative linkage
    netapi.link(n_b_a1, "por", n_b_a2, "por", -1)

    netapi.link(source, "gen", n_head, "sub")
    net.step()
    net.step()

    # quiet, first node requesting
    assert round(n_head.get_gate("gen").activation, 2) == 0
    assert round(n_a.get_gate("sub").activation, 2) == 1
    assert round(n_a.get_gate("sur").activation, 2) == 0
    assert round(n_b.get_gate("sub").activation, 2) == 0
    assert round(n_b.get_gate("sur").activation, 2) == 0
    assert round(n_c.get_gate("sub").activation, 2) == 0
    assert round(n_c.get_gate("sur").activation, 2) == 0

    # reply: good!
    netapi.link(source, "gen", n_a, "sur")
    net.step()
    assert round(n_a.get_gate("sub").activation, 2) == 1
    assert round(n_a.get_gate("sur").activation, 2) == 0
    assert round(n_b.get_gate("sub").activation, 2) == 0
    assert round(n_b.get_gate("sur").activation, 2) == 0
    assert round(n_c.get_gate("sub").activation, 2) == 0
    assert round(n_c.get_gate("sur").activation, 2) == 0

    # first alternative requesting
    net.step()
    net.step()
    assert round(n_b_a1.get_gate("sub").activation, 2) == 1
    assert round(n_b_a1.get_gate("sur").activation, 2) == 0
    assert round(n_b_a2.get_gate("sub").activation, 2) == 0
    assert round(n_b_a2.get_gate("sur").activation, 2) == 0

    # reply: fail!
    netapi.link(source, "gen", n_b_a1, "sur", -1)
    net.step()
    net.step()
    assert round(n_b_a1.get_gate("sur").activation, 2) == 0
    assert round(n_b_a1.get_gate("por").activation, 2) == -1

    # second alternative requesting
    assert round(n_b_a2.get_gate("sub").activation, 2) == 1
    assert round(n_b_a2.get_gate("sur").activation, 2) == 0
    assert round(n_b.get_gate("sur").activation, 2) == 0

    # reply: succeed!
    netapi.link(source, "gen", n_b_a2, "sur", 1)
    net.step()
    net.step()
    assert round(n_b_a1.get_gate("sur").activation, 2) == 0
    assert round(n_b_a1.get_gate("por").activation, 2) == -1
    assert round(n_b_a2.get_gate("sub").activation, 2) == 1
    assert round(n_b_a2.get_gate("sur").activation, 2) == 1

    # third node good
    netapi.link(source, "gen", n_c, "sur")
    net.step()
    net.step()
    assert round(n_a.get_gate("sub").activation, 2) == 1
    assert round(n_a.get_gate("sur").activation, 2) == 0
    assert round(n_b.get_gate("sub").activation, 2) == 1
    assert round(n_b.get_gate("sur").activation, 2) == 0
    assert round(n_c.get_gate("sub").activation, 2) == 1
    assert round(n_c.get_gate("sur").activation, 2) == 1

    # overall script good
    net.step()
    assert round(n_head.get_gate("gen").activation, 2) == 1

    # now let the second alternative also fail
    # whole script fails, third one muted
    netapi.link(source, "gen", n_b_a2, "sur", -1)
    net.step()
    net.step()
    net.step()     # extra steps because we're coming from a stable "all good state"
    net.step()
    assert round(n_a.get_gate("sub").activation, 2) == 1
    assert round(n_a.get_gate("sur").activation, 2) == 0
    assert round(n_b.get_gate("sub").activation, 2) == 1
    assert round(n_b.get_gate("sur").activation, 2) == -1
    assert round(n_c.get_gate("sub").activation, 2) == 0
    assert round(n_c.get_gate("sur").activation, 2) == 0

    net.step()
    assert round(n_head.get_gate("gen").activation, 2) == -1


def test_node_pipe_logic_timeout_fail(runtime, test_nodenet):
    # test whether scripts work
    net, netapi, source = prepare(runtime, test_nodenet)
    n_head = netapi.create_node("Pipe", None, "Head")
    n_head.set_parameter("wait", 100)
    n_a = netapi.create_node("Pipe", None, "A")
    n_a.set_parameter("wait", 100)
    n_b = netapi.create_node("Pipe", None, "B")
    n_b.set_parameter("wait", 5)
    n_b.set_parameter("expectation", 0.8)
    netapi.link_with_reciprocal(n_head, n_a, "subsur")
    netapi.link_with_reciprocal(n_head, n_b, "subsur")
    netapi.link_with_reciprocal(n_a, n_b, "porret")
    netapi.link(source, "gen", n_head, "sub")
    net.step()
    net.step()

    # quiet, first node requesting
    assert round(n_head.get_gate("gen").activation, 2) == 0
    assert round(n_a.get_gate("sub").activation, 2) == 1
    assert round(n_a.get_gate("sur").activation, 2) == 0
    assert round(n_b.get_gate("sub").activation, 2) == 0
    assert round(n_b.get_gate("sur").activation, 2) == 0

    # reply: good!
    netapi.link(source, "gen", n_a, "sur")
    net.step()
    assert round(n_a.get_gate("sub").activation, 2) == 1
    assert round(n_a.get_gate("sur").activation, 2) == 0
    assert round(n_b.get_gate("sub").activation, 2) == 0
    assert round(n_b.get_gate("sur").activation, 2) == 0

    # second node now requesting
    net.step()
    assert round(n_a.get_gate("sub").activation, 2) == 1
    assert round(n_a.get_gate("sur").activation, 2) == 0
    assert round(n_b.get_gate("sub").activation, 2) == 1
    assert round(n_b.get_gate("sur").activation, 2) == 0

    # second node good, third requesting
    netapi.link(source, "gen", n_b, "sur", 0.7)
    net.step()
    net.step()
    assert round(n_a.get_gate("sub").activation, 2) == 1
    assert round(n_a.get_gate("sur").activation, 2) == 0
    assert round(n_b.get_gate("sub").activation, 2) == 1
    assert round(n_b.get_gate("sur").activation, 2) == 0
    net.step()
    net.step()
    net.step()
    net.step()
    assert round(n_a.get_gate("sub").activation, 2) == 1
    assert round(n_a.get_gate("sur").activation, 2) == 0
    assert round(n_b.get_gate("sub").activation, 2) == 1
    assert round(n_b.get_gate("sur").activation, 2) == -1

    # overall script failed
    net.step()
    assert round(n_head.get_gate("gen").activation, 2) == -1


def test_node_pipe_unrequested_behaviour(runtime, test_nodenet):
    # two possible choices for sur-activation if not requested:
    # gen mirrors sur, or gen delivers incoming activation
    # current decision: gen mirrors sur, no gen-activation w/o being requested
    net, netapi, source = prepare(runtime, test_nodenet)
    pipe = netapi.create_node("Pipe", None, "pipe")
    netapi.link(source, 'gen', pipe, 'sur')
    net.step()
    assert round(pipe.get_gate("gen").activation, 2) == 0
    assert round(pipe.get_gate("por").activation, 2) == 0
    assert round(pipe.get_gate("ret").activation, 2) == 0
    assert round(pipe.get_gate("sub").activation, 2) == 0
    assert round(pipe.get_gate("sur").activation, 2) == 0
    assert round(pipe.get_gate("cat").activation, 2) == 0
    assert round(pipe.get_gate("exp").activation, 2) == 1


#def test_node_pipe_logic_feature_binding(runtime, test_nodenet):
#    # check if the same feature can be checked and bound twice
#    net, netapi, source = prepare(runtime, test_nodenet)
#    schema = netapi.create_node("Pipe", None, "Schema")
#    element1 = netapi.create_node("Pipe", None, "Element1")
#    element2 = netapi.create_node("Pipe", None, "Element2")
#    netapi.link_with_reciprocal(schema, element1, "subsur")
#    netapi.link_with_reciprocal(schema, element2, "subsur")
#
#    concrete_feature1 = netapi.create_node("Pipe", None, "ConcreteFeature1")
#    concrete_feature2 = netapi.create_node("Pipe", None, "ConcreteFeature2")
#    netapi.link_with_reciprocal(element1, concrete_feature1, "subsur")
#    netapi.link_with_reciprocal(element2, concrete_feature2, "subsur")
#
#    abstract_feature = netapi.create_node("Pipe", None, "AbstractFeature")
#    netapi.link_with_reciprocal(concrete_feature1, abstract_feature, "catexp")
#    netapi.link_with_reciprocal(concrete_feature2, abstract_feature, "catexp")
#
#    netapi.link(source, "gen", schema, "sub")
#    netapi.link(source, "gen", abstract_feature, "sur")
#
#    net.step()
#    assert abstract_feature.get_gate("gen").activation == 1
#    assert abstract_feature.get_gate("exp").activation == 1
#
#    net.step()
#    assert concrete_feature1.get_gate("gen").activation == 1
#    assert concrete_feature2.get_gate("gen").activation == 1
#
#    net.step()
#    net.step()
#
#    assert schema.get_gate("gen").activation == 1


#def test_node_pipe_logic_search_sub(runtime, test_nodenet):
#    # check if sub-searches work
#    net, netapi, source = prepare(runtime, test_nodenet)
#    n_a = netapi.create_node("Pipe", None, "A")
#    n_b = netapi.create_node("Pipe", None, "B")
#    netapi.link_with_reciprocal(n_a, n_b, "subsur")
#
#    sub_act, sur_act, por_act, ret_act, cat_act, exp_act = add_directional_activators(runtime, test_nodenet)
#    netapi.link(source, "gen", sub_act, "gen")
#
#    netapi.link(source, "gen", n_a, "sub")
#
#    net.step()
#    net.step()
#    net.step()
#
#    assert round(n_a.get_gate("sub").activation, 2) == 1
#    assert round(n_b.get_gate("sub").activation, 2) == 1
#
#
#def test_node_pipe_logic_search_sur(runtime, test_nodenet):
#    # check if sur-searches work
#    net, netapi, source = prepare(runtime, test_nodenet)
#    n_a = netapi.create_node("Pipe", None, "A")
#    n_b = netapi.create_node("Pipe", None, "B")
#    netapi.link_with_reciprocal(n_a, n_b, "subsur")
#
#    sub_act, sur_act, por_act, ret_act, cat_act, exp_act = add_directional_activators(runtime, test_nodenet)
#    netapi.link(source, "gen", sur_act, "gen")
#
#    netapi.link(source, "gen", n_b, "sur")
#
#    net.step()
#    net.step()
#    net.step()
#
#    assert n_b.get_gate("sur").activation > 0
#    assert n_a.get_gate("sur").activation > 0


def test_node_pipe_logic_search_por(runtime, test_nodenet):
    # check if por-searches work
    net, netapi, source = prepare(runtime, test_nodenet)
    n_a = netapi.create_node("Pipe", None, "A")
    n_b = netapi.create_node("Pipe", None, "B")
    netapi.link_with_reciprocal(n_a, n_b, "porret")

    sub_act, sur_act, por_act, ret_act, cat_act, exp_act = add_directional_activators(runtime, test_nodenet)
    netapi.link(source, "gen", por_act, "gen")

    netapi.link(source, "gen", n_a, "por")

    net.step()
    net.step()
    net.step()

    assert round(n_a.get_gate("por").activation, 2) == 1
    assert round(n_b.get_gate("por").activation, 2) == 1


def test_node_pipe_logic_search_ret(runtime, test_nodenet):
    # check if ret-searches work
    net, netapi, source = prepare(runtime, test_nodenet)
    n_a = netapi.create_node("Pipe", None, "A")
    n_b = netapi.create_node("Pipe", None, "B")
    netapi.link_with_reciprocal(n_a, n_b, "porret")

    sub_act, sur_act, por_act, ret_act, cat_act, exp_act = add_directional_activators(runtime, test_nodenet)
    netapi.link(source, "gen", ret_act, "gen")

    netapi.link(source, "gen", n_b, "ret")

    net.step()
    net.step()
    net.step()

    assert round(n_b.get_gate("ret").activation, 2) == 1
    assert round(n_a.get_gate("ret").activation, 2) == 1


def test_node_pipe_logic_search_cat(runtime, test_nodenet):
    # check if cat-searches work
    net, netapi, source = prepare(runtime, test_nodenet)
    n_a = netapi.create_node("Pipe", None, "A")
    n_b = netapi.create_node("Pipe", None, "B")
    netapi.link_with_reciprocal(n_a, n_b, "catexp")

    sub_act, sur_act, por_act, ret_act, cat_act, exp_act = add_directional_activators(runtime, test_nodenet)
    netapi.link(source, "gen", cat_act, "gen")

    netapi.link(source, "gen", n_a, "cat")

    net.step()
    net.step()
    net.step()

    assert round(n_a.get_gate("cat").activation, 2) == 1
    assert round(n_b.get_gate("cat").activation, 2) == 1


def test_node_pipe_logic_search_exp(runtime, test_nodenet):
    # check if exp-searches work
    net, netapi, source = prepare(runtime, test_nodenet)
    n_a = netapi.create_node("Pipe", None, "A")
    n_b = netapi.create_node("Pipe", None, "B")
    netapi.link_with_reciprocal(n_a, n_b, "catexp")

    sub_act, sur_act, por_act, ret_act, cat_act, exp_act = add_directional_activators(runtime, test_nodenet)
    netapi.link(source, "gen", exp_act, "gen")

    netapi.link(source, "gen", n_b, "exp")

    net.step()
    net.step()
    net.step()

    assert n_b.get_gate("exp").activation > 0
    assert n_a.get_gate("exp").activation > 0
