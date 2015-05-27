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
        self.calculate_node_functions(nativemodules)    # then native modules, so API sees a deterministic state
        self.calculate_node_functions(everythingelse)   # then all the peasant nodes get calculated

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
        obsoletelinks = []
        decay_factor = nodenet.get_modulator('base_porret_decay_factor')
        for uid, node in nodes.items():
            if node.type in ['Concept', 'Script', 'Pipe']:
                confirmation = node.get_gate('gen').activation

                porgate = node.get_gate('por')
                pordecay = porgate.get_parameter('decay') * decay_factor
                if pordecay is not None and pordecay > 0:
                    for link in porgate.get_links():
                        linkdelta = - pordecay

                        if link.weight > 0:
                            link.set_weight(max(link.weight + linkdelta, 0))
                        if link.weight == 0:
                            obsoletelinks.append(link)
        left_boundaries = []
        for link in obsoletelinks:
            netapi.unlink(link.source_node, 'por', link.target_node, 'por')
            netapi.unlink(link.target_node, 'ret', link.source_node, 'ret')
            left_boundaries.append(link.source_node)

        archive_nodespace = None
        for n in netapi.get_nodespaces():
            if n.name == 'automatisms':
                archive_nodespace = n

        for node in left_boundaries:
            step = node
            old_schema_node = step.get_gate('sur').get_links()[0].target_node
            if not step.get_gate('ret').get_links():
                # delete single steps without por/ret linkage (and their subsur children)
                nodes_to_delete = [step]
                nodes_to_delete.extend([l.target_node for l in step.get_gate('sub').get_links()])
                for n in nodes_to_delete:
                    netapi.delete_node(n)
            else:
                # create new schema nodes for fragments
                new_schema_node = netapi.create_node(old_schema_node.type, archive_nodespace.uid, old_schema_node.name + ' Fragment')
                while True:
                    netapi.unlink(old_schema_node, target_node=step)
                    netapi.unlink(step, target_node=old_schema_node)
                    netapi.link_with_reciprocal(new_schema_node, step, 'subsur')
                    step.parent_nodespace = archive_nodespace.uid
                    for l in step.get_gate('sub').get_links():
                        l.target_node.parent_nodespace = archive_nodespace.uid
                    if step.get_gate('ret').get_links():
                        step = step.get_gate('ret').get_links()[0].target_node
                    else:
                        break
            if len(old_schema_node.get_slot('sur').get_links()) <= 1:
                # schema node has 1 child or less, prune as whole
                delete_nodes = []
                if not old_schema_node.get_slot('gen').get_links():
                    delete_nodes.append(old_schema_node)
                for l1 in old_schema_node.get_slot('sur').get_links():
                    for l2 in l1.source_node.get_slot('sur').get_links():
                        delete_nodes.append(l2.source_node)
                    delete_nodes.append(l1.source_node)
                for node in delete_nodes:
                    netapi.delete_node(node)