
import math

####################################################################################################
#
# These are the reference implementations for the node functions of the standard node types.
# Node net engine implementations performing node calculations in Python are free to use
# these implementations directly.
# Non-python engine implementations, or performance-oriented python implementations,
# can use these implementations as definitions (or for equivalence tests) and implement them
# differently.
#
####################################################################################################


def neuron(netapi, node=None, **params):
    activation = node.get_slot('gen').activation
    node.activation = node.get_gate('gen').gate_function(activation)


def sensor(netapi, node=None, datasource=None, **params):
    if netapi.worldadapter and datasource in netapi.worldadapter.get_available_datasources():
        datasource_value = netapi.worldadapter.get_datasource_value(datasource)
    else:
        datasource_value = netapi.get_modulator(datasource)
    node.activation = datasource_value
    node.get_gate('gen').gate_function(datasource_value)


def actuator(netapi, node=None, datatarget=None, **params):
    activation_to_set = node.get_slot("gen").activation
    if netapi.worldadapter and datatarget in netapi.worldadapter.get_available_datatargets():
        netapi.worldadapter.add_to_datatarget(datatarget, activation_to_set)
        feedback = netapi.worldadapter.get_datatarget_feedback_value(datatarget)
    else:
        netapi.set_modulator(datatarget, activation_to_set)
        feedback = 1
    if feedback is not None:
        node.get_gate('gen').gate_function(feedback)


def concept(netapi, node=None, **params):
    activation = node.get_slot('gen').activation
    node.activation = activation
    for gate_type in node.get_gate_types():
        node.get_gate(gate_type).gate_function(activation)


def script(netapi, node=None, **params):
    """ Script nodes are state machines that use the node activation for determining their behavior.
        They form hierarchical scripts that are started via sub-activating their top-node. If the sur-activation
        is turned off, the script stops executing.
        At the bottom, the scripts must connect to activation sources (that yield positive sur activation), otherwise
        they will fail.
        The links have the following semantics:
            - sub determines sub-actions. Inactive sub-actions will turn "ready" if their parent action turns
              "requesting", by sending activation via sub.
            - por determines successors. If an action is neither inactive nor confirmed, it will inhibit its successors
              from requesting. Successors must wait for their predecessors to stop sending por-activation. The first
              action in a por-chain receives no such inhibition, it may turn from "ready" to "requesting". After
              an action has become "requesting", it turns "pending" and continues to request its sub-actions.
              All other "ready" actions will switch to "waiting" until their predecessors stop inhibiting them.
            - ret determines predecessors. Successors inhibit their predecessors from telling their parents when they
              confirm. (Once an action without sucessor confirms, we are done.)
            - sur has two functions. A high level of sur activation confirms the parent action. A low level of sur
              tells the parent action that at least one of its sub-actions has not given up yet. If no more sur
              activation is received by a pending parent action, it will fail.
            The distinction between "ready" and "waiting", and "requesting and "pending" is necessary to bridge the
            time until neighboring nodes have had time to make themselves heard.

        Currently, the node states correspond to the following activation levels:
        < 0     failed (will stick until requesting ends)
        < 0.01  inactive (will change to prepared when requested)
        < 0.3   preparing (inhibits neighbors  and changes to suppressed)
        < 0.5   suppressed (inhibits neighbors and goes to requesting when no longer inhibited)
        < 0.7   requesting (starts requesting and changes to pending)
        < 1     pending (keeps requesting, will either change to confirmed or failed)
        >=1     confirmed (will stick until requesting ends)

    """

    if node.get_slot("sub").activation < 0.01:  # node is not requested and is turned off
        node.activation = 0.0
        node.get_gate("por").gate_function(0.0)
        node.get_gate("ret").gate_function(0.0)
        node.get_gate("sub").gate_function(0.0)
        node.get_gate("sur").gate_function(0.0)
        return

    node.activation = (
        node.activation if node.activation < -0.01 else  # failed -> failed
        0.2 if node.activation < 0.01 else  # (we already tested that sub is positive): inactive -> preparing
        0.4 if node.activation < 0.5 and node.get_slot("por").activation < 0 else  # preparing -> supressed
        0.6 if node.activation < 0.5 else  # preparing/supressed -> requesting
        0.8 if node.activation < 0.7 else  # requesting -> pending
        1.0 if node.get_slot("sur").activation >= 1 else  # pending -> confirmed
        -1. if node.get_slot("sur").activation <= 0 else  # pending -> failed
        node.activation
    )

    # always inhibit successor, except when confirmed
    node.get_gate("por").gate_function(-1.0 if node.activation < 1 else 1.0)
    # inhibit confirmation of predecessor, and tell it to stop once successor is requested
    node.get_gate("ret").gate_function(-1.0 if 0.1 < node.activation < 1 else 1.0)
    # request children when becoming requesting
    node.get_gate("sub").gate_function(1.0 if 0.5 < node.activation else 0)
    # keep parent from failing while pending or processing, confirm parent when confirmed
    node.get_gate("sur").gate_function(
        0 if node.activation < 0.01 or node.get_slot("ret").activation > 0 else
        0.01 if node.activation < 1 else
        0.01 if node.get_slot("ret").activation < 0 else
        1)

def pipe(netapi, node=None, **params):
    gen = 0.0
    por = 0.0
    ret = 0.0
    sub = 0.0
    sur = 0.0
    cat = 0.0
    exp = 0.0

    countdown = int(node.get_state("countdown") or 0)
    expectation = float(node.get_parameter("expectation")) if node.get_parameter("expectation") is not None else 1
    if node.get_slot("sub").activation <= 0 or (not node.get_slot("por").empty and node.get_slot("por").activation <= 0):
        countdown = int(node.get_parameter("wait") or 1)
    else:
        countdown -= 1

    gen_sur_exp = node.get_slot("sur").get_activation() + node.get_slot("exp").get_activation()
    gen_sur_exp *= node.get_slot("sub").get_activation()
    if 0 < gen_sur_exp < expectation:                                   # don't report anything below expectation
        gen_sur_exp = 0

    gen += node.get_slot("gen").get_activation() * node.get_slot("sub").get_activation()
    if abs(gen) < 0.1: gen = gen_sur_exp                                # cut off gen loop at lower threshold

    if node.get_slot("por").get_activation() == 0 and not node.get_slot("por").empty:
        gen = gen_sur_exp

    sub += node.get_slot("sub").get_activation()
    sub += node.get_slot("cat").get_activation()
    sub *= max(node.get_slot("por").get_activation(), 0) if not node.get_slot("por").empty else 1
    sub *= 0 if node.get_slot("gen").get_activation() != 0 else 1
    if sub > 0: sub = 1
    if sub < 0: sub = -1

    sur += node.get_slot("sur").get_activation()
    if abs(node.get_slot("gen").get_activation() * node.get_slot("sub").get_activation()) > 0.2:               # cut off sur-reports from gen looping before the loop fades away
        sur += 1 if node.get_slot("gen").get_activation() > 0 else -1
    sur += node.get_slot("exp").get_activation() * node.get_slot("sub").get_activation()

    if sur > 0 and sur < expectation:                                       # don't report anything below expectation
        sur = 0

    if countdown <= 0 and sur < expectation:                                # timeout, fail
        sur = -1

    if sur >= expectation:                                                  # success, reset countdown counter
        countdown = int(node.get_parameter("wait") or 1)

    if not node.get_slot("ret").empty:
        sur = sur * node.get_slot("ret").get_activation()
    if node.get_slot("por").get_activation() < 0:
        sur = 0
    if node.get_slot("sub").get_activation() < 1:
        sur = 0

    if sur > 1:
        sur = 1
    if sur < -1:
        sur = -1

    por += node.get_slot("sur").get_activation()
    por += (0 if node.get_slot("gen").get_activation() < 0.1 else 1) * \
           (1+node.get_slot("por").get_activation())

    if countdown <= 0 and por < expectation:
        por = -1

    por *= node.get_slot("por").get_activation() if not node.get_slot("por").empty else 1  # only por if por
    por *= node.get_slot("sub").get_activation()                                           # only por if sub
    por += node.get_slot("por").get_activation() if node.get_slot("sub").get_activation() == 0 and node.get_slot("sur").get_activation() == 0 else 0

    if por > 0: por = 1

    ret += node.get_slot("ret").get_activation() if node.get_slot("sub").get_activation() == 0 and node.get_slot("sur").get_activation() == 0 else 0
    if node.get_slot("por").get_activation() < 0:
        ret = 1
    if ret > 1:
        ret = 1

    cat = sub
    if cat == 0: cat += node.get_slot("cat").get_activation()
    if cat < 0: cat = 0

    exp += node.get_slot("sur").get_activation()
    exp += node.get_slot("exp").get_activation()
    if abs(node.get_slot("gen").get_activation() * node.get_slot("sub").get_activation()) > 0.2:               # cut off sur-reports from gen looping before the loop fades away
        exp += 1
    if exp > 1: exp = 1

    if node.get_slot('sub').get_activation() > 0 and node.nodenet.use_modulators:
        if sur > 0:
            netapi.change_modulator('base_number_of_expected_events', 1)
        elif sur < 0:
            severity = len(node.get_gate("sub").get_links()) + len(node.get_gate("cat").get_links())
            netapi.change_modulator('base_number_of_unexpected_events', severity)

    node.set_state("countdown", countdown)

    # set gates
    node.get_gate("gen").gate_function(gen)
    node.get_gate("por").gate_function(por)
    node.get_gate("ret").gate_function(ret)
    node.get_gate("sub").gate_function(sub)
    node.get_gate("sur").gate_function(sur)
    node.get_gate("exp").gate_function(exp)
    node.get_gate("cat").gate_function(cat)


def activator(netapi, node, **params):
    node.activation = node.get_slot("gen").activation
    netapi.get_nodespace(node.parent_nodespace).set_activator_value(node.get_parameter('type'), node.activation)

def lstm(netapi, node, **params):

    def f(x):
        return 1.0 / (1.0 + math.exp(-x))                # (3)

    def h(x):
        return (2.0 / (1.0 + math.exp(-x))) - 1          # (4)

    def g(x):
        return (4.0 / (1.0 + math.exp(-x))) - 2          # (5)

    nodespace = netapi.get_nodespace(node.parent_nodespace)
    sample_activator = True
    if nodespace.has_activator("sampling"):
        sample_activator = nodespace.get_activator_value("sampling") > 0.99

    # both por and gen gate functions need to be set to linear
    if netapi.step % 3 == 0 and sample_activator:

        s_prev = node.get_slot("gen").activation
        net_c = node.get_slot("por").activation
        net_in = node.get_slot("gin").activation
        net_out = node.get_slot("gou").activation
        net_phi = node.get_slot("gfg").activation

        # simple-sigmoid squash lstm gating values
        y_in = f(net_in)                                     # (7)
        y_out = f(net_out)                                   # (8)
        y_phi = f(net_phi)

        # calculate node net gates (the gen gen loop is the lstm cec)
        # squash-shift-and-scale por input
        # double squash-shift-and-scale gen loop activation
        s = (y_phi * s_prev) + (y_in * g(net_c))             # (9)
        y_c = y_out * h(s)                                   # (9)

        node.activation = s
        node.get_gate("gen").gate_function(s)
        node.get_gate("por").gate_function(y_c)
        node.get_gate("gin").gate_function(y_in)
        node.get_gate("gou").gate_function(y_out)
        node.get_gate("gfg").gate_function(y_phi)
        node.set_state("s_prev", s)
        node.set_state("y_c_prev", y_c)
        node.set_state("y_in_prev", y_in)
        node.set_state("y_out_prev", y_out)
        node.set_state("y_phi_prev", y_phi)

    else:
        node.activation = float(node.get_state("s_prev") or 0)
        node.get_gate("gen").gate_function(float(node.get_state("s_prev") or 0))
        node.get_gate("por").gate_function(float(node.get_state("y_c_prev") or 0))
        node.get_gate("gin").gate_function(float(node.get_state("y_in_prev") or 0))
        node.get_gate("gou").gate_function(float(node.get_state("y_out_prev") or 0))
        node.get_gate("gfg").gate_function(float(node.get_state("y_phi_prev") or 0))
