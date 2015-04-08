

class NetAPI(object):
    """
    Node Net API facade class for use from within the node net (in node functions)
    """

    __locks_to_delete = []

    @property
    def uid(self):
        return self.__nodenet.uid

    @property
    def step(self):
        return self.__nodenet.current_step

    @property
    def world(self):
        return self.__nodenet.world

    def __init__(self, nodenet):
        self.__nodenet = nodenet

    @property
    def logger(self):
        return self.__nodenet.logger

    def get_nodespace(self, uid):
        """
        Returns the nodespace with the given uid
        """
        return self.__nodenet.get_nodespace(uid)

    def get_nodespaces(self, parent="Root"):
        """
        Returns a list of all nodespaces in the given nodespace
        """
        return [self.__nodenet.get_nodespace(uid) for
                uid in self.__nodenet.get_nodespace(parent).get_known_ids('nodespaces')]

    def get_node(self, uid):
        """
        Returns the node with the given uid
        """
        return self.__nodenet.get_node(uid)

    def get_nodes(self, nodespace=None, node_name_prefix=None):
        """
        Returns a list of nodes in the given nodespace (all Nodespaces if None) whose names start with
        the given prefix (all if None)
        """
        nodes = []
        for node_uid in self.__nodenet.get_node_uids():
            node = self.__nodenet.get_node(node_uid)
            if ((node_name_prefix is None or node.name.startswith(node_name_prefix)) and
                    (nodespace is None or node.parent_nodespace == nodespace)):
                nodes.append(node)
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
            gates = self.__nodenet.get_node(node.uid).get_gate_types()
        for gate in gates:
            for link in self.__nodenet.get_node(node.uid).get_gate(gate).get_links():
                candidate = link.target_node
                linked_gates = []
                for candidate_gate_name in candidate.get_gate_types():
                    if len(candidate.get_gate(candidate_gate_name).get_links()) > 0:
                        linked_gates.append(candidate_gate_name)
                if ((nodespace is None or nodespace == link.target_node.parent_nodespace) and
                    (no_links_to is None or not len(set(no_links_to).intersection(set(linked_gates))))):
                    nodes.append(candidate)
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
            slots = self.__nodenet.get_node(node.uid).get_slot_types()
        for slot in slots:
            for link in self.__nodenet.get_node(node.uid).get_slot(slot).get_links():
                candidate = link.source_node
                linked_gates = []
                for candidate_gate_name in candidate.get_gate_types():
                    if len(candidate.get_gate(candidate_gate_name).get_links()) > 0:
                        linked_gates.append(candidate_gate_name)
                if ((nodespace is None or nodespace == link.source_node.parent_nodespace) and
                    (no_links_to is None or not len(set(no_links_to).intersection(set(linked_gates))))):
                    nodes.append(candidate)
        return nodes

    def get_nodes_active(self, nodespace, type=None, min_activation=1, gate=None, sheaf='default'):
        """
        Returns all nodes with a min activation, of the given type, active at the given gate, or with node.activation
        """
        nodes = []
        for node in self.get_nodes(nodespace):
            if type is None or node.type == type:
                if gate is not None:
                    if gate in node.get_gate_types():
                        if node.get_gate(gate).activations[sheaf] >= min_activation:
                            nodes.append(node)
                else:
                    if node.activations[sheaf] >= min_activation:
                        nodes.append(node)
        return nodes

    def delete_node(self, node):
        """
        Deletes a node and all links connected to it.
        """
        self.__nodenet.delete_node(node.uid)

    def delete_nodespace(self, nodespace):
        """
        Deletes a node and all nodes and nodespaces contained within, and all links connected to it.
        """
        self.__nodenet.delete_nodespace(nodespace.uid)

    def create_node(self, nodetype, nodespace, name=None):
        """
        Creates a new node or node space of the given type, with the given name and in the given nodespace.
        Returns the newly created entity.
        """
        if name is None:
            name = ""   # TODO: empty names crash the client right now, but really shouldn't
        pos = (self.__nodenet.max_coords['x'] + 50, 100)  # default so native modules will not be bothered with positions

        # todo: There should be a separate method for this Nodespaces are net entities, but they're not nodes.
        if nodetype == "Nodespace":
            uid = self.__nodenet.create_nodespace(nodespace, pos, name=name)
            entity = self.__nodenet.get_nodespace(uid)
        else:
            uid = self.__nodenet.create_node(nodetype, nodespace, pos, name)
            entity = self.__nodenet.get_node(uid)
        self.__nodenet.update_node_positions()
        return entity

    def link(self, source_node, source_gate, target_node, target_slot, weight=1, certainty=1):
        """
        Creates a link between two nodes. If the link already exists, it will be updated
        with the given weight and certainty values (or the default 1 if not given)
        """
        self.__nodenet.create_link(source_node.uid, source_gate, target_node.uid, target_slot, weight, certainty)

    def link_with_reciprocal(self, source_node, target_node, linktype, weight=1, certainty=1):
        """
        Creates two (reciprocal) links between two nodes, valid linktypes are subsur, porret, catexp and symref
        """
        target_slot_types = target_node.get_slot_types()
        source_slot_types = source_node.get_slot_types()
        if linktype == "subsur":
            subslot = "sub" if "sub" in target_slot_types else "gen"
            surslot = "sur" if "sur" in source_slot_types else "gen"
            self.__nodenet.create_link(source_node.uid, "sub", target_node.uid, subslot, weight, certainty)
            self.__nodenet.create_link(target_node.uid, "sur", source_node.uid, surslot, weight, certainty)
        elif linktype == "porret":
            porslot = "por" if "por" in target_slot_types else "gen"
            retslot = "ret" if "ret" in source_slot_types else "gen"
            self.__nodenet.create_link(source_node.uid, "por", target_node.uid, porslot, weight, certainty)
            self.__nodenet.create_link(target_node.uid, "ret", source_node.uid, retslot, weight, certainty)
        elif linktype == "catexp":
            catslot = "cat" if "cat" in target_slot_types else "gen"
            expslot = "exp" if "exp" in source_slot_types else "gen"
            self.__nodenet.create_link(source_node.uid, "cat", target_node.uid, catslot, weight, certainty)
            self.__nodenet.create_link(target_node.uid, "exp", source_node.uid, expslot, weight, certainty)
        elif linktype == "symref":
            symslot = "sym" if "sym" in target_slot_types else "gen"
            refslot = "ref" if "ref" in source_slot_types else "gen"
            self.__nodenet.create_link(source_node.uid, "sym", target_node.uid, symslot, weight, certainty)
            self.__nodenet.create_link(target_node.uid, "ref", source_node.uid, refslot, weight, certainty)

    def unlink(self, source_node, source_gate=None, target_node=None, target_slot=None):
        """
        Deletes a link, or links, originating from the given node
        """
        target_node_uid = target_node.uid if target_node is not None else None
        source_node.unlink(source_gate, target_node_uid, target_slot)

    def unlink_direction(self, node, gateslot=None):
        """
        Deletes all links from a node ending at the given gate or originating at the given slot
        Read this as 'delete all por linkage from this node'
        """
        node.unlink(gateslot)

        links_to_delete = set()
        for slottype in node.get_slot_types():
            if gateslot is None or gateslot == slottype:
                for link in node.get_slot(slottype).get_links():
                    links_to_delete.add(link)

        for link in links_to_delete:
            link.source_node.unlink(gateslot, node.uid)

    def link_actor(self, node, datatarget, weight=1, certainty=1, gate='sub', slot='sur'):
        """
        Links a node to an actor. If no actor exists in the node's nodespace for the given datatarget,
        a new actor will be created, otherwise the first actor found will be used
        """
        if datatarget not in self.world.get_available_datatargets(self.__nodenet.uid):
            raise KeyError("Data target %s not found" % datatarget)
        actor = None
        for uid, candidate in self.__nodenet.get_actors(node.parent_nodespace).items():
            if candidate.get_parameter('datatarget') == datatarget:
                actor = candidate
        if actor is None:
            actor = self.create_node("Actor", node.parent_nodespace, datatarget)
            actor.set_parameter('datatarget', datatarget)

        self.link(node, gate, actor, 'gen', weight, certainty)
        #self.link(actor, 'gen', node, slot)

    def link_sensor(self, node, datasource, slot='sur'):
        """
        Links a node to a sensor. If no sensor exists in the node's nodespace for the given datasource,
        a new sensor will be created, otherwise the first sensor found will be used
        """
        if datasource not in self.world.get_available_datasources(self.__nodenet.uid):
            raise KeyError("Data source %s not found" % datasource)
        sensor = None
        for uid, candidate in self.__nodenet.get_sensors(node.parent_nodespace).items():
            if candidate.get_parameter('datasource') == datasource:
                sensor = candidate
        if sensor is None:
            sensor = self.create_node("Sensor", node.parent_nodespace, datasource)
            sensor.set_parameter('datasource', datasource)

        self.link(sensor, 'gen', node, slot)

    def import_actors(self, nodespace, datatarget_prefix=None):
        """
        Makes sure an actor for all datatargets whose names start with the given prefix, or all datatargets,
        exists in the given nodespace.
        """
        all_actors = []
        if self.world is None:
            return all_actors

        for datatarget in self.world.get_available_datatargets(self.__nodenet.uid):
            if datatarget_prefix is None or datatarget.startswith(datatarget_prefix):
                actor = None
                for uid, candidate in self.__nodenet.get_actors(nodespace).items():
                    if candidate.get_parameter('datatarget') == datatarget:
                        actor = candidate
                if actor is None:
                    actor = self.create_node("Actor", nodespace, datatarget)
                    actor.set_parameter('datatarget', datatarget)
                all_actors.append(actor)
        return all_actors

    def import_sensors(self, nodespace, datasource_prefix=None):
        """
        Makes sure a sensor for all datasources whose names start with the given prefix, or all datasources,
        exists in the given nodespace.
        """
        all_sensors = []
        if self.world is None:
            return all_sensors

        for datasource in self.world.get_available_datasources(self.__nodenet.uid):
            if datasource_prefix is None or datasource.startswith(datasource_prefix):
                sensor = None
                for uid, candidate in self.__nodenet.get_sensors(nodespace).items():
                    if candidate.get_parameter('datasource') == datasource:
                        sensor = candidate
                if sensor is None:
                    sensor = self.create_node("Sensor", nodespace, datasource)
                    sensor.set_parameter('datasource', datasource)
                all_sensors.append(sensor)
        return all_sensors

    def set_gatefunction(self, nodespace, nodetype, gatetype, gatefunction):
        """Sets the gatefunction for gates of type gatetype of nodes of type nodetype, in the given
            nodespace.
            The gatefunction needs to be given as a string.
        """
        nodespace = self.get_nodespace(nodespace)
        for uid in nodespace.get_known_ids(entitytype="nodes"):
            node = self.get_node(uid)
            if node.type == nodetype:
                node.set_gatefunction_name(gatetype, gatefunction)

    def is_locked(self, lock):
        """Returns true if the given lock is locked in the current net step
        """
        return self.__nodenet.is_locked(lock)

    def is_locked_by(self, lock, key):
        """Returns true if the given lock is locked in the current net step, with the given key
        """
        return self.__nodenet.is_locked_by(lock, key)

    def lock(self, lock, key, timeout=100):
        """
        Creates a lock with immediate effect.
        If two nodes try to create the same lock in the same net step, the second call will fail.
        As nodes need to check is_locked before acquiring locks anyway, this effectively means that if two
        nodes attempt to acquire the same lock at the same time (in the same net step), the node to get the
        lock will be chosen randomly.
        """
        self.__nodenet.lock(lock, key, timeout)

    def unlock(self, lock):
        """
        Removes a lock by the end of the net step, after all node functions have been called.
        Thus, locks can only be acquired in the next net step (no indeterminism based on node function execution
        order as with creating locks).
        """
        self.__locks_to_delete.append(lock)

    def notify_user(self, node, msg):
        """
        Stops the nodenetrunner for this nodenet, and displays an information to the user,
        who can then choose to continue or suspend running nodenet
        Parameters:
            node: the node object that emits this message
            msg: a string to display to the user
        """
        self.__nodenet.user_prompt = {
            'node': node.data,
            'msg': msg,
            'options': None
        }
        self.__nodenet.is_active = False

    def ask_user_for_parameter(self, node, msg, options):
        """
        Stops the nodenetrunner for this nodenet, and asks the user for values to the given parameters.
        These parameters will be passed into the nodefunction in the next step of the nodenet.
        The user can choose to either continue or suspend running the nodenet
        Parameters:
            node: the node object that emits this message
            msg: a string to display to the user
            options: an array of objects representing the variables to set by the user. Needs key, label. Optional: array or object of values

        example usage:
            options = [{
                'key': 'where',
                'label': 'Where should I go next?',
                'values': {'north': 'North', 'east': 'East', 'south': 'South', 'west': 'west'}
            }, {
                'key': 'wait':
                'label': 'How long should I wait until I go there?',
            }]
            netapi.ask_user_for_parameter(node, "Please decide what to do next", options)
        """
        self.__nodenet.user_prompt = {
            'node': node.data,
            'msg': msg,
            'options': options
        }
        self.__nodenet.is_active = False

    def autoalign_nodespace(self, nodespace):
        """ Calls the autoalignment on the given nodespace """
        from micropsi_core.nodenet.node_alignment import align
        if nodespace in self.__nodenet.get_nodespace_uids():
            align(self.__nodenet, nodespace)

    def get_modulator(self, modulator):
        """
        Returns the numeric value of the given global modulator
        """
        return self.__nodenet.get_modulator(modulator)

    def change_modulator(self, modulator, diff):
        """
        Changes the value of the given global modulator by the value of diff
        """
        self.__nodenet.change_modulator(modulator, diff)

    def set_modulator(self, modulator, value):
        """
        Changes the value of the given global modulator to the given value
        """
        self.__nodenet.set_modulator(modulator, value)

    def copy_nodes(self, nodes, nodespace_uid):
        """
        Copys the given nodes into the target nodespace. Also copies the internal linkage
        between these nodes
        """
        mapping = {}
        for node in nodes:
            new_uid = self.__nodenet.create_node(node.type, nodespace_uid, node.position, name=node.name, parameters=node.clone_parameters(), gate_parameters=node.get_gate_parameters())
            mapping[node] = self.get_node(new_uid)
        for node in nodes:
            for g in node.get_gate_types():
                for l in node.get_gate(g).get_links():
                    if l.target_node in nodes:
                        self.link(mapping[l.source_node], l.source_gate.type, mapping[l.target_node], l.target_slot.type, weight=l.weight, certainty=l.certainty)
        return mapping

    def _step(self):
        for lock in self.__locks_to_delete:
            self.__nodenet.unlock(lock)
        self.__locks_to_delete = []
