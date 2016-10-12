
"""

"""


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

    def set_output(self, output_name, target_uid, target_input):
        self.outputmap[output_name] = (target_uid, target_input)

    def _load_flowfunction(self):   
        from importlib.machinery import SourceFileLoader
        import inspect

        sourcefile = self.definition['path']
        funcname = self.definition['flowfunction_name']
        module = SourceFileLoader("nodefunctions", sourcefile).load_module()
        self.flowfunction = getattr(module, funcname)
        self.line_number = inspect.getsourcelines(self.flowfunction)[1]
