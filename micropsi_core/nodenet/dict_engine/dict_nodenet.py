__author__ = 'rvuine'

import json
import os

import micropsi_core
from micropsi_core.nodenet import monitor
from micropsi_core.nodenet.node import Nodetype, FlowNodetype, HighdimensionalNodetype
from micropsi_core.nodenet.nodenet import Nodenet, NODENET_VERSION
from micropsi_core.nodenet.stepoperators import DoernerianEmotionalModulators
from .dict_stepoperators import DictPropagate, DictCalculate
from .dict_node import DictNode
from .dict_nodespace import DictNodespace
import copy

STANDARD_NODETYPES = {
    "Comment": {
        "name": "Comment",
        "symbol": "#",
        'parameters': ['comment'],
        "shape": "Rectangle"
    },

    "Neuron": {
        "name": "Neuron",
        "slottypes": ["gen"],
        "nodefunction_name": "neuron",
        "gatetypes": ["gen"]
    },
    "Sensor": {
        "name": "Sensor",
        "parameters": ["datasource"],
        "nodefunction_name": "sensor",
        "gatetypes": ["gen"]
    },
    "Actuator": {
        "name": "Actuator",
        "parameters": ["datatarget"],
        "nodefunction_name": "actuator",
        "slottypes": ["gen"],
        "gatetypes": ["gen"]
    },
    "Concept": {
        "name": "Concept",
        "slottypes": ["gen"],
        "nodefunction_name": "concept",
        "gatetypes": ["gen", "por", "ret", "sub", "sur", "cat", "exp", "sym", "ref"]
    },
    "Script": {
        "name": "Script",
        "slottypes": ["gen", "por", "ret", "sub", "sur"],
        "nodefunction_name": "script",
        "gatetypes": ["gen", "por", "ret", "sub", "sur", "cat", "exp", "sym", "ref"]
    },
    "Pipe": {
        "name": "Pipe",
        "slottypes": ["gen", "por", "ret", "sub", "sur", "cat", "exp"],
        "nodefunction_name": "pipe",
        "gatetypes": ["gen", "por", "ret", "sub", "sur", "cat", "exp"],
        "parameters": ["expectation", "wait"],
        "symbol": "πp",
        "shape": "Rectangle",
        "parameter_defaults": {
            "expectation": 1,
            "wait": 10
        }
    },
    "Activator": {
        "name": "Activator",
        "slottypes": ["gen"],
        "parameters": ["type"],
        "parameter_values": {"type": ["por", "ret", "sub", "sur", "cat", "exp", "sym", "ref", "sampling"]},
        "nodefunction_name": "activator"
    },
    "LSTM": {
        "name": "LSTM",
        "slottypes": ["gen", "por", "gin", "gou", "gfg"],
        "gatetypes": ["gen", "por", "gin", "gou", "gfg"],
        "nodefunction_name": "lstm",
    }
}


class DictNodenet(Nodenet):
    """Main data structure for MicroPsi agents,

    Contains the net entities and runs the activation spreading. The nodenet stores persistent data.

    Attributes:
        state: a dict of persistent nodenet data; everything stored within the state can be stored and exported
        uid: a unique identifier for the node net
        name: an optional name for the node net
        nodespaces: a dictionary of node space UIDs and respective node spaces
        nodes: a dictionary of node UIDs and respective nodes
        links: a dictionary of link UIDs and respective links
        gate_types: a dictionary of gate type names and the individual types of gates
        slot_types: a dictionary of slot type names and the individual types of slots
        node_types: a dictionary of node type names and node type definitions
        world: an environment for the node net
        worldadapter: an actual world adapter object residing in a world implementation, provides interface
        owner: an id of the user who created the node net
        step: the current calculation step of the node net
    """

    @property
    def engine(self):
        return "dict_engine"

    @property
    def current_step(self):
        return self._step

    def __init__(self, persistency_path, name="", worldadapter="Default", world=None, owner="", uid=None, native_modules={}, use_modulators=True, worldadapter_instance=None, version=None):
        """Create a new MicroPsi agent.

        Arguments:
            agent_type (optional): the interface of this agent to its environment
            name (optional): the name of the agent
            owner (optional): the user that created this agent
            uid (optional): unique handle of the agent; if none is given, it will be generated
        """

        super().__init__(persistency_path, name, worldadapter, world, owner, uid, native_modules=native_modules, use_modulators=use_modulators, worldadapter_instance=worldadapter_instance, version=version)

        self.nodetypes = {}
        for type, data in STANDARD_NODETYPES.items():
            self.nodetypes[type] = Nodetype(nodenet=self, **data)

        self.stepoperators = [DictPropagate(), DictCalculate()]
        if self.use_modulators:
            self.stepoperators.append(DoernerianEmotionalModulators())
        self.stepoperators.sort(key=lambda op: op.priority)

        self._step = 0

        self._nodes = {}
        self._nodespaces = {}

        self.nodegroups = {}

        self.initialize_nodenet({})

    def get_data(self, **params):
        data = super().get_data(**params)
        data['nodes'] = self.construct_nodes_dict(**params)
        data['nodespaces'] = self.construct_nodespaces_dict("Root", transitive=True)
        data['modulators'] = self.construct_modulators_dict()
        return data

    def export_json(self):
        data = self.get_data(complete=True, include_links=False)
        data['links'] = self.construct_links_list()
        return data

    def get_links_for_nodes(self, node_uids):
        source_nodes = [self.get_node(uid) for uid in node_uids]
        links = {}
        nodes = {}
        for node in source_nodes:
            nodelinks = node.get_associated_links()
            for l in nodelinks:
                links[l.signature] = l.get_data(complete=True)
                if l.source_node.parent_nodespace != node.parent_nodespace:
                    nodes[l.source_node.uid] = l.source_node.get_data(include_links=False)
                if l.target_node.parent_nodespace != node.parent_nodespace:
                    nodes[l.target_node.uid] = l.target_node.get_data(include_links=False)
        return list(links.values()), nodes

    def get_nodes(self, nodespace_uids=[], include_links=True, links_to_nodespaces=[]):
        """
        Returns a dict with contents for the given nodespaces
        """
        data = {}
        data['nodes'] = {}
        data['nodespaces'] = {}
        followupnodes = []
        fetch_all = False

        if nodespace_uids == []:
            nodespace_uids = self.get_nodespace_uids()
            root = self.get_nodespace(None)
            data['nodespaces'][root.uid] = root.get_data()
            fetch_all = True
        else:
            nodespace_uids = [self.get_nodespace(uid).uid for uid in nodespace_uids]

        for nodespace_uid in nodespace_uids:
            data['nodespaces'].update(self.construct_nodespaces_dict(nodespace_uid))
            nodespace = self.get_nodespace(nodespace_uid)
            for uid in nodespace.get_known_ids(entitytype="nodes"):
                node = self.get_node(uid)
                data['nodes'][uid] = node.get_data(include_links=include_links)
                if include_links and not fetch_all:
                    followupnodes.extend(node.get_associated_node_uids())

        if include_links:
            for uid in set(followupnodes):
                if uid not in data['nodes']:
                    node = self.get_node(uid).get_data(include_links=True)
                    for gate in list(node['links'].keys()):
                        links = node['links'][gate]
                        for idx, l in enumerate(links):
                            if self._nodes[l['target_node_uid']].parent_nodespace not in nodespace_uids:
                                del links[idx]
                        if len(node['links'][gate]) == 0:
                            del node['links'][gate]
                    data['nodes'][uid] = node

        return data

    def save(self, base_path=None, zipfile=None):
        if base_path is None:
            base_path = self.persistency_path
        data = json.dumps(self.export_json(), sort_keys=True, indent=4)
        if zipfile:
            zipfile.writestr('nodenet.json', data)
        else:
            filename = os.path.join(base_path, 'nodenet.json')
            # dict_engine saves everything to json, just dump the json export
            with open(filename, 'w+', encoding="utf-8") as fp:
                fp.write(data)
            if os.path.getsize(filename) < 100:
                # kind of hacky, but we don't really know what was going on
                raise RuntimeError("Error writing nodenet file")

    def load(self):
        """Load the node net from a file"""
        # try to access file
        if self._version != NODENET_VERSION:
            self.logger.error("Wrong version of nodenet data in nodenet %s, cannot load." % self.uid)
            return False
        filename = os.path.join(self.persistency_path, 'nodenet.json')
        with self.netlock:

            initfrom = {}

            if os.path.isfile(filename):
                try:
                    self.logger.info("Loading nodenet %s from file %s", self.name, filename)
                    with open(filename, encoding="utf-8") as file:
                        initfrom.update(json.load(file))
                except ValueError:
                    self.logger.warning("Could not read nodenet data")
                    return False
                except IOError:
                    self.logger.warning("Could not open nodenet file")
                    return False

            self.initialize_nodenet(initfrom)
            return True

    def reload_native_modules(self, native_modules):
        """ reloads the native-module definition, and their nodefunctions
        and afterwards reinstantiates the nodenet."""
        self.native_modules = {}
        for key in native_modules:
            if native_modules[key].get('engine', self.engine) == self.engine:
                try:
                    if native_modules[key].get('flow_module'):
                        raise NotImplementedError("dict nodenet does not support flow modules")
                    elif native_modules[key].get('dimensionality'):
                        raise NotImplementedError("dict nodenet does not support highdimensional native modules")
                    else:
                        self.native_modules[key] = Nodetype(nodenet=self, **native_modules[key])
                except Exception as err:
                    self.logger.error("Can not instantiate node type %s: %s: %s" % (key, err.__class__.__name__, str(err)))

        saved = self.export_json()
        self.clear()
        self.merge_data(saved, keep_uids=True)

    def initialize_nodespace(self, id, data):
        if id not in self._nodespaces:
            # move up the nodespace tree until we find an existing parent or hit root
            while id != 'Root' and data[id].get('parent_nodespace') not in self._nodespaces:
                self.initialize_nodespace(data[id]['parent_nodespace'], data)
            self._nodespaces[id] = DictNodespace(self,
                data[id].get('parent_nodespace'),
                name=data[id].get('name', 'Root'),
                uid=id,
                index=data[id].get('index'))

    def initialize_nodenet(self, initfrom):
        """Called after reading new nodenet state.

        Parses the nodenet state and set up the non-persistent data structures necessary for efficient
        computation of the node net
        """

        self._modulators.update(initfrom.get("modulators", {}))

        if initfrom.get('runner_condition'):
            self.set_runner_condition(initfrom['runner_condition'])

        self._nodespace_ui_properties = initfrom.get('nodespace_ui_properties', {})

        # set up nodespaces; make sure that parent nodespaces exist before children are initialized
        self._nodespaces = {}
        self._nodespaces["Root"] = DictNodespace(self, None, name="Root", uid="Root")

        if 'current_step' in initfrom:
            self._step = initfrom['current_step']

        if len(initfrom) != 0:
            # now merge in all init data (from the persisted file typically)
            self.merge_data(initfrom, keep_uids=True)

    def construct_links_list(self):
        data = []
        for node_uid in self.get_node_uids():
            node = self.get_node(node_uid)
            for g in node.get_gate_types():
                data.extend([l.get_data(complete=True) for l in node.get_gate(g).get_links()])
        return data

    def construct_nodes_dict(self, **params):
        data = {}
        for node_uid in self.get_node_uids():
            data[node_uid] = self.get_node(node_uid).get_data(**params)
        return data

    def construct_nodespaces_dict(self, nodespace_uid, transitive=False):
        data = {}
        if nodespace_uid is None:
            nodespace_uid = "Root"

        if transitive:
            for nodespace_candidate_uid in self.get_nodespace_uids():
                is_in_hierarchy = False
                if nodespace_candidate_uid == nodespace_uid:
                    is_in_hierarchy = True
                else:
                    parent_uid = self.get_nodespace(nodespace_candidate_uid).parent_nodespace
                    while parent_uid is not None and parent_uid != nodespace_uid:
                        parent_uid = self.get_nodespace(parent_uid).parent_nodespace
                    if parent_uid == nodespace_uid:
                        is_in_hierarchy = True

                if is_in_hierarchy:
                    data[nodespace_candidate_uid] = self.get_nodespace(nodespace_candidate_uid).get_data()
        else:
            for uid in self.get_nodespace(nodespace_uid).get_known_ids('nodespaces'):
                data[uid] = self.get_nodespace(uid).get_data()
        return data

    def get_nodetype(self, type):
        """ Returns the nodetpype instance for the given nodetype or native_module or None if not found"""
        if type in self.nodetypes:
            return self.nodetypes[type]
        else:
            return self.native_modules[type]

    def get_activation_data(self, nodespace_uids=None, rounded=1):
        activations = {}

        node_ids = []
        if nodespace_uids == []:
            node_ids = self._nodes.keys()
        else:
            for nsuid in nodespace_uids:
                node_ids.extend(self.get_nodespace(nsuid).get_known_ids("nodes"))

        for uid in node_ids:
            node = self.get_node(uid)
            if rounded is None:
                act = [node.get_gate(gate_name).activation for gate_name in node.get_gate_types()]
                if set(act) != {0}:
                    activations[uid] = act
            else:
                act = [round(node.get_gate(gate_name).activation, rounded) for gate_name in node.get_gate_types()]
                if set(act) != {0}:
                    activations[uid] = act
        return activations

    def delete_node(self, node_uid):
        self.close_figures(node_uid)
        if node_uid in self._nodespaces:
            affected_entity_ids = self._nodespaces[node_uid].get_known_ids()
            for uid in affected_entity_ids:
                self.delete_node(uid)
            parent_nodespace = self._nodespaces.get(self._nodespaces[node_uid].parent_nodespace)
            if parent_nodespace and parent_nodespace.is_entity_known_as('nodespaces', node_uid):
                parent_nodespace._unregister_entity('nodespaces', node_uid)
                parent_nodespace.contents_last_changed = self.current_step
            del self._nodespaces[node_uid]
            self._track_deletion('nodespaces', node_uid)
        else:
            node = self._nodes[node_uid]
            node.unlink_completely()
            parent_nodespace = self._nodespaces.get(self._nodes[node_uid].parent_nodespace)
            parent_nodespace._unregister_entity('nodes', node_uid)
            parent_nodespace.contents_last_changed = self.current_step
            if self._nodes[node_uid].type == "Activator":
                parent_nodespace.unset_activator_value(self._nodes[node_uid].get_parameter('type'))
            del self._nodes[node_uid]
            self._track_deletion('nodes', node_uid)

    def delete_nodespace(self, nodespace_uid):
        self._nodespace_ui_properties.pop(nodespace_uid, None)
        self.delete_node(nodespace_uid)

    def clear(self):
        super(DictNodenet, self).clear()
        self._nodes = {}
        self.initialize_nodenet({})

    def _register_node(self, node):
        self._nodes[node.uid] = node
        node.last_changed = self.current_step
        self.get_nodespace(node.parent_nodespace).contents_last_changed = self.current_step

    def _register_nodespace(self, nodespace):
        self._nodespaces[nodespace.uid] = nodespace
        nodespace.last_changed = self.current_step
        self.get_nodespace(nodespace.parent_nodespace).contents_last_changed = self.current_step

    def merge_data(self, nodenet_data, keep_uids=False):
        """merges the nodenet state with the current node net, might have to give new UIDs to some entities"""

        # merge in spaces, make sure that parent nodespaces exist before children are initialized
        nodespaces_to_merge = set(nodenet_data.get('nodespaces', {}).keys())
        for nodespace in nodespaces_to_merge:
            self.initialize_nodespace(nodespace, nodenet_data['nodespaces'])

        uidmap = {}
        invalid_nodes = []

        # merge in nodes
        for uid in nodenet_data.get('nodes', {}):
            data = nodenet_data['nodes'][uid]
            if not keep_uids:
                newuid = micropsi_core.tools.generate_uid()
            else:
                newuid = uid
            data['uid'] = newuid
            uidmap[uid] = newuid
            if data['type'] not in self.nodetypes and data['type'] not in self.native_modules:
                self.logger.error("Invalid nodetype %s for node %s" % (data['type'], uid))
                invalid_nodes.append(uid)
                continue
            self._nodes[newuid] = DictNode(self, **data)

        # merge in links
        links = nodenet_data.get('links', [])
        if isinstance(links, dict):
            # compatibility
            links = links.values()
        for link in links:
            if link['source_node_uid'] in invalid_nodes or link['target_node_uid'] in invalid_nodes:
                continue
            try:
                self.create_link(
                    uidmap[link['source_node_uid']],
                    link['source_gate_name'],
                    uidmap[link['target_node_uid']],
                    link['target_slot_name'],
                    link['weight']
                )
            except ValueError:
                self.logger.warning("Invalid link data")

        for monitorid in nodenet_data.get('monitors', {}):
            data = nodenet_data['monitors'][monitorid]
            if 'node_uid' in data:
                old_node_uid = data['node_uid']
                if old_node_uid in uidmap:
                    data['node_uid'] = uidmap[old_node_uid]
            if 'classname' in data:
                if hasattr(monitor, data['classname']):
                    mon = getattr(monitor, data['classname'])(self, **data)
                    self._monitors[mon.uid] = mon
                else:
                    self.logger.warning('unknown classname for monitor: %s (uid:%s) ' % (data['classname'], monitorid))

    def step(self):
        """perform a calculation step"""
        with self.netlock:

            self._step += 1

            for operator in self.stepoperators:
                operator.execute(self, self._nodes.copy(), self.netapi)

        steps = sorted(list(self.deleted_items.keys()))
        if steps:
            for i in steps:
                if i >= self.current_step - 100:
                    break
                else:
                    del self.deleted_items[i]
        self.user_prompt_response = {}

    def create_node(self, nodetype, nodespace_uid, position, name="", uid=None, parameters=None, gate_configuration=None):
        nodespace_uid = self.get_nodespace(nodespace_uid).uid
        node = DictNode(
            self,
            nodespace_uid,
            position, name=name,
            type=nodetype,
            uid=uid,
            parameters=parameters,
            gate_configuration=gate_configuration)
        return node.uid

    def create_nodespace(self, parent_uid, name="", uid=None, options=None):
        parent_uid = self.get_nodespace(parent_uid).uid
        nodespace = DictNodespace(self, parent_uid, name=name, uid=uid)
        return nodespace.uid

    def get_node(self, uid):
        return self._nodes[uid]

    def get_nodespace(self, uid):
        if uid is None:
            uid = "Root"
        return self._nodespaces[uid]

    def get_node_uids(self, group_nodespace_uid=None, group=None):
        if group is not None:
            if group_nodespace_uid is None:
                group_nodespace_uid = self.get_nodespace(None).uid
            return [n.uid for n in self.nodegroups[group_nodespace_uid][group][0]]
        else:
            return list(self._nodes.keys())

    def get_nodespace_uids(self):
        return list(self._nodespaces.keys())

    def is_node(self, uid):
        return uid in self._nodes

    def is_nodespace(self, uid):
        return uid in self._nodespaces

    def set_node_positions(self, positions):
        """ Sets the position of nodes or nodespaces """
        for uid in positions:
            if uid in self._nodes:
                self._nodes[uid].position = positions[uid]

    def get_nativemodules(self, nodespace=None):
        """Returns a dict of native modules. Optionally filtered by the given nodespace"""
        nodes = self._nodes if nodespace is None else self._nodespaces[nodespace].get_known_ids('nodes')
        nativemodules = {}
        for uid in nodes:
            if self._nodes[uid].type not in STANDARD_NODETYPES:
                nativemodules.update({uid: self._nodes[uid]})
        return nativemodules

    def get_activators(self, nodespace=None, type=None):
        """Returns a dict of activator nodes. OPtionally filtered by the given nodespace and the given type"""
        nodes = self._nodes if nodespace is None else self._nodespaces[nodespace].get_known_ids('nodes')
        activators = {}
        for uid in nodes:
            if self._nodes[uid].type == 'Activator':
                if type is None or type == self._nodes[uid].get_parameter('type'):
                    activators.update({uid: self._nodes[uid]})
        return activators

    def get_sensors(self, nodespace=None, datasource=None):
        """Returns a dict of all sensor nodes. Optionally filtered by the given nodespace"""
        nodes = self._nodes if nodespace is None else self._nodespaces[nodespace].get_known_ids('nodes')
        sensors = {}
        for uid in nodes:
            if self._nodes[uid].type == 'Sensor':
                if datasource is None or self._nodes[uid].get_parameter('datasource') == datasource:
                    sensors[uid] = self._nodes[uid]
        return sensors

    def get_actuators(self, nodespace=None, datatarget=None):
        """Returns a dict of all actuator nodes. Optionally filtered by the given nodespace"""
        nodes = self._nodes if nodespace is None else self._nodespaces[nodespace].get_known_ids('nodes')
        actuators = {}
        for uid in nodes:
            if self._nodes[uid].type == 'Actuator':
                if datatarget is None or self._nodes[uid].get_parameter('datatarget') == datatarget:
                    actuators[uid] = self._nodes[uid]
        return actuators

    def set_link_weight(self, source_node_uid, gate_type, target_node_uid, slot_type, weight=1):
        """Set weight of the given link."""

        source_node = self.get_node(source_node_uid)
        if source_node is None:
            return False

        link = source_node.link(gate_type, target_node_uid, slot_type, weight)
        if link is None:
            return False
        else:
            return True

    def create_link(self, source_node_uid, gate_type, target_node_uid, slot_type, weight=1):
        """Creates a new link.

        Arguments.
            source_node_uid: uid of the origin node
            gate_type: type of the origin gate (usually defines the link type)
            target_node_uid: uid of the target node
            slot_type: type of the target slot
            weight: the weight of the link (a float)

        Returns:
            the link if successful,
            None if failure
        """

        source_node = self.get_node(source_node_uid)
        if source_node is None:
            return False, None

        source_node.link(gate_type, target_node_uid, slot_type, weight)
        return True

    def delete_link(self, source_node_uid, gate_type, target_node_uid, slot_type):
        """Delete the given link."""

        source_node = self.get_node(source_node_uid)
        if source_node is None:
            return False, None
        source_node.unlink(gate_type, target_node_uid, slot_type)
        return True

    def construct_modulators_dict(self):
        """
        Returns a new dict containing all modulators
        """
        return self._modulators.copy()

    def get_standard_nodetype_definitions(self):
        """
        Returns the standard node types supported by this nodenet
        """
        return copy.deepcopy(STANDARD_NODETYPES)

    def group_nodes_by_names(self, nodespace_uid, node_name_prefix=None, gatetype="gen", sortby='id', group_name=None):
        if nodespace_uid is None:
            nodespace_uid = self.get_nodespace(None).uid

        if nodespace_uid not in self.nodegroups:
            self.nodegroups[nodespace_uid] = {}

        if group_name is None:
            group_name = node_name_prefix

        nodes = self.netapi.get_nodes(nodespace_uid, node_name_prefix)
        if sortby == 'id':
            nodes = sorted(nodes, key=lambda node: node.uid)
        elif sortby == 'name':
            nodes = sorted(nodes, key=lambda node: node.name)
        self.nodegroups[nodespace_uid][group_name] = (nodes, gatetype)

    def group_nodes_by_ids(self, nodespace_uid, node_uids, group_name, gatetype="gen", sortby='id'):
        if nodespace_uid is None:
            nodespace_uid = self.get_nodespace(None).uid

        if nodespace_uid not in self.nodegroups:
            self.nodegroups[nodespace_uid] = {}

        nodes = []
        for node_uid in node_uids:
            node = self.get_node(node_uid)
            if node.parent_nodespace != nodespace_uid:
                raise ValueError("Node %s is not in nodespace %s" % (node_uid, nodespace_uid))
            nodes.append(node)
        if sortby == 'id':
            nodes = sorted(nodes, key=lambda node: node.uid)
        elif sortby == 'name':
            nodes = sorted(nodes, key=lambda node: node.name)
        self.nodegroups[nodespace_uid][group_name] = (nodes, gatetype)

    def ungroup_nodes(self, nodespace_uid, group):
        if nodespace_uid is None:
            nodespace_uid = self.get_nodespace(None).uid

        if group in self.nodegroups[nodespace_uid]:
            del self.nodegroups[nodespace_uid][group]

    def get_activations(self, nodespace_uid, group):
        if nodespace_uid is None:
            nodespace_uid = self.get_nodespace(None).uid

        if group not in self.nodegroups[nodespace_uid]:
            raise ValueError("Group %s does not exist in nodespace %s" % (group, nodespace_uid))
        activations = []
        nodes = self.nodegroups[nodespace_uid][group][0]
        gate = self.nodegroups[nodespace_uid][group][1]
        for node in nodes:
            activations.append(node.get_gate(gate).activation)
        return activations

    def set_activations(self, nodespace_uid, group, new_activations):
        if nodespace_uid is None:
            nodespace_uid = self.get_nodespace(None).uid

        if group not in self.nodegroups[nodespace_uid]:
            raise ValueError("Group %s does not exist in nodespace %s" % (group, nodespace_uid))
        nodes = self.nodegroups[nodespace_uid][group][0]
        gate = self.nodegroups[nodespace_uid][group][1]
        for i in range(len(nodes)):
            nodes[i].set_gate_activation(gate, new_activations[i])

    def get_gate_configurations(self, nodespace_uid, group, gatefunction_parameter=None):
        if nodespace_uid is None:
            nodespace_uid = self.get_nodespace(None).uid

        if group not in self.nodegroups[nodespace_uid]:
            raise ValueError("Group %s does not exist in nodespace %s" % (group, nodespace_uid))
        nodes = self.nodegroups[nodespace_uid][group][0]
        gate = self.nodegroups[nodespace_uid][group][1]
        data = {'gatefunction': set()}
        if gatefunction_parameter:
            data['parameter_values'] = []
        for node in nodes:
            config = node.get_gate_configuration(gate)
            data['gatefunction'].add(config['gatefunction'])
            if gatefunction_parameter is not None:
                data['parameter_values'].append(config['gatefunction_parameters'].get(gatefunction_parameter, 0))
        if len(data['gatefunction']) > 1:
            raise RuntimeError("Heterogenous gatefunction configuration")
        data['gatefunction'] = data['gatefunction'].pop()
        return data

    def set_gate_configurations(self, nodespace_uid, group, gatefunction, gatefunction_parameter=None, parameter_values=None):
        if nodespace_uid is None:
            nodespace_uid = self.get_nodespace(None).uid

        if group not in self.nodegroups[nodespace_uid]:
            raise ValueError("Group %s does not exist in nodespace %s" % (group, nodespace_uid))
        nodes = self.nodegroups[nodespace_uid][group][0]
        gate = self.nodegroups[nodespace_uid][group][1]
        for i in range(len(nodes)):
            parameter = {}
            if gatefunction_parameter:
                parameter[gatefunction_parameter] = parameter_values[i]
            nodes[i].set_gate_configuration(gate, gatefunction, parameter)

    def get_link_weights(self, nodespace_from_uid, group_from, nodespace_to_uid, group_to):
        if nodespace_from_uid is None:
            nodespace_from_uid = self.get_nodespace(None).uid
        if nodespace_to_uid is None:
            nodespace_to_uid = self.get_nodespace(None).uid

        if group_from not in self.nodegroups[nodespace_from_uid]:
            raise ValueError("Group %s does not exist in nodespace %s" % (group_from, nodespace_from_uid))
        if group_to not in self.nodegroups[nodespace_to_uid]:
            raise ValueError("Group %s does not exist in nodespace %s" % (group_to, nodespace_to_uid))
        rows = []
        to_nodes = self.nodegroups[nodespace_to_uid][group_to][0]
        to_slot = self.nodegroups[nodespace_to_uid][group_to][1]
        from_nodes = self.nodegroups[nodespace_from_uid][group_from][0]
        from_gate = self.nodegroups[nodespace_from_uid][group_from][1]
        for to_node in to_nodes:
            row = []
            for from_node in from_nodes:
                links = from_node.get_gate(from_gate).get_links()
                hit = None
                for link in links:
                    if link.target_node == to_node and link.target_slot.type == to_slot:
                        hit = link
                        break
                if hit is not None:
                    row.append(link.weight)
                else:
                    row.append(0)
            rows.append(row)
        return rows

    def set_link_weights(self, nodespace_from_uid, group_from, nodespace_to_uid, group_to, new_w):
        if nodespace_from_uid is None:
            nodespace_from_uid = self.get_nodespace(None).uid
        if nodespace_to_uid is None:
            nodespace_to_uid = self.get_nodespace(None).uid

        if group_from not in self.nodegroups[nodespace_from_uid]:
            raise ValueError("Group %s does not exist in nodespace %s" % (group_from, nodespace_from_uid))
        if group_to not in self.nodegroups[nodespace_to_uid]:
            raise ValueError("Group %s does not exist in nodespace %s" % (group_to, nodespace_to_uid))
        to_nodes = self.nodegroups[nodespace_to_uid][group_to][0]
        to_slot = self.nodegroups[nodespace_to_uid][group_to][1]
        from_nodes = self.nodegroups[nodespace_from_uid][group_from][0]
        from_gate = self.nodegroups[nodespace_from_uid][group_from][1]

        if type(new_w) == int and new_w == 1:
            if len(from_nodes) != len(to_nodes):
                raise ValueError("from_elements and to_elements need to have equal lengths for identity links")
            for i in range(len(to_nodes)):
                self.set_link_weight(
                    from_nodes[i].uid,
                    from_gate,
                    to_nodes[i].uid,
                    to_slot,
                    1
                )

        else:
            for row in range(len(to_nodes)):
                to_node = to_nodes[row]
                for column in range(len(from_nodes)):
                    from_node = from_nodes[column]
                    weight = new_w[row][column]
                    if weight != 0:
                        self.set_link_weight(from_node.uid, from_gate, to_node.uid, to_slot, weight)
                    else:
                        self.delete_link(from_node.uid, from_gate, to_node.uid, to_slot)

    def get_available_gatefunctions(self):
        """
        Returns a dict of the available gatefunctions and their parameters and parameter-defaults
        """
        import inspect
        from micropsi_core.nodenet import gatefunctions
        data = {}
        for name, func in inspect.getmembers(gatefunctions, inspect.isfunction):
            sig = inspect.signature(func)
            data[name] = {}
            skip = True
            for key in sig.parameters:
                if skip:
                    # first param is input_activation. skip
                    skip = False
                    continue
                default = sig.parameters[key].default
                if default == inspect.Signature.empty:
                    default = None
                data[name][key] = default
        return data

    def has_nodespace_changes(self, nodespace_uids=[], since_step=0):
        if nodespace_uids == []:
            nodespace_uids = self.get_nodespace_uids()

        for nodespace_uid in nodespace_uids:
            if self.get_nodespace(nodespace_uid).contents_last_changed >= since_step:
                return True
        return False

    def get_nodespace_changes(self, nodespace_uids=[], since_step=0, include_links=True):
        result = {
            'nodes_dirty': {},
            'nodespaces_dirty': {},
            'nodes_deleted': [],
            'nodespaces_deleted': []
        }

        if nodespace_uids == []:
            nodespace_uids = self.get_nodespace_uids()
        else:
            nodespace_uids = [self.get_nodespace(uid).uid for uid in nodespace_uids]

        for i in range(since_step, self.current_step + 1):
            if i in self.deleted_items:
                result['nodespaces_deleted'].extend(self.deleted_items[i].get('nodespaces_deleted', []))
                result['nodes_deleted'].extend(self.deleted_items[i].get('nodes_deleted', []))

        for nsuid in nodespace_uids:
            for uid in self.get_nodespace(nsuid).get_known_ids():
                if uid not in result['nodes_deleted'] and self.is_node(uid):
                    if self.get_node(uid).last_changed >= since_step:
                        result['nodes_dirty'][uid] = self.get_node(uid).get_data(include_links=include_links)
                        if include_links:
                            for assoc in self.get_node(uid).get_associated_node_uids():
                                if self.get_node(assoc).parent_nodespace not in nodespace_uids and assoc not in result['nodes_dirty']:
                                    result['nodes_dirty'][assoc] = self.get_node(assoc).get_data(include_links=include_links)

                elif uid not in result['nodespaces_deleted'] and self.is_nodespace(uid):
                    if self.get_nodespace(uid).last_changed >= since_step:
                        result['nodespaces_dirty'][uid] = self.get_nodespace(uid).get_data()
        return result

    def get_dashboard(self):
        data = super(DictNodenet, self).get_dashboard()
        link_uids = []
        node_uids = self.get_node_uids()
        data['count_nodes'] = len(node_uids)
        data['count_positive_nodes'] = 0
        data['count_negative_nodes'] = 0
        data['nodetypes'] = {"NativeModules": 0}
        data['concepts'] = {
            'checking': 0,
            'verified': 0,
            'failed': 0,
            'off': 0
        }
        data['schemas'] = {
            'checking': 0,
            'verified': 0,
            'failed': 0,
            'off': 0,
            'total': 0
        }
        for uid in node_uids:
            node = self.get_node(uid)
            link_uids.extend(node.get_associated_links())
            if node.type in STANDARD_NODETYPES:
                if node.type not in data['nodetypes']:
                    data['nodetypes'][node.type] = 1
                else:
                    data['nodetypes'][node.type] += 1
            else:
                data['nodetypes']['NativeModules'] += 1
            if node.activation > 0:
                data['count_positive_nodes'] += 1
            elif node.activation < 0:
                data['count_negative_nodes'] += 1
            if node.type == 'Pipe':
                if node.get_gate('gen').activation == 0 and node.get_gate('sub').activation > 0 and len(node.get_gate('sub').get_links()):
                    data['concepts']['checking'] += 1
                    if node.get_gate('sur').get_links() == []:
                        data['schemas']['checking'] += 1
                elif node.get_gate('sub').activation > 0 and node.activation > 0.5:
                    data['concepts']['verified'] += 1
                    if node.get_gate('sur').get_links() == []:
                        data['schemas']['verified'] += 1
                elif node.activation < 0:
                    data['concepts']['failed'] += 1
                    if node.get_gate('sur').get_links() == []:
                        data['schemas']['failed'] += 1
                else:
                    data['concepts']['off'] += 1
                    if node.get_gate('sur').get_links() == []:
                        data['schemas']['off'] += 1
        data['concepts']['total'] = sum(data['concepts'].values())
        data['schemas']['total'] = sum(data['schemas'].values())
        data['modulators'] = self.construct_modulators_dict()
        data['count_links'] = len(set(link_uids))
        return data
