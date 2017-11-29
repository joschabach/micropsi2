
"""
Flowmodules are a special kind of native modules, with the following properties:

* They have inputs and outputs, in addition to a sub-slot and a sur-gate
* They can be connected to create a flow between Flowmodules
* Flow-terminals are datasources, datatargets and Flow Endndoes
* Flow Endnodes are Flowmodules that have at least one link ending at their sub-slot
* If the sub-slot of an Endnode X receives activation, everything between X and other Flow-terminals (a Flowgraph) is calculated within one nodenet step.
* All Flowmodules that are part of an active Flowgraph show this via activation on their sur-gate

* Flow modules can currently have to kinds of implementation: Theano or python
** Theano-implemented Flowmodules have a buildfunction, that returns a symbolic theano-expression
** Python-implemented Flowmodules hav a runfunction, that can do anything it wants.

* Flowmodules delivering output might decide, that a certain output needs more data, and can choose to return None for that output
  (the total number of return values still must match the number of outputs they define)
  If a Flowgraph receives None as one of its inputs, it is prevented from running, even if it is requested.



"""

from micropsi_core.nodenet.flowmodule import FlowModule
from micropsi_core.nodenet.theano_engine.theano_node import TheanoNode


class TheanoFlowModule(FlowModule, TheanoNode):

    def __init__(self, nodenet, partition, parent_uid, uid, numerictype, parameters={}, inputmap={}, outputmap={}, is_copy_of=False, initialized=False):
        super().__init__(nodenet, partition=partition, parent_uid=parent_uid, uid=uid, numerictype=numerictype, parameters=parameters, inputmap=inputmap, outputmap=outputmap, is_copy_of=is_copy_of, initialized=initialized)
