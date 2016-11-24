
"""
Flowmodule implementation
"""

from micropsi_core.nodenet.theano_engine.theano_node import TheanoNode


class FlowModule(TheanoNode):

    @property
    def inputs(self):
        return self.definition['inputs']

    @property
    def outputs(self):
        return self.definition['outputs']

    def __init__(self, nodenet, partition, parent_uid, uid, type, parameters={}, inputmap={}, outputmap={}, is_copy_of=False):
        super().__init__(nodenet, partition, parent_uid, uid, type, parameters=parameters)
        self.definition = nodenet.native_module_definitions[self.type]
        self.implementation = self.definition['implementation']
        self.outexpression = None
        self.outputmap = {}
        self.inputmap = {}
        self.is_copy_of = is_copy_of
        self._load_functions()
        self.is_part_of_active_graph = False
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

    def get_flow_data(self, *args, **kwargs):
        inmap = {}
        outmap = {}
        data = {}
        for name in self.inputmap:
            inmap[name] = list(self.inputmap[name])
        for name in self.outputmap:
            outmap[name] = []
            for link in self.outputmap[name]:
                outmap[name].append(list(link))
        data = {
            'flow_module': True,
            'inputmap': inmap,
            'outputmap': outmap,
            'is_copy_of': self.is_copy_of
        }
        return data

    def is_output_connected(self):
        if len(self.outputs) == 0:
            return False
        else:
            return len(set.union(*list(self.outputmap.values()))) > 0

    def is_output_node(self):
        return len(self.get_slot('sub').get_links()) > 0

    def is_input_node(self):
        if len(self.inputs) == 0:
            return True
        else:
            return ('worldadapter', 'datasources') in self.inputmap.values()

    def is_requested(self):
        return self.get_slot_activations(slot_type='sub') > 0

    def set_theta(self, name, val):
        if self.is_copy_of:
            raise RuntimeError("Shallow copies can not set shared variables")
        self._nodenet.set_theta(self.uid, name, val)

    def get_theta(self, name):
        if self.is_copy_of:
            return self._nodenet.get_theta(self.is_copy_of, name)
        return self._nodenet.get_theta(self.uid, name)

    def set_parameter(self, name, val):
        if self.is_copy_of:
            raise RuntimeError("Shallow copies can not set parameters")
        super().set_parameter(name, val)

    def get_parameter(self, name):
        if self.is_copy_of:
            return self._nodenet.get_node(self.is_copy_of).get_parameter(name)
        return super().get_parameter(name)

    def clone_parameters(self):
        if self.is_copy_of:
            return self._nodenet.get_node(self.is_copy_of).clone_parameters()
        return super().clone_parameters()

    def set_input(self, input_name, source_uid, source_output):
        if input_name not in self.inputs:
            raise NameError("Unknown input %s" % input_name)
        self.dependencies.add(source_uid)
        if self.inputmap.get(input_name):
            raise RuntimeError("This input is already connected")
        self.inputmap[input_name] = (source_uid, source_output)

    def unset_input(self, input_name, source_uid, source_output):
        remove = True
        if input_name not in self.inputs:
            raise NameError("Unknown input %s" % input_name)
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
        self.get_gate('sur').gate_function(1 if self.is_part_of_active_graph else 0)

    def build(self, *inputs):
        if not self.__initialized and not self.is_copy_of:
            self._initfunction(self._nodenet.netapi, self, self.parameters)
            self.__initialized = True

        if self.implementation == 'theano':
            outexpression = self._buildfunction(*inputs, netapi=self._nodenet.netapi, node=self, parameters=self.clone_parameters())
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
            self._flowfunction = getattr(module, self.definition['run_function_name'])
            self.line_number = inspect.getsourcelines(self._flowfunction)[1]
