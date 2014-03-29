
def register(nodenet, node=None, **params):
    for type, gate in node.gates.items():
        gate.gate_function(node.get_slot("gen").activation)

def sensor(nodenet, node=None, datasource=None, **params):
    node.gates["gen"].gate_function(nodenet.world.get_datasource(nodenet.uid, datasource))

def actor(nodenet, node=None, datatarget=None, **params):
    node.nodenet.world.set_datatarget(nodenet.uid, datatarget, node.get_slot("gen").activation)
    node.activation = node.get_slot("gen").activation

def concept(nodenet, node=None, **params):
    for type, gate in node.gates.items():
        gate.gate_function(node.get_slot("gen").activation)

def pipe(nodenet, node=None, **params):
    gen = 0.0
    por = 0.0
    ret = 0.0
    sub = 0.0
    sur = 0.0

    sub += node.get_slot("gen").activation      # push gen activation down: someone wants to check this concept
                                                # it's debatable whether such a request should only be allowed on the
                                                # sub channel itself or whether the gen alternative is cleaner because
                                                # it does not require a sub link that has no sur correlate.
    sub += node.get_slot("sub").activation      # sub is pushed down: the concept we're part of is requested to be
                                                # checked
    sub += node.get_slot("por").activation      # por is pushed down: our predecessor is confirmed and wants us to be
                                                # next
    if sub > 1: sub = 1                         # more than one condition met, normalize to 1 for now
    if sub < 0: sub = 0                         # negative sub has no semantics and is messy, normalize to 0 for now

    por += node.get_slot("sur").activation      # send confirmation from our parts onwards to our successors

    ret += node.get_slot("sur").activation      # send confirmation from pir parts backwards, cancelling the inhibition
                                                # we're normally sending on ret (see normalization)
    ret += node.get_slot("ret").activation      # propagate ret back-and-upwards for confirmation
    if ret < 1: ret = -1                        # normalize to inhibition if we're not positively confirmed yet
    if ret > 1: ret = 1                         # normalize to 1 if more than one condition met

    sur += (node.get_slot("sub").activation *   # sur is activated if we're being requested and a sensor is
            node.get_slot("gen").activation)    # gen-connected and active. Again, it's debatable whether sensors
                                                # should be gen-connected or non-reciprocal sur-links would be
                                                # preferable
    sur += (node.get_slot("sub").activation *   # sur is activated if we're being requested and a sensor or subscript
            node.get_slot("sur").activation)    # is sur-connected and active.
    sur += node.get_slot("ret").activation      # sur is activated if ret is active: propagate success upwards
    if sur < -1: sur = -1                       # normalize negative sur to -1
    if sur > 1: sur = 1                         # normalize positive sur to 1

    gen += node.get_slot("sur").activation      # gen is activated if confirmation is being propagated from below
                                                # if we decide to go for non-reciprocal sur, this can be dropped
    gen += (node.get_slot("sub").activation *   # if requested from above, we allow gen-loops to keep state after
            node.get_slot("gen").activation)    # a sensor has activated us once
    if gen < 0: gen = 0                         # negative gen undefined for now

    node.get_gate("gen").gate_function(gen)
    node.get_gate("por").gate_function(por)
    node.get_gate("ret").gate_function(ret)
    node.get_gate("sub").gate_function(sub)
    node.get_gate("sur").gate_function(sur)

def label(nodenet, node, **params):
    for type, gate in node.gates.items():
        gate.gate_function(node.get_slot("gen").activation)

def event(nodenet, node, **params):
    for type, gate in node.gates.items():
        gate.gate_function(node.get_slot("gen").activation)

def activator(nodenet, node, **params):
    nodenet.nodespaces[node.parent_nodespace].activators[node.parameters["type"]] = node.activation