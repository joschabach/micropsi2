

def sensor(nodenet, node=None, datasource=None, **params):
    node.gates["gen"].gate_function(nodenet.world.get_datasource(nodenet.uid, datasource))

def actor(nodenet, node=None, datatarget=None, **params):
    node.nodenet.world.set_datatarget(nodenet.uid, datatarget, node.activation)

def concept(nodenet, node=None, **params):
    for type, gate in node.gates.items():
        gate.gate_function(node.activation)

def label(nodenet, node, **params):
    for type, gate in node.gates.items():
        gate.gate_function(node.activation)

def event(nodenet, node, **params):
    for type, gate in node.gates.items():
        gate.gate_function(node.activation)

def activator(nodenet, node, **params):
    nodenet.nodespaces[node.parent_nodespace].activators[node.parameters["type"]] = node.activation