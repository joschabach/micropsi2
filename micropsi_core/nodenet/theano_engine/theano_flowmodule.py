
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
from theano.tensor.var import TensorVariable


class TheanoFlowModule(FlowModule, TheanoNode):

    def __init__(self, nodenet, partition, parent_uid, uid, numerictype, parameters={}, inputmap={}, outputmap={}, is_copy_of=False, initialized=False):
        super().__init__(nodenet, partition=partition, parent_uid=parent_uid, uid=uid, numerictype=numerictype, parameters=parameters, inputmap=inputmap, outputmap=outputmap, is_copy_of=is_copy_of, initialized=initialized)

    def build(self, *inputs):
        """ Builds the node, calls the initfunction if needed, and returns an outexpression.
        This can be either a symbolic theano expression or a python function """
        if self.is_copy_of:
            self._nodenet.get_node(self.is_copy_of).ensure_initialized()
        self.ensure_initialized()
        if self.implementation == 'theano':
            outexpression = self._buildfunction(*inputs, netapi=self._nodenet.netapi, node=self, parameters=self.clone_parameters())

            # add names to the theano expressions returned by the build function.
            # names are added if we received a single expression OR exactly one per documented output,
            # but not for lists of expressions (which may have arbitrary many items).
            name_outexs = outexpression
            if len(self.outputs) == 1:
                name_outexs = [outexpression]
            for out_idx, subexpression in enumerate(name_outexs):
                if isinstance(subexpression, TensorVariable):
                    existing_name = "({})".format(subexpression.name) if subexpression.name is not None else ""
                    subexpression.name = "{}_{}{}".format(self.uid, self.outputs[out_idx], existing_name)

        elif self.implementation == 'python':
            outexpression = self._flowfunction

        else:
            raise ValueError("Unknown flow-implementation: %s" % self.implementation)

        self.outexpression = outexpression

        return outexpression
