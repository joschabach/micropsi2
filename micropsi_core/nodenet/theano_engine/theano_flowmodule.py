
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
            for name in module.inputs:
                if name not in inputmap[module.uid]:
                    inputmap[module.uid][name] = flow_in
                else:
                    print("Input %s of node %s has multiple incoming values" % (name, module.name))
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
                            if target_name not in inputmap[target_uid]:
                                inputmap[target_uid][target_name] = out[idx]
                            else:
                                print("Input %s of node %s has multiple incoming values" % (name, module.name))
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
        self.implementation = self.definition['implementation']
        self.outexpression = None
        self.outputmap = {}
        self.inputmap = {}
        self._load_functions()
        for i in self.definition['inputs']:
            self.inputmap[i] = tuple()
        for i in self.definition['outputs']:
            self.outputmap[i] = set()
        self.dependencies = set()

        for name in inputmap:
            self.inputmap[name] = tuple(inputmap[name])
        for name in outputmap:
            for link in outputmap[name]:
                self.outputmap[name].add(tuple(link))

    def get_data(self, *args, **kwargs):
        inmap = {}
        outmap = {}
        for name in self.inputmap:
            inmap[name] = list(self.inputmap[name])
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
        if self.inputmap.get(input_name):
            raise RuntimeError("This input is already connected")
        self.inputmap[input_name] = (source_uid, source_output)

    def unset_input(self, input_name, source_uid, source_output):
        remove = True
        self.inputmap[input_name] = tuple()
        for name in self.inputmap:
            if self.inputmap[name] and self.inputmap[name][0] == source_uid:
                remove = False
        if remove:
            self.dependencies.discard(source_uid)

    def set_output(self, output_name, target_uid, target_input):
        self.outputmap[output_name].add((target_uid, target_input))

    def unset_output(self, output_name, target_uid, target_input):
        self.outputmap[output_name].discard((target_uid, target_input))

    def node_function(self):
        pass

    def build(self, *inputs):
        if not self.__initialized:
            self._initfunction(self._nodenet.netapi, self, self.parameters)
            self.__initialized = True

        if self.implementation == 'theano':
            outexpression = self._buildfunction(*inputs, netapi=self._nodenet.netapi, node=self, parameters=self.parameters)
        elif self.implementation == 'python':
            outexpression = self._flowfunction

        store = True
        if store:
            self.outexpression = outexpression

        return outexpression

    def _load_functions(self):
        from importlib.machinery import SourceFileLoader
        import inspect

        sourcefile = self.definition['path']
        module = SourceFileLoader("nodefunctions", sourcefile).load_module()

        if self.definition.get('init_function_name'):
            self._initfunction = getattr(module, self.definition['init_function_name'])
            self.__initialized = False
        else:
            self._initfunction = lambda x, y, z: None
            self.__initialized = True

        if self.implementation == 'theano':
            self._buildfunction = getattr(module, self.definition['build_function_name'])
            self.line_number = inspect.getsourcelines(self._buildfunction)[1]
        elif self.implementation == 'python':
            self._flowfunction = getattr(module, self.definition['flow_function_name'])
            self.line_number = inspect.getsourcelines(self._flowfunction)[1]
