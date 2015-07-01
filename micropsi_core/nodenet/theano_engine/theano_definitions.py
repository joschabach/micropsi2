REGISTER = 1
SENSOR = 2
ACTUATOR = 3
ACTIVATOR = 4
CONCEPT = 5
SCRIPT = 6
PIPE = 7
COMMENT = 8

MAX_STD_NODETYPE = COMMENT

GEN = 0
POR = 1
RET = 2
SUB = 3
SUR = 4
CAT = 5
EXP = 6

MAX_STD_GATE = EXP


GATE_FUNCTION_IDENTITY = 0
GATE_FUNCTION_ABSOLUTE = 1
GATE_FUNCTION_SIGMOID = 2
GATE_FUNCTION_TANH = 3
GATE_FUNCTION_RECT = 4
GATE_FUNCTION_DIST = 5

NFPG_PIPE_NON = 0
NFPG_PIPE_GEN = 1
NFPG_PIPE_POR = 2
NFPG_PIPE_RET = 3
NFPG_PIPE_SUB = 4
NFPG_PIPE_SUR = 5
NFPG_PIPE_CAT = 6
NFPG_PIPE_EXP = 7

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
    else:
        raise ValueError("Supplied type is not a valid slot type: "+str(type))


def get_numerical_node_type(type, nativemodules=None):
    if type == "Register":
        return REGISTER
    elif type == "Actor":
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
    elif type == "Comment":
        return COMMENT
    elif nativemodules is not None and type in nativemodules:
        return MAX_STD_NODETYPE + 1 + sorted(nativemodules).index(type)
    else:
        raise ValueError("Supplied type is not a valid node type: "+str(type))


def get_string_node_type(type, nativemodules=None):
    if type == REGISTER:
        return "Register"
    elif type == ACTUATOR:
        return "Actor"
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
    elif type == "tanh":
        return GATE_FUNCTION_TANH
    elif type == "rect":
        return GATE_FUNCTION_RECT
    elif type == "one_over_x":
        return GATE_FUNCTION_DIST
    else:
        raise ValueError("Supplied gatefunction type is not a valid type: "+str(type))


def get_string_gatefunction_type(type):
    if type == GATE_FUNCTION_IDENTITY:
        return "identity"
    elif type == GATE_FUNCTION_ABSOLUTE:
        return "absolute"
    elif type == GATE_FUNCTION_SIGMOID:
        return "sigmoid"
    elif type == GATE_FUNCTION_TANH:
        return "tanh"
    elif type == GATE_FUNCTION_RECT:
        return "rect"
    elif type == GATE_FUNCTION_DIST:
        return "one_over_x"
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
    elif type == COMMENT:
        return 0
    elif nativemodules is not None and get_string_node_type(type, nativemodules) in nativemodules:
        native_module_definition = nativemodules[get_string_node_type(type, nativemodules)]
        return len(native_module_definition.slottypes)
    else:
        raise ValueError("Supplied type is not a valid node type: "+str(type))


def node_to_id(numericid, partition):
    return "n%03i%i" % (partition, numericid)


def node_from_id(stringid):
    return int(stringid[4:])


def nodespace_to_id(numericid, partition):
    return "s%03i%i" % (partition, numericid)


def nodespace_from_id(stringid):
    return int(stringid[4:])