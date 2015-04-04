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


def register(netapi, node=None, **params):
    activation = node.get_slot('gen').activation
    node.activation = activation
    node.get_gate('gen').gate_function(activation)


def sensor(netapi, node=None, datasource=None, **params):
    if datasource in netapi.world.get_available_datasources(netapi.uid):
        datasource_value = netapi.world.get_datasource(netapi.uid, datasource)
    else:
        datasource_value = netapi.get_modulator(datasource)
    node.activation = datasource_value
    node.get_gate('gen').gate_function(datasource_value)


def actor(netapi, node=None, datatarget=None, **params):
    if not netapi.world:
        return
    activation_to_set = node.get_slot("gen").activation
    if datatarget in netapi.world.get_available_datatargets(netapi.uid):
        netapi.world.add_to_datatarget(netapi.uid, datatarget, activation_to_set)
        feedback = netapi.world.get_datatarget_feedback(netapi.uid, datatarget)
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

def pipe(netapi, node=None, sheaf="default", **params):
    gen = 0.0
    por = 0.0
    ret = 0.0
    sub = 0.0
    sur = 0.0
    cat = 0.0
    exp = 0.0

    gen += node.get_slot("gen").get_activation(sheaf) * node.get_slot("sub").get_activation(sheaf)
    if abs(gen) < 0.1: gen = 0                                          # cut off gen loop at lower threshold

    if node.get_slot("por").get_activation(sheaf) == 0 and not node.get_slot("por").empty:
        gen = 0

    if gen == 0:
        gen += node.get_slot("sur").get_activation(sheaf)
        gen += node.get_slot("exp").get_activation(sheaf)

    # commented: trigger and pipes should be able to escape the [-1;1] cage on gen
    # if gen > 1: gen = 1
    # if gen < -1: gen = -1

    sub += max(node.get_slot("sur").get_activation(sheaf), 0)
    sub += node.get_slot("sub").get_activation(sheaf)
    sub += node.get_slot("cat").get_activation(sheaf)
    sub *= max(node.get_slot("por").get_activation(sheaf), 0) if not node.get_slot("por").empty else 1
    sub *= 0 if node.get_slot("gen").get_activation(sheaf) != 0 else 1
    if sub > 0: sub = 1
    if sub < 0: sub = -1

    sur += node.get_slot("sur").get_activation(sheaf)
    if sur == 0: sur += node.get_slot("sur").get_activation("default")      # no activation in our sheaf, maybe from sensors?
    if abs(node.get_slot("gen").get_activation(sheaf) * node.get_slot("sub").get_activation(sheaf)) > 0.2:               # cut off sur-reports from gen looping before the loop fades away
        sur += 1 if node.get_slot("gen").get_activation(sheaf) > 0 else -1
    sur += node.get_slot("exp").get_activation(sheaf)

    if node.get_slot("ret").get_activation(sheaf) < 0:
        sur = 0
    if node.get_slot("por").empty and not node.get_slot("ret").empty and sur > 0:
        sur = 0                                                             # first nodes in scripts can never report sur
    if node.get_slot("por").get_activation(sheaf) <= 0 and not node.get_slot("por").empty:
        sur = 0

    if node.get_slot('por').empty and node.get_slot('ret').empty:           # both empty
        classifierelements = 0
        if len(node.get_gate("sur").get_links()) == 1:
            surnode = node.get_gate("sur").get_links()[0].target_node
            if surnode.type == "Pipe":
                classifierelements = len(surnode.get_slot("sur").get_links())
        sur /= classifierelements if classifierelements > 1 else 1          # classifier case

    if sur > 1:
        sur = 1
    if sur < -1:
        sur = -1

    por += node.get_slot("sur").get_activation(sheaf)
    por += (0 if node.get_slot("gen").get_activation(sheaf) < 0.1 else 1) * \
           (1+node.get_slot("por").get_activation(sheaf))
    por *= node.get_slot("por").get_activation(sheaf) if not node.get_slot("por").empty else 1  # only por if por
    por *= node.get_slot("sub").get_activation(sheaf)                                           # only por if sub
    por += node.get_slot("por").get_activation(sheaf) if node.get_slot("sub").get_activation(sheaf) == 0 and node.get_slot("sur").get_activation(sheaf) == 0 else 0
    if por > 0: por = 1

    ret += node.get_slot("ret").get_activation(sheaf) if node.get_slot("sub").get_activation(sheaf) == 0 and node.get_slot("sur").get_activation(sheaf) == 0 else 0
    if node.get_slot("por").get_activation(sheaf) >= 0:
        ret -= node.get_slot("sub").get_activation(sheaf)
    if ret > 1:
        ret = 1

    cat = sub
    if cat == 0: cat += node.get_slot("cat").get_activation(sheaf)
    if cat < 0: cat = 0

    exp += node.get_slot("sur").get_activation(sheaf)
    exp += node.get_slot("exp").get_activation(sheaf)
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
    if cat > 0 and node.get_slot("sub").get_activation(sheaf) > 0:     # cats will be checked in their own sheaf
        node.get_gate("cat").open_sheaf(cat, sheaf)
        node.get_gate("cat").gate_function(0, sheaf)
    else:
        node.get_gate("cat").gate_function(cat, sheaf)


def trigger(netapi, node=None, sheaf="default", **params):
    """
    Trigger nodes, when activated on their sub slot, create a single burst of activation and wait for
    activation on their sur slot that equals or exceeds a configured value.
    If the value does not show up after a configured number of timeout steps, trigger nodes fail,
    else, they succeed.
    """

    gen = 0
    sub = 0
    sur = 0

    if abs(node.get_slot('gen').activation) != 0:
        sur = node.get_slot('gen').activation
    else:
        waitfrom = node.get_state("waitfrom") or -1

        condition = node.get_parameter("condition") or "="
        try:
            timeout = int(node.get_parameter("timeout"))         # todo: use emo_resolution
        except TypeError or ValueError:
            timeout = 10
        try:
            response = float(node.get_parameter("response"))
        except TypeError or ValueError:
            response = 1

        if node.get_slot('sub').activation > 0:
            currentstep = netapi.step

            success = (condition == "=" and node.get_slot('sur').activation == response) or \
                      (condition == ">" and node.get_slot('sur').activation > response)

            if waitfrom > 0:                       # waiting for results
                if success:
                    sur = 1
                    node.set_state("waitfrom", currentstep)
                elif currentstep > waitfrom + timeout or node.get_slot('sur').activation < 0:
                    sur = -1
            else:                                   # perform burst
                sub = 1
                node.set_state("waitfrom", currentstep)
                if success:
                    sur = 1

        else:

            if waitfrom > 0:
                node.set_state("waitfrom", -1)

            if node.get_slot('sur').activation:
                success = (condition == "=" and node.get_slot('sur').activation == response) or \
                          (condition == ">" and node.get_slot('sur').activation > response)
                if success:
                    sur = 1

    if sur < 0:
        # if trigger is failing, gen should also propagate failing
        gen = sur
    else:
        # otherwise, gen should be allowed to pass on the original sur-activation
        # and not be confined to {0;1}
        gen = node.get_slot('sur').activation + node.get_slot('gen').activation

    node.activation = gen

    node.get_gate("gen").gate_function(gen, sheaf)
    node.get_gate("sub").gate_function(sub, sheaf)
    node.get_gate("sur").gate_function(sur, sheaf)


def activator(netapi, node, **params):
    node.activation = node.get_slot("gen").activation
    netapi.get_nodespace(node.parent_nodespace).set_activator_value(node.get_parameter('type'), node.activation)
