# -*- coding: utf-8 -*-

"""
Nodenet definition
"""
import json
import os
import copy
import warnings

import theano
from theano import tensor as T
import numpy as np
import scipy.sparse as sp
import scipy

from micropsi_core.nodenet import monitor
from micropsi_core.nodenet.nodenet import Nodenet
from micropsi_core.nodenet.node import Nodetype
from micropsi_core.nodenet.stepoperators import DoernerianEmotionalModulators
from micropsi_core.nodenet.theano_engine.theano_node import *
from micropsi_core.nodenet.theano_engine.theano_definitions import *
from micropsi_core.nodenet.theano_engine.theano_stepoperators import *
from micropsi_core.nodenet.theano_engine.theano_nodespace import *
from micropsi_core.nodenet.theano_engine.theano_netapi import TheanoNetAPI

from configuration import config as settings


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
    "Pipe": {
        "name": "Pipe",
        "slottypes": ["gen", "por", "ret", "sub", "sur", "cat", "exp"],
        "nodefunction_name": "pipe",
        "gatetypes": ["gen", "por", "ret", "sub", "sur", "cat", "exp"],
        "gate_defaults": {
            "gen": {
                "minimum": -1,
                "maximum": 1,
                "threshold": -1,
                "spreadsheaves": 0
            },
            "por": {
                "minimum": -1,
                "maximum": 1,
                "threshold": -1,
                "spreadsheaves": 0
            },
            "ret": {
                "minimum": -1,
                "maximum": 1,
                "threshold": -1,
                "spreadsheaves": 0
            },
            "sub": {
                "minimum": -1,
                "maximum": 1,
                "threshold": -1,
                "spreadsheaves": True
            },
            "sur": {
                "minimum": -1,
                "maximum": 1,
                "threshold": -1,
                "spreadsheaves": 0
            },
            "cat": {
                "minimum": -1,
                "maximum": 1,
                "threshold": -1,
                "spreadsheaves": 1
            },
            "exp": {
                "minimum": -1,
                "maximum": 1,
                "threshold": -1,
                "spreadsheaves": 0
            }
        },
        "parameters": ["expectation", "wait"],
        "parameter_defaults": {
            "expectation": 1,
            "wait": 10
        },
        'symbol': 'πp'
    },
    "Activator": {
        "name": "Activator",
        "slottypes": ["gen"],
        "parameters": ["type"],
        "parameter_values": {"type": ["por", "ret", "sub", "sur", "cat", "exp"]},
        "nodefunction_name": "activator"
    }
}

NODENET_VERSION = 1

class TheanoNodenet(Nodenet):
    """
        theano runtime engine implementation
    """

    @property
    def engine(self):
        return "theano_engine"

    @property
    def current_step(self):
        return self.__step

    @property
    def data(self):
        data = super(TheanoNodenet, self).data
        data['links'] = self.construct_links_dict()
        data['nodes'] = self.construct_nodes_dict()
        # for uid in data['nodes']:
        #    data['nodes'][uid]['gate_parameters'] = self.get_node(uid).clone_non_default_gate_parameters()
        data['nodespaces'] = self.construct_nodespaces_dict(None)
        data['version'] = self.__version
        data['modulators'] = self.construct_modulators_dict()
        return data

    @property
    def has_new_usages(self):
        return self.__has_new_usages

    @has_new_usages.setter
    def has_new_usages(self, value):
        self.__has_new_usages = value

    @property
    def has_pipes(self):
        return self.__has_pipes

    @has_pipes.setter
    def has_pipes(self, value):
        if value != self.__has_pipes:
            self.__has_new_usages = True
            self.__has_pipes = value

    @property
    def has_directional_activators(self):
        return self.__has_directional_activators

    @has_directional_activators.setter
    def has_directional_activators(self, value):
        if value != self.__has_directional_activators:
            self.__has_new_usages = True
            self.__has_directional_activators = value

    @property
    def has_gatefunction_absolute(self):
        return self.__has_gatefunction_absolute

    @has_gatefunction_absolute.setter
    def has_gatefunction_absolute(self, value):
        if value != self.__has_gatefunction_absolute:
            self.__has_new_usages = True
            self.__has_gatefunction_absolute = value

    @property
    def has_gatefunction_sigmoid(self):
        return self.__has_gatefunction_sigmoid

    @has_gatefunction_sigmoid.setter
    def has_gatefunction_sigmoid(self, value):
        if value != self.__has_gatefunction_sigmoid:
            self.__has_new_usages = True
            self.__has_gatefunction_sigmoid = value

    @property
    def has_gatefunction_tanh(self):
        return self.__has_gatefunction_tanh

    @has_gatefunction_tanh.setter
    def has_gatefunction_tanh(self, value):
        if value != self.__has_gatefunction_tanh:
            self.__has_new_usages = True
            self.__has_gatefunction_tanh = value

    @property
    def has_gatefunction_rect(self):
        return self.__has_gatefunction_rect

    @has_gatefunction_rect.setter
    def has_gatefunction_rect(self, value):
        if value != self.__has_gatefunction_rect:
            self.__has_new_usages = True
            self.__has_gatefunction_rect = value

    @property
    def has_gatefunction_one_over_x(self):
        return self.__has_gatefunction_one_over_x

    @has_gatefunction_one_over_x.setter
    def has_gatefunction_one_over_x(self, value):
        if value != self.__has_gatefunction_one_over_x:
            self.__has_new_usages = True
            self.__has_gatefunction_one_over_x = value

    def __init__(self, name="", worldadapter="Default", world=None, owner="", uid=None, native_modules={}):

        # array, index is node id, value is numeric node type
        self.allocated_nodes = None

        # array, index is node id, value is offset in a and w
        self.allocated_node_offsets = None

        # array, index is node id, value is nodespace id
        self.allocated_node_parents = None

        # array, index is element index, value is node id
        self.allocated_elements_to_nodes = None

        # array, index is nodespace id, value is parent nodespace id
        self.allocated_nodespaces = None

        # directional activator assignment, key is nodespace ID, value is activator ID
        self.allocated_nodespaces_por_activators = None
        self.allocated_nodespaces_ret_activators = None
        self.allocated_nodespaces_sub_activators = None
        self.allocated_nodespaces_sur_activators = None
        self.allocated_nodespaces_cat_activators = None
        self.allocated_nodespaces_exp_activators = None

        # directional activators map, index is element id, value is the directional activator's element id
        self.allocated_elements_to_activators = None

        self.last_allocated_node = 0
        self.last_allocated_offset = 0
        self.last_allocated_nodespace = 0

        self.native_module_instances = {}
        self.comment_instances = {}

        # map of string uids to positions. Not all nodes necessarily have an entry.
        self.positions = {}

        # map of string uids to names. Not all nodes neccessarily have an entry.
        self.names = {}

        # map of data sources to numerical node IDs
        self.sensormap = {}

        # map of numerical node IDs to data sources
        self.inverted_sensor_map = {}

        # map of data targets to numerical node IDs
        self.actuatormap = {}

        # map of numerical node IDs to data targets
        self.inverted_actuator_map = {}

        # theano tensors for performing operations
        self.w = None            # matrix of weights
        self.a = None            # vector of activations
        self.a_shifted = None    # matrix with each row defined as [a[n], a[n+1], a[n+2], a[n+3], a[n+4], a[n+5], a[n+6]]
                            # this is a view on the activation values instrumental in calculating concept node functions

        self.g_factor = None     # vector of gate factors, controlled by directional activators
        self.g_threshold = None  # vector of thresholds (gate parameters)
        self.g_amplification = None  # vector of amplification factors
        self.g_min = None        # vector of lower bounds
        self.g_max = None        # vector of upper bounds

        self.g_function_selector = None # vector of gate function selectors

        self.g_theta = None      # vector of thetas (i.e. biases, use depending on gate function)

        self.g_expect = None     # vector of expectations
        self.g_countdown = None  # vector of number of steps until expectation needs to be met
        self.g_wait = None       # vector of initial values for g_countdown

        self.n_function_selector = None      # vector of per-gate node function selectors
        self.n_node_porlinked = None         # vector with 0/1 flags to indicated whether the element belongs to a por-linked
                                             # node. This could in theory be inferred with T.max() on upshifted versions of w,
                                             # but for now, we manually track this property
        self.n_node_retlinked = None         # same for ret

        self.__por_ret_dirty = True

        self.sparse = True

        self.__has_new_usages = True
        self.__has_pipes = False
        self.__has_directional_activators = False
        self.__has_gatefunction_absolute = False
        self.__has_gatefunction_sigmoid = False
        self.__has_gatefunction_tanh = False
        self.__has_gatefunction_rect = False
        self.__has_gatefunction_one_over_x = False

        super(TheanoNodenet, self).__init__(name, worldadapter, world, owner, uid)

        INITIAL_NUMBER_OF_NODESPACES = 10

        AVERAGE_ELEMENTS_PER_NODE_ASSUMPTION = 4
        configured_elements_per_node_assumption = settings['theano']['elements_per_node_assumption']
        try:
            AVERAGE_ELEMENTS_PER_NODE_ASSUMPTION = int(configured_elements_per_node_assumption)
        except:
            self.logger.warn("Unsupported elements_per_node_assumption value from configuration: %s, falling back to 4", configured_elements_per_node_assumption)

        INITIAL_NUMBER_OF_NODES = 2000
        configured_initial_number_of_nodes = settings['theano']['initial_number_of_nodes']
        try:
            INITIAL_NUMBER_OF_NODES = int(configured_initial_number_of_nodes)
        except:
            self.logger.warn("Unsupported initial_number_of_nodes value from configuration: %s, falling back to 2000", configured_initial_number_of_nodes)

        INITIAL_NUMBER_OF_ELEMENTS = INITIAL_NUMBER_OF_NODES * AVERAGE_ELEMENTS_PER_NODE_ASSUMPTION

        self.sparse = True
        configuredsparse = settings['theano']['sparse_weight_matrix']
        if configuredsparse == "True":
            self.sparse = True
        elif configuredsparse == "False":
            self.sparse = False
        else:
            self.logger.warn("Unsupported sparse_weight_matrix value from configuration: %s, falling back to True", configuredsparse)
            self.sparse = True

        precision = settings['theano']['precision']
        if precision == "32":
            T.config.floatX = "float32"
            self.scipyfloatX = scipy.float32
            self.numpyfloatX = np.float32
            self.byte_per_float = 4
        elif precision == "64":
            T.config.floatX = "float64"
            self.scipyfloatX = scipy.float64
            self.numpyfloatX = np.float64
            self.byte_per_float = 8
        else:
            self.logger.warn("Unsupported precision value from configuration: %s, falling back to float64", precision)
            T.config.floatX = "float64"
            self.scipyfloatX = scipy.float64
            self.numpyfloatX = np.float64
            self.byte_per_float = 8

        device = T.config.device
        self.logger.info("Theano configured to use %s", device)
        if device.startswith("gpu"):
            self.logger.info("Using CUDA with cuda_root=%s and theano_flags=%s", os.environ["CUDA_ROOT"], os.environ["THEANO_FLAGS"])
            if T.config.floatX != "float32":
                self.logger.warn("Precision set to %s, but attempting to use gpu.", precision)

        self.netapi = TheanoNetAPI(self)

        self.NoN = INITIAL_NUMBER_OF_NODES
        self.NoE = INITIAL_NUMBER_OF_ELEMENTS
        self.NoNS = INITIAL_NUMBER_OF_NODESPACES

        self.__version = NODENET_VERSION  # used to check compatibility of the node net data
        self.__step = 0
        self.__modulators = {}
        self.__modulators['por_ret_decay'] = 0.

        self.proxycache = {}

        self.allocated_nodes = np.zeros(self.NoN, dtype=np.int32)
        self.allocated_node_parents = np.zeros(self.NoN, dtype=np.int32)
        self.allocated_node_offsets = np.zeros(self.NoN, dtype=np.int32)
        self.allocated_elements_to_nodes = np.zeros(self.NoE, dtype=np.int32)
        self.allocated_elements_to_activators = np.zeros(self.NoE, dtype=np.int32)
        self.allocated_nodespaces = np.zeros(self.NoNS, dtype=np.int32)

        self.allocated_nodespaces_por_activators = np.zeros(self.NoNS, dtype=np.int32)
        self.allocated_nodespaces_ret_activators = np.zeros(self.NoNS, dtype=np.int32)
        self.allocated_nodespaces_sub_activators = np.zeros(self.NoNS, dtype=np.int32)
        self.allocated_nodespaces_sur_activators = np.zeros(self.NoNS, dtype=np.int32)
        self.allocated_nodespaces_cat_activators = np.zeros(self.NoNS, dtype=np.int32)
        self.allocated_nodespaces_exp_activators = np.zeros(self.NoNS, dtype=np.int32)

        if self.sparse:
            self.w = theano.shared(sp.csr_matrix((self.NoE, self.NoE), dtype=self.scipyfloatX), name="w")
        else:
            w_matrix = np.zeros((self.NoE, self.NoE), dtype=self.scipyfloatX)
            self.w = theano.shared(value=w_matrix.astype(T.config.floatX), name="w", borrow=True)

        a_array = np.zeros(self.NoE, dtype=self.numpyfloatX)
        self.a = theano.shared(value=a_array.astype(T.config.floatX), name="a", borrow=True)

        a_shifted_matrix = np.lib.stride_tricks.as_strided(a_array, shape=(self.NoE, 7), strides=(self.byte_per_float, self.byte_per_float))
        self.a_shifted = theano.shared(value=a_shifted_matrix.astype(T.config.floatX), name="a_shifted", borrow=True)

        g_theta_array = np.zeros(self.NoE, dtype=self.numpyfloatX)
        self.g_theta = theano.shared(value=g_theta_array.astype(T.config.floatX), name="theta", borrow=True)

        g_factor_array = np.ones(self.NoE, dtype=self.numpyfloatX)
        self.g_factor = theano.shared(value=g_factor_array.astype(T.config.floatX), name="g_factor", borrow=True)

        g_threshold_array = np.zeros(self.NoE, dtype=self.numpyfloatX)
        self.g_threshold = theano.shared(value=g_threshold_array.astype(T.config.floatX), name="g_threshold", borrow=True)

        g_amplification_array = np.ones(self.NoE, dtype=self.numpyfloatX)
        self.g_amplification = theano.shared(value=g_amplification_array.astype(T.config.floatX), name="g_amplification", borrow=True)

        g_min_array = np.zeros(self.NoE, dtype=self.numpyfloatX)
        self.g_min = theano.shared(value=g_min_array.astype(T.config.floatX), name="g_min", borrow=True)

        g_max_array = np.ones(self.NoE, dtype=self.numpyfloatX)
        self.g_max = theano.shared(value=g_max_array.astype(T.config.floatX), name="g_max", borrow=True)

        g_function_selector_array = np.zeros(self.NoE, dtype=np.int8)
        self.g_function_selector = theano.shared(value=g_function_selector_array, name="gatefunction", borrow=True)

        g_expect_array = np.ones(self.NoE, dtype=self.numpyfloatX)
        self.g_expect = theano.shared(value=g_expect_array, name="expectation", borrow=True)

        g_countdown_array = np.zeros(self.NoE, dtype=np.int8)
        self.g_countdown = theano.shared(value=g_countdown_array, name="countdown", borrow=True)

        g_wait_array = np.ones(self.NoE, dtype=np.int8)
        self.g_wait = theano.shared(value=g_wait_array, name="wait", borrow=True)

        n_function_selector_array = np.zeros(self.NoE, dtype=np.int8)
        self.n_function_selector = theano.shared(value=n_function_selector_array, name="nodefunction_per_gate", borrow=True)

        n_node_porlinked_array = np.zeros(self.NoE, dtype=np.int8)
        self.n_node_porlinked = theano.shared(value=n_node_porlinked_array, name="porlinked", borrow=True)

        n_node_retlinked_array = np.zeros(self.NoE, dtype=np.int8)
        self.n_node_retlinked = theano.shared(value=n_node_retlinked_array, name="retlinked", borrow=True)

        self.stepoperators = []
        self.initialize_stepoperators()

        self.__nodetypes = {}
        for type, data in STANDARD_NODETYPES.items():
            self.__nodetypes[type] = Nodetype(nodenet=self, **data)

        self.native_module_definitions = native_modules
        self.native_modules = {}
        for type, data in self.native_module_definitions.items():
            self.native_modules[type] = Nodetype(nodenet=self, **data)

        self.nodegroups = {}

        self.create_nodespace(None, None, "Root", nodespace_to_id(1))

        self.initialize_nodenet({})

    def initialize_stepoperators(self):
        self.stepoperators = [
            TheanoPropagate(self),
            TheanoCalculate(self),
            TheanoPORRETDecay(self),
            DoernerianEmotionalModulators()]
        self.stepoperators.sort(key=lambda op: op.priority)

    def save(self, filename):

        # write json metadata, which will be used by runtime to manage the net
        with open(filename, 'w+') as fp:
            metadata = self.metadata
            metadata['positions'] = self.positions
            metadata['names'] = self.names
            metadata['actuatormap'] = self.actuatormap
            metadata['sensormap'] = self.sensormap
            metadata['nodes'] = self.construct_native_modules_and_comments_dict()
            metadata['monitors'] = self.construct_monitors_dict()
            metadata['modulators'] = self.construct_modulators_dict()
            fp.write(json.dumps(metadata, sort_keys=True, indent=4))

        # write bulk data to our own numpy-based file format
        datafilename = os.path.join(os.path.dirname(filename), self.uid + "-data")

        allocated_nodes = self.allocated_nodes
        allocated_node_offsets = self.allocated_node_offsets
        allocated_elements_to_nodes = self.allocated_elements_to_nodes
        allocated_node_parents = self.allocated_node_parents
        allocated_nodespaces = self.allocated_nodespaces
        allocated_elements_to_activators = self.allocated_elements_to_activators

        allocated_nodespaces_por_activators = self.allocated_nodespaces_por_activators
        allocated_nodespaces_ret_activators = self.allocated_nodespaces_ret_activators
        allocated_nodespaces_sub_activators = self.allocated_nodespaces_sub_activators
        allocated_nodespaces_sur_activators = self.allocated_nodespaces_sur_activators
        allocated_nodespaces_cat_activators = self.allocated_nodespaces_cat_activators
        allocated_nodespaces_exp_activators = self.allocated_nodespaces_exp_activators

        w = self.w.get_value(borrow=True)

        # if we're sparse, convert to sparse matrix for persistency
        if not self.sparse:
            w = sp.csr_matrix(w)

        a = self.a.get_value(borrow=True)
        g_theta = self.g_theta.get_value(borrow=True)
        g_factor = self.g_factor.get_value(borrow=True)
        g_threshold = self.g_threshold.get_value(borrow=True)
        g_amplification = self.g_amplification.get_value(borrow=True)
        g_min = self.g_min.get_value(borrow=True)
        g_max = self.g_max.get_value(borrow=True)
        g_function_selector = self.g_function_selector.get_value(borrow=True)
        g_expect = self.g_expect.get_value(borrow=True)
        g_countdown = self.g_countdown.get_value(borrow=True)
        g_wait = self.g_wait.get_value(borrow=True)
        n_function_selector = self.n_function_selector.get_value(borrow=True)

        sizeinformation = [self.NoN, self.NoE, self.NoNS]

        np.savez(datafilename,
                 allocated_nodes=allocated_nodes,
                 allocated_node_offsets=allocated_node_offsets,
                 allocated_elements_to_nodes=allocated_elements_to_nodes,
                 allocated_node_parents=allocated_node_parents,
                 allocated_nodespaces=allocated_nodespaces,
                 w_data=w.data,
                 w_indices=w.indices,
                 w_indptr=w.indptr,
                 a=a,
                 g_theta=g_theta,
                 g_factor=g_factor,
                 g_threshold=g_threshold,
                 g_amplification=g_amplification,
                 g_min=g_min,
                 g_max=g_max,
                 g_function_selector=g_function_selector,
                 g_expect=g_expect,
                 g_countdown=g_countdown,
                 g_wait=g_wait,
                 n_function_selector=n_function_selector,
                 sizeinformation=sizeinformation,
                 allocated_elements_to_activators=allocated_elements_to_activators,
                 allocated_nodespaces_por_activators=allocated_nodespaces_por_activators,
                 allocated_nodespaces_ret_activators=allocated_nodespaces_ret_activators,
                 allocated_nodespaces_sub_activators=allocated_nodespaces_sub_activators,
                 allocated_nodespaces_sur_activators=allocated_nodespaces_sur_activators,
                 allocated_nodespaces_cat_activators=allocated_nodespaces_cat_activators,
                 allocated_nodespaces_exp_activators=allocated_nodespaces_exp_activators)

    def load(self, filename):
        """Load the node net from a file"""
        # try to access file

        datafilename = os.path.join(os.path.dirname(filename), self.uid + "-data.npz")

        with self.netlock:
            initfrom = {}
            datafile = None
            if os.path.isfile(filename):
                try:
                    self.logger.info("Loading nodenet %s metadata from file %s", self.name, filename)
                    with open(filename) as file:
                        initfrom.update(json.load(file))
                except ValueError:
                    warnings.warn("Could not read nodenet metadata from file %s", filename)
                    return False
                except IOError:
                    warnings.warn("Could not open nodenet metadata file %s", filename)
                    return False

            if os.path.isfile(datafilename):
                try:
                    self.logger.info("Loading nodenet %s bulk data from file %s", self.name, datafilename)
                    datafile = np.load(datafilename)
                except ValueError:
                    warnings.warn("Could not read nodenet data from file %", datafile)
                    return False
                except IOError:
                    warnings.warn("Could not open nodenet file %s", datafile)
                    return False

            # initialize with metadata
            self.initialize_nodenet(initfrom)

            if datafile:

                if 'sizeinformation' in datafile:
                    self.NoN = datafile['sizeinformation'][0]
                    self.NoE = datafile['sizeinformation'][1]
                    self.NoNS = datafile['sizeinformation'][2]
                else:
                    self.logger.warn("no sizeinformation in file, falling back to defaults")

                # the load bulk data into numpy arrays
                if 'allocated_nodes' in datafile:
                    self.allocated_nodes = datafile['allocated_nodes']
                else:
                    self.logger.warn("no allocated_nodes in file, falling back to defaults")

                if 'allocated_node_offsets' in datafile:
                    self.allocated_node_offsets = datafile['allocated_node_offsets']
                else:
                    self.logger.warn("no allocated_node_offsets in file, falling back to defaults")

                if 'allocated_elements_to_nodes' in datafile:
                    self.allocated_elements_to_nodes = datafile['allocated_elements_to_nodes']
                else:
                    self.logger.warn("no allocated_elements_to_nodes in file, falling back to defaults")

                if 'allocated_nodespaces' in datafile:
                    self.allocated_nodespaces = datafile['allocated_nodespaces']
                else:
                    self.logger.warn("no allocated_nodespaces in file, falling back to defaults")

                if 'allocated_node_parents' in datafile:
                    self.allocated_node_parents = datafile['allocated_node_parents']
                else:
                    self.logger.warn("no allocated_node_parents in file, falling back to defaults")

                if 'allocated_elements_to_activators' in datafile:
                    self.allocated_elements_to_activators = datafile['allocated_elements_to_activators']
                else:
                    self.logger.warn("no allocated_elements_to_activators in file, falling back to defaults")

                if 'allocated_nodespaces_por_activators' in datafile:
                    self.allocated_nodespaces_por_activators = datafile['allocated_nodespaces_por_activators']
                else:
                    self.logger.warn("no allocated_nodespaces_por_activators in file, falling back to defaults")

                if 'allocated_nodespaces_ret_activators' in datafile:
                    self.allocated_nodespaces_ret_activators = datafile['allocated_nodespaces_ret_activators']
                else:
                    self.logger.warn("no allocated_nodespaces_ret_activators in file, falling back to defaults")

                if 'allocated_nodespaces_sub_activators' in datafile:
                    self.allocated_nodespaces_sub_activators = datafile['allocated_nodespaces_sub_activators']
                else:
                    self.logger.warn("no allocated_nodespaces_sub_activators in file, falling back to defaults")

                if 'allocated_nodespaces_sur_activators' in datafile:
                    self.allocated_nodespaces_sur_activators = datafile['allocated_nodespaces_sur_activators']
                else:
                    self.logger.warn("no allocated_nodespaces_sur_activators in file, falling back to defaults")

                if 'allocated_nodespaces_cat_activators' in datafile:
                    self.allocated_nodespaces_cat_activators = datafile['allocated_nodespaces_cat_activators']
                else:
                    self.logger.warn("no allocated_nodespaces_cat_activators in file, falling back to defaults")

                if 'allocated_nodespaces_exp_activators' in datafile:
                    self.allocated_nodespaces_exp_activators = datafile['allocated_nodespaces_exp_activators']
                else:
                    self.logger.warn("no allocated_nodespaces_exp_activators in file, falling back to defaults")


                if 'w_data' in datafile and 'w_indices' in datafile and 'w_indptr' in datafile:
                    w = sp.csr_matrix((datafile['w_data'], datafile['w_indices'], datafile['w_indptr']), shape = (self.NoE, self.NoE))
                    # if we're configured to be dense, convert from csr
                    if not self.sparse:
                        w = w.todense()
                    self.w = theano.shared(value=w.astype(T.config.floatX), name="w", borrow=False)
                    self.a = theano.shared(value=datafile['a'].astype(T.config.floatX), name="a", borrow=False)
                else:
                    self.logger.warn("no w_data, w_indices or w_indptr in file, falling back to defaults")

                if 'g_theta' in datafile:
                    self.g_theta = theano.shared(value=datafile['g_theta'].astype(T.config.floatX), name="theta", borrow=False)
                else:
                    self.logger.warn("no g_theta in file, falling back to defaults")

                if 'g_factor' in datafile:
                    self.g_factor = theano.shared(value=datafile['g_factor'].astype(T.config.floatX), name="g_factor", borrow=False)
                else:
                    self.logger.warn("no g_factor in file, falling back to defaults")

                if 'g_threshold' in datafile:
                    self.g_threshold = theano.shared(value=datafile['g_threshold'].astype(T.config.floatX), name="g_threshold", borrow=False)
                else:
                    self.logger.warn("no g_threshold in file, falling back to defaults")

                if 'g_amplification' in datafile:
                    self.g_amplification = theano.shared(value=datafile['g_amplification'].astype(T.config.floatX), name="g_amplification", borrow=False)
                else:
                    self.logger.warn("no g_amplification in file, falling back to defaults")

                if 'g_min' in datafile:
                    self.g_min = theano.shared(value=datafile['g_min'].astype(T.config.floatX), name="g_min", borrow=False)
                else:
                    self.logger.warn("no g_min in file, falling back to defaults")

                if 'g_max' in datafile:
                    self.g_max = theano.shared(value=datafile['g_max'].astype(T.config.floatX), name="g_max", borrow=False)
                else:
                    self.logger.warn("no g_max in file, falling back to defaults")

                if 'g_function_selector' in datafile:
                    self.g_function_selector = theano.shared(value=datafile['g_function_selector'], name="gatefunction", borrow=False)
                else:
                    self.logger.warn("no g_function_selector in file, falling back to defaults")

                if 'g_expect' in datafile:
                    self.g_expect = theano.shared(value=datafile['g_expect'], name="expectation", borrow=False)
                else:
                    self.logger.warn("no g_expect in file, falling back to defaults")

                if 'g_countdown' in datafile:
                    self.g_countdown = theano.shared(value=datafile['g_countdown'], name="countdown", borrow=False)
                else:
                    self.logger.warn("no g_countdown in file, falling back to defaults")

                if 'g_wait' in datafile:
                    self.g_wait = theano.shared(value=datafile['g_wait'], name="wait", borrow=False)
                else:
                    self.logger.warn("no g_wait in file, falling back to defaults")

                if 'n_function_selector' in datafile:
                    self.n_function_selector = theano.shared(value=datafile['n_function_selector'], name="nodefunction_per_gate", borrow=False)
                else:
                    self.logger.warn("no n_function_selector in file, falling back to defaults")

                # reconstruct other states

                self.__por_ret_dirty = True

                if 'g_function_selector' in datafile:
                    g_function_selector = datafile['g_function_selector']
                    self.has_new_usages = True
                    self.has_pipes = PIPE in self.allocated_nodes
                    self.has_directional_activators = ACTIVATOR in self.allocated_nodes
                    self.has_gatefunction_absolute = GATE_FUNCTION_ABSOLUTE in g_function_selector
                    self.has_gatefunction_sigmoid = GATE_FUNCTION_SIGMOID in g_function_selector
                    self.has_gatefunction_tanh = GATE_FUNCTION_TANH in g_function_selector
                    self.has_gatefunction_rect = GATE_FUNCTION_RECT in g_function_selector
                    self.has_gatefunction_one_over_x = GATE_FUNCTION_DIST in g_function_selector
                else:
                    self.logger.warn("no g_function_selector in file, falling back to defaults")

                for id in range(len(self.allocated_nodes)):
                    if self.allocated_nodes[id] > MAX_STD_NODETYPE:
                        uid = node_to_id(id)
                        if 'nodes' in initfrom and uid in initfrom['nodes']:
                            self.allocated_nodes[id] = get_numerical_node_type(initfrom['nodes'][uid]['type'], self.native_modules)
                        self.native_module_instances[uid] = self.get_node(uid)
                    elif self.allocated_nodes[id] == COMMENT:
                        uid = node_to_id(id)
                        self.comment_instances[uid] = self.get_node(uid)

                # reloading native modules ensures the types in allocated_nodes are up to date
                # (numerical native module types are runtime dependent and may differ from when allocated_nodes
                # was saved).
                self.reload_native_modules(self.native_module_definitions)

            for sensor, id_list in self.sensormap.items():
                for id in id_list:
                    self.inverted_sensor_map[node_to_id(id)] = sensor
            for actuator, id_list in self.actuatormap.items():
                for id in id_list:
                    self.inverted_actuator_map[node_to_id(id)] = actuator

            # re-initialize step operators for theano recompile to new shared variables
            self.initialize_stepoperators()

            return True

    def remove(self, filename):
        datafilename = os.path.join(os.path.dirname(filename), self.uid + "-data.npz")
        try:
            os.remove(datafilename)
        except IOError:
            pass
        os.remove(filename)

    def initialize_nodenet(self, initfrom):

        self.__modulators.update(initfrom.get("modulators", {}))

        if len(initfrom) != 0:
            # now merge in all init data (from the persisted file typically)
            self.merge_data(initfrom, keep_uids=True)
            if 'names' in initfrom:
                self.names = initfrom['names']
            if 'positions' in initfrom:
                self.positions = initfrom['positions']
            if 'actuatormap' in initfrom:
                self.actuatormap = initfrom['actuatormap']
            if 'sensormap' in initfrom:
                self.sensormap = initfrom['sensormap']

    def merge_data(self, nodenet_data, keep_uids=False):
        """merges the nodenet state with the current node net, might have to give new UIDs to some entities"""

        uidmap = {}
        # for dict_engine compatibility
        uidmap["Root"] = "s1"

        # re-use the root nodespace
        uidmap["s1"] = "s1"

        # merge in spaces, make sure that parent nodespaces exist before children are initialized
        nodespaces_to_merge = set(nodenet_data.get('nodespaces', {}).keys())
        for nodespace in nodespaces_to_merge:
            self.merge_nodespace_data(nodespace, nodenet_data['nodespaces'], uidmap, keep_uids)

        # merge in nodes
        for uid in nodenet_data.get('nodes', {}):
            data = nodenet_data['nodes'][uid]
            parent_uid = data['parent_nodespace']
            if not keep_uids:
                parent_uid = uidmap[data['parent_nodespace']]
            if data['type'] in self.__nodetypes or data['type'] in self.native_modules:
                olduid = None
                if keep_uids:
                    olduid = uid
                new_uid = self.create_node(
                    data['type'],
                    parent_uid,
                    data['position'],
                    name=data['name'],
                    uid=olduid,
                    parameters=data.get('parameters'),
                    gate_parameters=data.get('gate_parameters'),
                    gate_functions=data.get('gate_functions'))
                uidmap[uid] = new_uid
                node_proxy = self.get_node(new_uid)
                for gatetype in data.get('gate_activations', {}):   # todo: implement sheaves
                    if gatetype in node_proxy.nodetype.gatetypes:
                        node_proxy.get_gate(gatetype).activation = data['gate_activations'][gatetype]['default']['activation']
                state = data.get('state', {})
                if state is not None:
                    for key, value in state.items():
                        node_proxy.set_state(key, value)

            else:
                warnings.warn("Invalid nodetype %s for node %s" % (data['type'], uid))

        # merge in links
        for linkid in nodenet_data.get('links', {}):
            data = nodenet_data['links'][linkid]
            self.create_link(
                uidmap[data['source_node_uid']],
                data['source_gate_name'],
                uidmap[data['target_node_uid']],
                data['target_slot_name'],
                data['weight']
            )

        for monitorid in nodenet_data.get('monitors', {}):
            data = nodenet_data['monitors'][monitorid]
            if 'node_uid' in data:
                old_node_uid = data['node_uid']
                if old_node_uid in uidmap:
                    data['node_uid'] = uidmap[old_node_uid]
            if 'classname' in data:
                if hasattr(monitor, data['classname']):
                    getattr(monitor, data['classname'])(self, **data)
                else:
                    self.logger.warn('unknown classname for monitor: %s (uid:%s) ' % (data['classname'], monitorid))
            else:
                # Compatibility mode
                monitor.NodeMonitor(self, name=data['node_name'], **data)

    def merge_nodespace_data(self, nodespace_uid, data, uidmap, keep_uids=False):
        """
        merges the given nodespace with the given nodespace data dict
        This will make sure all parent nodespaces for the given nodespace exist (and create the parents
        if necessary)
        """
        if keep_uids:
            id = nodespace_from_id(nodespace_uid)
            if self.allocated_nodespaces[id] == 0:
                # move up the nodespace tree until we find an existing parent or hit root
                if id != 1:
                    parent_id = nodespace_from_id(data[nodespace_uid].get('parent_nodespace'))
                    if self.allocated_nodespaces[parent_id] == 0:
                        self.merge_nodespace_data(nodespace_to_id(parent_id), data, uidmap, keep_uids)
                self.create_nodespace(
                    data[nodespace_uid].get('parent_nodespace'),
                    data[nodespace_uid].get('position'),
                    name=data[nodespace_uid].get('name', 'Root'),
                    uid=nodespace_uid
                )
        else:
            if not nodespace_uid in uidmap:
                parent_uid = data[nodespace_uid].get('parent_nodespace')
                if not parent_uid in uidmap:
                    self.merge_nodespace_data(parent_uid, data, uidmap, keep_uids)
                newuid = self.create_nodespace(
                    uidmap[data[nodespace_uid].get('parent_nodespace')],
                    data[nodespace_uid].get('position'),
                    name=data[nodespace_uid].get('name', 'Root'),
                    uid=None
                )
                uidmap[nodespace_uid] = newuid

    def step(self):
        self.user_prompt = None
        if self.world is not None and self.world.agents is not None and self.uid in self.world.agents:
            self.world.agents[self.uid].snapshot()      # world adapter snapshot
                                                        # TODO: Not really sure why we don't just know our world adapter,
                                                        # but instead the world object itself

        with self.netlock:

            if self.__por_ret_dirty:
                self.rebuild_por_linked()
                self.rebuild_ret_linked()
                self.__por_ret_dirty = False

            for operator in self.stepoperators:
                operator.execute(self, None, self.netapi)

            self.__step += 1

    def get_node(self, uid):
        if uid in self.native_module_instances:
            return self.native_module_instances[uid]
        elif uid in self.comment_instances:
            return self.comment_instances[uid]
        elif uid in self.proxycache:
            return self.proxycache[uid]
        elif self.is_node(uid):
            id = node_from_id(uid)
            parent_id = self.allocated_node_parents[id]
            node = TheanoNode(self, nodespace_to_id(parent_id), uid, self.allocated_nodes[id])
            self.proxycache[node.uid] = node
            return node
        else:
            raise KeyError("No node with id %s exists", uid)

    def get_node_uids(self):
        return [node_to_id(id) for id in np.nonzero(self.allocated_nodes)[0]]

    def is_node(self, uid):
        numid = node_from_id(uid)
        return numid < self.NoN and self.allocated_nodes[numid] != 0

    def announce_nodes(self, number_of_nodes, average_elements_per_node):
        self.grow_number_of_nodes(number_of_nodes)
        self.grow_number_of_elements(number_of_nodes*average_elements_per_node)

    def grow_number_of_nodes(self, growby):

        new_NoN = int(self.NoN + growby)

        new_allocated_nodes = np.zeros(new_NoN, dtype=np.int32)
        new_allocated_node_parents = np.zeros(new_NoN, dtype=np.int32)
        new_allocated_node_offsets = np.zeros(new_NoN, dtype=np.int32)

        new_allocated_nodes[0:self.NoN] = self.allocated_nodes
        new_allocated_node_parents[0:self.NoN] = self.allocated_node_parents
        new_allocated_node_offsets[0:self.NoN] = self.allocated_node_offsets

        self.NoN = new_NoN
        self.allocated_nodes = new_allocated_nodes
        self.allocated_node_parents = new_allocated_node_parents
        self.allocated_node_offsets = new_allocated_node_offsets
        self.has_new_usages = True

    def grow_number_of_nodespaces(self, growby):

        new_NoNS = int(self.NoNS + growby)

        new_allocated_nodespaces = np.zeros(new_NoNS, dtype=np.int32)
        new_allocated_nodespaces_por_activators = np.zeros(new_NoNS, dtype=np.int32)
        new_allocated_nodespaces_ret_activators = np.zeros(new_NoNS, dtype=np.int32)
        new_allocated_nodespaces_sub_activators = np.zeros(new_NoNS, dtype=np.int32)
        new_allocated_nodespaces_sur_activators = np.zeros(new_NoNS, dtype=np.int32)
        new_allocated_nodespaces_cat_activators = np.zeros(new_NoNS, dtype=np.int32)
        new_allocated_nodespaces_exp_activators = np.zeros(new_NoNS, dtype=np.int32)

        new_allocated_nodespaces[0:self.NoNS] = self.allocated_nodespaces
        new_allocated_nodespaces_por_activators[0:self.NoNS] = self.allocated_nodespaces_por_activators
        new_allocated_nodespaces_ret_activators[0:self.NoNS] = self.allocated_nodespaces_ret_activators
        new_allocated_nodespaces_sub_activators[0:self.NoNS] = self.allocated_nodespaces_sub_activators
        new_allocated_nodespaces_sur_activators[0:self.NoNS] = self.allocated_nodespaces_sur_activators
        new_allocated_nodespaces_cat_activators[0:self.NoNS] = self.allocated_nodespaces_cat_activators
        new_allocated_nodespaces_exp_activators[0:self.NoNS] = self.allocated_nodespaces_exp_activators

        with self.netlock:
            self.NoNS = new_NoNS
            self.allocated_nodespaces = new_allocated_nodespaces
            self.allocated_nodespaces_por_activators = new_allocated_nodespaces_por_activators
            self.allocated_nodespaces_ret_activators = new_allocated_nodespaces_ret_activators
            self.allocated_nodespaces_sub_activators = new_allocated_nodespaces_sub_activators
            self.allocated_nodespaces_sur_activators = new_allocated_nodespaces_sur_activators
            self.allocated_nodespaces_cat_activators = new_allocated_nodespaces_cat_activators
            self.allocated_nodespaces_exp_activators = new_allocated_nodespaces_exp_activators
            self.has_new_usages = True

    def grow_number_of_elements(self, growby):

        new_NoE = int(self.NoE + growby)

        new_allocated_elements_to_nodes = np.zeros(new_NoE, dtype=np.int32)
        new_allocated_elements_to_activators = np.zeros(new_NoE, dtype=np.int32)

        if self.sparse:
            new_w = sp.csr_matrix((new_NoE, new_NoE), dtype=self.scipyfloatX)
        else:
            new_w = np.zeros((new_NoE, new_NoE), dtype=self.scipyfloatX)

        new_a = np.zeros(new_NoE, dtype=self.numpyfloatX)
        new_a_shifted = np.lib.stride_tricks.as_strided(new_a, shape=(new_NoE, 7), strides=(self.byte_per_float, self.byte_per_float))
        new_g_theta = np.zeros(new_NoE, dtype=self.numpyfloatX)
        new_g_factor = np.ones(new_NoE, dtype=self.numpyfloatX)
        new_g_threshold = np.zeros(new_NoE, dtype=self.numpyfloatX)
        new_g_amplification = np.ones(new_NoE, dtype=self.numpyfloatX)
        new_g_min = np.zeros(new_NoE, dtype=self.numpyfloatX)
        new_g_max = np.ones(new_NoE, dtype=self.numpyfloatX)
        new_g_function_selector = np.zeros(new_NoE, dtype=np.int8)
        new_g_expect = np.ones(new_NoE, dtype=self.numpyfloatX)
        new_g_countdown = np.zeros(new_NoE, dtype=np.int8)
        new_g_wait = np.ones(new_NoE, dtype=np.int8)
        new_n_function_selector = np.zeros(new_NoE, dtype=np.int8)
        new_n_node_porlinked = np.zeros(new_NoE, dtype=np.int8)
        new_n_node_retlinked = np.zeros(new_NoE, dtype=np.int8)

        new_allocated_elements_to_nodes[0:self.NoE] = self.allocated_elements_to_nodes
        new_allocated_elements_to_activators[0:self.NoE] = self.allocated_elements_to_activators

        new_w[0:self.NoE, 0:self.NoE] = self.w.get_value(borrow=True)

        new_a[0:self.NoE] = self.a.get_value(borrow=True)
        new_g_theta[0:self.NoE] = self.g_theta.get_value(borrow=True)
        new_g_factor[0:self.NoE] = self.g_factor.get_value(borrow=True)
        new_g_threshold[0:self.NoE] = self.g_threshold.get_value(borrow=True)
        new_g_amplification[0:self.NoE] = self.g_amplification.get_value(borrow=True)
        new_g_min[0:self.NoE] = self.g_min.get_value(borrow=True)
        new_g_max[0:self.NoE] =  self.g_max.get_value(borrow=True)
        new_g_function_selector[0:self.NoE] = self.g_function_selector.get_value(borrow=True)
        new_g_expect[0:self.NoE] = self.g_expect.get_value(borrow=True)
        new_g_countdown[0:self.NoE] = self.g_countdown.get_value(borrow=True)
        new_g_wait[0:self.NoE] = self.g_wait.get_value(borrow=True)
        new_n_function_selector[0:self.NoE] = self.n_function_selector.get_value(borrow=True)
        new_n_node_porlinked[0:self.NoE] = self.n_node_porlinked.get_value(borrow=True)
        new_n_node_retlinked[0:self.NoE] = self.n_node_retlinked.get_value(borrow=True)

        with self.netlock:
            self.NoE = new_NoE
            self.allocated_elements_to_nodes = new_allocated_elements_to_nodes
            self.allocated_elements_to_activators = new_allocated_elements_to_activators
            self.w.set_value(new_w, borrow=True)
            self.a.set_value(new_a, borrow=True)
            self.a_shifted.set_value(new_a_shifted, borrow=True)
            self.g_theta.set_value(new_g_theta, borrow=True)
            self.g_factor.set_value(new_g_factor, borrow=True)
            self.g_threshold.set_value(new_g_threshold, borrow=True)
            self.g_amplification.set_value(new_g_amplification, borrow=True)
            self.g_min.set_value(new_g_min, borrow=True)
            self.g_max.set_value(new_g_max, borrow=True)
            self.g_function_selector.set_value(new_g_function_selector, borrow=True)
            self.g_expect.set_value(new_g_expect, borrow=True)
            self.g_countdown.set_value(new_g_countdown, borrow=True)
            self.g_wait.set_value(new_g_wait, borrow=True)
            self.n_function_selector.set_value(new_n_function_selector, borrow=True)
            self.n_node_porlinked.set_value(new_n_node_porlinked, borrow=True)
            self.n_node_retlinked.set_value(new_n_node_retlinked, borrow=True)
            self.has_new_usages = True

    def create_node(self, nodetype, nodespace_uid, position, name=None, uid=None, parameters=None, gate_parameters=None, gate_functions=None):

        nodespace_uid = self.get_nodespace(nodespace_uid).uid

        # find a free ID / index in the allocated_nodes vector to hold the node type
        if uid is None:
            id = 0
            for i in range((self.last_allocated_node + 1), self.NoN):
                if self.allocated_nodes[i] == 0:
                    id = i
                    break

            if id < 1:
                for i in range(self.last_allocated_node - 1):
                    if self.allocated_nodes[i] == 0:
                        id = i
                        break

            if id < 1:
                growby = self.NoN // 2
                self.logger.info("All %d node IDs in use, growing id vectors by %d elements" % (self.NoN, growby))
                id = self.NoN
                self.grow_number_of_nodes(growby)

        else:
            id = node_from_id(uid)
            if id > self.NoN:
                growby = id - (self.NoN - 2)
                self.grow_number_of_nodes(growby)

        uid = node_to_id(id)

        # now find a range of free elements to be used by this node
        number_of_elements = get_elements_per_type(get_numerical_node_type(nodetype, self.native_modules), self.native_modules)
        has_restarted_from_zero = False
        offset = 0
        i = self.last_allocated_offset + 1
        while offset < 1:
            freecount = 0
            for j in range(0, number_of_elements):
                if i+j < len(self.allocated_elements_to_nodes) and self.allocated_elements_to_nodes[i+j] == 0:
                    freecount += 1
                else:
                    break
            if freecount >= number_of_elements:
                offset = i
                break
            else:
                i += freecount+1

            if i >= self.NoE:
                if not has_restarted_from_zero:
                    i = 0
                    has_restarted_from_zero = True
                else:
                    growby = max(number_of_elements +1, self.NoE // 2)
                    self.logger.info("All %d elements in use, growing elements vectors by %d elements" % (self.NoE, growby))
                    offset = self.NoE
                    self.grow_number_of_elements(growby)

        self.last_allocated_node = id
        self.last_allocated_offset = offset
        self.allocated_nodes[id] = get_numerical_node_type(nodetype, self.native_modules)
        self.allocated_node_parents[id] = nodespace_from_id(nodespace_uid)
        self.allocated_node_offsets[id] = offset

        for element in range (0, get_elements_per_type(self.allocated_nodes[id], self.native_modules)):
            self.allocated_elements_to_nodes[offset + element] = id

        if position is not None:
            self.positions[uid] = position
        if name is not None and name != "" and name != uid:
            self.names[uid] = name

        if parameters is None:
            parameters = {}

        if nodetype == "Sensor":
            if 'datasource' in parameters:
                datasource = parameters['datasource']
                if datasource is not None:
                    connectedsensors = self.sensormap.get(datasource, [])
                    connectedsensors.append(id)
                    self.sensormap[datasource] = connectedsensors
                    self.inverted_sensor_map[uid] = datasource
        elif nodetype == "Actor":
            if 'datatarget' in parameters:
                datatarget = parameters['datatarget']
                if datatarget is not None:
                    connectedactuators = self.actuatormap.get(datatarget, [])
                    connectedactuators.append(id)
                    self.actuatormap[datatarget] = connectedactuators
                    self.inverted_actuator_map[uid] = datatarget
        elif nodetype == "Pipe":
            self.has_pipes = True
            n_function_selector_array = self.n_function_selector.get_value(borrow=True)
            n_function_selector_array[offset + GEN] = NFPG_PIPE_GEN
            n_function_selector_array[offset + POR] = NFPG_PIPE_POR
            n_function_selector_array[offset + RET] = NFPG_PIPE_RET
            n_function_selector_array[offset + SUB] = NFPG_PIPE_SUB
            n_function_selector_array[offset + SUR] = NFPG_PIPE_SUR
            n_function_selector_array[offset + CAT] = NFPG_PIPE_CAT
            n_function_selector_array[offset + EXP] = NFPG_PIPE_EXP
            self.n_function_selector.set_value(n_function_selector_array, borrow=True)
            self.allocated_elements_to_activators[offset + POR] = \
                self.allocated_node_offsets[self.allocated_nodespaces_por_activators[nodespace_from_id(nodespace_uid)]]
            self.allocated_elements_to_activators[offset + RET] = \
                self.allocated_node_offsets[self.allocated_nodespaces_ret_activators[nodespace_from_id(nodespace_uid)]]
            self.allocated_elements_to_activators[offset + SUB] = \
                self.allocated_node_offsets[self.allocated_nodespaces_sub_activators[nodespace_from_id(nodespace_uid)]]
            self.allocated_elements_to_activators[offset + SUR] = \
                self.allocated_node_offsets[self.allocated_nodespaces_sur_activators[nodespace_from_id(nodespace_uid)]]
            self.allocated_elements_to_activators[offset + CAT] = \
                self.allocated_node_offsets[self.allocated_nodespaces_cat_activators[nodespace_from_id(nodespace_uid)]]
            self.allocated_elements_to_activators[offset + EXP] = \
                self.allocated_node_offsets[self.allocated_nodespaces_exp_activators[nodespace_from_id(nodespace_uid)]]

            if self.__nodetypes[nodetype].parameter_defaults.get('expectation'):
                value = self.__nodetypes[nodetype].parameter_defaults['expectation']
                g_expect_array = self.g_expect.get_value(borrow=True)
                g_expect_array[offset + SUR] = float(value)
                g_expect_array[offset + POR] = float(value)
                self.g_expect.set_value(g_expect_array, borrow=True)

            if self.__nodetypes[nodetype].parameter_defaults.get('wait'):
                value = self.__nodetypes[nodetype].parameter_defaults['wait']
                g_wait_array = self.g_wait.get_value(borrow=True)
                g_wait_array[offset + SUR] = int(min(value, 128))
                g_wait_array[offset + POR] = int(min(value, 128))
                self.g_wait.set_value(g_wait_array, borrow=True)
        elif nodetype == "Activator":
            self.has_directional_activators = True
            activator_type = parameters.get("type")
            if activator_type is not None and len(activator_type) > 0:
                self.set_nodespace_gatetype_activator(nodespace_uid, activator_type, uid)

        if nodetype not in STANDARD_NODETYPES:
            node_proxy = self.get_node(uid)
            self.native_module_instances[uid] = node_proxy
            for key, value in parameters.items():
                node_proxy.set_parameter(key, value)
        elif nodetype == "Comment":
            node_proxy = self.get_node(uid)
            self.comment_instances[uid] = node_proxy
            for key, value in parameters.items():
                node_proxy.set_parameter(key, value)

        for gate, parameters in self.get_nodetype(nodetype).gate_defaults.items():
            if gate in self.get_nodetype(nodetype).gatetypes:
                for gate_parameter in parameters:
                    self.set_node_gate_parameter(uid, gate, gate_parameter, parameters[gate_parameter])
        if gate_parameters is not None:
            for gate, parameters in gate_parameters.items():
                if gate in self.get_nodetype(nodetype).gatetypes:
                    for gate_parameter in parameters:
                        self.set_node_gate_parameter(uid, gate, gate_parameter, parameters[gate_parameter])

        if gate_functions is not None:
            for gate, gate_function in gate_functions.items():
                if gate in self.get_nodetype(nodetype).gatetypes:
                    self.set_node_gatefunction_name(uid, gate, gate_function)

        # initialize activation to zero
        a_array = self.a.get_value(borrow=True)
        for element in range (0, get_elements_per_type(get_numerical_node_type(nodetype, self.native_modules), self.native_modules)):
            a_array[offset + element] = 0
        self.a.set_value(a_array)

        return uid

    def delete_node(self, uid):

        type = self.allocated_nodes[node_from_id(uid)]
        offset = self.allocated_node_offsets[node_from_id(uid)]
        parent = self.allocated_node_parents[node_from_id(uid)]

        # unlink
        self.get_node(uid).unlink_completely()

        # forget
        self.allocated_nodes[node_from_id(uid)] = 0
        self.allocated_node_offsets[node_from_id(uid)] = 0
        self.allocated_node_parents[node_from_id(uid)] = 0
        g_function_selector_array = self.g_function_selector.get_value(borrow=True)
        for element in range (0, get_elements_per_type(type, self.native_modules)):
            self.allocated_elements_to_nodes[offset + element] = 0
            g_function_selector_array[offset + element] = 0
        self.g_function_selector.set_value(g_function_selector_array, borrow=True)
        self.allocated_elements_to_nodes[np.where(self.allocated_elements_to_nodes == node_from_id(uid))[0]] = 0

        if type == PIPE:
            n_function_selector_array = self.n_function_selector.get_value(borrow=True)
            n_function_selector_array[offset + GEN] = NFPG_PIPE_NON
            n_function_selector_array[offset + POR] = NFPG_PIPE_NON
            n_function_selector_array[offset + RET] = NFPG_PIPE_NON
            n_function_selector_array[offset + SUB] = NFPG_PIPE_NON
            n_function_selector_array[offset + SUR] = NFPG_PIPE_NON
            n_function_selector_array[offset + CAT] = NFPG_PIPE_NON
            n_function_selector_array[offset + EXP] = NFPG_PIPE_NON
            self.n_function_selector.set_value(n_function_selector_array, borrow=True)

        # clear from proxycache
        if uid in self.proxycache:
            del self.proxycache[uid]

        # clear from name and positions dicts
        if uid in self.names:
            del self.names[uid]
        if uid in self.positions:
            del self.positions[uid]

        # hint at the free ID
        self.last_allocated_node = node_from_id(uid) - 1

        # remove the native module or comment instance if there should be one
        if uid in self.native_module_instances:
            del self.native_module_instances[uid]
        if uid in self.comment_instances:
            del self.comment_instances[uid]

        # remove sensor association if there should be one
        if uid in self.inverted_sensor_map:
            sensor = self.inverted_sensor_map[uid]
            del self.inverted_sensor_map[uid]
            if sensor in self.sensormap:
                self.sensormap[sensor].remove(node_from_id(uid))
                if len(self.sensormap[sensor]) == 0:
                    del self.sensormap[sensor]

        # remove actuator association if there should be one
        if uid in self.inverted_actuator_map:
            actuator = self.inverted_actuator_map[uid]
            del self.inverted_actuator_map[uid]
            if actuator in self.actuatormap:
                self.actuatormap[actuator].remove(node_from_id(uid))
                if len(self.actuatormap[actuator]) == 0:
                    del self.actuatormap[actuator]

        # clear activator usage if there should be one
        used_as_activator_by = np.where(self.allocated_elements_to_activators == offset)
        if len(used_as_activator_by) > 0:
            self.allocated_elements_to_activators[used_as_activator_by] = 0

        if self.allocated_nodespaces_por_activators[parent] == node_from_id(uid):
            self.allocated_nodespaces_por_activators[parent] = 0
        elif self.allocated_nodespaces_ret_activators[parent] == node_from_id(uid):
            self.allocated_nodespaces_ret_activators[parent] = 0
        elif self.allocated_nodespaces_sub_activators[parent] == node_from_id(uid):
            self.allocated_nodespaces_sub_activators[parent] = 0
        elif self.allocated_nodespaces_sur_activators[parent] == node_from_id(uid):
            self.allocated_nodespaces_sur_activators[parent] = 0
        elif self.allocated_nodespaces_cat_activators[parent] == node_from_id(uid):
            self.allocated_nodespaces_cat_activators[parent] = 0
        elif self.allocated_nodespaces_exp_activators[parent] == node_from_id(uid):
            self.allocated_nodespaces_exp_activators[parent] = 0

    def set_node_gate_parameter(self, uid, gate_type, parameter, value):
        id = node_from_id(uid)
        numerical_node_type = self.allocated_nodes[id]
        nodetype = None
        if numerical_node_type > MAX_STD_NODETYPE:
            nodetype = self.get_nodetype(get_string_node_type(numerical_node_type, self.native_modules))

        elementindex = self.allocated_node_offsets[id] + get_numerical_gate_type(gate_type, nodetype)
        if parameter == 'threshold':
            g_threshold_array = self.g_threshold.get_value(borrow=True)
            g_threshold_array[elementindex] = value
            self.g_threshold.set_value(g_threshold_array, borrow=True)
        elif parameter == 'amplification':
            g_amplification_array = self.g_amplification.get_value(borrow=True)
            g_amplification_array[elementindex] = value
            self.g_amplification.set_value(g_amplification_array, borrow=True)
        elif parameter == 'minimum':
            g_min_array = self.g_min.get_value(borrow=True)
            g_min_array[elementindex] = value
            self.g_min.set_value(g_min_array, borrow=True)
        elif parameter == 'maximum':
            g_max_array = self.g_max.get_value(borrow=True)
            g_max_array[elementindex] = value
            self.g_max.set_value(g_max_array, borrow=True)
        elif parameter == 'theta':
            g_theta_array = self.g_theta.get_value(borrow=True)
            g_theta_array[elementindex] = value
            self.g_theta.set_value(g_theta_array, borrow=True)

    def set_node_gatefunction_name(self, uid, gate_type, gatefunction_name):
        id = node_from_id(uid)
        numerical_node_type = self.allocated_nodes[id]
        nodetype = None
        if numerical_node_type > MAX_STD_NODETYPE:
            nodetype = self.get_nodetype(get_string_node_type(numerical_node_type, self.native_modules))

        elementindex = self.allocated_node_offsets[id] + get_numerical_gate_type(gate_type, nodetype)
        g_function_selector = self.g_function_selector.get_value(borrow=True)
        g_function_selector[elementindex] = get_numerical_gatefunction_type(gatefunction_name)
        self.g_function_selector.set_value(g_function_selector, borrow=True)
        if g_function_selector[elementindex] == GATE_FUNCTION_ABSOLUTE:
            self.has_gatefunction_absolute = True
        elif g_function_selector[elementindex] == GATE_FUNCTION_SIGMOID:
            self.has_gatefunction_sigmoid = True
        elif g_function_selector[elementindex] == GATE_FUNCTION_TANH:
            self.has_gatefunction_tanh = True
        elif g_function_selector[elementindex] == GATE_FUNCTION_RECT:
            self.has_gatefunction_rect = True
        elif g_function_selector[elementindex] == GATE_FUNCTION_DIST:
            self.has_gatefunction_one_over_x = True

    def set_nodespace_gatetype_activator(self, nodespace_uid, gate_type, activator_uid):

        activator_id = 0
        if activator_uid is not None and len(activator_uid) > 0:
            activator_id = node_from_id(activator_uid)

        nodespace_id = nodespace_from_id(nodespace_uid)

        if gate_type == "por":
            self.allocated_nodespaces_por_activators[nodespace_id] = activator_id
        elif gate_type == "ret":
            self.allocated_nodespaces_ret_activators[nodespace_id] = activator_id
        elif gate_type == "sub":
            self.allocated_nodespaces_sub_activators[nodespace_id] = activator_id
        elif gate_type == "sur":
            self.allocated_nodespaces_sur_activators[nodespace_id] = activator_id
        elif gate_type == "cat":
            self.allocated_nodespaces_cat_activators[nodespace_id] = activator_id
        elif gate_type == "exp":
            self.allocated_nodespaces_exp_activators[nodespace_id] = activator_id

        nodes_in_nodespace = np.where(self.allocated_node_parents == nodespace_id)[0]
        for nid in nodes_in_nodespace:
            if self.allocated_nodes[nid] == PIPE:
                self.allocated_elements_to_activators[self.allocated_node_offsets[nid] +
                                                      get_numerical_gate_type(gate_type)] = self.allocated_node_offsets[activator_id]

    def get_nodespace(self, uid):
        if uid is None:
            uid = nodespace_to_id(1)

        if uid in self.proxycache:
            return self.proxycache[uid]
        else:
            nodespace = TheanoNodespace(self, uid)
            self.proxycache[uid] = nodespace
            return nodespace

    def get_nodespace_uids(self):
        ids = [nodespace_to_id(id) for id in np.nonzero(self.allocated_nodespaces)[0]]
        ids.append(nodespace_to_id(1))
        return ids

    def is_nodespace(self, uid):
        return uid in self.get_nodespace_uids()

    def create_nodespace(self, parent_uid, position, name="", uid=None):

        # find a free ID / index in the allocated_nodespaces vector to hold the nodespaces's parent
        if uid is None:
            id = 0
            for i in range((self.last_allocated_nodespace + 1), self.NoNS):
                if self.allocated_nodespaces[i] == 0:
                    id = i
                    break

            if id < 1:
                for i in range(self.last_allocated_nodespace - 1):
                    if self.allocated_nodespaces[i] == 0:
                        id = i
                        break

            if id < 1:
                growby = self.NoNS // 2
                self.logger.info("All %d nodespace IDs in use, growing nodespace ID vector by %d elements" % (self.NoNS, growby))
                id = self.NoNS
                self.grow_number_of_nodespaces(growby)
        else:
            id = nodespace_from_id(uid)

        self.last_allocated_nodespace = id

        parent_id = 0
        if parent_uid is not None:
            parent_id = nodespace_from_id(parent_uid)
        elif id != 1:
            parent_id = 1

        uid = nodespace_to_id(id)

        self.allocated_nodespaces[id] = parent_id
        if name is not None and len(name) > 0 and name != uid:
            self.names[uid] = name
        if position is not None:
            self.positions[uid] = position

        return uid

    def delete_nodespace(self, uid):
        nodespace_id = nodespace_from_id(uid)
        children_ids = np.where(self.allocated_nodespaces == nodespace_id)[0]
        for child_id in children_ids:
            self.delete_nodespace(nodespace_to_id(child_id))
        node_ids = np.where(self.allocated_node_parents == nodespace_id)[0]
        for node_id in node_ids:
            self.delete_node(node_to_id(node_id))

        # clear from proxycache
        if uid in self.proxycache:
            del self.proxycache[uid]

        # clear from name and positions dicts
        if uid in self.names:
            del self.names[uid]
        if uid in self.positions:
            del self.positions[uid]

        self.allocated_nodespaces[nodespace_id] = 0

        self.last_allocated_nodespace = nodespace_id

    def get_sensors(self, nodespace=None, datasource=None):
        sensors = {}
        sensorlist = []
        if datasource is None:
            for ds_sensors in self.sensormap.values():
                sensorlist.extend(ds_sensors)
        elif datasource in self.sensormap:
            sensorlist = self.sensormap[datasource]
        for id in sensorlist:
            if nodespace is None or self.allocated_node_parents[id] == nodespace_from_id(nodespace):
                uid = node_to_id(id)
                sensors[uid] = self.get_node(uid)
        return sensors

    def get_actors(self, nodespace=None, datatarget=None):
        actuators = {}
        actuatorlist = []
        if datatarget is None:
            for dt_actuators in self.actuatormap.values():
                actuatorlist.extend(dt_actuators)
        elif datatarget in self.actuatormap:
            actuatorlist = self.actuatormap[datatarget]
        for id in actuatorlist:
            if nodespace is None or self.allocated_node_parents[id] == nodespace_from_id(nodespace):
                uid = node_to_id(id)
                actuators[uid] = self.get_node(uid)
        return actuators

    def create_link(self, source_node_uid, gate_type, target_node_uid, slot_type, weight=1, certainty=1):
        self.set_link_weight(source_node_uid, gate_type, target_node_uid, slot_type, weight)
        return True

    def set_link_weight(self, source_node_uid, gate_type, target_node_uid, slot_type, weight=1, certainty=1):

        source_nodetype = None
        target_nodetype = None
        if self.allocated_nodes[node_from_id(source_node_uid)] > MAX_STD_NODETYPE:
            source_nodetype = self.get_nodetype(get_string_node_type(self.allocated_nodes[node_from_id(source_node_uid)], self.native_modules))
        if self.allocated_nodes[node_from_id(target_node_uid)] > MAX_STD_NODETYPE:
            target_nodetype = self.get_nodetype(get_string_node_type(self.allocated_nodes[node_from_id(target_node_uid)], self.native_modules))

        ngt = get_numerical_gate_type(gate_type, source_nodetype)
        nst = get_numerical_slot_type(slot_type, target_nodetype)
        w_matrix = self.w.get_value(borrow=True)
        x = self.allocated_node_offsets[node_from_id(target_node_uid)] + nst
        y = self.allocated_node_offsets[node_from_id(source_node_uid)] + ngt
        if self.sparse:
            w_matrix[x, y] = weight
        else:
            w_matrix[x][y] = weight
        self.w.set_value(w_matrix, borrow=True)

        if slot_type == "por" and self.allocated_nodes[node_from_id(target_node_uid)] == PIPE:
            n_node_porlinked_array = self.n_node_porlinked.get_value(borrow=True)
            if weight == 0:
                for g in range(7):
                    n_node_porlinked_array[self.allocated_node_offsets[node_from_id(target_node_uid)] + g] = 0
            else:
                for g in range(7):
                    n_node_porlinked_array[self.allocated_node_offsets[node_from_id(target_node_uid)] + g] = 1
            self.n_node_porlinked.set_value(n_node_porlinked_array, borrow=True)

        if slot_type == "ret" and self.allocated_nodes[node_from_id(target_node_uid)] == PIPE:
            n_node_retlinked_array = self.n_node_retlinked.get_value(borrow=True)
            if weight == 0:
                for g in range(7):
                    n_node_retlinked_array[self.allocated_node_offsets[node_from_id(target_node_uid)] + g] = 0
            else:
                for g in range(7):
                    n_node_retlinked_array[self.allocated_node_offsets[node_from_id(target_node_uid)] + g] = 1
            self.n_node_retlinked.set_value(n_node_retlinked_array, borrow=True)

        if weight == 0:
            linkid = "%s:%s:%s:%s" % (source_node_uid, gate_type, slot_type, target_node_uid)
            if linkid in self.proxycache:
                del self.proxycache[linkid]

        return True

    def delete_link(self, source_node_uid, gate_type, target_node_uid, slot_type):
        self.set_link_weight(source_node_uid, gate_type, target_node_uid, slot_type, 0)
        return True

    def reload_native_modules(self, native_modules):

        self.native_module_definitions = native_modules

        # check which instances need to be recreated because of gate/slot changes and keep their .data
        instances_to_recreate = {}
        instances_to_delete = {}
        for uid, instance in self.native_module_instances.items():
            if instance.type not in native_modules:
                self.logger.warn("No more definition available for node type %s, deleting instance %s" %
                                (instance.type, uid))
                instances_to_delete[uid] = instance
                continue

            numeric_id = node_from_id(uid)
            number_of_elements = len(np.where(self.allocated_elements_to_nodes == numeric_id)[0])
            new_numer_of_elements = max(len(native_modules[instance.type]['slottypes']), len(native_modules[instance.type]['gatetypes']))
            if number_of_elements != new_numer_of_elements:
                self.logger.warn("Number of elements changed for node type %s from %d to %d, recreating instance %s" %
                                (instance.type, number_of_elements, new_numer_of_elements, uid))
                instances_to_recreate[uid] = instance.data

        # actually remove the instances
        for uid in instances_to_delete.keys():
            self.delete_node(uid)
        for uid in instances_to_recreate.keys():
            self.delete_node(uid)

        # update the node functions of all Nodetypes
        self.native_modules = {}
        for type, data in native_modules.items():
            self.native_modules[type] = Nodetype(nodenet=self, **native_modules[type])

        # update the living instances that have the same slot/gate numbers
        new_instances = {}
        for id, instance in self.native_module_instances.items():
            parameters = instance.clone_parameters()
            state = instance.clone_state()
            position = instance.position
            name = instance.name
            new_native_module_instance = TheanoNode(self, instance.parent_nodespace, id, self.allocated_nodes[node_from_id(id)])
            new_native_module_instance.position = position
            new_native_module_instance.name = name
            for key, value in parameters.items():
                new_native_module_instance.set_parameter(key, value)
            for key, value in state.items():
                new_native_module_instance.set_state(key, value)
            new_instances[id] = new_native_module_instance
        self.native_module_instances = new_instances

        # recreate the deleted ones. Gate configurations and links will not be transferred.
        for uid, data in instances_to_recreate.items():
            new_uid = self.create_node(
                data['type'],
                data['parent_nodespace'],
                data['position'],
                name=data['name'],
                uid=uid,
                parameters=data['parameters'])

        # update native modules numeric types, as these may have been set with a different native module
        # node types list
        native_module_ids = np.where(self.allocated_nodes > MAX_STD_NODETYPE)[0]
        for id in native_module_ids:
            instance = self.get_node(node_to_id(id))
            self.allocated_nodes[id] = get_numerical_node_type(instance.type, self.native_modules)

    def get_nodespace_data(self, nodespace_uid, include_links):
        data = {
            'links': {},
            'nodes': self.construct_nodes_dict(nodespace_uid, self.NoN),
            'nodespaces': self.construct_nodespaces_dict(nodespace_uid),
            'monitors': self.construct_monitors_dict(),
            'modulators': self.construct_modulators_dict()
        }
        if include_links:
            data['links'] = self.construct_links_dict(nodespace_uid)

            followupnodes = []
            for uid in data['nodes']:
                followupnodes.extend(self.get_node(uid).get_associated_node_uids())

            for uid in followupnodes:
                if self.allocated_node_parents[node_from_id(uid)] != nodespace_from_id(nodespace_uid):
                    data['nodes'][uid] = self.get_node(uid).data

        if self.user_prompt is not None:
            data['user_prompt'] = self.user_prompt.copy()
            self.user_prompt = None
        return data

    def get_modulator(self, modulator):
        return self.__modulators.get(modulator, 1)

    def change_modulator(self, modulator, diff):
        self.__modulators[modulator] = self.__modulators.get(modulator, 0) + diff

    def set_modulator(self, modulator, value):
        self.__modulators[modulator] = value

    def get_nodetype(self, type):
        if type in self.__nodetypes:
            return self.__nodetypes[type]
        else:
            return self.native_modules.get(type)

    def construct_links_dict(self, nodespace_uid=None):
        data = {}
        if nodespace_uid is not None:
            parent = nodespace_from_id(nodespace_uid)
            node_ids = np.where(self.allocated_node_parents == parent)[0]
        else:
            node_ids = np.nonzero(self.allocated_nodes)[0]
        w_matrix = self.w.get_value(borrow=True)
        for source_id in node_ids:
            source_type = self.allocated_nodes[source_id]
            for gate_type in range(get_elements_per_type(source_type, self.native_modules)):
                gatecolumn = w_matrix[:, self.allocated_node_offsets[source_id] + gate_type]
                links_indices = np.nonzero(gatecolumn)[0]
                for index in links_indices:
                    target_id = self.allocated_elements_to_nodes[index]
                    if nodespace_uid is not None:
                        if self.allocated_node_parents[source_id] != parent and self.allocated_node_parents[target_id] != parent:
                            continue
                    target_type = self.allocated_nodes[target_id]
                    target_slot_numerical = index - self.allocated_node_offsets[target_id]
                    target_slot_type = get_string_slot_type(target_slot_numerical, self.get_nodetype(get_string_node_type(target_type, self.native_modules)))
                    source_gate_type = get_string_gate_type(gate_type, self.get_nodetype(get_string_node_type(source_type, self.native_modules)))
                    if self.sparse:               # sparse matrices return matrices of dimension (1,1) as values
                        weight = float(gatecolumn[index].data)
                    else:
                        weight = gatecolumn[index].item()

                    linkuid = "n%i:%s:%s:n%i" % (source_id, source_gate_type, target_slot_type, target_id)
                    linkdata = {
                        "uid": linkuid,
                        "weight": weight,
                        "certainty": 1,
                        "source_gate_name": source_gate_type,
                        "source_node_uid": node_to_id(source_id),
                        "target_slot_name": target_slot_type,
                        "target_node_uid": node_to_id(target_id)
                    }
                    data[linkuid] = linkdata
        return data

    def construct_native_modules_and_comments_dict(self):
        data = {}
        i = 0
        nodeids = np.where((self.allocated_nodes > MAX_STD_NODETYPE) | (self.allocated_nodes == COMMENT))[0]
        for node_id in nodeids:
            i += 1
            node_uid = node_to_id(node_id)
            data[node_uid] = self.get_node(node_uid).data
        return data

    def construct_nodes_dict(self, nodespace_uid=None, max_nodes=-1):
        data = {}
        i = 0
        nodeids = np.nonzero(self.allocated_nodes)[0]
        if nodespace_uid is not None:
            parent_id = nodespace_from_id(nodespace_uid)
            nodeids = np.where(self.allocated_node_parents == parent_id)[0]
        for node_id in nodeids:
            i += 1
            node_uid = node_to_id(node_id)
            data[node_uid] = self.get_node(node_uid).data
            if max_nodes > 0 and i > max_nodes:
                break
        return data

    def construct_nodespaces_dict(self, nodespace_uid):
        data = {}
        if nodespace_uid is None:
            nodespace_uid = self.get_nodespace(None).uid

        nodespace_id = nodespace_from_id(nodespace_uid)
        nodespace_ids = np.nonzero(self.allocated_nodespaces)[0]
        nodespace_ids = np.append(nodespace_ids, 1)
        for candidate_id in nodespace_ids:
            is_in_hierarchy = False
            if candidate_id == nodespace_id:
                is_in_hierarchy = True
            else:
                parent_id = self.allocated_nodespaces[candidate_id]
                while parent_id > 0 and parent_id != nodespace_id:
                    parent_id = self.allocated_nodespaces[parent_id]
                if parent_id == nodespace_id:
                    is_in_hierarchy = True

            if is_in_hierarchy:
                data[nodespace_to_id(candidate_id)] = self.get_nodespace(nodespace_to_id(candidate_id)).data

        return data

    def construct_modulators_dict(self):
        return self.__modulators.copy()

    def get_standard_nodetype_definitions(self):
        """
        Returns the standard node types supported by this nodenet
        """
        return copy.deepcopy(STANDARD_NODETYPES)

    def set_sensors_and_actuator_feedback_to_values(self, datasource_to_value_map, datatarget_to_value_map):
        """
        Sets the sensors for the given data sources to the given values
        """

        a_array = self.a.get_value(borrow=True)

        for datasource in datasource_to_value_map:
            value = datasource_to_value_map.get(datasource)
            sensor_uids = self.sensormap.get(datasource, [])

            for sensor_uid in sensor_uids:
                a_array[self.allocated_node_offsets[sensor_uid] + GEN] = value

        for datatarget in datatarget_to_value_map:
            value = datatarget_to_value_map.get(datatarget)
            actuator_uids = self.actuatormap.get(datatarget, [])

            for actuator_uid in actuator_uids:
                a_array[self.allocated_node_offsets[actuator_uid] + GEN] = value

        self.a.set_value(a_array, borrow=True)

    def read_actuators(self):
        """
        Returns a map of datatargets to values for writing back to the world adapter
        """

        actuator_values_to_write = {}

        a_array = self.a.get_value(borrow=True)

        for datatarget in self.actuatormap:
            actuator_node_activations = 0
            for actuator_id in self.actuatormap[datatarget]:
                actuator_node_activations += a_array[self.allocated_node_offsets[actuator_id] + GEN]

            actuator_values_to_write[datatarget] = actuator_node_activations

        self.a.set_value(a_array, borrow=True)

        return actuator_values_to_write

    def group_nodes_by_names(self, nodespace=None, node_name_prefix=None, gatetype="gen", sortby='id'):
        ids = []
        for uid, name in self.names.items():
            if name.startswith(node_name_prefix) and \
                    (nodespace is None or self.allocated_node_parents[node_from_id(uid)] == nodespace_from_id(nodespace)):
                ids.append(uid)
        self.group_nodes_by_ids(ids, node_name_prefix, gatetype, sortby)

    def group_nodes_by_ids(self, node_ids, group_name, gatetype="gen", sortby='id'):
        ids = [node_from_id(uid) for uid in node_ids]
        if sortby == 'id':
            ids = sorted(ids)
        elif sortby == 'name':
            ids = sorted(ids, key=lambda id: self.names[node_to_id(id)])
        gate = get_numerical_gate_type(gatetype)
        self.nodegroups[group_name] = self.allocated_node_offsets[ids] + gate

    def ungroup_nodes(self, group):
        if group in self.nodegroups:
            del self.nodegroups[group]

    def dump_group(self, group):
        ids = self.nodegroups[group]
        for element in ids:
            nid = self.allocated_elements_to_nodes[element]
            uid = node_to_id(nid)
            node = self.get_node(uid)
            print("%s %s" % (node.uid, node.name))

    def get_activations(self, group):
        if group not in self.nodegroups:
            raise ValueError("Group %s does not exist." % group)
        a_array = self.a.get_value(borrow=True)
        return a_array[self.nodegroups[group]]

    def set_activations(self, group, new_activations):
        if group not in self.nodegroups:
            raise ValueError("Group %s does not exist." % group)
        a_array = self.a.get_value(borrow=True)
        a_array[self.nodegroups[group]] = new_activations
        self.a.set_value(a_array, borrow=True)

    def get_thetas(self, group):
        if group not in self.nodegroups:
            raise ValueError("Group %s does not exist." % group)
        g_theta_array = self.g_theta.get_value(borrow=True)
        return g_theta_array[self.nodegroups[group]]

    def set_thetas(self, group, thetas):
        if group not in self.nodegroups:
            raise ValueError("Group %s does not exist." % group)
        g_theta_array = self.g_theta.get_value(borrow=True)
        g_theta_array[self.nodegroups[group]] = thetas
        self.g_theta.set_value(g_theta_array, borrow=True)

    def get_link_weights(self, group_from, group_to):
        if group_from not in self.nodegroups:
            raise ValueError("Group %s does not exist." % group_from)
        if group_to not in self.nodegroups:
            raise ValueError("Group %s does not exist." % group_to)
        w_matrix = self.w.get_value(borrow=True)
        cols, rows = np.meshgrid(self.nodegroups[group_from], self.nodegroups[group_to])
        if self.sparse:
            return w_matrix[rows,cols].todense()
        else:
            return w_matrix[rows,cols]

    def set_link_weights(self, group_from, group_to, new_w):
        if group_from not in self.nodegroups:
            raise ValueError("Group %s does not exist." % group_from)
        if group_to not in self.nodegroups:
            raise ValueError("Group %s does not exist." % group_to)
        w_matrix = self.w.get_value(borrow=True)
        grp_from = self.nodegroups[group_from]
        grp_to = self.nodegroups[group_to]
        cols, rows = np.meshgrid(grp_from, grp_to)
        w_matrix[rows, cols] = new_w
        self.w.set_value(w_matrix, borrow=True)

        if self.has_pipes:
            self.__por_ret_dirty = True

    def get_available_gatefunctions(self):
        return ["identity", "absolute", "sigmoid", "tanh", "rect", "one_over_x"]

    def rebuild_shifted(self):
        a_array = self.a.get_value(borrow=True)
        a_rolled_array = np.roll(a_array, 7)
        a_shifted_matrix = np.lib.stride_tricks.as_strided(a_rolled_array, shape=(self.NoE, 14), strides=(self.byte_per_float, self.byte_per_float))
        self.a_shifted.set_value(a_shifted_matrix, borrow=True)

    def rebuild_por_linked(self):

        n_node_porlinked_array = np.zeros(self.NoE, dtype=np.int8)

        n_function_selector_array = self.n_function_selector.get_value(borrow=True)
        w_matrix = self.w.get_value(borrow=True)

        por_indices = np.where(n_function_selector_array == NFPG_PIPE_POR)[0]

        slotrows = w_matrix[por_indices, :]
        if not self.sparse:
            linkedflags = np.any(slotrows, axis=1)
        else:
            # for some reason, sparse matrices won't do any with an axis parameter, so we need to do this...
            max_values = slotrows.max(axis=1).todense()
            linkedflags = max_values.astype(np.int8, copy=False)
            linkedflags = np.minimum(linkedflags, 1)

        n_node_porlinked_array[por_indices - 1] = linkedflags       # gen
        n_node_porlinked_array[por_indices] = linkedflags           # por
        n_node_porlinked_array[por_indices + 1] = linkedflags       # ret
        n_node_porlinked_array[por_indices + 2] = linkedflags       # sub
        n_node_porlinked_array[por_indices + 3] = linkedflags       # sur
        n_node_porlinked_array[por_indices + 4] = linkedflags       # sub
        n_node_porlinked_array[por_indices + 5] = linkedflags       # sur

        self.n_node_porlinked.set_value(n_node_porlinked_array)

    def rebuild_ret_linked(self):

        n_node_retlinked_array = np.zeros(self.NoE, dtype=np.int8)

        n_function_selector_array = self.n_function_selector.get_value(borrow=True)
        w_matrix = self.w.get_value(borrow=True)

        ret_indices = np.where(n_function_selector_array == NFPG_PIPE_RET)[0]

        slotrows = w_matrix[ret_indices, :]
        if not self.sparse:
            linkedflags = np.any(slotrows, axis=1)
        else:
            # for some reason, sparse matrices won't do any with an axis parameter, so we need to do this...
            max_values = slotrows.max(axis=1).todense()
            linkedflags = max_values.astype(np.int8, copy=False)
            linkedflags = np.minimum(linkedflags, 1)

        n_node_retlinked_array[ret_indices - 2] = linkedflags       # gen
        n_node_retlinked_array[ret_indices - 1] = linkedflags       # por
        n_node_retlinked_array[ret_indices] = linkedflags           # ret
        n_node_retlinked_array[ret_indices + 1] = linkedflags       # sub
        n_node_retlinked_array[ret_indices + 2] = linkedflags       # sur
        n_node_retlinked_array[ret_indices + 3] = linkedflags       # cat
        n_node_retlinked_array[ret_indices + 4] = linkedflags       # exp

        self.n_node_retlinked.set_value(n_node_retlinked_array)