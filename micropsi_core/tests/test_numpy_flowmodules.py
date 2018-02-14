#!/usr/local/bin/python
# -*- coding: utf-8 -*-


import pytest
# skip these tests if numpy is not installed
pytest.importorskip("numpy")

import numpy as np


def prepare(runtime, test_nodenet, resourcepath, wa_class=None):
    """ Create a bunch of available flowmodules for the following tests """
    import os
    foodir = os.path.join(resourcepath, "nodetypes", 'foobar')
    os.makedirs(foodir)
    with open(os.path.join(resourcepath, "nodetypes", "out12345.py"), 'w') as fp:
        fp.write("""nodetype_definition = {
    "flow_module": True,
    "name": "out12345",
    "run_function_name": "out12345",
    "inputs": [],
    "outputs": ["out"],
    "parameters": ["default_test"],
    "parameter_defaults": {"default_test": "defaultvalue"}
}

def out12345(netapi, node, parameters):
    import numpy as np
    assert parameters['default_test'] == 'defaultvalue'
    return np.asarray([1,2,3,4,5])
""")

    with open(os.path.join(foodir, "Double.py"), 'w') as fp:
        fp.write("""nodetype_definition = {
    "flow_module": True,
    "name": "Double",
    "run_function_name": "double",
    "init_function_name": "double_init",
    "inputs": ["inputs"],
    "outputs": ["outputs"],
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
    "name": "Add",
    "run_function_name": "add",
    "inputs": ["input1", "input2"],
    "outputs": ["outputs"],
}

def add(input1, input2, netapi, node, parameters):
    return input1 + input2
""")
    with open(os.path.join(resourcepath, "nodetypes", "Bisect.py"), 'w') as fp:
        fp.write("""nodetype_definition = {
    "flow_module": True,
    "name": "Bisect",
    "run_function_name": "bisect",
    "inputs": ["inputs"],
    "outputs": ["outputs"],
}

def bisect(inputs, netapi, node, parameters):
    return inputs / 2
""")
    with open(os.path.join(resourcepath, "nodetypes", "Numpy.py"), 'w') as fp:
        fp.write("""nodetype_definition = {
    "flow_module": True,
    "name": "Numpy",
    "init_function_name": "numpyfunc_init",
    "run_function_name": "numpyfunc",
    "inputs": ["inputs"],
    "outputs": ["outputs"],
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
    with open(os.path.join(resourcepath, "nodetypes", "TwoOutputs.py"), 'w') as fp:
        fp.write("""nodetype_definition = {
    "flow_module": True,
    "name": "TwoOutputs",
    "run_function_name": "two_outputs",
    "inputs": ["X"],
    "outputs": ["A", "B"],
}

def two_outputs(X, netapi, node, parameters):
    return X, X+1
""")
    with open(os.path.join(resourcepath, "nodetypes", "list_inf_maker.py"), 'w') as fp:
        fp.write("""nodetype_definition = {
    "flow_module": True,
    "name": "ListInfMaker",
    "run_function_name": "list_inf_maker",
    "inputs": ["X"],
    "outputs": ["Y", "Z"],
    "parameters": ["makeinf"],
    "parameter_defaults": {"makeinf": "False"}
}

def list_inf_maker(X, netapi, node, parameters):
    from theano import tensor as T
    if parameters["makeinf"] == "False":
        return [X, X+1, X*2], T.exp(X)
    else:
        return [X, X/0, X*2], T.exp(X)
""")
    with open(os.path.join(resourcepath, "nodetypes", "infmaker.py"), 'w') as fp:
        fp.write("""nodetype_definition = {
    "flow_module": True,
    "name": "infmaker",
    "run_function_name": "infmaker",
    "inputs": [],
    "outputs": ["A"],
    "parameters": ["what"],
    "parameter_values": {"what": ["nan", "inf", "neginf"]},
    "parameter_defaults": {"what": "nan"}
}

import numpy as np

def infmaker(netapi, node, parameters):
    data = np.ones(12)
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
            self.flow_datatarget_feedbacks[key] = np.copy(self.flow_datatargets[key])
        for key in self.flow_datasources:
            self.flow_datasources[key] = np.random.rand(len(self.flow_datasources[key]))
""")

    nodenet = runtime.nodenets[test_nodenet]
    netapi = nodenet.netapi
    runtime.reload_code()

    res, wuid = runtime.new_world("FlowWorld", "FlowWorld")
    runtime.set_nodenet_properties(test_nodenet, worldadapter="SimpleArrayWA", world_uid=wuid)
    worldadapter = nodenet.worldadapter_instance

    return nodenet, netapi, worldadapter


@pytest.mark.engine("numpy_engine")
def test_flowmodule_definition(runtime, test_nodenet, resourcepath):
    """ Basic definition and existance test """
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, resourcepath)

    result, metadata = runtime.get_nodenet_metadata(test_nodenet)
    assert 'Double' not in metadata['native_modules']
    assert metadata['flow_modules']['Double']['inputs'] == ["inputs"]
    assert metadata['flow_modules']['Double']['outputs'] == ["outputs"]
    assert metadata['flow_modules']['Double']['category'] == 'foobar'
    flowmodule = netapi.create_node("Double", None, "Double")
    assert not hasattr(flowmodule, 'initfunction_ran')

    nodenet.flow('worldadapter', 'foo', flowmodule.uid, "inputs")
    nodenet.flow(flowmodule.uid, "outputs", 'worldadapter', 'bar')

    sources = np.zeros((5))
    sources[:] = np.random.randn(*sources.shape)
    datasources = netapi.get_node(nodenet.worldadapter_flow_nodes['datasources'])
    datatargets = netapi.get_node(nodenet.worldadapter_flow_nodes['datatargets'])

    runtime.run_operation(test_nodenet, "autoalign", {}, [flowmodule.uid, datasources.uid, datatargets.uid])
    assert datasources.position[0] < flowmodule.position[0] < datatargets.position[0]
    assert datasources.position[1] == flowmodule.position[1] == datatargets.position[1]

    worldadapter.set_flow_datasource('foo', sources)
    # step & assert that nothing happened without sub-activation
    nodenet.step()
    assert flowmodule.activation == 0
    assert datasources.activation == 1
    assert datatargets.activation == 0

    assert np.all(worldadapter.get_flow_datatarget('bar') == np.zeros(5))

    # create activation source:
    source = netapi.create_node("Neuron", None)
    netapi.link(source, 'gen', source, 'gen')
    netapi.link(source, 'gen', flowmodule, 'sub')
    source.activation = 1

    # # step & assert that the initfunction and flowfunction ran
    nodenet.step()
    assert flowmodule.activation == 1
    assert datasources.activation == 1
    assert datatargets.activation == 1

    assert np.all(worldadapter.get_flow_datatarget('bar') == sources * 2)
    assert hasattr(flowmodule, 'initfunction_ran')


@pytest.mark.engine("numpy_engine")
def test_multiple_flowgraphs(runtime, test_nodenet, resourcepath):
    """ Testing a flow from datasources to datatargets """
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, resourcepath)

    with netapi.flowbuilder:
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

        # create a second graph
        nodenet.flow('worldadapter', 'foo', bisect.uid, "inputs")
        nodenet.flow(bisect.uid, "outputs", 'worldadapter', 'bar')

        assert not hasattr(double, 'initfunction_ran')
    assert double.initfunction_ran
    # assert len(nodenet.flowfunctions) == 0

    sources = np.zeros((5))
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


@pytest.mark.engine("numpy_engine")
def test_disconnect_flowmodules(runtime, test_nodenet, resourcepath):
    """ test disconnecting flowmodules """
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, resourcepath)

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

    sources = np.zeros((5))
    sources[:] = np.random.randn(*sources.shape)
    worldadapter.set_flow_datasource('foo', sources)

    nodenet.step()
    assert np.all(worldadapter.get_flow_datatarget('bar') == np.zeros_like(worldadapter.get_flow_datatarget('bar')))


@pytest.mark.engine("numpy_engine")
def test_diverging_flowgraph(runtime, test_nodenet, resourcepath):
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, resourcepath)

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

    sources = np.zeros((5))
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


@pytest.mark.engine("numpy_engine")
def test_converging_flowgraphs(runtime, test_nodenet, resourcepath):
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, resourcepath)

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

    sources = np.zeros((5))
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


@pytest.mark.engine("numpy_engine")
def test_flowmodule_persistency(runtime, test_nodenet, resourcepath):
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, resourcepath)

    double = netapi.create_node("Double", None, "Double")

    nodenet.flow('worldadapter', 'foo', double.uid, "inputs")
    nodenet.flow(double.uid, 'outputs', 'worldadapter', 'bar')
    source = netapi.create_node("Neuron", None)
    netapi.link(source, 'gen', source, 'gen')
    netapi.link(source, 'gen', double, 'sub')
    source.activation = 1

    assert double.initfunction_ran

    sources = np.zeros((5))
    sources[:] = np.random.randn(*sources.shape)
    worldadapter.set_flow_datasource('foo', sources)

    nodenet.step()

    result = worldadapter.get_flow_datatarget('bar')

    assert np.allclose(result, sources * 2)

    runtime.save_nodenet(test_nodenet)
    runtime.revert_nodenet(test_nodenet)

    nodenet = runtime.nodenets[test_nodenet]
    netapi = nodenet.netapi
    worldadapter = nodenet.worldadapter_instance
    worldadapter.set_flow_datasource('foo', sources)

    nodenet.step()
    assert np.allclose(worldadapter.get_flow_datatarget('bar'), result)
    assert netapi.get_node(double.uid).initfunction_ran
    # also assert, that the edge-keys are preserved:
    # this would raise an exception otherwise
    netapi.unflow(netapi.get_node(double.uid), 'outputs', 'worldadapter', 'bar')


@pytest.mark.engine("numpy_engine")
def test_flowmodule_reload_code_behaviour(runtime, test_nodenet, resourcepath):
    import os
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, resourcepath)
    double = netapi.create_node("Double", None, "Double")
    netapi.flow('worldadapter', 'foo', double, 'inputs')
    netapi.flow(double, 'outputs', 'worldadapter', 'bar')
    double.ensure_initialized()
    double.set_state('teststate', np.ones(3))
    source = netapi.create_node("Neuron", None)
    netapi.link(source, 'gen', source, 'gen')
    netapi.link(source, 'gen', double, 'sub')
    source.activation = 1
    with open(os.path.join(resourcepath, "nodetypes", "foobar", "Double.py"), 'w') as fp:
        fp.write("""nodetype_definition = {
    "flow_module": True,
    "name": "Double",
    "run_function_name": "double",
    "init_function_name": "double_init",
    "inputs": ["inputs"],
    "outputs": ["outputs"],
}

def double_init(netapi, node, parameters):
    node.initfunction_ran = 'yep'

def double(inputs, netapi, node, parameters):
    return inputs * 4
""")
    runtime.reload_code()
    double = netapi.get_node(double.uid)
    assert double.initfunction_ran == 'yep'
    assert np.all(double.get_state('teststate') == np.ones(3))
    worldadapter = nodenet.worldadapter_instance
    sources = np.zeros((5))
    sources[:] = np.random.randn(*sources.shape)
    worldadapter.set_flow_datasource('foo', sources)
    nodenet.step()
    assert np.all(worldadapter.get_flow_datatarget("bar") == sources * 4)


@pytest.mark.engine("numpy_engine")
def test_delete_flowmodule(runtime, test_nodenet, resourcepath):
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, resourcepath)

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

    sources = np.zeros((5))
    sources[:] = np.random.randn(*sources.shape)
    worldadapter.set_flow_datasource('foo', sources)

    nodenet.step()
    assert np.all(worldadapter.get_flow_datatarget('bar') == np.zeros(5))


@pytest.mark.engine("numpy_engine")
def test_link_large_graph(runtime, test_nodenet, resourcepath):
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, resourcepath)

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

    sources = np.zeros((5))
    sources[:] = np.random.randn(*sources.shape)
    worldadapter.set_flow_datasource('foo', sources)

    nodenet.step()
    assert np.all(worldadapter.get_flow_datatarget('bar') == sources * 2)


@pytest.mark.engine("numpy_engine")
def test_flow_edgecase(runtime, test_nodenet, resourcepath):
    """ Tests a structural edge case: diverging and again converging graph with a numpy node in one arm"""
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, resourcepath)

    twoout = netapi.create_node("TwoOutputs", None, "twoout")
    double = netapi.create_node("Double", None, "double")
    numpy = netapi.create_node("Numpy", None, "numpy")
    add = netapi.create_node("Add", None, "add")

    netapi.flow("worldadapter", "foo", twoout, "X")
    netapi.flow(twoout, "A", double, "inputs")
    netapi.flow(twoout, "B", numpy, "inputs")
    netapi.flow(double, "outputs", add, "input1")
    netapi.flow(numpy, "outputs", add, "input2")
    netapi.flow(add, "outputs", "worldadapter", "bar")

    source = netapi.create_node("Neuron", None)
    source.activation = 1
    netapi.link(source, 'gen', add, 'sub')

    worldadapter.set_flow_datasource('foo', np.ones(5))
    nodenet.timed_step()
    assert np.all(worldadapter.get_flow_datatarget("bar") == np.asarray([5, 5, 5, 5, 5]))


@pytest.mark.engine("numpy_engine")
def test_none_output_skips_following_graphs(runtime, test_nodenet, resourcepath):
    """ Tests the "staudamm" functionality: a graph can return None, thus preventing graphs
    depending on this output as their input from being executed, even if they are requested """
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, resourcepath)

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

    sources = np.zeros((5))
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


@pytest.mark.engine("numpy_engine")
def test_connect_flow_modules_to_structured_flow_datasource(runtime, test_nodenet, resourcepath):
    import os
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, resourcepath)
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

    sources = np.zeros((6))
    sources[:] = np.random.randn(*sources.shape)
    worldadapter.set_flow_datasource('vision', sources)
    worldadapter.set_flow_datasource('start', np.asarray([0.73]))

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

    sources = np.zeros((6))
    sources[:] = np.random.randn(*sources.shape)
    worldadapter.set_flow_datasource('vision', sources)
    worldadapter.set_flow_datasource('start', np.asarray([0.64]))
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
    nodenet.step()
    # assert nodenet.get_node(double.uid).inputmap['inputs'] == tuple()
    # assert nodenet.get_node(sources.uid).outputmap['vision'] == set()
    # assert nodenet.get_node(double.uid).outputmap['outputs'] == set()


@pytest.mark.engine("numpy_engine")
def test_flownode_output_only(runtime, test_nodenet, resourcepath):
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, resourcepath)
    out = netapi.create_node("out12345")
    source = netapi.create_node("Neuron")
    source.activation = 1
    netapi.link(source, 'gen', source, 'gen')
    netapi.link(source, 'gen', out, 'sub')
    netapi.flow(out, 'out', 'worldadapter', 'bar')
    nodenet.step()
    assert np.all(worldadapter.get_flow_datatarget('bar') == [1, 2, 3, 4, 5])


@pytest.mark.engine("numpy_engine")
def test_flownode_generate_netapi_fragment(runtime, engine, test_nodenet, resourcepath):
    """ Takes the above-tested edgecase, creates a recipe via generate_netapi_fragment
    and runs the result"""
    import os
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, resourcepath)
    datasources, datatargets = None, None
    for node in netapi.get_nodes():
        if node.name == 'datasources':
            datasources = node
        elif node.name == 'datatargets':
            datatargets = node

    twoout = netapi.create_node("TwoOutputs", None, "twoout")
    double = netapi.create_node("Double", None, "double")
    numpy = netapi.create_node("Numpy", None, "numpy")
    add = netapi.create_node("Add", None, "add")

    netapi.flow('worldadapter', 'foo', twoout, 'X')
    netapi.flow(twoout, "A", double, "inputs")
    netapi.flow(twoout, "B", numpy, "inputs")
    netapi.flow(double, "outputs", add, "input1")
    netapi.flow(numpy, "outputs", add, "input2")
    netapi.flow(add, "outputs", "worldadapter", "bar")

    source = netapi.create_node("Neuron")
    source.activation = 1.0
    netapi.link(source, 'gen', source, 'gen')
    netapi.link(source, 'gen', add, 'sub')

    nodes = [twoout, double, numpy, add, source, datasources, datatargets]
    fragment = runtime.generate_netapi_fragment(test_nodenet, [n.uid for n in nodes])
    assert "datasources" not in fragment
    assert "datatargets" not in fragment
    source_values = np.random.randn(5)
    worldadapter.set_flow_datasource('foo', source_values)
    nodenet.step()
    result = worldadapter.get_flow_datatarget('bar')

    res, pastenet_uid = runtime.new_nodenet('pastenet', engine, world_uid=nodenet.world, worldadapter="SimpleArrayWA")
    code = """
def foo(netapi):
    %s

""" % "\n    ".join(fragment.split('\n'))
    # save the fragment as recipe & run
    with open(os.path.join(resourcepath, 'recipes', 'test.py'), 'w+') as fp:
        fp.write(code)
    runtime.reload_code()
    runtime.run_recipe(pastenet_uid, 'foo', {})

    pastenet = runtime.get_nodenet(pastenet_uid)
    paste_wa = pastenet.worldadapter_instance
    for n in pastenet.netapi.get_nodes():
        if n.type == "Neuron":
            n.activation = 1

    paste_wa.set_flow_datasource('foo', source_values)
    pastenet.step()
    assert np.all(paste_wa.get_flow_datatarget('bar') == result)


@pytest.mark.engine("numpy_engine")
def test_flow_inf_guard(runtime, test_nodenet, resourcepath):
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, resourcepath)

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


@pytest.mark.engine("numpy_engine")
def test_flow_overlapping_graphs(runtime, test_nodenet, resourcepath):
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, resourcepath)

    with netapi.flowbuilder:
        neuron1 = netapi.create_node('Neuron', None, "Neuron1")
        neuron2 = netapi.create_node('Neuron', None, "Neuron2")
        neuron2.activation = 1
        double1 = netapi.create_node('Double', None, "Double1")
        double2 = netapi.create_node('Double', None, "Double2")

        netapi.link(neuron1, 'gen', double1, 'sub')
        netapi.link(neuron2, 'gen', double2, 'sub')
        netapi.link(neuron2, 'gen', neuron2, 'gen')
        netapi.flow("worldadapter", "vision", double1, "inputs")
        netapi.flow(double1, "outputs", double2, "inputs")
        netapi.flow(double1, "outputs", "worldadapter", "motor")
        netapi.flow(double2, "outputs", "worldadapter", "motor")
    oldval = worldadapter.flow_datasources['vision']
    nodenet.step()
    assert np.all(worldadapter.flow_datatargets['motor'] == oldval * 6)


@pytest.mark.engine("numpy_engine")
def test_flow_nodes_in_nodespaces(runtime, test_nodenet, resourcepath):
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, resourcepath)
    with netapi.flowbuilder:
        neuron = netapi.create_node('Neuron', None, "Neuron1")
        neuron.activation = 1
        netapi.link(neuron, 'gen', neuron, 'gen')
        ns = netapi.create_nodespace(None, name="subnodespace")
        double1 = netapi.create_node('Double', None, "Double1")
        double2 = netapi.create_node('Double', ns.uid, "Double2")

        netapi.link(neuron, 'gen', double1, 'sub')
        netapi.link(neuron, 'gen', double2, 'sub')
        netapi.flow("worldadapter", "vision", double1, "inputs")
        netapi.flow(double1, "outputs", double2, "inputs")
        netapi.flow(double2, "outputs", "worldadapter", "motor")
    oldval = worldadapter.flow_datasources['vision']
    nodenet.step()
    assert np.all(worldadapter.flow_datatargets['motor'] == oldval * 4)
    runtime.save_nodenet(test_nodenet)
    runtime.unload_nodenet(test_nodenet)
    nodenet = runtime.get_nodenet(test_nodenet)
    netapi = nodenet.netapi
    assert netapi.get_node(double2.uid).parent_nodespace == ns.uid
    oldval = nodenet.worldadapter_instance.flow_datasources['vision']
    nodenet.step()
    assert np.all(nodenet.worldadapter_instance.flow_datatargets['motor'] == oldval * 4)
