__author__ = 'rvuine'

from micropsi_core.nodenet.stepoperators import StepOperator, Propagate, Calculate


class DictPropagate(Propagate):
    """
    The default dict implementation of the Propagate operator.
    """
    def execute(self, nodenet, nodes, netapi):
        """ propagate activation from gates to slots via their links.
            Arguments:
                nodes: the dict of nodes to consider
                limit_gatetypes (optional): a list of gatetypes to restrict the activation to links originating
                    from the given slottypes.
        """
        for uid, node in nodes.items():
            node.reset_slots()

        # propagate sheaf existence
        for uid, node in nodes.items():
            for gate_type in node.get_gate_types():
                gate = node.get_gate(gate_type)
                if gate.get_parameter('spreadsheaves'):
                    for sheaf in gate.sheaves:
                        for link in gate.get_links():
                            for slotname in link.target_node.get_slot_types():
                                if sheaf not in link.target_node.get_slot(slotname).sheaves and link.target_node.type != "Actor":
                                    link.target_node.get_slot(slotname).sheaves[sheaf] = dict(
                                        uid=gate.sheaves[sheaf]['uid'],
                                        name=gate.sheaves[sheaf]['name'],
                                        activation=0)

        # propagate activation
        for uid, node in nodes.items():
            for gate_type in node.get_gate_types():
                gate = node.get_gate(gate_type)
                for link in gate.get_links():
                    for sheaf in gate.sheaves:
                        targetsheaf = sheaf
                        if link.target_node.type != "Pipe":
                            targetsheaf = "default"

                        if targetsheaf in link.target_slot.sheaves:
                            link.target_slot.sheaves[targetsheaf]['activation'] += \
                                float(gate.sheaves[sheaf]['activation']) * float(link.weight)  # TODO: where's the string coming from?
                        elif sheaf.endswith(link.target_node.uid):
                            targetsheaf = sheaf[:-(len(link.target_node.uid) + 1)]
                            link.target_slot.sheaves[targetsheaf]['activation'] += \
                                float(gate.sheaves[sheaf]['activation']) * float(link.weight)  # TODO: where's the string coming from?


class DictCalculate(Calculate):
    """
    The default dict implementation of the Calculate operator.
    """
    def execute(self, nodenet, nodes, netapi):
        activators = nodenet.get_activators()
        nativemodules = nodenet.get_nativemodules()
        everythingelse = nodes
        for key in nativemodules:
            del everythingelse[key]

        self.calculate_node_functions(activators)       # activators go first
        self.calculate_node_functions(everythingelse)   # then all the peasant nodes get calculated
        self.calculate_node_functions(nativemodules)    # then native modules, so API sees a deterministic state

        for uid, node in activators.items():
            node.activation = nodenet.get_nodespace(node.parent_nodespace).get_activator_value(node.get_parameter('type'))

    def calculate_node_functions(self, nodes):
        for uid, node in nodes.copy().items():
            node.node_function()


class DictPORRETDecay(StepOperator):
    """
    Implementation of POR/RET link decaying
    """

    @property
    def priority(self):
        return 100

    def execute(self, nodenet, nodes, netapi):
        decay_factor = nodenet.get_modulator('base_porret_decay_factor')
        for uid, node in nodes.items():
            if node.type in ['Concept', 'Script', 'Pipe']:
                porgate = node.get_gate('por')
                pordecay = (1 - nodenet.get_modulator('por_ret_decay'))
                if decay_factor and pordecay is not None and pordecay > 0:
                    for link in porgate.get_links():
                        if link.weight > 0:
                            link._set_weight(max(link.weight * pordecay, 0))
