
def register(netapi, node=None, **params):
    node.activation = node.get_slot("gen").activation
    for type, gate in node.gates.items():
        gate.gate_function(node.get_slot("gen").activation)


def sensor(netapi, node=None, datasource=None, **params):
    datasource_value = netapi.world.get_datasource(netapi.uid, datasource)
    node.activation = datasource_value
    node.gates["gen"].gate_function(datasource_value)


def actor(netapi, node=None, datatarget=None, **params):
    if not netapi.world:
        return
    activation_to_set = node.get_slot("gen").activation
    netapi.world.set_datatarget(netapi.uid, datatarget, activation_to_set)
    # if activation_to_set > 0:
        # node.activation = 1
    feedback = netapi.world.get_datatarget_feedback(netapi.uid, datatarget)
    if feedback is not None:
        node.get_gate('gen').gate_function(feedback)


def concept(netapi, node=None, **params):
    node.activation = node.get_slot("gen").activation
    for type, gate in node.gates.items():
        gate.gate_function(node.get_slot("gen").activation)


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

def pipe(netapi, node=None, sheaf="default", **params):
    gen = 0.0
    por = 0.0
    ret = 0.0
    sub = 0.0
    sur = 0.0
    cat = 0.0
    exp = 0.0

    neighbors = len(node.get_slot("por").incoming)

    gen += node.get_slot("gen").get_activation(sheaf)
    if gen < 0.1: gen = 0
    gen += node.get_slot("sur").get_activation(sheaf)
    gen += node.get_slot("exp").get_activation(sheaf)
    if gen > 1: gen = 1

    sub += max(node.get_slot("sur").get_activation(sheaf), 0)
    sub += node.get_slot("sub").get_activation(sheaf)
    sub *= 0 if node.get_slot("por").get_activation(sheaf) < 0 else 1
    sub *= 0 if node.get_slot("gen").get_activation(sheaf) > 0 else 1
    if sub > 0: sub = 1

    sur += node.get_slot("sur").get_activation(sheaf)
    if sur == 0: sur += node.get_slot("sur").get_activation("default")      # no activation in our sheaf, maybe from sensors?
    sur += 0 if node.get_slot("gen").get_activation(sheaf) < 0.1 else 1
    sur += node.get_slot("exp").get_activation(sheaf)
    if sur > 0:     # else: always propagate failure
        sur *= 0 if node.get_slot("por").get_activation(sheaf) < 0 else 1
        sur *= 0 if node.get_slot("ret").get_activation(sheaf) < 0 else 1
    if sur < -1: sur = -1
    if sur > 1: sur = 1
    sur /= neighbors if neighbors > 1 else 1

    por += node.get_slot("sur").get_activation(sheaf) * \
           (1+node.get_slot("por").get_activation(sheaf))
    por += (0 if node.get_slot("gen").get_activation(sheaf) < 0.1 else 1) * \
           (1+node.get_slot("por").get_activation(sheaf))
    por += node.get_slot("por").get_activation(sheaf) if node.get_slot("sub").get_activation(sheaf) == 0 and node.get_slot("sur").get_activation(sheaf) == 0 else 0
    por += 1 if neighbors > 1 else 0
    if por <= 0: por = -1
    if por > 0: por = 1

    ret += node.get_slot("ret").get_activation(sheaf) if node.get_slot("sub").get_activation(sheaf) == 0 and node.get_slot("sur").get_activation(sheaf) == 0 else 0
    ret += 1 if neighbors > 1 else 0
    if ret <= 0: ret = -1

    cat = sub
    if cat == 0: cat += node.get_slot("cat").get_activation(sheaf)
    if cat < 0: cat = 0

    exp += node.get_slot("sur").get_activation(sheaf)
    exp += node.get_slot("exp").get_activation(sheaf) * 0.1                 # magic priming number
    if exp == 0: exp += node.get_slot("sur").get_activation("default")      # no activation in our sheaf, maybe from sensors?
    if exp > 1: exp = 1

    # handle locking if configured for this node
    sub_lock_needed = node.get_parameter('sublock')
    if sub_lock_needed is not None:
        surinput = node.get_slot("sur").get_activation(sheaf)
        if sub > 0 and surinput < 1:
            # we want to go sub, but we need to acquire a lock for that
            if netapi.is_locked(sub_lock_needed):
                if not netapi.is_locked_by(sub_lock_needed, node.uid+sheaf):
                    # it's locked and not by us, so we need to pace ourselves and wait
                    sub = 0
            else:
                # we can proceed, but we need to lock
                netapi.lock(sub_lock_needed, node.uid+sheaf)

        if surinput >= 1:
            # we can clear a lock if it's us who had acquired it
            if netapi.is_locked_by(sub_lock_needed, node.uid+sheaf):
                netapi.unlock(sub_lock_needed)

    # set gates
    node.set_sheaf_activation(gen, sheaf)
    node.get_gate("gen").gate_function(gen, sheaf)
    node.get_gate("por").gate_function(por, sheaf)
    node.get_gate("ret").gate_function(ret, sheaf)
    node.get_gate("sub").gate_function(sub, sheaf)
    node.get_gate("sur").gate_function(sur, sheaf)
    node.get_gate("exp").gate_function(exp, sheaf)
    if cat > 0 and sub > 0:     # cats will be checked in their own sheaf
        node.get_gate("cat").open_sheaf(cat, sheaf)
        node.get_gate("cat").gate_function(0, sheaf)
    else:
        node.get_gate("cat").gate_function(cat, sheaf)


def activator(netapi, node, **params):
    node.activation = node.get_slot("gen").activation
    netapi.nodespaces[node.parent_nodespace].activators[node.parameters["type"]] = node.activation
