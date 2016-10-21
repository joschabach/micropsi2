
"""

"""

import theano
from micropsi_core.nodenet.theano_engine.theano_definitions import node_from_id
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

    def add(self, flownode):
        if flownode.uid not in self.members:
            self.members.add(flownode.uid)
            self._instances[flownode.uid] = flownode
            if flownode.outputmap == {}:
                self.endnode_uid = flownode.uid

    def update(self):
        self._instances = dict((uid, self.nodenet.flow_modules[uid]) for uid in self.members)
        self.set_path()
        self.compile()

    def is_requested(self):
        partition = self.nodenet.get_partition(self.endnode_uid)
        _a = partition.a.get_value(borrow=True)
        _id = node_from_id(self.endnode_uid)
        idx = partition.allocated_node_offsets[_id]
        return _a[idx] > 0

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
            self.write_datatargets = False
            inputmap = dict((k, {}) for k in self.path)
            for uid in self.path:
                module = self._instances[uid]
                if 'worldadapter' in module.dependencies:
                    for name in module.inputmap:
                        if module.inputmap[name] == ('worldadapter', 'datasources'):
                            inputmap[module.uid][name] = self.flow_in
                out = module.flowfunction(**inputmap[uid])
                if len(module.outputs) == 1:
                    out = [out]
                for idx, name in enumerate(module.outputs):
                    if name in module.outputmap:
                        target_uid, target_name = module.outputmap[name]
                        if target_uid not in self.members:
                            # endnode
                            self.endnode_uid = uid
                            if target_uid == "worldadapter":
                                self.write_datatargets = True
                            self.flow_out = out[idx]
                        else:
                            inputmap[target_uid][target_name] = out[idx]
                    else:
                        # non-connected output
                        self.flow_out = out[idx]
            self.function = theano.function([self.flow_in], [self.flow_out], on_unused_input='warn')
        except Exception as e:
            self.nodenet.logger.error("Error compiling graph function:  %s" % str(e))
            self.function = lambda x: self.flow_out


class FlowModule(object):

    @property
    def inputs(self):
        return self.definition['inputs']

    @property
    def outputs(self):
        return self.definition['outputs']

    @property
    def name(self):
        return self.nodenet.names.get(self.uid, self.uid)

    def __init__(self, uid, nodenet, nodespace_uid, flowtype, definition):
        self.uid = uid
        self.nodenet = nodenet
        self.nodespace_uid = nodespace_uid
        self.flowtype = flowtype
        self.definition = definition
        self._load_flowfunction()
        self.flowlinks = {}
        for i in self.definition['outputs']:
            self.flowlinks[i] = {}
        self.dependencies = set()
        self.outputmap = {}
        self.inputmap = {}

    def get_data(self):
        return {
            'uid': self.uid,
            'nodespace_uid': self.nodespace_uid,
            'flowtype': self.flowtype,
            'input_map': self.input_map,
            'output_map': self.output_map
        }

    def set_input(self, input_name, source_uid, source_output):
        self.dependencies.add(source_uid)
        self.inputmap[input_name] = (source_uid, source_output)

    def unset_input(self, input_name, source_uid, source_output):
        del self.inputmap[input_name]
        remove = True
        for name in list(self.inputmap.keys()):
            if self.inputmap[name][0] == source_uid:
                remove = False
        if remove:
            self.dependencies.discard(source_uid)

    def set_output(self, output_name, target_uid, target_input):
        self.outputmap[output_name] = (target_uid, target_input)

    def unset_output(self, output_name, target_uid, target_input):
        del self.outputmap[output_name]

    def _load_flowfunction(self):
        from importlib.machinery import SourceFileLoader
        import inspect

        sourcefile = self.definition['path']
        funcname = self.definition['flowfunction_name']
        module = SourceFileLoader("nodefunctions", sourcefile).load_module()
        self.flowfunction = getattr(module, funcname)
        self.line_number = inspect.getsourcelines(self.flowfunction)[1]

    def __repr__(self):
        return "<Flowmodule %s \"%s\" (%s)>" % (self.flowtype, self.name, self.uid)

