
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

def label(nodenet, node, **params):
    node.activation = sum([node.slots[slot].activation for slot in node.slots])
    for type, gate in node.gates.items():
        gate.gate_function(node.get_slot("gen").activation)

def event(nodenet, node, **params):
    node.activation = sum([node.slots[slot].activation for slot in node.slots])
    for type, gate in node.gates.items():
        gate.gate_function(node.get_slot("gen").activation)

def activator(nodenet, node, **params):
    node.activation = node.get_slot("gen").activation
    nodenet.nodespaces[node.parent_nodespace].activators[node.parameters["type"]] = node.activation
