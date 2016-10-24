
"""

"""

import theano
from micropsi_core.nodenet.theano_engine.theano_node import TheanoNode
from theano import tensor as T


class FlowGraph(object):

    def __init__(self, nodenet, nodes=[]):
        self.nodenet = nodenet
        self.members = set()
        self.path = []
        self._instances = {}
        self.function = None
        self.endnode_uid = None
        self.write_datatargets = False
        self.flow_in = T.vector('inputs', dtype=nodenet.theanofloatX)
        self.flow_out = T.vector('outputs', dtype=nodenet.theanofloatX)
        for n in nodes:
            self.add(n)

    def get_data(self):
        return {
            'members': list(self.members)
        }

    def add(self, flownode):
        if flownode.uid not in self.members:
            self.members.add(flownode.uid)
            self._instances[flownode.uid] = flownode
            if not flownode.is_output_connected():
                self.endnode_uid = flownode.uid

    def update(self):
        self._instances = dict((uid, self.nodenet.get_node(uid)) for uid in self.members)
        self.set_path()
        self.compile()

    def is_requested(self):
        result = False
        if self.endnode_uid is not None:
            return self._instances[self.endnode_uid].is_requested()
        return result

    def set_path(self):
        self.path = []
        for uid, item in self._instances.items():
            if len(item.dependencies & self.members) == 0:
                self.path = [uid]

        for uid, item in self._instances.items():
            if uid in self.path:
                continue
            idxs = []
            for dep in item.dependencies:
                try:
                    idxs.append(self.path.index(dep))
                except:
                    pass
            idx = (max(idxs) + 1) if len(idxs) else len(self.path)
            self.path.insert(idx, uid)

    def compile(self):
        try:
            self.endnode_uid = None
            self.write_datatargets = False
            inputmap = dict((k, {}) for k in self.path)
            for uid in self.path:
                module = self._instances[uid]
                for name in module.inputmap:
                    if ('worldadapter', 'datasources') in module.inputmap[name]:
                        if name in inputmap[module.uid]:
                            inputmap[module.uid][name] += self.flow_in
                        else:
                            inputmap[module.uid][name] = self.flow_in
                out = module.flowfunction(**inputmap[uid])
                if len(module.outputs) == 1:
                    out = [out]
                for idx, name in enumerate(module.outputs):
                    if name in module.outputmap:
                        for target_uid, target_name in module.outputmap[name]:
                            if target_uid not in self.members:
                                # endnode
                                self.endnode_uid = uid
                                if target_uid == "worldadapter":
                                    self.write_datatargets = True
                                self.flow_out = out[idx]
                            else:
                                if target_name in inputmap[target_uid]:
                                    inputmap[target_uid][target_name] += out[idx]
                                else:
                                    inputmap[target_uid][target_name] = out[idx]
                    else:
                        # non-connected output
                        self.endnode_uid = uid
                        self.flow_out = out[idx]
            self.function = theano.function([self.flow_in], [self.flow_out], on_unused_input='warn')
        except Exception as e:
            self.nodenet.logger.error("Error compiling graph function:  %s" % str(e))
            self.function = lambda x: self.flow_out
            if self.endnode_uid is None:
                for uid, item in self._instances.items():
                    if not item.is_output_connected() or ('worldadapter', 'datatargets') in set.intersection(*list(item.outputmap.values())):
                        self.endnode_uid = uid


class FlowModule(TheanoNode):

    @property
    def inputs(self):
        return self.definition['inputs']

    @property
    def outputs(self):
        return self.definition['outputs']

    def __init__(self, nodenet, partition, parent_uid, uid, type, parameters={}):
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

    def parse_data(self, data):
        for name in data['inputmap']:
            for link in data['inputmap'][name]:
                self.inputmap[name].add(tuple(link))
        for name in data['outputmap']:
            for link in data['outputmap'][name]:
                self.outputmap[name].add(tuple(link))

    def get_data(self):
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
        data = super().get_data()
        data.update({
            'uid': self.uid,
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

    def node_function(self, *args, **kwargs):
        pass

    def _load_flowfunction(self):
        from importlib.machinery import SourceFileLoader
        import inspect

        sourcefile = self.definition['path']
        funcname = self.definition['flowfunction_name']
        module = SourceFileLoader("nodefunctions", sourcefile).load_module()
        self.flowfunction = getattr(module, funcname)
        self.line_number = inspect.getsourcelines(self.flowfunction)[1]
