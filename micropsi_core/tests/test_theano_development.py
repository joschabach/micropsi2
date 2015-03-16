__author__ = 'rvuine'

from micropsi_core.nodenet import *
from micropsi_core.nodenet.node import STANDARD_NODETYPES
from micropsi_core.nodenet.theano_engine.theano_nodenet import *

nodenet = TheanoNodenet('/tmp/theanotest.json',
                    name="theanotest", worldadapter=None,
                    world=None, owner=None, uid="theanotest",
                    nodetypes=STANDARD_NODETYPES, native_modules={})

uid = nodenet.create_node("Register", "Root", None)
node = nodenet.get_node(uid)
print(node.uid)

uid = nodenet.create_node("Register", "Root", None)
node = nodenet.get_node(uid)
print(node.uid)

nodenet.delete_node(0)

uid = nodenet.create_node("Register", "Root", None)
node = nodenet.get_node(uid)
print(node.uid)

uid = nodenet.create_node("Register", "Root", None)
node = nodenet.get_node(uid)
print(node.uid)

node.activation = 0.4

print(node.activation)

gate = node.get_gate("gen")

print(gate.activation)

nodenet.create_link(1, "gen", 0, "por", 0.6)

#print(nodenet.w_matrix[0])

node1 = nodenet.get_node(1)
gengate = node1.get_gate("gen")

link = gengate.get_links()[0]

print(link.uid + " "+ str(link.weight))

node = nodenet.get_node(1)
print(node.get_gate("gen").activation)


nodenet.step()

node = nodenet.get_node(1)
print(node.get_gate("gen").activation)
