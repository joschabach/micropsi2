
"""

"""

import theano
from micropsi_core.nodenet.theano_engine.theano_node import TheanoNode
from theano import tensor as T


def compilefunc(nodenet, nodes):
    flow_in = T.vector('inputs', dtype=nodenet.theanofloatX)
    flow_out = T.vector('outputs', dtype=nodenet.theanofloatX)
    uids = [n.uid for n in nodes]
    try:
        inputmap = dict((k.uid, {}) for k in nodes)
        for module in nodes:
            for name in module.inputmap:
                if ('worldadapter', 'datasources') in module.inputmap[name]:
                    if name in inputmap[module.uid]:
                        inputmap[module.uid][name] += flow_in
                    else:
                        inputmap[module.uid][name] = flow_in
            out = module.flowfunction(**inputmap[module.uid])
            if len(module.outputs) == 1:
                out = [out]
            for idx, name in enumerate(module.outputs):
                if name in module.outputmap and len(module.outputmap[name]):
                    for target_uid, target_name in module.outputmap[name]:
                        if target_uid not in uids:
                            # endnode
                            flow_out = out[idx]
                        else:
                            if target_name in inputmap[target_uid]:
                                inputmap[target_uid][target_name] += out[idx]
                            else:
                                inputmap[target_uid][target_name] = out[idx]
                else:
                    flow_out = out[idx]
        return theano.function([flow_in], [flow_out], on_unused_input='warn')
    except Exception as e:
        nodenet.logger.warning("Error compiling graph function:  %s" % str(e))
        return lambda x: None


class FlowModule(TheanoNode):

    @property
    def inputs(self):
        return self.definition['inputs']

    @property
    def outputs(self):
        return self.definition['outputs']

    def __init__(self, nodenet, partition, parent_uid, uid, type, parameters={}, inputmap={}, outputmap={}):
        super().__init__(nodenet, partition, parent_uid, uid, type, parameters=parameters)
        self.definition = nodenet.native_module_definitions[self.type]
        self._load_flowfunction()
        self.outputmap = {}
        self.inputmap = {}
        for i in self.definition['outputs']:
            self.outputmap[i] = set()
        for i in self.definition['inputs']:
            self.inputmap[i] = set()
        self.dependencies = set()

        for name in inputmap:
            for link in inputmap[name]:
                self.inputmap[name].add(tuple(link))
        for name in outputmap:
            for link in outputmap[name]:
                self.outputmap[name].add(tuple(link))

    def get_data(self, *args, **kwargs):
        inmap = {}
        outmap = {}
        for name in self.inputmap:
            inmap[name] = []
            for link in self.inputmap[name]:
                inmap[name].append(list(link))
        for name in self.outputmap:
            outmap[name] = []
            for link in self.outputmap[name]:
                outmap[name].append(list(link))
        data = super().get_data(*args, **kwargs)
        data.update({
            'uid': self.uid,
            'flow_module': True,
            'inputmap': inmap,
            'outputmap': outmap
        })
        return data

    def is_output_connected(self):
        return len(set.intersection(*list(self.outputmap.values()))) > 0

    def is_requested(self):
        return self.get_slot_activations(slot_type='sub') > 0

    def set_input(self, input_name, source_uid, source_output):
        self.dependencies.add(source_uid)
        self.inputmap[input_name].add((source_uid, source_output))

    def unset_input(self, input_name, source_uid, source_output):
        remove = True
        self.inputmap[input_name].discard((source_uid, source_output))
        for name in self.inputmap:
            for link in self.inputmap[name]:
                if link[0] == source_uid:
                    remove = False
        if remove:
            self.dependencies.discard(source_uid)

    def set_output(self, output_name, target_uid, target_input):
        self.outputmap[output_name].add((target_uid, target_input))

    def unset_output(self, output_name, target_uid, target_input):
        self.outputmap[output_name].discard((target_uid, target_input))

    def node_function(self):
        pass

    def _load_flowfunction(self):
        from importlib.machinery import SourceFileLoader
        import inspect

        sourcefile = self.definition['path']
        funcname = self.definition['flowfunction_name']
        module = SourceFileLoader("nodefunctions", sourcefile).load_module()
        self.flowfunction = getattr(module, funcname)
        self.line_number = inspect.getsourcelines(self.flowfunction)[1]
