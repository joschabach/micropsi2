__author__ = 'rvuine'

import json
import os

import warnings
from micropsi_core.nodenet import monitor
from micropsi_core.nodenet.node import Nodetype
from micropsi_core.nodenet.nodenet import Nodenet, NODENET_VERSION, NodenetLockException
from .dict_stepoperators import DictPropagate, DictPORRETDecay, DictCalculate, DictDoernerianEmotionalModulators
from .dict_node import DictNode
from .dict_nodespace import DictNodespace
import copy

STANDARD_NODETYPES = {
    "Nodespace": {
        "name": "Nodespace"
    },

    "Comment": {
        "name": "Comment",
        "symbol": "#",
        'parameters': ['comment'],
        "shape": "Rectangle"
    },

    "Register": {
        "name": "Register",
        "slottypes": ["gen"],
        "nodefunction_name": "register",
        "gatetypes": ["gen"]
    },
    "Sensor": {
        "name": "Sensor",
        "parameters": ["datasource"],
        "nodefunction_name": "sensor",
        "gatetypes": ["gen"]
    },
    "Actor": {
        "name": "Actor",
        "parameters": ["datatarget"],
        "nodefunction_name": "actor",
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
        "gatetypes": ["gen", "por", "ret", "sub", "sur", "cat", "exp", "sym", "ref"],
        "gate_defaults": {
            "por": {
                "threshold": -1
            },
            "ret": {
                "threshold": -1
            },
            "sub": {
                "threshold": -1
            },
            "sur": {
                "threshold": -1
            }
        }
    },
    "Pipe": {
        "name": "Pipe",
        "slottypes": ["gen", "por", "ret", "sub", "sur", "cat", "exp"],
        "nodefunction_name": "pipe",
        "gatetypes": ["gen", "por", "ret", "sub", "sur", "cat", "exp"],
        "gate_defaults": {
            "gen": {
                "minimum": -100,
                "maximum": 100,
                "threshold": -100,
                "spreadsheaves": 0
            },
            "por": {
                "minimum": -100,
                "maximum": 100,
                "threshold": -100,
                "spreadsheaves": 0
            },
            "ret": {
                "minimum": -100,
                "maximum": 100,
                "threshold": -100,
                "spreadsheaves": 0
            },
            "sub": {
                "minimum": -100,
                "maximum": 100,
                "threshold": -100,
                "spreadsheaves": True
            },
            "sur": {
                "minimum": -100,
                "maximum": 100,
                "threshold": -100,
                "spreadsheaves": 0
            },
            "cat": {
                "minimum": -100,
                "maximum": 100,
                "threshold": -100,
                "spreadsheaves": 1
            },
            "exp": {
                "minimum": -100,
                "maximum": 100,
                "threshold": -100,
                "spreadsheaves": 0
            }
        },
        'symbol': 'πp',
        'shape': 'Rectangle'
    },
    "Trigger": {
        "name": "Trigger",
        "slottypes": ["gen", "sub", "sur"],
        "nodefunction_name": "trigger",
        "gatetypes": ["gen", "sub", "sur"],
        "gate_defaults": {
            "gen": {
                "minimum": -100,
                "maximum": 100,
                "threshold": -100,
                "spreadsheaves": 0
            },
            "sub": {
                "minimum": -100,
                "maximum": 100,
                "threshold": -100,
                "spreadsheaves": 0
            },
            "sur": {
                "minimum": -100,
                "maximum": 100,
                "threshold": -100,
                "spreadsheaves": 0
            }
        },
        "parameters": ["timeout", "condition", "response"],
        "parameter_values": {
            "condition": ["=", ">"]
        }
    },
    "Activator": {
        "name": "Activator",
        "slottypes": ["gen"],
        "parameters": ["type"],
        "parameter_values": {"type": ["gen", "por", "ret", "sub", "sur", "cat", "exp", "sym", "ref"]},
        "nodefunction_name": "activator"
    }
}

class DictNodenet(Nodenet):
    """Main data structure for MicroPsi agents,

    Contains the net entities and runs the activation spreading. The nodenet stores persistent data.

    Attributes:
        state: a dict of persistent nodenet data; everything stored within the state can be stored and exported
        uid: a unique identifier for the node net
        name: an optional name for the node net
        filename: the path and file name to the file storing the persisted net data
        nodespaces: a dictionary of node space UIDs and respective node spaces
        nodes: a dictionary of node UIDs and respective nodes
        links: a dictionary of link UIDs and respective links
        gate_types: a dictionary of gate type names and the individual types of gates
        slot_types: a dictionary of slot type names and the individual types of slots
        node_types: a dictionary of node type names and node type definitions
        world: an environment for the node net
        worldadapter: an actual world adapter object residing in a world implementation, provides interface
        owner: an id of the user who created the node net
        step: the current simulation step of the node net
    """

    @property
    def data(self):
        data = super(DictNodenet, self).data
        data['links'] = self.construct_links_dict()
        data['nodes'] = self.construct_nodes_dict()
        for uid in data['nodes']:
            data['nodes'][uid]['gate_parameters'] = self.get_node(uid).clone_non_default_gate_parameters()
        data['nodespaces'] = self.construct_nodespaces_dict("Root")
        data['version'] = self.__version
        data['modulators'] = self.construct_modulators_dict()
        return data

    @property
    def engine(self):
        return "dict_engine"

    @property
    def current_step(self):
        return self.__step

    def __init__(self, filename, name="", worldadapter="Default", world=None, owner="", uid=None, native_modules={}):
        """Create a new MicroPsi agent.

        Arguments:
            filename: the path and filename of the agent
            agent_type (optional): the interface of this agent to its environment
            name (optional): the name of the agent
            owner (optional): the user that created this agent
            uid (optional): unique handle of the agent; if none is given, it will be generated
        """

        super(DictNodenet, self).__init__(name or os.path.basename(filename), worldadapter, world, owner, uid)

        self.stepoperators = [DictPropagate(), DictCalculate(), DictPORRETDecay(), DictDoernerianEmotionalModulators()]
        self.stepoperators.sort(key=lambda op: op.priority)

        self.__version = NODENET_VERSION  # used to check compatibility of the node net data
        self.__step = 0
        self.__modulators = {}
        self.settings = {}

        self.filename = filename
        if world and worldadapter:
            self.worldadapter = worldadapter

        self.__nodes = {}
        self.__nodetypes = STANDARD_NODETYPES
        self.__native_modules = native_modules
        self.__nodespaces = {}
        self.__nodespaces["Root"] = DictNodespace(self, None, (0, 0), name="Root", uid="Root")

        self.__locks = {}
        self.__nodes_by_coords = {}

        self.load()

    def load(self, string=None):
        """Load the node net from a file"""
        # try to access file
        with self.netlock:

            initfrom = {}

            if string:
                self.logger.info("Loading nodenet %s from string", self.name)
                try:
                    initfrom.update(json.loads(string))
                except ValueError:
                    warnings.warn("Could not read nodenet data from string")
                    return False
            else:
                try:
                    self.logger.info("Loading nodenet %s from file %s", self.name, self.filename)
                    with open(self.filename) as file:
                        initfrom.update(json.load(file))
                except ValueError:
                    warnings.warn("Could not read nodenet data")
                    return False
                except IOError:
                    warnings.warn("Could not open nodenet file")

            if self.__version == NODENET_VERSION:
                self.initialize_nodenet(initfrom)
                return True
            else:
                raise NotImplementedError("Wrong version of nodenet data, cannot import.")

    def reload_native_modules(self, native_modules):
        """ reloads the native-module definition, and their nodefunctions
        and afterwards reinstantiates the nodenet."""
        self.__native_modules = {}
        for key in native_modules:
            self.__native_modules[key] = Nodetype(nodenet=self, **native_modules[key])
            self.__native_modules[key].reload_nodefunction()
        saved = self.data
        self.clear()
        self.merge_data(saved)

    def initialize_nodespace(self, id, data):
        if id not in self.__nodespaces:
            # move up the nodespace tree until we find an existing parent or hit root
            while id != 'Root' and data[id].get('parent_nodespace') not in self.__nodespaces:
                self.initialize_nodespace(data[id]['parent_nodespace'], data)
            self.__nodespaces[id] = DictNodespace(self,
                data[id].get('parent_nodespace'),
                data[id].get('position'),
                name=data[id].get('name', 'Root'),
                uid=id,
                index=data[id].get('index'),
                gatefunction_strings=data[id].get('gatefunctions'))

    def initialize_nodenet(self, initfrom):
        """Called after reading new nodenet state.

        Parses the nodenet state and set up the non-persistent data structures necessary for efficient
        computation of the node net
        """

        nodetypes = {}
        for type, data in self.__nodetypes.items():
            nodetypes[type] = Nodetype(nodenet=self, **data)
        self.__nodetypes = nodetypes

        native_modules = {}
        for type, data in self.__native_modules.items():
            native_modules[type] = Nodetype(nodenet=self, **data)
        self.__native_modules = native_modules

        self.__modulators = initfrom.get("modulators", {})

        # set up nodespaces; make sure that parent nodespaces exist before children are initialized
        self.__nodespaces = {}
        self.__nodespaces["Root"] = DictNodespace(self, None, (0, 0), name="Root", uid="Root")

        # now merge in all init data (from the persisted file typically)
        self.merge_data(initfrom)

    def construct_links_dict(self):
        data = {}
        for node_uid in self.get_node_uids():
            links = self.get_node(node_uid).get_associated_links()
            for link in links:
                data[link.uid] = link.data
        return data

    def construct_nodes_dict(self, max_nodes=-1):
        data = {}
        i = 0
        for node_uid in self.get_node_uids():
            i += 1
            data[node_uid] = self.get_node(node_uid).data
            if max_nodes > 0 and i > max_nodes:
                break
        return data

    def construct_nodespaces_dict(self, nodespace_uid):
        data = {}
        for nodespace_candidate_uid in self.get_nodespace_uids():
            if self.get_nodespace(nodespace_candidate_uid).parent_nodespace == nodespace_uid or nodespace_candidate_uid == nodespace_uid:
                data[nodespace_candidate_uid] = self.get_nodespace(nodespace_candidate_uid).data
        return data

    def get_nodetype(self, type):
        """ Returns the nodetpype instance for the given nodetype or native_module or None if not found"""
        if type in self.__nodetypes:
            return self.__nodetypes[type]
        else:
            return self.__native_modules.get(type)

    def get_nodespace_area_data(self, nodespace, x1, x2, y1, y2):
        x_range = (x1 - (x1 % 100), 100 + x2 - (x2 % 100), 100)
        y_range = (y1 - (y1 % 100), 100 + y2 - (y2 % 100), 100)

        world_uid = self.world.uid if self.world is not None else None

        data = {
            'links': {},
            'nodes': {},
            'name': self.name,
            'max_coords': {'x': 0, 'y': 0},
            'is_active': self.is_active,
            'current_step': self.current_step,
            'nodespaces': self.construct_nodespaces_dict(nodespace),
            'world': world_uid,
            'worldadapter': self.worldadapter,
            'modulators': self.construct_modulators_dict()
        }
        if self.user_prompt is not None:
            data['user_prompt'] = self.user_prompt.copy()
            self.user_prompt = None
        links = []
        followupnodes = []
        for x in range(*x_range):
            if x in self.__nodes_by_coords:
                for y in range(*y_range):
                    if y in self.__nodes_by_coords[x]:
                        for uid in self.__nodes_by_coords[x][y]:
                            if self.get_node(uid).parent_nodespace == nodespace:  # maybe sort directly by nodespace??
                                node = self.get_node(uid)
                                data['nodes'][uid] = node.data
                                if node.position[0] > data['max_coords']['x']:
                                    data['max_coords']['x'] = node.position[0]
                                if node.position[1] > data['max_coords']['y']:
                                    data['max_coords']['y'] = node.position[1]
                                links.extend(self.get_node(uid).get_associated_links())
                                followupnodes.extend(self.get_node(uid).get_associated_node_uids())
        for link in links:
            data['links'][link.uid] = link.data
        for uid in followupnodes:
            if uid not in data['nodes']:
                data['nodes'][uid] = self.get_node(uid).data
        return data

    def update_node_positions(self):
        """ recalculates the position hash """
        self.__nodes_by_coords = {}
        self.max_coords = {'x': 0, 'y': 0}
        for uid in self.get_node_uids():
            pos = self.get_node(uid).position
            xpos = int(pos[0] - (pos[0] % 100))
            ypos = int(pos[1] - (pos[1] % 100))
            if xpos not in self.__nodes_by_coords:
                self.__nodes_by_coords[xpos] = {}
                if xpos > self.max_coords['x']:
                    self.max_coords['x'] = xpos
            if ypos not in self.__nodes_by_coords[xpos]:
                self.__nodes_by_coords[xpos][ypos] = []
                if ypos > self.max_coords['y']:
                    self.max_coords['y'] = ypos
            self.__nodes_by_coords[xpos][ypos].append(uid)

    def delete_node(self, node_uid):
        if node_uid in self.__nodespaces:
            affected_entity_ids = self.__nodespaces[node_uid].get_known_ids()
            for uid in affected_entity_ids:
                self.delete_node(uid)
            parent_nodespace = self.__nodespaces.get(self.__nodespaces[node_uid].parent_nodespace)
            if parent_nodespace and parent_nodespace.is_entity_known_as('nodespaces', node_uid):
                parent_nodespace._unregister_entity('nodespaces', node_uid)
            del self.__nodespaces[node_uid]
        else:
            node = self.__nodes[node_uid]
            node.unlink_completely()
            parent_nodespace = self.__nodespaces.get(self.__nodes[node_uid].parent_nodespace)
            parent_nodespace._unregister_entity('nodes', node_uid)
            if self.__nodes[node_uid].type == "Activator":
                parent_nodespace.unset_activator_value(self.__nodes[node_uid].get_parameter('type'))
            del self.__nodes[node_uid]
            self.update_node_positions()

    def delete_nodespace(self, uid):
        self.delete_node(uid)

    def get_nodespace_data(self, nodespace_uid, max_nodes):
        """returns the nodes and links in a given nodespace"""
        data = {
            'nodes': self.construct_nodes_dict(max_nodes),
            'links': self.construct_links_dict(),
            'nodespaces': self.construct_nodespaces_dict(nodespace_uid),
            'monitors': self.construct_monitors_dict()
        }
        if self.user_prompt is not None:
            data['user_prompt'] = self.user_prompt.copy()
            self.user_prompt = None
        return data

    def clear(self):
        super(DictNodenet, self).clear()
        self.__nodes = {}

        self.__nodes_by_coords = {}
        self.max_coords = {'x': 0, 'y': 0}

        self.__nodespaces = {}
        DictNodespace(self, None, (0, 0), "Root", "Root")

    def _register_node(self, node):
        self.__nodes[node.uid] = node

    def _register_nodespace(self, nodespace):
        self.__nodespaces[nodespace.uid] = nodespace

    def merge_data(self, nodenet_data):
        """merges the nodenet state with the current node net, might have to give new UIDs to some entities"""

        # Because of the horrible initialize_nodenet design that replaces existing dictionary objects with
        # Python objects between initial loading and first use, none of the nodenet setup code is reusable.
        # Instantiation should be a state-independent method or a set of state-independent methods that can be
        # called whenever new data needs to be merged in, initially or later on.
        # Potentially, initialize_nodenet can be replaced with merge_data.

        # net will have the name of the one to be merged into us
        self.name = nodenet_data['name']

        # merge in spaces, make sure that parent nodespaces exist before children are initialized
        nodespaces_to_merge = set(nodenet_data.get('nodespaces', {}).keys())
        for nodespace in nodespaces_to_merge:
            self.initialize_nodespace(nodespace, nodenet_data['nodespaces'])

        # merge in nodes
        for uid in nodenet_data.get('nodes', {}):
            data = nodenet_data['nodes'][uid]
            if data['type'] in self.__nodetypes or data['type'] in self.__native_modules:
                self.__nodes[uid] = DictNode(self, **data)
                pos = self.__nodes[uid].position
                xpos = int(pos[0] - (pos[0] % 100))
                ypos = int(pos[1] - (pos[1] % 100))
                if xpos not in self.__nodes_by_coords:
                    self.__nodes_by_coords[xpos] = {}
                    if xpos > self.max_coords['x']:
                        self.max_coords['x'] = xpos
                if ypos not in self.__nodes_by_coords[xpos]:
                    self.__nodes_by_coords[xpos][ypos] = []
                    if ypos > self.max_coords['y']:
                        self.max_coords['y'] = ypos
                self.__nodes_by_coords[xpos][ypos].append(uid)
            else:
                warnings.warn("Invalid nodetype %s for node %s" % (data['type'], uid))

        # merge in links
        for uid in nodenet_data.get('links', {}):
            data = nodenet_data['links'][uid]
            if data['source_node_uid'] in self.__nodes:
                source_node = self.__nodes[data['source_node_uid']]
                source_node.link(data['source_gate_name'],
                                 data['target_node_uid'],
                                 data['target_slot_name'],
                                 data['weight'],
                                 data['certainty'])

        for uid in nodenet_data.get('monitors', {}):
            data = nodenet_data['monitors'][uid]
            if 'classname' in data:
                if hasattr(monitor, data['classname']):
                    getattr(monitor, data['classname'])(self, **data)
                else:
                    self.logger.warn('unknown classname for monitor: %s (uid:%s) ' % (data['classname'], uid))
            else:
                # Compatibility mode
                monitor.NodeMonitor(self, name=data['node_name'], **data)

    def step(self):
        """perform a simulation step"""
        self.user_prompt = None
        if self.world is not None and self.world.agents is not None and self.uid in self.world.agents:
            self.world.agents[self.uid].snapshot()      # world adapter snapshot
                                                        # TODO: Not really sure why we don't just know our world adapter,
                                                        # but instead the world object itself

        with self.netlock:

            self.timeout_locks()

            for operator in self.stepoperators:
                operator.execute(self, self.__nodes.copy(), self.netapi)

            self.netapi._step()

            self.__step += 1

    def timeout_locks(self):
        """
        Removes all locks that time out in the current step
        """
        locks_to_delete = []
        for lock, data in self.__locks.items():
            self.__locks[lock] = (data[0] + 1, data[1], data[2])
            if data[0] + 1 >= data[1]:
                locks_to_delete.append(lock)
        for lock in locks_to_delete:
            del self.__locks[lock]

    def create_node(self, nodetype, nodespace_uid, position, name="", uid=None, parameters=None, gate_parameters=None):
        node = DictNode(
            self,
            nodespace_uid,
            position, name=name,
            type=nodetype,
            uid=uid,
            parameters=parameters,
            gate_parameters=gate_parameters)
        self.update_node_positions()
        return node.uid

    def create_nodespace(self, parent_uid, position, name="", uid=None, gatefunction_strings=None):
        nodespace = DictNodespace(self, parent_uid, position=position, name=name, uid=uid, gatefunction_strings=gatefunction_strings)
        return nodespace.uid

    def get_node(self, uid):
        return self.__nodes[uid]

    def get_nodespace(self, uid):
        return self.__nodespaces[uid]

    def get_node_uids(self):
        return list(self.__nodes.keys())

    def get_nodespace_uids(self):
        return list(self.__nodespaces.keys())

    def is_node(self, uid):
        return uid in self.__nodes

    def is_nodespace(self, uid):
        return uid in self.__nodespaces

    def get_nativemodules(self, nodespace=None):
        """Returns a dict of native modules. Optionally filtered by the given nodespace"""
        nodes = self.__nodes if nodespace is None else self.__nodespaces[nodespace].get_known_ids('nodes')
        nativemodules = {}
        for uid in nodes:
            if self.__nodes[uid].type not in STANDARD_NODETYPES:
                nativemodules.update({uid: self.__nodes[uid]})
        return nativemodules

    def get_activators(self, nodespace=None, type=None):
        """Returns a dict of activator nodes. OPtionally filtered by the given nodespace and the given type"""
        nodes = self.__nodes if nodespace is None else self.__nodespaces[nodespace].get_known_ids('nodes')
        activators = {}
        for uid in nodes:
            if self.__nodes[uid].type == 'Activator':
                if type is None or type == self.__nodes[uid].get_parameter('type'):
                    activators.update({uid: self.__nodes[uid]})
        return activators

    def get_sensors(self, nodespace=None):
        """Returns a dict of all sensor nodes. Optionally filtered by the given nodespace"""
        nodes = self.__nodes if nodespace is None else self.__nodespaces[nodespace].get_known_ids('nodes')
        sensors = {}
        for uid in nodes:
            if self.__nodes[uid].type == 'Sensor':
                sensors[uid] = self.__nodes[uid]
        return sensors

    def get_actors(self, nodespace=None):
        """Returns a dict of all sensor nodes. Optionally filtered by the given nodespace"""
        nodes = self.__nodes if nodespace is None else self.__nodespaces[nodespace].get_known_ids('nodes')
        actors = {}
        for uid in nodes:
            if self.__nodes[uid].type == 'Actor':
                actors[uid] = self.__nodes[uid]
        return actors

    def set_link_weight(self, source_node_uid, gate_type, target_node_uid, slot_type, weight=1, certainty=1):
        """Set weight of the given link."""

        source_node = self.get_node(source_node_uid)
        if source_node is None:
            return False

        link = source_node.link(gate_type, target_node_uid, slot_type, weight, certainty)
        if link is None:
            return False
        else:
            return True

    def create_link(self, source_node_uid, gate_type, target_node_uid, slot_type, weight=1, certainty=1):
        """Creates a new link.

        Arguments.
            source_node_uid: uid of the origin node
            gate_type: type of the origin gate (usually defines the link type)
            target_node_uid: uid of the target node
            slot_type: type of the target slot
            weight: the weight of the link (a float)
            certainty (optional): a probabilistic parameter for the link

        Returns:
            the link if successful,
            None if failure
        """

        source_node = self.get_node(source_node_uid)
        if source_node is None:
            return False, None

        link = source_node.link(gate_type, target_node_uid, slot_type, weight, certainty)
        if link is None:
            return False, None
        else:
            return True, link

    def delete_link(self, source_node_uid, gate_type, target_node_uid, slot_type):
        """Delete the given link."""

        source_node = self.get_node(source_node_uid)
        if source_node is None:
            return False, None
        source_node.unlink(gate_type, target_node_uid, slot_type)
        return True

    def is_locked(self, lock):
        """Returns true if a lock of the given name exists"""
        return lock in self.__locks

    def is_locked_by(self, lock, key):
        """Returns true if a lock of the given name exists and the key used is the given one"""
        return lock in self.__locks and self.__locks[lock][2] == key

    def lock(self, lock, key, timeout=100):
        """Creates a lock with the given name that will time out after the given number of steps
        """
        if self.is_locked(lock):
            raise NodenetLockException("Lock %s is already locked." % lock)
        self.__locks[lock] = (0, timeout, key)

    def unlock(self, lock):
        """Removes the given lock
        """
        del self.__locks[lock]

    def get_modulator(self, modulator):
        """
        Returns the numeric value of the given global modulator
        """
        return self.__modulators.get(modulator, 1)

    def change_modulator(self, modulator, diff):
        """
        Changes the value of the given global modulator by the value of diff
        """
        self.__modulators[modulator] = self.__modulators.get(modulator, 0) + diff

    def construct_modulators_dict(self):
        """
        Returns a new dict containing all modulators
        """
        return self.__modulators.copy()

    def set_modulator(self, modulator, value):
        """
        Changes the value of the given global modulator to the given value
        """
        self.__modulators[modulator] = value

    def get_standard_nodetype_definitions(self):
        """
        Returns the standard node types supported by this nodenet
        """
        return copy.deepcopy(STANDARD_NODETYPES)
