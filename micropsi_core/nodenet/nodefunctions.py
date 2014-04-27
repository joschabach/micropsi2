
def register(nodenet, node=None, **params):
    node.activation = node.get_slot("gen").activation
    for type, gate in node.gates.items():
        gate.gate_function(node.get_slot("gen").activation)

def sensor(nodenet, node=None, datasource=None, **params):
    node.activation = node.get_slot("gen").activation = nodenet.world.get_datasource(nodenet.uid, datasource)
    node.gates["gen"].gate_function(nodenet.world.get_datasource(nodenet.uid, datasource))

def actor(nodenet, node=None, datatarget=None, **params):
    node.activation = node.get_slot("gen").activation
    if not nodenet.world: return
    node.nodenet.world.set_datatarget(nodenet.uid, datatarget, node.get_slot("gen").activation)

def concept(nodenet, node=None, **params):
    node.activation = node.get_slot("gen").activation
    for type, gate in node.gates.items():
        gate.gate_function(node.get_slot("gen").activation)

def script(nodenet, node=None, **params):
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
    node.get_gate("por").gate_function(-1.0 if node.activation<1 else 1.0)
    # inhibit confirmation of predecessor, and tell it to stop once successor is requested
    node.get_gate("ret").gate_function(-1.0 if 0.1 < node.activation < 1 else 1.0)
    # request children when becoming requesting
    node.get_gate("sub").gate_function(1.0 if 0.5 < node.activation else 0)
    # keep parent from failing while pending or processing, confirm parent when confirmed
    node.get_gate("sur").gate_function(
        0 if node.activation < 0.01 or node.get_slot("ret").activation>0 else
        0.01 if node.activation<1 else
        0.01 if node.get_slot("ret").activation<0 else
        1)


def pipe(nodenet, node=None, **params):
    gen = 0.0
    por = 0.0
    ret = 0.0
    sub = 0.0
    sur = 0.0

    gen += node.get_slot("sur").voted_activation
    if gen < 0: gen = 0
    if gen > 1: gen = 1

    sub += node.get_slot("gen").activation
    sub += node.get_slot("sur").activation
    sub += node.get_slot("sub").activation
    sub += node.get_slot("por").activation
    if sub > 0: sub = 1

    sur += node.get_slot("sur").voted_activation
    if sur < 0: sur = 0

    por += node.get_slot("sur").voted_activation * \
           (1+node.get_slot("por").activation)
    por += node.get_slot("por").activation * \
           (1+node.get_slot("ret").activation)
    if por < 1: por = -1
    if por > 1: por = 1

    ret += node.get_slot("ret").activation
    if ret == 0: ret = -1

    node.activation = gen
    node.get_gate("gen").gate_function(gen)
    node.get_gate("por").gate_function(por)
    node.get_gate("ret").gate_function(ret)
    node.get_gate("sub").gate_function(sub)
    node.get_gate("sur").gate_function(sur)


def activator(nodenet, node, **params):
    node.activation = node.get_slot("gen").activation
    nodenet.nodespaces[node.parent_nodespace].activators[node.parameters["type"]] = node.activation
