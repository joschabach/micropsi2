
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

def pipe(nodenet, node=None, sheaf="default", **params):
    gen = 0.0
    por = 0.0
    ret = 0.0
    sub = 0.0
    sur = 0.0

    gen += node.get_slot("sur").get_voted_activation(sheaf)
    if gen < 0: gen = 0
    if gen > 1: gen = 1

    sub += node.get_slot("gen").get_activation(sheaf)
    sub += node.get_slot("sur").get_activation(sheaf)
    sub += node.get_slot("sub").get_activation(sheaf)
    sub += node.get_slot("por").get_activation(sheaf)
    if sub > 0: sub = 1

    sur += node.get_slot("sur").get_voted_activation(sheaf)
    if sur < 0: sur = 0

    por += node.get_slot("sur").get_voted_activation(sheaf) * \
           (1+node.get_slot("por").get_activation(sheaf))
    por += node.get_slot("por").get_activation(sheaf) * \
           (1+node.get_slot("ret").get_activation(sheaf))
    if por < 1: por = -1
    if por > 1: por = 1

    ret += node.get_slot("ret").get_activation(sheaf)
    if ret == 0: ret = -1

    node.set_sheaf_activation(gen, sheaf)
    node.get_gate("gen").gate_function(gen, sheaf)
    node.get_gate("por").gate_function(por, sheaf)
    node.get_gate("ret").gate_function(ret, sheaf)
    node.get_gate("sur").gate_function(sur, sheaf)

    # example implementation for now: we open a new sheaf on positiv sub
    # (properties will be check in their own sheaf)
    if sub > 0:
        node.get_gate("sub").open_sheaf(sub, sheaf)
        node.get_gate("sub").gate_function(0, sheaf)
    else:
        node.get_gate("sub").gate_function(sub, sheaf)



def activator(nodenet, node, **params):
    node.activation = node.get_slot("gen").activation
    nodenet.nodespaces[node.parent_nodespace].activators[node.parameters["type"]] = node.activation
