REGISTER = 1
SENSOR = 2
ACTUATOR = 3
ACTIVATOR = 4
CONCEPT = 5
SCRIPT = 6
PIPE = 7
LSTM = 8
COMMENT = 9

MAX_STD_NODETYPE = COMMENT

GEN = 0
POR = 1
RET = 2
SUB = 3
SUR = 4
CAT = 5
EXP = 6
GIN = 2
GOU = 3
GFG = 4

GATE_FUNCTION_IDENTITY = 0
GATE_FUNCTION_ABSOLUTE = 1
GATE_FUNCTION_SIGMOID = 2
#GATE_FUNCTION_TANH = 3
GATE_FUNCTION_RELU = 4
GATE_FUNCTION_DIST = 5
GATE_FUNCTION_ELU = 6
GATE_FUNCTION_THRESHOLD = 7


NFPG_PIPE_NON = 0
NFPG_PIPE_GEN = 1
NFPG_PIPE_POR = 2
NFPG_PIPE_RET = 3
NFPG_PIPE_SUB = 4
NFPG_PIPE_SUR = 5
NFPG_PIPE_CAT = 6
NFPG_PIPE_EXP = 7
NFPG_LSTM_GEN = 8
NFPG_LSTM_POR = 9
NFPG_LSTM_GIN = 10
NFPG_LSTM_GOU = 11
NFPG_LSTM_GFG = 10


def get_numerical_gate_type(type, nodetype=None):
    if nodetype is not None and type in nodetype.gatetypes:
        return nodetype.gatetypes.index(type)
    elif type == "gen":
        return GEN
    elif type == "por":
        return POR
    elif type == "ret":
        return RET
    elif type == "sub":
        return SUB
    elif type == "sur":
        return SUR
    elif type == "cat":
        return CAT
    elif type == "exp":
        return EXP
    elif type == "gin":
        return GIN
    elif type == "gou":
        return GOU
    elif type == "gfg":
        return GFG
    else:
        raise ValueError("Supplied type is not a valid gate type: "+str(type))


def get_string_gate_type(type, nodetype=None):
    if nodetype is not None and len(nodetype.gatetypes) > 0:
        return nodetype.gatetypes[type]
    elif type == GEN:
        return "gen"
    elif type == POR:
        return "por"
    elif type == RET:
        return "ret"
    elif type == SUB:
        return "sub"
    elif type == SUR:
        return "sur"
    elif type == CAT:
        return "cat"
    elif type == EXP:
        return "exp"
    elif type == GIN:
        return "gin"
    elif type == GOU:
        return "gou"
    elif type == GFG:
        return "gfg"
    else:
        raise ValueError("Supplied type is not a valid gate type: "+str(type))


def get_numerical_slot_type(type, nodetype=None):
    if nodetype is not None and type in nodetype.slottypes:
        return nodetype.slottypes.index(type)
    elif type == "gen":
        return GEN
    elif type == "por":
        return POR
    elif type == "ret":
        return RET
    elif type == "sub":
        return SUB
    elif type == "sur":
        return SUR
    elif type == "cat":
        return CAT
    elif type == "exp":
        return EXP
    elif type == "gin":
        return GIN
    elif type == "gou":
        return GOU
    elif type == "gfg":
        return GFG
    else:
        raise ValueError("Supplied type is not a valid slot type: "+str(type))


def get_string_slot_type(type, nodetype=None):
    if nodetype is not None and len(nodetype.slottypes) > 0:
        return nodetype.slottypes[type]
    elif type == GEN:
        return "gen"
    elif type == POR:
        return "por"
    elif type == RET:
        return "ret"
    elif type == SUB:
        return "sub"
    elif type == SUR:
        return "sur"
    elif type == CAT:
        return "cat"
    elif type == EXP:
        return "exp"
    elif type == GIN:
        return "gin"
    elif type == GOU:
        return "gou"
    elif type == GFG:
        return "gfg"
    else:
        raise ValueError("Supplied type is not a valid slot type: "+str(type))


def get_numerical_node_type(type, nativemodules=None):
    if type == "Neuron":
        return REGISTER
    elif type == "Actuator":
        return ACTUATOR
    elif type == "Sensor":
        return SENSOR
    elif type == "Activator":
        return ACTIVATOR
    elif type == "Concept":
        return CONCEPT
    elif type == "Script":
        return SCRIPT
    elif type == "Pipe":
        return PIPE
    elif type == "LSTM":
        return LSTM
    elif type == "Comment":
        return COMMENT
    elif nativemodules is not None and type in nativemodules:
        return MAX_STD_NODETYPE + 1 + sorted(nativemodules).index(type)
    else:
        raise ValueError("Supplied type is not a valid node type: "+str(type))


def get_string_node_type(type, nativemodules=None):
    if type == REGISTER:
        return "Neuron"
    elif type == ACTUATOR:
        return "Actuator"
    elif type == SENSOR:
        return "Sensor"
    elif type == ACTIVATOR:
        return "Activator"
    elif type == CONCEPT:
        return "Concept"
    elif type == SCRIPT:
        return "Script"
    elif type == PIPE:
        return "Pipe"
    elif type == LSTM:
        return "LSTM"
    elif type == COMMENT:
        return "Comment"
    elif nativemodules is not None and len(nativemodules) >= (type - MAX_STD_NODETYPE):
        return sorted(nativemodules)[(type-1) - MAX_STD_NODETYPE]
    else:
        raise ValueError("Supplied type is not a valid node type: "+str(type))


def get_numerical_gatefunction_type(type):
    if type == "identity" or type is None:
        return GATE_FUNCTION_IDENTITY
    elif type == "absolute":
        return GATE_FUNCTION_ABSOLUTE
    elif type == "sigmoid":
        return GATE_FUNCTION_SIGMOID
    elif type == "relu":
        return GATE_FUNCTION_RELU
    elif type == "one_over_x":
        return GATE_FUNCTION_DIST
    elif type == "elu":
        return GATE_FUNCTION_ELU
    elif type == "threshold":
        return GATE_FUNCTION_THRESHOLD
    else:
        raise ValueError("Supplied gatefunction type is not a valid type: "+str(type))


def get_string_gatefunction_type(type):
    if type == GATE_FUNCTION_IDENTITY:
        return "identity"
    elif type == GATE_FUNCTION_ABSOLUTE:
        return "absolute"
    elif type == GATE_FUNCTION_SIGMOID:
        return "sigmoid"
    elif type == GATE_FUNCTION_RELU:
        return "relu"
    elif type == GATE_FUNCTION_DIST:
        return "one_over_x"
    elif type == GATE_FUNCTION_ELU:
        return "elu"
    elif type == GATE_FUNCTION_THRESHOLD:
        return "threshold"
    else:
        raise ValueError("Supplied gatefunction type is not a valid type: "+str(type))


def get_elements_per_type(type, nativemodules=None):
    if type == REGISTER:
        return 1
    elif type == SENSOR:
        return 1
    elif type == ACTUATOR:
        return 1
    elif type == ACTIVATOR:
        return 1
    elif type == CONCEPT:
        return 7
    elif type == SCRIPT:
        return 7
    elif type == PIPE:
        return 7
    elif type == LSTM:
        return 5
    elif type == COMMENT:
        return 0
    elif nativemodules is not None and get_string_node_type(type, nativemodules) in nativemodules:
        native_module_definition = nativemodules[get_string_node_type(type, nativemodules)]
        return max(len(native_module_definition.gatetypes), len(native_module_definition.slottypes))
    else:
        raise ValueError("Supplied type is not a valid node type: "+str(type))


def get_gates_per_type(type, nativemodules=None):
    if type == REGISTER:
        return 1
    elif type == SENSOR:
        return 1
    elif type == ACTUATOR:
        return 1
    elif type == ACTIVATOR:
        return 0
    elif type == CONCEPT:
        return 7
    elif type == SCRIPT:
        return 7
    elif type == PIPE:
        return 7
    elif type == LSTM:
        return 5
    elif type == COMMENT:
        return 0
    elif nativemodules is not None and get_string_node_type(type, nativemodules) in nativemodules:
        native_module_definition = nativemodules[get_string_node_type(type, nativemodules)]
        return len(native_module_definition.gatetypes)
    else:
        raise ValueError("Supplied type is not a valid node type: "+str(type))


def get_slots_per_type(type, nativemodules=None):
    if type == REGISTER:
        return 1
    elif type == SENSOR:
        return 0
    elif type == ACTUATOR:
        return 1
    elif type == ACTIVATOR:
        return 1
    elif type == CONCEPT:
        return 7
    elif type == SCRIPT:
        return 7
    elif type == PIPE:
        return 7
    elif type == LSTM:
        return 5
    elif type == COMMENT:
        return 0
    elif nativemodules is not None and get_string_node_type(type, nativemodules) in nativemodules:
        native_module_definition = nativemodules[get_string_node_type(type, nativemodules)]
        return len(native_module_definition.slottypes)
    else:
        raise ValueError("Supplied type is not a valid node type: "+str(type))


def node_to_id(numericid, partitionid):
    return "n%03i%i" % (partitionid, numericid)


def node_from_id(stringid):
    return int(stringid[4:])


def nodespace_to_id(numericid, partitionid):
    return "s%03i%i" % (partitionid, numericid)


def nodespace_from_id(stringid):
    return int(stringid[4:])


def create_tensor(ndim, dtype, name="tensor"):
    # return a theano tensor with the given dimensionality
    from theano import tensor as T
    if ndim == 0:
        return T.scalar(name=name, dtype=dtype)
    elif ndim == 1:
        return T.vector(name=name, dtype=dtype)
    elif ndim == 2:
        return T.matrix(name=name, dtype=dtype)
    elif ndim == 3:
        return T.tensor3(name=name, dtype=dtype)
    elif ndim == 4:
        return T.tensor4(name=name, dtype=dtype)
