#!/usr/local/bin/python
# -*- coding: utf-8 -*-


import pytest
# skip these tests if numpy is not installed
pytest.importorskip("numpy")

import numpy as np


def prepare(runtime, test_nodenet, default_world, resourcepath, wa_class=None):
    """ Create a bunch of available flowmodules for the following tests """
    import os
    foodir = os.path.join(resourcepath, "nodetypes", 'foobar')
    os.makedirs(foodir)
    with open(os.path.join(resourcepath, "nodetypes", "out12345.py"), 'w') as fp:
        fp.write("""nodetype_definition = {
    "flow_module": True,
    "implementation": "python",
    "name": "out12345",
    "run_function_name": "out12345",
    "inputs": [],
    "outputs": ["out"],
    "inputdims": [],
    "parameters": ["default_test"],
    "parameter_defaults": {"default_test": "defaultvalue"}
}

def out12345(netapi, node, parameters):
    import numpy as np
    assert parameters['default_test'] == 'defaultvalue'
    return np.asarray([1,2,3,4,5]).astype(netapi.floatX)
""")

    with open(os.path.join(foodir, "Double.py"), 'w') as fp:
        fp.write("""nodetype_definition = {
    "flow_module": True,
    "implementation": "theano",
    "name": "Double",
    "build_function_name": "double",
    "init_function_name": "double_init",
    "inputs": ["inputs"],
    "outputs": ["outputs"],
    "inputdims": [1],
    "parameters": ["test_param"],
    "parameter_defaults": {"test_param": "defaultvalue"}
}

def double_init(netapi, node, parameters):
    assert nodetype_definition['name'] == 'Double'
    node.initfunction_ran = True
    assert parameters['test_param'] == 'defaultvalue'

def double(inputs, netapi, node, parameters):
    return inputs * 2
""")
    with open(os.path.join(resourcepath, "nodetypes", "Add.py"), 'w') as fp:
        fp.write("""nodetype_definition = {
    "flow_module": True,
    "implementation": "theano",
    "name": "Add",
    "build_function_name": "add",
    "inputs": ["input1", "input2"],
    "outputs": ["outputs"],
    "inputdims": [1, 1]
}

def add(input1, input2, netapi, node, parameters):
    return input1 + input2
""")
    with open(os.path.join(resourcepath, "nodetypes", "Bisect.py"), 'w') as fp:
        fp.write("""nodetype_definition = {
    "flow_module": True,
    "implementation": "theano",
    "name": "Bisect",
    "build_function_name": "bisect",
    "inputs": ["inputs"],
    "outputs": ["outputs"],
    "inputdims": [1]
}

def bisect(inputs, netapi, node, parameters):
    return inputs / 2
""")
    with open(os.path.join(resourcepath, "nodetypes", "Numpy.py"), 'w') as fp:
        fp.write("""nodetype_definition = {
    "flow_module": True,
    "implementation": "python",
    "name": "Numpy",
    "init_function_name": "numpyfunc_init",
    "run_function_name": "numpyfunc",
    "inputs": ["inputs"],
    "outputs": ["outputs"],
    "inputdims": [1],
    "parameters": ["no_return_flag"]
}

def numpyfunc_init(netapi, node, parameters):
    node.initfunction_ran = True

def numpyfunc(inputs, netapi, node, parameters):
    import numpy as np
    netapi.notify_user(node, "numpyfunc ran")
    if parameters.get('no_return_flag') != 1:
        ones = np.zeros_like(inputs)
        ones[:] = 1.0
        return inputs + ones
""")
    with open(os.path.join(resourcepath, "nodetypes", "Thetas.py"), 'w') as fp:
        fp.write("""nodetype_definition = {
    "flow_module": True,
    "implementation": "theano",
    "name": "Thetas",
    "init_function_name": "thetas_init",
    "build_function_name": "thetas",
    "parameters": ["weights_shape", "use_thetas"],
    "inputs": ["X"],
    "outputs": ["Y"],
    "inputdims": [1]
}

import theano

def thetas_init(netapi, node, parameters):
    import numpy as np
    w_array = np.random.rand(parameters['weights_shape']).astype(netapi.floatX)
    b_array = np.random.rand(parameters['weights_shape']).astype(netapi.floatX)

    node.set_theta('weights', w_array)
    node.set_theta('bias', theano.shared(b_array))

def thetas(X, netapi, node, parameters):
    if parameters.get('use_thetas'):
        return X * node.get_theta('weights') + node.get_theta('bias')
    else:
        return X
""")
    with open(os.path.join(resourcepath, "nodetypes", "TwoOutputs.py"), 'w') as fp:
        fp.write("""nodetype_definition = {
    "flow_module": True,
    "implementation": "theano",
    "name": "TwoOutputs",
    "build_function_name": "two_outputs",
    "inputs": ["X"],
    "outputs": ["A", "B"],
    "inputdims": [1]
}

def two_outputs(X, netapi, node, parameters):
    return X, X+1
""")
    with open(os.path.join(resourcepath, "nodetypes", "TRPOOut.py"), 'w') as fp:
        fp.write("""nodetype_definition = {
    "flow_module": True,
    "implementation": "theano",
    "name": "TRPOOut",
    "build_function_name": "trpoout",
    "inputs": ["X"],
    "outputs": ["Y", "Z"],
    "inputdims": [1],
    "parameters": ["makeinf"],
    "parameter_defaults": {"makeinf": "False"}
}

def trpoout(X, netapi, node, parameters):
    from theano import tensor as T
    if parameters["makeinf"] == "False":
        return [X, X+1, X*2], T.exp(X)
    else:
        return [X, X/0, X*2], T.exp(X)
""")
    with open(os.path.join(resourcepath, "nodetypes", "TRPOIn.py"), 'w') as fp:
        fp.write("""nodetype_definition = {
    "flow_module": True,
    "implementation": "theano",
    "name": "TRPOIn",
    "build_function_name": "trpoin",
    "inputs": ["Y", "Z"],
    "outputs": ["A"],
    "inputdims": ["list", 1]
}

def trpoin(X, Y, netapi, node, parameters):
    for thing in X:
        Y += thing
    return Y
""")
    with open(os.path.join(resourcepath, "nodetypes", "TRPOInPython.py"), 'w') as fp:
        fp.write("""nodetype_definition = {
    "flow_module": True,
    "implementation": "python",
    "name": "TRPOInPython",
    "run_function_name": "trpoinpython",
    "inputs": ["Y", "Z"],
    "outputs": ["A"],
    "inputdims": ["list", 1]
}

def trpoinpython(X, Y, netapi, node, parameters):
    for thing in X:
        Y += thing
    return Y
""")

    with open(os.path.join(resourcepath, "nodetypes", "infmaker.py"), 'w') as fp:
        fp.write("""nodetype_definition = {
    "flow_module": True,
    "implementation": "python",
    "name": "infmaker",
    "run_function_name": "infmaker",
    "inputs": [],
    "outputs": ["A"],
    "inputdims": [],
    "parameters": ["what"],
    "parameter_values": {"what": ["nan", "inf", "neginf"]},
    "parameter_defaults": {"what": "nan"}
}

import numpy as np

def infmaker(netapi, node, parameters):
    data = np.ones(12).astype(netapi.floatX)
    what = np.nan
    if parameters['what'] == 'inf':
        what = np.inf
    elif parameters['what'] == 'neginf':
        what = -np.inf
    data[np.random.randint(0, 11)] = what
    return data
""")

    with open(os.path.join(resourcepath, 'worlds.json'), 'w') as fp:
        fp.write("""{"worlds":["flowworld.py"],"worldadapters":["flowworld.py"]}""")

    with open(os.path.join(resourcepath, 'flowworld.py'), 'w') as fp:
        fp.write("""
import numpy as np
from micropsi_core.world.world import World
from micropsi_core.world.worldadapter import ArrayWorldAdapter

class FlowWorld(World):
    supported_worldadapters = ["SimpleArrayWA"]

class SimpleArrayWA(ArrayWorldAdapter):
    def __init__(self, world, **kwargs):
        super().__init__(world, **kwargs)
        self.add_datasource("execute")
        self.add_flow_datasource("foo", shape=(5))
        self.add_flow_datasource("vision", (6))
        self.add_flow_datasource("start", (1))
        self.add_datatarget("reset")
        self.add_flow_datatarget("bar", shape=(5))
        self.add_flow_datatarget("motor", (6))
        self.add_flow_datatarget("stop", (1))

        self.update_data_sources_and_targets()

    def update_data_sources_and_targets(self):
        for key in self.flow_datatargets:
            self.flow_datatarget_feedbacks[key] = np.copy(self.flow_datatargets[key]).astype(self.floatX)
        for key in self.flow_datasources:
            self.flow_datasources[key] = np.random.rand(len(self.flow_datasources[key])).astype(self.floatX)
""")

    nodenet = runtime.nodenets[test_nodenet]
    netapi = nodenet.netapi
    runtime.reload_code()

    res, wuid = runtime.new_world("FlowWorld", "FlowWorld")
    runtime.set_nodenet_properties(test_nodenet, worldadapter="SimpleArrayWA", world_uid=wuid)
    worldadapter = nodenet.worldadapter_instance

    return nodenet, netapi, worldadapter


@pytest.mark.engine("theano_engine")
def test_flowmodule_definition(runtime, test_nodenet, default_world, resourcepath):
    """ Basic definition and existance test """
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, default_world, resourcepath)

    result, metadata = runtime.get_nodenet_metadata(test_nodenet)
    assert 'Double' not in metadata['native_modules']
    assert metadata['flow_modules']['Double']['inputs'] == ["inputs"]
    assert metadata['flow_modules']['Double']['outputs'] == ["outputs"]
    assert metadata['flow_modules']['Double']['category'] == 'foobar'
    flowmodule = netapi.create_node("Double", None, "Double")
    assert not hasattr(flowmodule, 'initfunction_ran')

    nodenet.flow('worldadapter', 'foo', flowmodule.uid, "inputs")
    nodenet.flow(flowmodule.uid, "outputs", 'worldadapter', 'bar')

    sources = np.zeros((5), dtype=nodenet.numpyfloatX)
    sources[:] = np.random.randn(*sources.shape)

    worldadapter.set_flow_datasource('foo', sources)

    # step & assert that nothing happened without sub-activation
    nodenet.step()
    assert np.all(worldadapter.get_flow_datatarget('bar') == np.zeros(5, dtype=nodenet.numpyfloatX))
    # assert len(nodenet.flowfunctions) == 0

    # create activation source:
    source = netapi.create_node("Neuron", None)
    netapi.link(source, 'gen', source, 'gen')
    netapi.link(source, 'gen', flowmodule, 'sub')
    source.activation = 1

    # assert len(nodenet.flowfunctions) == 1

    # # step & assert that the initfunction and flowfunction ran
    nodenet.step()
    assert np.all(worldadapter.get_flow_datatarget('bar') == sources * 2)
    assert hasattr(flowmodule, 'initfunction_ran')


@pytest.mark.engine("theano_engine")
def test_multiple_flowgraphs(runtime, test_nodenet, default_world, resourcepath):
    """ Testing a flow from datasources to datatargets """
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, default_world, resourcepath)

    double = netapi.create_node("Double", None, "Double")
    add = netapi.create_node("Add", None, "Add")
    bisect = netapi.create_node("Bisect", None, "Bisect")

    # create a first graph
    # link datasources to double & add
    nodenet.flow('worldadapter', 'foo', double.uid, "inputs")
    nodenet.flow('worldadapter', 'foo', add.uid, "input2")
    # link double to add:
    nodenet.flow(double.uid, "outputs", add.uid, "input1")

    # link add to datatargets
    nodenet.flow(add.uid, "outputs", 'worldadapter', 'bar')

    # assert len(nodenet.flowfunctions) == 0

    # create a second graph
    nodenet.flow('worldadapter', 'foo', bisect.uid, "inputs")
    nodenet.flow(bisect.uid, "outputs", 'worldadapter', 'bar')

    # assert len(nodenet.flowfunctions) == 0

    sources = np.zeros((5), dtype=nodenet.numpyfloatX)
    sources[:] = np.random.randn(*sources.shape)

    worldadapter.set_flow_datasource('foo', sources)

    # create activation source
    source = netapi.create_node("Neuron", None)
    netapi.link(source, 'gen', source, 'gen')
    source.activation = 1

    # link to first graph:
    netapi.link(source, 'gen', add, 'sub')
    # assert len(nodenet.flowfunctions) == 1

    # step & assert that only the first graph ran
    nodenet.step()
    assert np.all(worldadapter.get_flow_datatarget('bar') == sources * 3)

    # link source to second graph:
    netapi.link(source, 'gen', bisect, 'sub')
    # assert len(nodenet.flowfunctions) == 2
    worldadapter.flow_datatargets['bar'] = np.zeros_like(worldadapter.get_flow_datatarget('bar'))

    nodenet.step()
    assert np.allclose(worldadapter.get_flow_datatarget('bar'), sources * 3.5)


@pytest.mark.engine("theano_engine")
def test_disconnect_flowmodules(runtime, test_nodenet, default_world, resourcepath):
    """ test disconnecting flowmodules """
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, default_world, resourcepath)

    double = netapi.create_node("Double", None, "Double")
    add = netapi.create_node("Add", None, "Add")
    source = netapi.create_node("Neuron", None, "Source")

    # link datasources to double & add
    nodenet.flow('worldadapter', 'foo', double.uid, "inputs")
    nodenet.flow('worldadapter', 'foo', add.uid, "input2")
    # link double to add:
    nodenet.flow(double.uid, "outputs", add.uid, "input1")
    # link add to datatargets
    nodenet.flow(add.uid, "outputs", 'worldadapter', 'bar')
    netapi.link(source, 'gen', add, 'sub')
    # have one connected graph

    # assert len(nodenet.flowfunctions) == 1

    # unlink double from add
    netapi.unflow(double, "outputs", add, "input1")

    # unlink add from datatargets
    netapi.unflow(add, "outputs", "worldadapter", "bar")

    # we still have one graph, but it doesn't do anything
    # assert len(nodenet.flowfunctions) == 1

    sources = np.zeros((5), dtype=nodenet.numpyfloatX)
    sources[:] = np.random.randn(*sources.shape)
    worldadapter.set_flow_datasource('foo', sources)

    nodenet.step()
    assert np.all(worldadapter.get_flow_datatarget('bar') == np.zeros_like(worldadapter.get_flow_datatarget('bar')))


@pytest.mark.engine("theano_engine")
def test_diverging_flowgraph(runtime, test_nodenet, default_world, resourcepath):
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, default_world, resourcepath)

    double = netapi.create_node("Double", None, "Double")
    add = netapi.create_node("Add", None, "Add")
    bisect = netapi.create_node("Bisect", None, "Bisect")

    # link sources to bisect
    nodenet.flow('worldadapter', 'foo', bisect.uid, "inputs")
    # link bisect to double:
    nodenet.flow(bisect.uid, "outputs", double.uid, "inputs")
    # link bisect to add:
    nodenet.flow(bisect.uid, "outputs", add.uid, "input1")
    # link sources to add:
    nodenet.flow('worldadapter', 'foo', add.uid, "input2")

    # link double and add to targets:
    nodenet.flow(double.uid, "outputs", 'worldadapter', 'bar')
    nodenet.flow(add.uid, "outputs", 'worldadapter', 'bar')

    sources = np.zeros((5), dtype=nodenet.numpyfloatX)
    sources[:] = np.random.randn(*sources.shape)
    worldadapter.set_flow_datasource('foo', sources)

    # create activation source
    source = netapi.create_node("Neuron", None)
    netapi.link(source, 'gen', source, 'gen')
    source.activation = 1

    # link activation source to double
    netapi.link(source, 'gen', double, 'sub')
    nodenet.step()
    assert np.all(worldadapter.get_flow_datatarget('bar') == sources)
    worldadapter.flow_datatargets['bar'] = np.zeros_like(worldadapter.get_flow_datatarget('bar'))

    # unlink double, link add:
    netapi.unlink(source, 'gen', double, 'sub')
    netapi.link(source, 'gen', add, 'sub')
    nodenet.step()
    assert np.all(worldadapter.get_flow_datatarget('bar') == sources * 1.5)


@pytest.mark.engine("theano_engine")
def test_converging_flowgraphs(runtime, test_nodenet, default_world, resourcepath):
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, default_world, resourcepath)

    double1 = netapi.create_node("Double", None, "Double")
    double2 = netapi.create_node("Double", None, "Double")
    add = netapi.create_node("Add", None, "Add")

    # link sources
    nodenet.flow('worldadapter', 'foo', double1.uid, "inputs")
    nodenet.flow('worldadapter', 'foo', double2.uid, "inputs")

    # link both doubles to add
    nodenet.flow(double1.uid, "outputs", add.uid, "input1")
    nodenet.flow(double2.uid, "outputs", add.uid, "input2")

    # link add to targets.
    nodenet.flow(add.uid, "outputs", 'worldadapter', 'bar')

    sources = np.zeros((5), dtype=nodenet.numpyfloatX)
    sources[:] = np.random.randn(*sources.shape)
    worldadapter.set_flow_datasource('foo', sources)

    # create activation source
    source = netapi.create_node("Neuron", None)
    netapi.link(source, 'gen', source, 'gen')
    source.activation = 1

    # link activation source to double
    netapi.link(source, 'gen', add, 'sub')
    nodenet.step()
    assert np.all(worldadapter.get_flow_datatarget('bar') == sources * 4)


@pytest.mark.engine("theano_engine")
def test_flowmodule_persistency(runtime, test_nodenet, default_world, resourcepath):
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, default_world, resourcepath)

    double = netapi.create_node("Double", None, "Double")
    thetas = netapi.create_node("Thetas", None, "Thetas")
    thetas.set_parameter("weights_shape", 5)
    thetas.set_parameter("use_thetas", True)

    nodenet.flow('worldadapter', 'foo', double.uid, "inputs")
    nodenet.flow(double.uid, 'outputs', thetas.uid, "X")
    nodenet.flow(thetas.uid, "Y", 'worldadapter', 'bar')
    source = netapi.create_node("Neuron", None)
    netapi.link(source, 'gen', source, 'gen')
    netapi.link(source, 'gen', thetas, 'sub')
    source.activation = 1
    custom_theta = np.random.rand(5).astype(netapi.floatX)
    thetas.set_theta("weights", custom_theta)

    assert double.initfunction_ran

    sources = np.zeros((5), dtype=netapi.floatX)
    sources[:] = np.random.randn(*sources.shape)
    worldadapter.set_flow_datasource('foo', sources)

    nodenet.step()

    result = worldadapter.get_flow_datatarget('bar')

    assert np.allclose(result, sources * 2 * thetas.get_theta("weights").get_value() + thetas.get_theta("bias").get_value())

    runtime.save_nodenet(test_nodenet)
    runtime.revert_nodenet(test_nodenet)

    nodenet = runtime.nodenets[test_nodenet]
    netapi = nodenet.netapi
    worldadapter = nodenet.worldadapter_instance
    worldadapter.set_flow_datasource('foo', sources)
    thetas = netapi.get_node(thetas.uid)

    assert np.allclose(thetas.get_theta("weights").get_value(), custom_theta)
    nodenet.step()
    assert np.allclose(worldadapter.get_flow_datatarget('bar'), result)
    assert netapi.get_node(double.uid).initfunction_ran
    # also assert, that the edge-keys are preserved:
    # this would raise an exception otherwise
    netapi.unflow(netapi.get_node(double.uid), 'outputs', netapi.get_node(thetas.uid), 'X')

    # assert that custom thetas survive reloadCode:
    runtime.reload_code()
    assert np.allclose(netapi.get_node(thetas.uid).get_theta('weights').get_value(), custom_theta)


@pytest.mark.engine("theano_engine")
def test_flowmodule_reload_code_behaviour(runtime, test_nodenet, default_world, resourcepath):
    import os
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, default_world, resourcepath)
    node = netapi.create_node("Thetas", None, "Thetas", weights_shape=5)
    double = netapi.create_node("Double", None, "Double")
    netapi.flow('worldadapter', 'foo', double, 'inputs')
    netapi.flow(double, 'outputs', 'worldadapter', 'bar')
    node.ensure_initialized()
    weights = node.get_theta('weights').get_value()
    source = netapi.create_node("Neuron", None)
    netapi.link(source, 'gen', source, 'gen')
    netapi.link(source, 'gen', double, 'sub')
    source.activation = 1
    with open(os.path.join(resourcepath, "nodetypes", "Thetas.py"), 'w') as fp:
        fp.write("""nodetype_definition = {
    "flow_module": True,
    "implementation": "theano",
    "name": "Thetas",
    "init_function_name": "thetas_init",
    "build_function_name": "thetas",
    "parameters": ["weights_shape", "use_thetas"],
    "inputs": ["Y"],
    "outputs": ["Z"],
    "inputdims": [1]
}

import theano

def thetas_init(netapi, node, parameters):
    import numpy as np
    w_array = np.random.rand(parameters['weights_shape']).astype(netapi.floatX)
    b_array = np.random.rand(parameters['weights_shape']).astype(netapi.floatX)
    node.initfunction_ran = 'yep'
    node.set_theta('weights', w_array)
    node.set_theta('bias', theano.shared(b_array))

def thetas(Y, netapi, node, parameters):
    if parameters.get('use_thetas'):
        return Y * node.get_theta('weights') + node.get_theta('bias')
    else:
        return Y
""")
    with open(os.path.join(resourcepath, "nodetypes", "foobar", "Double.py"), 'w') as fp:
        fp.write("""nodetype_definition = {
    "flow_module": True,
    "implementation": "theano",
    "name": "Double",
    "build_function_name": "double",
    "init_function_name": "double_init",
    "inputs": ["inputs"],
    "outputs": ["outputs"],
    "inputdims": [1]
}

def double_init(netapi, node, parameters):
    node.initfunction_ran = True

def double(inputs, netapi, node, parameters):
    return inputs * 4
""")
    runtime.reload_code()
    node = netapi.get_node(node.uid)
    assert node.inputs == ["Y"]
    assert node.outputs == ["Z"]
    assert not np.all(weights == node.get_theta('weights').get_value())
    assert weights.shape == node.get_theta('weights').get_value().shape
    assert node.initfunction_ran == 'yep'
    worldadapter = nodenet.worldadapter_instance
    sources = np.zeros((5), dtype=worldadapter.floatX)
    sources[:] = np.random.randn(*sources.shape)
    worldadapter.set_flow_datasource('foo', sources)
    nodenet.step()
    assert np.all(worldadapter.get_flow_datatarget("bar") == sources * 4)


@pytest.mark.engine("theano_engine")
def test_delete_flowmodule(runtime, test_nodenet, default_world, resourcepath):
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, default_world, resourcepath)

    double1 = netapi.create_node("Double", None, "Double")
    double2 = netapi.create_node("Double", None, "Double")
    add = netapi.create_node("Add", None, "Add")
    bisect = netapi.create_node("Bisect", None, "Bisect")

    # build graph:
    netapi.flow(bisect, "outputs", add, "input1")
    netapi.flow(add, "outputs", double1, "inputs")
    netapi.flow(add, "outputs", double2, "inputs")
    netapi.flow('worldadapter', 'foo', bisect, "inputs")
    netapi.flow('worldadapter', 'foo', add, "input2")
    netapi.flow(double1, "outputs", 'worldadapter', 'bar')
    netapi.flow(double2, "outputs", 'worldadapter', 'bar')

    source = netapi.create_node("Neuron", None, "Source")
    netapi.link(source, 'gen', source, 'gen')
    source.activation = 1
    netapi.link(source, 'gen', double1, 'sub')
    netapi.link(source, 'gen', double2, 'sub')
    # assert len(nodenet.flowfunctions) == 2

    netapi.delete_node(add)

    # no possible connections anymore
    # assert len(nodenet.flowfunctions) == 0

    assert not nodenet.flow_module_instances[bisect.uid].is_output_connected()

    sources = np.zeros((5), dtype=nodenet.numpyfloatX)
    sources[:] = np.random.randn(*sources.shape)
    worldadapter.set_flow_datasource('foo', sources)

    nodenet.step()
    assert np.all(worldadapter.get_flow_datatarget('bar') == np.zeros(5))


@pytest.mark.engine("theano_engine")
def test_link_large_graph(runtime, test_nodenet, default_world, resourcepath):
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, default_world, resourcepath)

    double = netapi.create_node("Double", None, "Double")
    bisect = netapi.create_node("Bisect", None, "Bisect")
    add = netapi.create_node("Add", None, "Add")

    # create activation source:
    source = netapi.create_node("Neuron", None)
    source.activation = 1

    nodenet.flow('worldadapter', 'foo', bisect.uid, "inputs")
    nodenet.flow(bisect.uid, "outputs", double.uid, "inputs")

    nodenet.flow('worldadapter', 'foo', add.uid, "input1")
    nodenet.flow(add.uid, "outputs", 'worldadapter', 'bar')

    nodenet.flow(double.uid, "outputs", add.uid, "input2")

    netapi.link(source, 'gen', add, 'sub')
    # assert len(nodenet.flowfunctions) == 1

    sources = np.zeros((5), dtype=nodenet.numpyfloatX)
    sources[:] = np.random.randn(*sources.shape)
    worldadapter.set_flow_datasource('foo', sources)

    nodenet.step()
    assert np.all(worldadapter.get_flow_datatarget('bar') == sources * 2)


@pytest.mark.engine("theano_engine")
def test_python_flowmodules(runtime, test_nodenet, default_world, resourcepath):
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, default_world, resourcepath)

    double = netapi.create_node("Double", None, "Double")
    py = netapi.create_node("Numpy", None, "Numpy")
    bisect = netapi.create_node("Bisect", None, "Bisect")

    source = netapi.create_node("Neuron", None)
    netapi.link(source, 'gen', source, 'gen')
    source.activation = 1

    assert not hasattr(py, 'initfunction_ran')

    netapi.flow('worldadapter', 'foo', double, "inputs")
    netapi.flow(double, "outputs", py, "inputs")
    netapi.flow(py, "outputs", bisect, "inputs")
    netapi.flow(bisect, "outputs", 'worldadapter', 'bar')

    sources = np.zeros((5), dtype=nodenet.numpyfloatX)
    sources[:] = np.random.randn(*sources.shape)
    worldadapter.set_flow_datasource('foo', sources)

    nodenet.step()
    assert np.all(worldadapter.get_flow_datatarget('bar') == 0)

    # netapi.link(source, 'gen', bisect, 'sub')

    nodenet.step()
    assert np.all(worldadapter.get_flow_datatarget('bar') == 0)

    netapi.link(source, 'gen', bisect, 'sub')

    nodenet.step()
    # ((x * 2) + 1) / 2 == x + .5
    assert np.all(worldadapter.get_flow_datatarget('bar') == sources + 0.5)
    assert py.initfunction_ran


@pytest.mark.engine("theano_engine")
def test_compile_flow_subgraph(runtime, test_nodenet, default_world, resourcepath):
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, default_world, resourcepath)

    double = netapi.create_node("Double", None, "Double")
    bisect = netapi.create_node("Bisect", None, "Bisect")

    netapi.flow(double, "outputs", bisect, "inputs")

    func, ins, outs = nodenet.compile_flow_subgraph([double.uid, bisect.uid])

    assert np.all(func(inputs=[1, 2, 3, 4]) == np.asarray([1, 2, 3, 4], dtype=nodenet.numpyfloatX))


@pytest.mark.engine("theano_engine")
def test_get_callable_flowgraph_bridges_numpy_gaps(runtime, test_nodenet, default_world, resourcepath):
    """ Asserts that callable_flowgraph wraps everything in one callable, symbolic or numeric """
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, default_world, resourcepath)

    double = netapi.create_node("Double", None, "Double")
    py = netapi.create_node("Numpy", None, "Numpy")
    bisect = netapi.create_node("Bisect", None, "Bisect")

    netapi.flow(double, "outputs", py, "inputs")
    netapi.flow(py, "outputs", bisect, "inputs")

    func = netapi.get_callable_flowgraph([bisect, double, py])

    assert np.all(func(inputs=[1, 2, 3, 4]) == np.asarray([1.5, 2.5, 3.5, 4.5], dtype=nodenet.numpyfloatX))


@pytest.mark.engine("theano_engine")
def test_collect_thetas(runtime, test_nodenet, default_world, resourcepath):
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, default_world, resourcepath)

    module = netapi.create_node("Thetas", None, "module")
    module.set_parameter('use_thetas', True)
    module.set_parameter('weights_shape', 5)

    netapi.flow('worldadapter', 'foo', module, "X")
    netapi.flow(module, "Y", 'worldadapter', 'bar')

    sources = np.zeros((5), dtype=nodenet.numpyfloatX)
    sources[:] = np.random.randn(*sources.shape)
    worldadapter.set_flow_datasource('foo', sources)

    source = netapi.create_node("Neuron", None)
    netapi.link(source, 'gen', source, 'gen')
    source.activation = 1
    netapi.link(source, 'gen', module, 'sub')

    nodenet.step()

    collected = netapi.collect_thetas([module])
    assert len(collected) == 2
    # assert collect sorts alphabetically
    assert collected[0] == module.get_theta('bias')
    assert collected[1] == module.get_theta('weights')

    result = sources * module.get_theta('weights').get_value() + module.get_theta('bias').get_value()
    assert np.allclose(worldadapter.get_flow_datatarget('bar'), result)

    func = netapi.get_callable_flowgraph([module], use_different_thetas=True)

    x = np.ones(5).astype(netapi.floatX)
    weights = np.random.rand(5).astype(netapi.floatX)
    bias = np.ones(5).astype(netapi.floatX)

    result = func(thetas=[bias, weights], X=x)

    assert np.all(result == x * weights + bias)


@pytest.mark.engine("theano_engine")
def test_flow_edgecase(runtime, test_nodenet, default_world, resourcepath):
    """ Tests a structural edge case: diverging and again converging graph with a numpy node in one arm"""
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, default_world, resourcepath)

    twoout = netapi.create_node("TwoOutputs", None, "twoout")
    double = netapi.create_node("Double", None, "double")
    numpy = netapi.create_node("Numpy", None, "numpy")
    add = netapi.create_node("Add", None, "add")

    netapi.flow(twoout, "A", double, "inputs")
    netapi.flow(twoout, "B", numpy, "inputs")
    netapi.flow(double, "outputs", add, "input1")
    netapi.flow(numpy, "outputs", add, "input2")

    function = netapi.get_callable_flowgraph([twoout, double, numpy, add])

    x = np.array([1, 2, 3], dtype=netapi.floatX)
    result = np.array([5, 8, 11], dtype=netapi.floatX)
    assert np.all(function(X=x) == result)


@pytest.mark.engine("theano_engine")
def test_flow_trpo_modules(runtime, test_nodenet, default_world, resourcepath):
    """ Test the trpo modules, that can return list-outputs """
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, default_world, resourcepath)

    trpoout = netapi.create_node("TRPOOut", None, "TRPOOut")
    trpoin = netapi.create_node("TRPOIn", None, "TRPOIn")

    netapi.flow(trpoout, "Y", trpoin, "Y")
    netapi.flow(trpoout, "Z", trpoin, "Z")

    function = netapi.get_callable_flowgraph([trpoin, trpoout])

    x = np.array([1, 2, 3], dtype=netapi.floatX)
    result = sum([np.exp(x), x, x * 2, x + 1])
    assert np.all(function(X=x) == result)

    netapi.delete_node(trpoin)
    trpoinpy = netapi.create_node("TRPOInPython", None, "TRPOInPython")

    netapi.flow(trpoout, "Y", trpoinpy, "Y")
    netapi.flow(trpoout, "Z", trpoinpy, "Z")

    function = netapi.get_callable_flowgraph([trpoinpy, trpoout])
    assert np.all(function(X=x) == result)


@pytest.mark.engine("theano_engine")
def test_none_output_skips_following_graphs(runtime, test_nodenet, default_world, resourcepath):
    """ Tests the "staudamm" functionality: a graph can return None, thus preventing graphs
    depending on this output as their input from being executed, even if they are requested """
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, default_world, resourcepath)

    with netapi.flowbuilder:
        double = netapi.create_node("Double", None, "Double")
        py = netapi.create_node("Numpy", None, "Numpy")
        bisect = netapi.create_node("Bisect", None, "Bisect")

        netapi.flow("worldadapter", "foo", double, "inputs")
        netapi.flow(double, "outputs", py, "inputs")
        netapi.flow(py, "outputs", bisect, "inputs")
        netapi.flow(bisect, "outputs", "worldadapter", "bar")

        source = netapi.create_node("Neuron", None, "Source")
        netapi.link(source, 'gen', source, 'gen')
        source.activation = 1
        netapi.link(source, 'gen', py, 'sub')
        netapi.link(source, 'gen', bisect, 'sub')
        # assert len(nodenet.flowfunctions) == 0

    sources = np.zeros((5), dtype=nodenet.numpyfloatX)
    sources[:] = np.random.randn(*sources.shape)
    worldadapter.set_flow_datasource('foo', sources)

    py.set_parameter('no_return_flag', 1)

    nodenet.step()
    # assert that the bisect function did not run
    assert np.all(worldadapter.get_flow_datatarget('bar') == np.zeros(5))
    # but python did
    assert nodenet.consume_user_prompt()['msg'] == 'numpyfunc ran'
    # and assert that you can get that info from the sur-gates:
    assert bisect.get_gate('sur').activation == 0
    assert py.get_gate('sur').activation == 1

    py.set_parameter('no_return_flag', 0)
    nodenet.step()
    assert np.all(worldadapter.get_flow_datatarget('bar') == (2 * sources + 1) / 2)


@pytest.mark.engine("theano_engine")
def test_shadow_flowgraph(runtime, test_nodenet, default_world, resourcepath):
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, default_world, resourcepath)

    node1 = netapi.create_node("Thetas", None, "node1")
    node1.set_parameter('use_thetas', True)
    node1.set_parameter('weights_shape', 5)
    node1.set_state('foo', 'bar')
    node2 = netapi.create_node("Thetas", None, "node2")
    node2.set_parameter('use_thetas', False)
    node2.set_parameter('weights_shape', 5)

    netapi.flow(node1, "Y", node2, "X")

    function = netapi.get_callable_flowgraph([node1, node2])

    x = np.array([1, 2, 3, 4, 5], dtype=netapi.floatX)
    result = function(X=x)[0]

    copies = netapi.shadow_flowgraph([node1, node2])

    copyfunction = netapi.get_callable_flowgraph([copies[0], copies[1]])

    assert np.all(copyfunction(X=x) == result)
    assert netapi.collect_thetas(copies) == netapi.collect_thetas([node1, node2])
    assert copies[0].get_state('foo') == 'bar'
    assert not copies[1].get_parameter('use_thetas')

    # change original
    node2.set_parameter('use_thetas', True)
    node1.set_state('foo', 'baz')

    # recompile, assert change took effect
    assert copies[1].get_parameter('use_thetas')
    assert copies[0].get_state('foo') == 'baz'
    function = netapi.get_callable_flowgraph([node1, node2])
    result2 = function(X=x)[0]
    assert np.all(result2 != result)

    # recompile copy, assert change took effect here as well.
    copyfunc = netapi.get_callable_flowgraph([copies[0], copies[1]])
    assert np.all(copyfunc(X=x) == result2)

    # change back, save and reload and assert the copy
    # still returs the original's value
    node2.set_parameter('use_thetas', False)
    runtime.save_nodenet(test_nodenet)
    runtime.revert_nodenet(test_nodenet)
    nodenet = runtime.nodenets[test_nodenet]
    netapi = nodenet.netapi
    copies = [netapi.get_node(copies[0].uid), netapi.get_node(copies[1].uid)]
    assert not copies[1].get_parameter('use_thetas')


@pytest.mark.engine("theano_engine")
def test_naming_collision_in_callable_subgraph(runtime, test_nodenet, default_world, resourcepath):
    """ Asserts that compiling a graph that has naming collisions raises an Exception,
    asserts that unique_inputs_names fixes the collision"""
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, default_world, resourcepath)

    double = netapi.create_node("Double", None, "Double")
    bisect = netapi.create_node("Bisect", None, "Bisect")
    add = netapi.create_node("Add", None, "Add")

    netapi.flow(double, "outputs", add, "input1")
    netapi.flow(bisect, "outputs", add, "input2")

    with pytest.raises(RuntimeError):
        netapi.get_callable_flowgraph([double, bisect, add])

    function = netapi.get_callable_flowgraph([double, bisect, add], use_unique_input_names=True)
    kwargs = {
        "%s_inputs" % double.uid: [1.],
        "%s_inputs" % bisect.uid: [1.]
    }
    assert function(**kwargs) == [2.5]


@pytest.mark.engine("theano_engine")
def test_filter_subgraph_outputs(runtime, test_nodenet, default_world, resourcepath):
    """ Tests requesting only specific outputs from a subgraph """
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, default_world, resourcepath)

    double = netapi.create_node("Double", None, "Double")
    twoout = netapi.create_node("TwoOutputs", None, "TwoOutputs")

    netapi.flow(twoout, "A", double, "inputs")

    function = netapi.get_callable_flowgraph([twoout, double])
    assert function(X=[2.]) == [3., 4.]
    assert "B of %s" % twoout.uid in function.__doc__

    function = netapi.get_callable_flowgraph([twoout, double], requested_outputs=[(double.uid, "outputs")])
    assert function(X=[2.]) == [4.]
    assert "B of %s" % twoout.uid not in function.__doc__


@pytest.mark.engine("theano_engine")
def test_connect_flow_modules_to_structured_flow_datasource(runtime, test_nodenet, default_world, resourcepath):
    import os
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, default_world, resourcepath)
    # get ndoetype defs
    assert nodenet.native_module_definitions['datatargets']['is_autogenerated']
    nodenet.native_modules['datatargets'].inputs == ['motor', 'stop']
    nodenet.native_modules['datatargets'].outputs == []
    assert nodenet.native_module_definitions['datasources']['is_autogenerated']
    nodenet.native_modules['datasources'].inputs == []
    nodenet.native_modules['datasources'].outputs == ['vision', 'start']
    in_node_found = False
    out_node_found = False

    assert len(nodenet.flow_module_instances) == 2
    for uid, node in nodenet.flow_module_instances.items():
        if node.name == 'datatargets':
            assert node.type == 'datatargets'
            in_node_found = True
            assert node.outputs == []
            assert node.inputs == ['bar', 'motor', 'stop']
            assert node.get_data()['type'] == 'datatargets'
        elif node.name == 'datasources':
            assert node.type == 'datasources'
            out_node_found = True
            assert node.outputs == ['foo', 'vision', 'start']
            assert node.inputs == []
            assert node.get_data()['type'] == 'datasources'

    assert in_node_found
    assert out_node_found

    sources = np.zeros((6), dtype=nodenet.numpyfloatX)
    sources[:] = np.random.randn(*sources.shape)
    worldadapter.set_flow_datasource('vision', sources)
    worldadapter.set_flow_datasource('start', np.asarray([0.73]).astype(nodenet.numpyfloatX))

    double = netapi.create_node("Double", None, "Double")
    netapi.flow('worldadapter', 'vision', double, 'inputs')
    netapi.flow(double, 'outputs', 'worldadapter', 'motor')
    netapi.flow('worldadapter', 'start', 'worldadapter', 'stop')

    source = netapi.create_node("Neuron", None)
    source.activation = 1
    netapi.link(source, 'gen', double, 'sub')

    runtime.step_nodenet(test_nodenet)
    assert worldadapter.datatarget_values[0] == 0
    assert np.all(worldadapter.get_flow_datatarget_feedback('motor') == sources * 2)
    assert np.allclose(worldadapter.get_flow_datatarget_feedback('stop'), [0.73])

    runtime.save_nodenet(test_nodenet)
    runtime.revert_nodenet(test_nodenet)

    nodenet = runtime.nodenets[test_nodenet]
    worldadapter = nodenet.worldadapter_instance

    assert len(nodenet.flow_module_instances) == 3

    sources = np.zeros((6), dtype=nodenet.numpyfloatX)
    sources[:] = np.random.randn(*sources.shape)
    worldadapter.set_flow_datasource('vision', sources)
    worldadapter.set_flow_datasource('start', np.asarray([0.64]).astype(nodenet.numpyfloatX))
    runtime.step_nodenet(test_nodenet)
    assert np.all(worldadapter.get_flow_datatarget_feedback('motor') == np.zeros(6))
    assert np.allclose(worldadapter.get_flow_datatarget_feedback('stop'), [0.64])

    with open(os.path.join(resourcepath, 'flowworld.py'), 'w') as fp:
        fp.write("""
import numpy as np
from micropsi_core.world.world import World
from micropsi_core.world.worldadapter import ArrayWorldAdapter

class FlowWorld(World):
    supported_worldadapters = ["SimpleArrayWA"]

class SimpleArrayWA(ArrayWorldAdapter):
    def __init__(self, world, **kwargs):
        super().__init__(world, **kwargs)
        self.add_datasource("execute")
        self.add_flow_datasource("renamed", shape=(5))
        self.add_flow_datasource("vision", (6))
        self.add_datatarget("reset")
        self.add_flow_datatarget("renamed", shape=(5))
        self.add_flow_datatarget("motor", (6))
        self.update_data_sources_and_targets()

    def update_data_sources_and_targets(self):
        pass
""")
    runtime.reload_code()
    assert len(nodenet.flow_module_instances) == 3
    sources = nodenet.get_node(nodenet.worldadapter_flow_nodes['datasources'])
    targets = nodenet.get_node(nodenet.worldadapter_flow_nodes['datatargets'])
    assert sources.outputs == ["renamed", "vision"]
    assert targets.inputs == ["renamed", "motor"]
    assert nodenet.get_node(double.uid).inputmap['inputs'] == (sources.uid, 'vision')
    assert (double.uid, 'inputs') in nodenet.get_node(sources.uid).outputmap['vision']
    assert (targets.uid, 'motor') in nodenet.get_node(double.uid).outputmap['outputs']


@pytest.mark.engine("theano_engine")
def test_flownode_output_only(runtime, test_nodenet, default_world, resourcepath):
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, default_world, resourcepath)
    out = netapi.create_node("out12345")
    source = netapi.create_node("Neuron")
    source.activation = 1
    netapi.link(source, 'gen', source, 'gen')
    netapi.link(source, 'gen', out, 'sub')
    netapi.flow(out, 'out', 'worldadapter', 'bar')
    nodenet.step()
    assert np.all(worldadapter.get_flow_datatarget('bar') == [1, 2, 3, 4, 5])


@pytest.mark.engine("theano_engine")
def test_flownode_generate_netapi_fragment(runtime, test_nodenet, default_world, resourcepath):
    """ Takes the above-tested edgecase, creates a recipe via generate_netapi_fragment
    and runs the result"""
    import os
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, default_world, resourcepath)

    twoout = netapi.create_node("TwoOutputs", None, "twoout")
    double = netapi.create_node("Double", None, "double")
    numpy = netapi.create_node("Numpy", None, "numpy")
    add = netapi.create_node("Add", None, "add")
    nodes = [twoout, double, numpy, add]

    netapi.flow(twoout, "A", double, "inputs")
    netapi.flow(twoout, "B", numpy, "inputs")
    netapi.flow(double, "outputs", add, "input1")
    netapi.flow(numpy, "outputs", add, "input2")

    fragment = runtime.generate_netapi_fragment(test_nodenet, [n.uid for n in nodes])

    res, pastenet = runtime.new_nodenet('pastnet', "theano_engine")
    code = "def foo(netapi):\n    " + "\n    ".join(fragment.split('\n'))
    # save the fragment as recipe & run
    with open(os.path.join(resourcepath, 'recipes', 'test.py'), 'w+') as fp:
        fp.write(code)
    runtime.reload_code()
    runtime.run_recipe(pastenet, 'foo', {})
    pastnetapi = runtime.get_nodenet(pastenet).netapi

    function = pastnetapi.get_callable_flowgraph(netapi.get_nodes())

    x = np.array([1, 2, 3], dtype=netapi.floatX)
    result = np.array([5, 8, 11], dtype=netapi.floatX)
    assert np.all(function(X=x) == result)


@pytest.mark.engine("theano_engine")
def test_flow_inf_guard(runtime, test_nodenet, default_world, resourcepath):
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, default_world, resourcepath)

    infmaker = netapi.create_node("infmaker")
    add = netapi.create_node("Add")
    netapi.flow(infmaker, "A", add, "input1")
    netapi.flow('worldadapter', 'foo', add, "input2")
    netapi.flow(add, 'outputs', 'worldadapter', 'bar')
    source = netapi.create_node("Neuron")
    source.activation = 1
    netapi.link(source, 'gen', source, 'gen')
    netapi.link(source, 'gen', add, 'sub')
    with pytest.raises(ValueError) as excinfo:
        runtime.step_nodenet(test_nodenet)
    assert "output A" in str(excinfo.value)
    assert "infmaker" in str(excinfo.value)
    assert "NAN value" in str(excinfo.value)

    infmaker.set_parameter('what', 'inf')
    with pytest.raises(ValueError) as excinfo:
        runtime.step_nodenet(test_nodenet)
    assert "INF value" in str(excinfo.value)

    worldadapter.flow_datasources['foo'][3] = np.nan
    with pytest.raises(ValueError) as excinfo:
        runtime.step_nodenet(test_nodenet)
    assert type(worldadapter).__name__ in str(excinfo.value)
    assert "foo" in str(excinfo.value)


@pytest.mark.engine("theano_engine")
def test_flow_inf_guard_on_list_outputs(runtime, test_nodenet, default_world, resourcepath):
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, default_world, resourcepath)

    trpoout = netapi.create_node("TRPOOut", None, "TRPOOut")
    trpoout.set_parameter("makeinf", "True")
    trpoin = netapi.create_node("TRPOIn", None, "TRPOIn")

    netapi.flow(trpoout, "Y", trpoin, "Y")
    netapi.flow(trpoout, "Z", trpoin, "Z")
    netapi.flow('worldadapter', 'foo', trpoout, "X")
    netapi.flow(trpoin, 'A', 'worldadapter', 'bar')
    source = netapi.create_node("Neuron")
    source.activation = 1
    netapi.link(source, 'gen', source, 'gen')
    netapi.link(source, 'gen', trpoin, 'sub')
    with pytest.raises(ValueError) as excinfo:
        runtime.step_nodenet(test_nodenet)
    assert "INF value in" in str(excinfo.value)
    assert "output A of graph" in str(excinfo.value)
