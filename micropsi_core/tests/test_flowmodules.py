#!/usr/local/bin/python
# -*- coding: utf-8 -*-


import pytest
# skip these tests if numpy is not installed
pytest.importorskip("numpy")

import numpy as np
from micropsi_core.world.worldadapter import ArrayWorldAdapter


class SimpleArrayWA(ArrayWorldAdapter):
    def __init__(self, world, **kwargs):
        super().__init__(world, **kwargs)
        self.add_flow_datasource("foo", shape=(5))
        self.add_flow_datatarget("bar", shape=(5))
        self.update_data_sources_and_targets()

    def update_data_sources_and_targets(self):
        for key in self.flow_datatargets:
            self.flow_datatarget_feedbacks[key] = np.copy(self.flow_datatargets[key])
        for key in self.flow_datasources:
            self.flow_datasources[key] = np.random.rand(len(self.flow_datasources[key]))


def prepare(runtime, test_nodenet, default_world, resourcepath, wa_class=SimpleArrayWA):
    """ Create a bunch of available flowmodules for the following tests """
    import os
    with open(os.path.join(resourcepath, 'nodetypes.json'), 'w') as fp:
        fp.write("""
    {"Double": {
        "flow_module": true,
        "implementation": "theano",
        "name": "Double",
        "build_function_name": "double",
        "init_function_name": "double_init",
        "inputs": ["inputs"],
        "outputs": ["outputs"],
        "inputdims": [1]
    },
    "Add": {
        "flow_module": true,
        "implementation": "theano",
        "name": "Add",
        "build_function_name": "add",
        "inputs": ["input1", "input2"],
        "outputs": ["outputs"],
        "inputdims": [1, 1]
    },
    "Bisect": {
        "flow_module": true,
        "implementation": "theano",
        "name": "Bisect",
        "build_function_name": "bisect",
        "inputs": ["inputs"],
        "outputs": ["outputs"],
        "inputdims": [1]
    },
    "Numpy": {
        "flow_module": true,
        "implementation": "python",
        "name": "Numpy",
        "init_function_name": "numpyfunc_init",
        "run_function_name": "numpyfunc",
        "inputs": ["inputs"],
        "outputs": ["outputs"],
        "inputdims": [1],
        "parameters": ["no_return_flag"]
    },
    "Thetas": {
        "flow_module": true,
        "implementation": "theano",
        "name": "Thetas",
        "init_function_name": "thetas_init",
        "build_function_name": "thetas",
        "parameters": ["weights_shape", "use_thetas"],
        "inputs": ["X"],
        "outputs": ["Y"],
        "inputdims": [1]
    },
    "TwoOutputs":{
        "flow_module": true,
        "implementation": "theano",
        "name": "TwoOutputs",
        "build_function_name": "two_outputs",
        "inputs": ["X"],
        "outputs": ["A", "B"],
        "inputdims": [1]
    },
    "TRPOOut":{
        "flow_module": true,
        "implementation": "theano",
        "name": "TRPOOut",
        "build_function_name": "trpoout",
        "inputs": ["X"],
        "outputs": ["Y", "Z"],
        "inputdims": [1]
    },
    "TRPOIn":{
        "flow_module": true,
        "implementation": "theano",
        "name": "TRPOIn",
        "build_function_name": "trpoin",
        "inputs": ["Y", "Z"],
        "outputs": ["A"],
        "inputdims": ["list", 1]
    },
    "TRPOInPython":{
        "flow_module": true,
        "implementation": "python",
        "name": "TRPOIn",
        "run_function_name": "trpoinpython",
        "inputs": ["Y", "Z"],
        "outputs": ["A"],
        "inputdims": ["list", 1]
    }}""")
    with open(os.path.join(resourcepath, 'nodefunctions.py'), 'w') as fp:
        fp.write("""
def double_init(netapi, node, parameters):
    node.initfunction_ran = True

def double(inputs, netapi, node, parameters):
    return inputs * 2

def add(input1, input2, netapi, node, parameters):
    return input1 + input2

def bisect(inputs, netapi, node, parameters):
    return inputs / 2

def numpyfunc_init(netapi, node, parameters):
    node.initfunction_ran = True

def numpyfunc(inputs, netapi, node, parameters):
    import numpy as np
    netapi.notify_user(node, "numpyfunc ran")
    if parameters.get('no_return_flag') != 1:
        ones = np.zeros_like(inputs)
        ones[:] = 1.0
        return inputs + ones

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

def two_outputs(X, netapi, node, parameters):
    return X, X+1

def trpoout(X, netapi, node, parameters):
    from theano import tensor as T
    return [X, X+1, X*2], T.exp(X)

def trpoin(X, Y, netapi, node, parameters):
    for thing in X:
        Y += thing
    return Y

def trpoinpython(X, Y, netapi, node, parameters):
    for thing in X:
        Y += thing
    return Y
""")

    nodenet = runtime.nodenets[test_nodenet]
    netapi = nodenet.netapi

    res, wuid = runtime.new_world("FlowWorld", "DefaultWorld")
    worldobj = runtime.load_world(wuid)
    worldobj.supported_worldadapters[wa_class.__name__] = wa_class
    runtime.set_nodenet_properties(test_nodenet, worldadapter=wa_class.__name__, world_uid=wuid)
    worldadapter = nodenet.worldadapter_instance

    runtime.reload_native_modules()
    return nodenet, netapi, worldadapter


@pytest.mark.engine("theano_engine")
def test_flowmodule_definition(runtime, test_nodenet, default_world, resourcepath):
    """ Basic definition and existance test """
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, default_world, resourcepath)

    result, metadata = runtime.get_nodenet_metadata(test_nodenet)
    assert 'Double' not in metadata['native_modules']
    assert metadata['flow_modules']['Double']['inputs'] == ["inputs"]
    assert metadata['flow_modules']['Double']['outputs'] == ["outputs"]

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

    sources = np.zeros((5), dtype=netapi.floatX)
    sources[:] = np.random.randn(*sources.shape)
    worldadapter.set_flow_datasource('foo', sources)

    nodenet.step()

    result = worldadapter.get_flow_datatarget('bar')

    assert np.all(result == sources * 2 * thetas.get_theta("weights").get_value() + thetas.get_theta("bias").get_value())

    runtime.save_nodenet(test_nodenet)
    runtime.revert_nodenet(test_nodenet)

    nodenet = runtime.nodenets[test_nodenet]
    netapi = nodenet.netapi
    worldadapter = nodenet.worldadapter_instance
    worldadapter.set_flow_datasource('foo', sources)
    thetas = netapi.get_node(thetas.uid)

    assert np.all(thetas.get_theta("weights").get_value() == custom_theta)
    nodenet.step()
    assert np.all(worldadapter.get_flow_datatarget('bar') == result)

    # also assert, that the edge-keys are preserved:
    # this would raise an exception otherwise
    netapi.unflow(netapi.get_node(double.uid), 'outputs', netapi.get_node(thetas.uid), 'X')


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
    assert nodenet.user_prompt['msg'] == 'numpyfunc ran'
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

    class StructuredArrayWA(ArrayWorldAdapter):
        def __init__(self, world, **kwargs):
            super().__init__(world)
            self.add_datasource('execute')
            self.add_flow_datasource('vision', (6))
            self.add_datatarget('reset')
            self.add_flow_datatarget('motor', (6))
            self.update_data_sources_and_targets()

        def update_data_sources_and_targets(self):
            for key in self.flow_datatargets:
                self.flow_datatarget_feedbacks[key] = np.copy(self.flow_datatargets[key])
            for key in self.flow_datasources:
                self.flow_datasources[key] = np.random.rand(*self.flow_datasources[key].shape)

    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, default_world, resourcepath, wa_class=StructuredArrayWA)
    # get ndoetype defs
    assert nodenet.native_module_definitions['datatargets']['is_autogenerated']
    nodenet.native_modules['datatargets'].inputs == ['motor']
    nodenet.native_modules['datatargets'].outputs == []
    assert nodenet.native_module_definitions['datasources']['is_autogenerated']
    nodenet.native_modules['datasources'].inputs == []
    nodenet.native_modules['datasources'].outputs == ['vision']
    in_node_found = False
    out_node_found = False

    assert len(nodenet.flow_module_instances) == 2
    for uid, node in nodenet.flow_module_instances.items():
        if node.name == 'datatargets':
            assert node.type == 'datatargets'
            in_node_found = True
            assert node.outputs == []
            assert node.inputs == ['motor']
            assert node.get_data()['type'] == 'datatargets'
        elif node.name == 'datasources':
            assert node.type == 'datasources'
            out_node_found = True
            assert node.outputs == ['vision']
            assert node.inputs == []
            assert node.get_data()['type'] == 'datasources'

    assert in_node_found
    assert out_node_found

    sources = np.zeros((6), dtype=nodenet.numpyfloatX)
    sources[:] = np.random.randn(*sources.shape)
    worldadapter.set_flow_datasource('vision', sources)

    double = netapi.create_node("Double", None, "Double")
    netapi.flow('worldadapter', 'vision', double, 'inputs')
    netapi.flow(double, 'outputs', 'worldadapter', 'motor')

    source = netapi.create_node("Neuron", None)
    source.activation = 1
    netapi.link(source, 'gen', source, 'gen')
    netapi.link(source, 'gen', double, 'sub')

    runtime.step_nodenet(test_nodenet)
    assert worldadapter.datatarget_values[0] == 0
    assert np.all(worldadapter.get_flow_datatarget_feedback('motor') == sources * 2)

    runtime.save_nodenet(test_nodenet)
    runtime.revert_nodenet(test_nodenet)

    nodenet = runtime.nodenets[test_nodenet]
    assert len(nodenet.flow_module_instances) == 3
