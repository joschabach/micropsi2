

def sensor(nodenet, node=None, datasource=None, **params):
    node.gates["gen"].gate_function(nodenet.world.get_datasource(nodenet.uid, datasource))

def actor(nodenet, node=None, datatarget=None, **params):
    node.nodenet.world.set_datatarget(nodenet.uid, datatarget, node.activation)

def concept(nodenet, node=None, **params):
    for type, gate in node.gates.items():
        gate.gate_function(node.activation)

def pipe(nodenet, node=None, **params):
    gen = 0.0
    por = 0.0
    ret = 0.0
    sub = 0.0
    sur = 0.0

def label(nodenet, node, **params):
    for type, gate in node.gates.items():
        gate.gate_function(node.activation)

def event(nodenet, node, **params):
    for type, gate in node.gates.items():
        gate.gate_function(node.activation)

def activator(nodenet, node, **params):
    nodenet.nodespaces[node.parent_nodespace].activators[node.parameters["type"]] = node.activation