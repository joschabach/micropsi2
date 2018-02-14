

class NetAPI(object):
    # Node Net API facade class for use from within the node net (in node functions)

    @property
    def uid(self):
        return self._nodenet.uid

    @property
    def step(self):
        """ The current step of the nodenet """
        return self._nodenet.current_step

    @property
    def is_running(self):
        return self._nodenet.is_active

    @property
    def worldadapter(self):
        """ The worldadapter instance """
        return self._nodenet.worldadapter_instance

    @property
    def logger(self):
        """ The nodenet logger """
        return self._nodenet.logger

    @property
    def statuslogger(self):
        return self._nodenet.statuslogger

    def __init__(self, nodenet):
        self._nodenet = nodenet

    def get_nodespace(self, uid):
        """
        Return the nodespace with the given uid
        """
        return self._nodenet.get_nodespace(uid)

    def get_nodespaces(self, parent=None):
        """
        Return a list of all nodespaces inside the given nodespace

        Params
        ------
            parent: uid (string), optional
                consider only nodespaces inside this nodespace
        """
        return [self._nodenet.get_nodespace(uid) for
                uid in self._nodenet.get_nodespace(parent).get_known_ids('nodespaces')]

    def get_node(self, uid):
        """
        Return the node with the given uid
        """
        return self._nodenet.get_node(uid)

    def get_nodes(self, nodespace=None, node_name_prefix=None, nodetype=None, sortby='ids'):
        """
        Search for nodes by name, nodespace and nodetype

        Params
        ------
            nodespace: uid (string), optional
                return only nodes from this nodespace

            node_name_prefix: string, optional
                return only nodes whose name starts with this string

            nodetype: string
                return only nodes of the given type

            sortby: string 'ids' or 'names'
                sort returned list of nodes by node.uid or by node.name

        Returns
        -------
            List of node instances

        """
        nodes = []
        all_ids = None
        if nodespace is not None:
            all_ids = self._nodenet.get_nodespace(nodespace).get_known_ids('nodes')
        else:
            all_ids = self._nodenet.get_node_uids()

        for node_uid in all_ids:
            node = self._nodenet.get_node(node_uid)
            if nodetype is not None and nodetype != node.type:
                continue
            if node_name_prefix is not None and not node.name.startswith(node_name_prefix):
                continue
            nodes.append(node)

        if sortby == 'ids':
            nodes = sorted(nodes, key=lambda node: node.uid)
        elif sortby == 'names':
            nodes = sorted(nodes, key=lambda node: node.name)
        else:
            raise ValueError("Unknown sortby value %s" % sortby)

        return nodes

    def get_nodes_in_gate_field(self, node, gate=None, no_links_to=None, nodespace=None):
        """
        Returns all nodes linked to a given node on the gate, excluding the ones that have
        links of any of the given types
        """
        nodes = []
        if gate is not None:
            gates = [gate]
        else:
            gates = self._nodenet.get_node(node.uid).get_gate_types()
        for gate in gates:
            for link in self._nodenet.get_node(node.uid).get_gate(gate).get_links():
                skip = False
                if no_links_to is not None:
                    for g in no_links_to:
                        g = link.target_node.get_gate(g)
                        if g and g.get_links():
                            skip = True
                            break
                if skip or (nodespace is not None and nodespace != link.target_node.parent_nodespace):
                    continue
                nodes.append(link.target_node)
        return nodes

    def get_nodes_in_slot_field(self, node, slot=None, no_links_to=None, nodespace=None):
        """
        Returns all nodes linking to a given node on the given slot, excluding the ones that
        have links of any of the given types
        """
        nodes = []
        if slot is not None:
            slots = [slot]
        else:
            slots = self._nodenet.get_node(node.uid).get_slot_types()
        for slot in slots:
            for link in self._nodenet.get_node(node.uid).get_slot(slot).get_links():
                skip = False
                if no_links_to is not None:
                    for g in no_links_to:
                        g = link.source_node.get_gate(g)
                        if g and g.get_links():
                            skip = True
                            break
                if skip or (nodespace is not None and nodespace != link.source_node.parent_nodespace):
                    continue
                nodes.append(link.source_node)
        return nodes

    def get_nodes_active(self, nodespace, type=None, min_activation=1, gate=None):
        """
        Returns all nodes with a min activation, of the given type, active at the given gate, or with node.activation
        """
        nodes = []
        for node in self.get_nodes(nodespace):
            if type is None or node.type == type:
                if gate is not None:
                    if gate in node.get_gate_types():
                        if node.get_gate(gate).activation >= min_activation:
                            nodes.append(node)
                else:
                    if node.activation >= min_activation:
                        nodes.append(node)
        return nodes

    def delete_node(self, node):
        """
        Delete a node and all links connected to it.

        Params
        ------
            node: node instance
        """
        self._nodenet.delete_node(node.uid)

    def delete_nodespace(self, nodespace):
        """
        Delete a nodesace and all nodes and nodespaces contained within, and all links connected to it.

        Params
        ------
            nodespace: nodespace instance
        """
        self._nodenet.delete_nodespace(nodespace.uid)

    def create_node(self, nodetype, nodespace=None, name=None, **parameters):
        """
        Creates a new node of the given type

        Params
        ------
            nodetype: string
                the `name` field of the nodetype definition

            nodespace: uid (string)
                the nodespace that the new node should belong to.

            name: string
                name of the new node

            **parameters:
                additional keyword arguments will set the value of the corresponding
                node parameter.

        Returns
        -------
            the new node instance

        """
        if name is None:
            name = ""   # TODO: empty names crash the client right now, but really shouldn't
        pos = [100, 100, 0]  # default so native modules will not be bothered with positions

        uid = self._nodenet.create_node(nodetype, nodespace, pos, name, parameters=parameters)
        entity = self._nodenet.get_node(uid)
        return entity

    def create_nodespace(self, parent_nodespace, name=None, options=None):
        """
        Create a new nodespace with the given name in the given parent_nodespace
        Options:
            new_partition - Whether or not to create a seperate partition for this nodespace
                            Attention: Experimental Feature, Sensors & Actuators only work in the root-partition
        """
        if name is None:
            name = ""   # TODO: empty names crash the client right now, but really shouldn't

        uid = self._nodenet.create_nodespace(parent_nodespace, name=name, options=options)
        entity = self._nodenet.get_nodespace(uid)
        return entity

    def link(self, source_node, source_gate, target_node, target_slot, weight=1):
        """
        Create a link between two nodes.

        If the link already exists, it will be updated
        with the given weight (or the default 1 if not given)

        Params
        ------
            source_node: node instance

            source_gate: gate type (string)
                selects from which of the source node's gates the link should originate

            target_node: node instance

            target_slot: slot type (string)
                selects in which of the target node's slots the link should land

            weight: numeric
                the link weight

        """
        self._nodenet.create_link(source_node.uid, source_gate, target_node.uid, target_slot, weight)

    def link_with_reciprocal(self, source_node, target_node, linktype, weight=1):
        """
        Creates two (reciprocal) links between two nodes, valid linktypes are subsur, porret, catexp and symref
        """
        target_slot_types = target_node.get_slot_types()
        source_slot_types = source_node.get_slot_types()
        if linktype == "subsur":
            subslot = "sub" if "sub" in target_slot_types else "gen"
            surslot = "sur" if "sur" in source_slot_types else "gen"
            self._nodenet.create_link(source_node.uid, "sub", target_node.uid, subslot, weight)
            self._nodenet.create_link(target_node.uid, "sur", source_node.uid, surslot, weight)
        elif linktype == "porret":
            porslot = "por" if "por" in target_slot_types else "gen"
            retslot = "ret" if "ret" in source_slot_types else "gen"
            self._nodenet.create_link(source_node.uid, "por", target_node.uid, porslot, weight)
            self._nodenet.create_link(target_node.uid, "ret", source_node.uid, retslot, weight)
        elif linktype == "catexp":
            catslot = "cat" if "cat" in target_slot_types else "gen"
            expslot = "exp" if "exp" in source_slot_types else "gen"
            self._nodenet.create_link(source_node.uid, "cat", target_node.uid, catslot, weight)
            self._nodenet.create_link(target_node.uid, "exp", source_node.uid, expslot, weight)
        elif linktype == "symref":
            symslot = "sym" if "sym" in target_slot_types else "gen"
            refslot = "ref" if "ref" in source_slot_types else "gen"
            self._nodenet.create_link(source_node.uid, "sym", target_node.uid, symslot, weight)
            self._nodenet.create_link(target_node.uid, "ref", source_node.uid, refslot, weight)

    def unlink(self, source_node, source_gate=None, target_node=None, target_slot=None):
        """
        Deletes a link, or links, originating from the given node

        Params
        ------
            source_node: node instance

            source_gate: gate type (string)
                origin of the to-be-deleted link on the source node

            target_node: node instance

            target_slot: slot type (string)
                endpoint of the to-be-deleted link on the target node

        """
        target_node_uid = target_node.uid if target_node is not None else None
        source_node.unlink(source_gate, target_node_uid, target_slot)

    def unlink_gate(self, node, gate_name, target_node_uid=None, target_slot_name=None):
        """
        Deletes all links from the given gate, optionally filtered by target_node_uid or target_slot_name
        """
        node.unlink(gate_name, target_node_uid=target_node_uid, slot_name=target_slot_name)

    def unlink_slot(self, node, slot_name, source_node_uid=None, source_gate_name=None):
        """
        Deletes all links to the given slot, optionally filtered by source_node_uid or source_gate_name
        """
        for l in node.get_slot(slot_name).get_links():
            if source_node_uid is None or l.source_node.uid == source_node_uid:
                if source_gate_name is None or l.source_gate.type == source_gate_name:
                    l.source_node.unlink(l.source_gate.type, target_node_uid=node.uid, slot_name=slot_name)

    def link_actuator(self, node, datatarget, weight=1, gate='sub', slot='sur'):
        """
        Links a node to an actuator. If no actuator exists in the node's nodespace for the given datatarget,
        a new actuator will be created, otherwise the first actuator found will be used
        """
        actuator = None
        for uid, candidate in self._nodenet.get_actuators(node.parent_nodespace).items():
            if candidate.get_parameter('datatarget') == datatarget:
                actuator = candidate
        if actuator is None:
            actuator = self.create_node("Actuator", node.parent_nodespace, datatarget)
            actuator.set_parameter('datatarget', datatarget)

        self.link(node, gate, actuator, 'gen', weight)
        # self.link(actuator, 'gen', node, slot)

    def link_sensor(self, node, datasource, slot='sur', weight=1):
        """
        Links a node to a sensor. If no sensor exists in the node's nodespace for the given datasource,
        a new sensor will be created, otherwise the first sensor found will be used
        """
        sensor = None
        for uid, candidate in self._nodenet.get_sensors(node.parent_nodespace).items():
            if candidate.get_parameter('datasource') == datasource:
                sensor = candidate
        if sensor is None:
            sensor = self.create_node("Sensor", node.parent_nodespace, datasource)
            sensor.set_parameter('datasource', datasource)

        self.link(sensor, 'gen', node, slot, weight)

    def import_actuators(self, nodespace, datatarget_prefix=None):
        """
        Makes sure an actuator for all datatargets whose names start with the given prefix, or all datatargets,
        exists in the given nodespace.
        """
        all_actuators = []
        if self.worldadapter is None:
            return all_actuators

        datatargets = self.worldadapter.get_available_datatargets()

        for datatarget in datatargets:
            if datatarget_prefix is None or datatarget.startswith(datatarget_prefix):
                actuator = None
                for uid, candidate in self._nodenet.get_actuators(nodespace, datatarget).items():
                    actuator = candidate
                    break
                if actuator is None:
                    actuator = self.create_node("Actuator", nodespace, datatarget)
                    actuator.set_parameter('datatarget', datatarget)
                all_actuators.append(actuator)
        return all_actuators

    def import_sensors(self, nodespace, datasource_prefix=None):
        """
        Makes sure a sensor for all datasources whose names start with the given prefix, or all datasources,
        exists in the given nodespace.
        """
        all_sensors = []
        if self.worldadapter is None:
            return all_sensors

        datasources = self.worldadapter.get_available_datasources()

        for datasource in datasources:
            if datasource_prefix is None or datasource.startswith(datasource_prefix):
                sensor = None
                for uid, candidate in self._nodenet.get_sensors(nodespace, datasource).items():
                    sensor = candidate
                    break
                if sensor is None:
                    sensor = self.create_node("Sensor", nodespace, datasource)
                    sensor.set_parameter('datasource', datasource)
                all_sensors.append(sensor)
        return all_sensors

    def notify_user(self, node, msg):
        """
        Stops the nodenetrunner for this nodenet and displays some information to the user,
        who can then choose to continue running or keep it stopped.

        Params
        ------
            node: node instance
                the node object that emits this message
            msg: a string to display to the user
        """
        self._nodenet.set_user_prompt(node, None, msg, [])

    def show_user_prompt(self, node, key):
        """
        Stop the nodenetrunner and display a dialogue that collects user input

        Params
        ------
            node: node instance
                the node that wants to create this dialoge - must have a
                `user_prompts` field in its nodetype definition

            key: str
                select a particular prompt from the nodetype's 'user_prompts' field.

        """
        promptinfo = node.get_user_prompt(key)
        self._nodenet.set_user_prompt(node, key, promptinfo['callback'].__doc__, promptinfo['parameters'])

    def autoalign_nodespace(self, nodespace):
        """ Calls the autoalignment on the given nodespace """
        from micropsi_core.nodenet.node_alignment import align
        if nodespace in self._nodenet.get_nodespace_uids():
            align(self._nodenet, nodespace)

    def autoalign_entities(self, nodespace, entity_uids):
        """ Calls the autoalignment on the given entities in the given nodespace """
        from micropsi_core.nodenet.node_alignment import align
        if nodespace in self._nodenet.get_nodespace_uids():
            align(self._nodenet, nodespace, entity_uids)

    def get_modulator(self, modulator):
        """
        Returns the numeric value of the given global modulator
        """
        return self._nodenet.get_modulator(modulator)

    def change_modulator(self, modulator, diff):
        """
        Changes the value of the given global modulator by the value of diff
        """
        self._nodenet.change_modulator(modulator, diff)

    def set_modulator(self, modulator, value):
        """
        Changes the value of the given global modulator to the given value
        """
        self._nodenet.set_modulator(modulator, value)

    def copy_nodes(self, nodes, nodespace_uid):
        """
        Copys the given nodes into the target nodespace. Also copies the internal linkage
        between these nodes
        """
        uids = [node.uid for node in nodes]
        uidmap = {}
        for node in nodes:
            new_uid = self._nodenet.create_node(node.type, nodespace_uid, node.position, name=node.name, parameters=node.clone_parameters(), gate_configuration=node.get_gate_configuration())
            uidmap[node.uid] = new_uid
        for node in nodes:
            for g in node.get_gate_types():
                for l in node.get_gate(g).get_links():
                    if l.target_node.uid in uids:
                        self.link(self.get_node(uidmap[l.source_node.uid]),
                                  l.source_gate.type,
                                  self.get_node(uidmap[l.target_node.uid]),
                                  l.target_slot.type,
                                  weight=l.weight)
        mapping = {}
        for node in nodes:
            mapping[node] = self.get_node(uidmap[node.uid])
        return mapping

    def group_nodes_by_names(self, nodespace_uid, node_name_prefix=None, gate="gen", sortby='id', group_name=None):
        """
        Will group the given set of nodes.
        Groups can be used in bulk operations.
        Grouped nodes will have stable sorting accross all bulk operations.
        If no group name is given, the node_name_prefix will be used as group name.
        """
        self._nodenet.group_nodes_by_names(nodespace_uid, node_name_prefix, gatetype=gate, sortby=sortby, group_name=group_name)

    def group_nodes_by_ids(self, nodespace_uid, node_uids, group_name, gate="gen", sortby='id'):
        """
        Will group the given set of nodes.
        Groups can be used in bulk operations.
        Grouped nodes will have stable sorting accross all bulk operations.
        """
        self._nodenet.group_nodes_by_ids(nodespace_uid, node_uids, group_name, gatetype=gate, sortby=sortby)

    def ungroup_nodes(self, nodespace_uid, group):
        """
        Deletes the given group (not the nodes, just the group assignment)
        """
        self._nodenet.ungroup_nodes(nodespace_uid, group)

    def get_activations(self, nodespace_uid, group):
        """
        Returns an array of activations for the given group.
        """
        return self._nodenet.get_activations(nodespace_uid, group)

    def substitute_activations(self, nodespace_uid, group, new_activations):
        """
        Sets the activation of the given elements to the given value.
        Note that this overrides the calculated activations, including all gate mechanics,
        including gate function, thresholds, min, max, amplification and directional
        activators - the values passed will be propagated in the next step.
        """
        return self._nodenet.set_activations(nodespace_uid, group, new_activations)

    def get_gate_configurations(self, nodespace_uid, group, gatefunction_parameter=None):
        """
        Returns a dictionary containing a list of gatefunction names, and a list of the values
        of the given gatefunction_parameter (if given)
        """
        return self._nodenet.get_gate_configurations(nodespace_uid, group, gatefunction_parameter)

    def set_gate_configurations(self, nodespace_uid, group, gatefunction, gatefunction_parameter=None, parameter_values=None):
        """
        Bulk-sets gatefunctions and a gatefunction_parameter for the given group.
        Arguments:
            nodespace_uid (string) - id of the parent nodespace
            group (string) - name of the group
            gatefunction (string) - name of the gatefunction to set
            gatefunction_parameter (optinoal) - name of the gatefunction_paramr to set
            parameter_values (optional) - values to set for the gatefunction_parameetr
        """
        self._nodenet.set_gate_configurations(nodespace_uid, group, gatefunction, gatefunction_parameter, parameter_values)

    def get_link_weights(self, nodespace_from_uid, group_from, nodespace_to_uid, group_to):
        """
        Returns the weights of links between two groups as a matrix.
        Rows are group_to slots, columns are group_from gates.
        Non-existing links will be returned as 0-entries in the matrix.
        """
        return self._nodenet.get_link_weights(nodespace_from_uid, group_from, nodespace_to_uid, group_to)

    def set_link_weights(self, nodespace_from_uid, group_from, nodespace_to_uid, group_to, new_w):
        """
        Sets the weights of links between two groups from the given matrix new_w.
        Rows are group_to slots, columns are group_from gates.
        Note that setting matrix entries to non-0 values will implicitly create links.
        """
        self._nodenet.set_link_weights(nodespace_from_uid, group_from, nodespace_to_uid, group_to, new_w)

    def get_node_ids(self, nodespace_uid, group):
        """
        Returns the uids of the nodes in the given group
        """
        return self._nodenet.get_node_uids(nodespace_uid, group)

    def add_gate_monitor(self, node_uid, gate, name=None, color=None):
        """Adds a continuous monitor to the activation of a gate. The monitor will collect the activation
        value in every calculation step.
        Returns the uid of the new monitor."""
        return self._nodenet.add_gate_monitor(node_uid, gate, name=name, color=color)

    def add_slot_monitor(self, node_uid, slot, name=None, color=None):
        """Adds a continuous monitor to the activation of a slot. The monitor will collect the activation
        value in every calculation step.
        Returns the uid of the new monitor."""
        return self._nodenet.add_slot_monitor(node_uid, slot, name=name, color=color)

    def add_link_monitor(self, source_node_uid, gate_type, target_node_uid, slot_type, name=None, color=None):
        """Adds a continuous weightmonitor to a link. The monitor will record the linkweight in every calculation step.
        Returns the uid of the new monitor."""
        return self._nodenet.add_link_monitor(source_node_uid, gate_type, target_node_uid, slot_type, name=name, color=color)

    def add_modulator_monitor(self, modulator, name, color=None):
        """Adds a continuous monitor to a global modulator.
        The monitor will collect respective value in every calculation step.
        Returns the uid of the new monitor."""
        return self._nodenet.add_modulator_monitor(modulator, name, color=color)

    def add_custom_monitor(self, function, name, color=None):
        """Adds a continuous monitor, that evaluates the given python-code and collects the
        return-value for every calculation step.
        Returns the uid of the new monitor."""
        return self._nodenet.add_custom_monitor(function, name, color=color)

    def add_adhoc_monitor(self, function, name, parameters={}):
        return self._nodenet.add_adhoc_monitor(function, name, parameters)

    def add_group_monitor(self, nodespace, name, node_name_prefix='', node_uids=[], gate='gen', color=None):
        """Adds a continuous monitor, that tracks the activations of the given group
        return-value for every calculation step.
        Returns the uid of the new monitor."""
        return self._nodenet.add_group_monitor(nodespace, name, node_name_prefix=node_name_prefix, node_uids=node_uids, gate=gate, color=color)

    def get_monitor(self, uid):
        """Returns the monitor with the given uid"""
        return self._nodenet.get_monitor(uid)

    def remove_monitor(self, uid):
        """Removes the monitor with the given uid"""
        return self._nodenet.remove_monitor(uid)

    def set_dashboard_value(self, name, value):
        """Allows the netapi to set values for the statistics and dashboard"""
        self._nodenet.dashboard_values[name] = value

    def decay_por_links(self, nodespace_uid):
        """ Decayes all por-links in the given nodespace """
        porretdecay = self._nodenet.get_modulator('base_porret_decay_factor')
        nodes = self.get_nodes(nodespace=nodespace_uid, nodetype="Pipe")
        decay_factor = (1 - porretdecay)
        if porretdecay != 0:
            for node in nodes:
                porgate = node.get_gate('por')
                for link in porgate.get_links():
                    if link.weight > 0:
                        link._set_weight(max(link.weight * decay_factor, 0))

    def get_nodespace_properties(self, nodespace_uid=None):
        """ retrieve the ui properties for the given nodespace"""
        return self._nodenet.get_nodespace_properties(nodespace_uid)

    def set_nodespace_properties(self, nodespace_uid, properties):
        """ sets the ui properties for the given nodespace"""
        self._nodenet.set_nodespace_properties(nodespace_uid, properties)

    def announce_nodes(self, nodespace_uid, numer_of_nodes, average_element_per_node):
        pass
