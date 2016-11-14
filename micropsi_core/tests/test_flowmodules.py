#!/usr/local/bin/python
# -*- coding: utf-8 -*-


import pytest
# skip these tests if numpy is not installed
pytest.importorskip("numpy")

import numpy as np
from micropsi_core.world.worldadapter import ArrayWorldAdapter


class SimpleArrayWA(ArrayWorldAdapter):
    def __init__(self, world):
        super().__init__(world)
        self.add_datasources(['a', 'b', 'c', 'd', 'e'])
        self.add_datatargets(['a', 'b', 'c', 'd', 'e'])
        self.update_data_sources_and_targets()

    def update_data_sources_and_targets(self):
        self.datatarget_feedback_values = np.copy(self.datatarget_values)
        self.datasources = np.random.rand(len(self.datasources))


def prepare(runtime, test_nodenet, default_world, resourcepath):
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
        "inputdims": [1, 2]
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
        "flow_function_name": "numpyfunc",
        "inputs": ["inputs"],
        "outputs": ["outputs"]
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
    ones = np.zeros_like(inputs)
    ones[:] = 1.0
    netapi.notify_user(node, "numpyfunc ran")
    return inputs + ones
""")

    nodenet = runtime.nodenets[test_nodenet]
    netapi = nodenet.netapi
    worldadapter = SimpleArrayWA(runtime.worlds[default_world])
    nodenet.worldadapter_instance = worldadapter
    runtime.reload_native_modules()
    return nodenet, netapi, worldadapter


@pytest.mark.engine("theano_engine")
def test_flowmodule_definition(runtime, test_nodenet, default_world, resourcepath):
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, default_world, resourcepath)

    metadata = runtime.get_nodenet_metadata(test_nodenet)
    assert 'Double' not in metadata['native_modules']
    assert metadata['flow_modules']['Double']['inputs'] == ["inputs"]
    assert metadata['flow_modules']['Double']['outputs'] == ["outputs"]

    flowmodule = netapi.create_node("Double", None, "Double")
    assert not hasattr(flowmodule, 'initfunction_ran')

    nodenet.connect_flow_module_to_worldadapter(flowmodule.uid, "inputs")
    nodenet.connect_flow_module_to_worldadapter(flowmodule.uid, "outputs")

    sources = np.zeros((5), dtype=nodenet.numpyfloatX)
    sources[:] = np.random.randn(*sources.shape)

    worldadapter.datasource_values = sources

    # step & assert that nothing happened without sub-activation
    nodenet.step()
    assert np.all(worldadapter.datatarget_values == np.zeros(5, dtype=nodenet.numpyfloatX))

    # create activation source:
    source = netapi.create_node("Neuron", None)
    netapi.link(source, 'gen', source, 'gen')
    netapi.link(source, 'gen', flowmodule, 'sub')
    source.activation = 1

    # # step & assert that the initfunction and flowfunction ran
    nodenet.step()
    assert np.all(worldadapter.datatarget_values == sources * 2)
    assert hasattr(flowmodule, 'initfunction_ran')


@pytest.mark.engine("theano_engine")
def test_multiple_flowgraphs(runtime, test_nodenet, default_world, resourcepath):
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, default_world, resourcepath)

    double = netapi.create_node("Double", None, "Double")
    add = netapi.create_node("Add", None, "Add")
    bisect = netapi.create_node("Bisect", None, "Bisect")

    # create a first graph
    # link datasources to double & add
    nodenet.connect_flow_module_to_worldadapter(double.uid, "inputs")
    nodenet.connect_flow_module_to_worldadapter(add.uid, "input2")
    # link double to add:
    nodenet.connect_flow_modules(double.uid, "outputs", add.uid, "input1")

    # link add to datatargets
    nodenet.connect_flow_module_to_worldadapter(add.uid, "outputs")

    assert len(nodenet.flowfuncs) == 1

    # create a second graph
    nodenet.connect_flow_module_to_worldadapter(bisect.uid, "inputs")
    nodenet.connect_flow_module_to_worldadapter(bisect.uid, "outputs")

    assert len(nodenet.flowfuncs) == 2

    sources = np.zeros((5), dtype=nodenet.numpyfloatX)
    sources[:] = np.random.randn(*sources.shape)

    worldadapter.datasource_values = sources

    # create activation source
    source = netapi.create_node("Neuron", None)
    netapi.link(source, 'gen', source, 'gen')
    source.activation = 1

    # link to first graph:
    netapi.link(source, 'gen', add, 'sub')

    # step & assert that only the first graph ran
    nodenet.step()
    assert np.all(worldadapter.datatarget_values == sources * 3)

    # link source to second graph:
    worldadapter.datatarget_values = np.zeros(len(worldadapter.datatarget_values), dtype=nodenet.numpyfloatX)
    netapi.link(source, 'gen', bisect, 'sub')
    nodenet.step()
    datatargets = np.around(worldadapter.datatarget_values, decimals=4)
    sources = np.around(sources * 3.5, decimals=4)
    assert np.all(datatargets == sources)


@pytest.mark.engine("theano_engine")
def test_disconnect_flowmodules(runtime, test_nodenet, default_world, resourcepath):
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, default_world, resourcepath)

    double = netapi.create_node("Double", None, "Double")
    add = netapi.create_node("Add", None, "Add")

    # link datasources to double & add
    nodenet.connect_flow_module_to_worldadapter(double.uid, "inputs")
    nodenet.connect_flow_module_to_worldadapter(add.uid, "input2")
    # link double to add:
    nodenet.connect_flow_modules(double.uid, "outputs", add.uid, "input1")
    # link add to datatargets
    nodenet.connect_flow_module_to_worldadapter(add.uid, "outputs")

    # have one connected graph
    assert len(nodenet.flowfuncs) == 1

    # unlink double from add
    nodenet.disconnect_flow_modules(double.uid, "outputs", add.uid, "input1")

    # assert dependencies cleaned
    assert double.uid not in nodenet.flow_module_instances[add.uid].dependencies

    # unlink add from datatargets
    nodenet.disconnect_flow_module_from_worldadapter(add.uid, "outputs")

    assert len(nodenet.flowfuncs) == 0

    sources = np.zeros((5), dtype=nodenet.numpyfloatX)
    sources[:] = np.random.randn(*sources.shape)
    worldadapter.datasource_values = sources

    nodenet.step()
    assert np.all(worldadapter.datatarget_values == np.zeros(5))


@pytest.mark.engine("theano_engine")
def test_diverging_flowgraph(runtime, test_nodenet, default_world, resourcepath):
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, default_world, resourcepath)

    double = netapi.create_node("Double", None, "Double")
    add = netapi.create_node("Add", None, "Add")
    bisect = netapi.create_node("Bisect", None, "Bisect")

    # link sources to bisect
    nodenet.connect_flow_module_to_worldadapter(bisect.uid, "inputs")
    # link bisect to double:
    nodenet.connect_flow_modules(bisect.uid, "outputs", double.uid, "inputs")
    # link bisect to add:
    nodenet.connect_flow_modules(bisect.uid, "outputs", add.uid, "input1")
    # link sources to add:
    nodenet.connect_flow_module_to_worldadapter(add.uid, "input2")

    # link double and add to targets:
    nodenet.connect_flow_module_to_worldadapter(double.uid, "outputs")
    nodenet.connect_flow_module_to_worldadapter(add.uid, "outputs")

    assert len(nodenet.flowfuncs) == 2

    sources = np.zeros((5), dtype=nodenet.numpyfloatX)
    sources[:] = np.random.randn(*sources.shape)
    worldadapter.datasource_values = sources

    # create activation source
    source = netapi.create_node("Neuron", None)
    netapi.link(source, 'gen', source, 'gen')
    source.activation = 1

    # link activation source to double
    netapi.link(source, 'gen', double, 'sub')
    nodenet.step()
    assert np.all(worldadapter.datatarget_values == sources)

    # unlink double, link add:
    netapi.unlink(source, 'gen', double, 'sub')
    netapi.link(source, 'gen', add, 'sub')
    worldadapter.datatarget_values = np.zeros(len(worldadapter.datatarget_values), dtype=nodenet.numpyfloatX)
    nodenet.step()
    assert np.all(worldadapter.datatarget_values == sources * 1.5)


@pytest.mark.engine("theano_engine")
def test_converging_flowgraphs(runtime, test_nodenet, default_world, resourcepath):
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, default_world, resourcepath)

    double1 = netapi.create_node("Double", None, "Double")
    double2 = netapi.create_node("Double", None, "Double")
    bisect = netapi.create_node("Bisect", None, "Bisect")

    # link sources
    nodenet.connect_flow_module_to_worldadapter(double1.uid, "inputs")
    nodenet.connect_flow_module_to_worldadapter(double2.uid, "inputs")

    # link both doubles to bisect
    nodenet.connect_flow_modules(double1.uid, "outputs", bisect.uid, "inputs")
    nodenet.connect_flow_modules(double2.uid, "outputs", bisect.uid, "inputs")

    # clear the cache?
    import theano
    theano.gof.cc.get_module_cache().clear()

    # link bisect to targets.
    nodenet.connect_flow_module_to_worldadapter(bisect.uid, "outputs")

    sources = np.zeros((5), dtype=nodenet.numpyfloatX)
    sources[:] = np.random.randn(*sources.shape)
    worldadapter.datasource_values = sources

    # create activation source
    source = netapi.create_node("Neuron", None)
    netapi.link(source, 'gen', source, 'gen')
    source.activation = 1

    # link activation source to double
    netapi.link(source, 'gen', bisect, 'sub')
    nodenet.step()
    assert np.all(worldadapter.datatarget_values == sources * 2)


@pytest.mark.engine("theano_engine")
def test_flowmodule_persistency(runtime, test_nodenet, default_world, resourcepath):
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, default_world, resourcepath)

    flowmodule = netapi.create_node("Double", None, "Double")
    nodenet.connect_flow_module_to_worldadapter(flowmodule.uid, "inputs")
    nodenet.connect_flow_module_to_worldadapter(flowmodule.uid, "outputs")
    source = netapi.create_node("Neuron", None)
    netapi.link(source, 'gen', source, 'gen')
    netapi.link(source, 'gen', flowmodule, 'sub')
    source.activation = 1

    runtime.save_nodenet(test_nodenet)
    runtime.revert_nodenet(test_nodenet)

    nodenet = runtime.nodenets[test_nodenet]
    flowmodule = nodenet.get_node(flowmodule.uid)
    netapi = nodenet.netapi
    nodenet.worldadapter_instance = worldadapter

    sources = np.zeros((5), dtype=nodenet.numpyfloatX)
    sources[:] = np.random.randn(*sources.shape)

    worldadapter.datasource_values = sources

    nodenet.step()
    assert np.all(worldadapter.datatarget_values == sources * 2)


@pytest.mark.engine("theano_engine")
def test_delete_flowmodule(runtime, test_nodenet, default_world, resourcepath):
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, default_world, resourcepath)

    double1 = netapi.create_node("Double", None, "Double")
    double2 = netapi.create_node("Double", None, "Double")
    add = netapi.create_node("Add", None, "Add")
    bisect = netapi.create_node("Bisect", None, "Bisect")

    # build graph:
    netapi.connect_flow_modules(bisect, "outputs", add, "input1")
    netapi.connect_flow_modules(add, "outputs", double1, "inputs")
    netapi.connect_flow_modules(add, "outputs", double2, "inputs")
    netapi.connect_flow_module_to_worldadapter(bisect, "inputs")
    netapi.connect_flow_module_to_worldadapter(add, "input2")
    netapi.connect_flow_module_to_worldadapter(double1, "outputs")
    netapi.connect_flow_module_to_worldadapter(double2, "outputs")

    assert len(nodenet.flowfuncs) == 2

    netapi.delete_node(add)

    assert len(nodenet.flowfuncs) == 0

    assert not nodenet.flow_module_instances[bisect.uid].is_output_connected()
    for node in nodenet.flow_module_instances.values():
        assert add.uid not in node.dependencies

    sources = np.zeros((5), dtype=nodenet.numpyfloatX)
    sources[:] = np.random.randn(*sources.shape)
    worldadapter.datasource_values = sources

    nodenet.step()
    assert np.all(worldadapter.datatarget_values == np.zeros(5))


@pytest.mark.engine("theano_engine")
def test_link_large_graph(runtime, test_nodenet, default_world, resourcepath):
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, default_world, resourcepath)

    double = netapi.create_node("Double", None, "Double")
    bisect = netapi.create_node("Bisect", None, "Bisect")
    add = netapi.create_node("Add", None, "Add")

    # create activation source:
    source = netapi.create_node("Neuron", None)
    source.activation = 1

    nodenet.connect_flow_module_to_worldadapter(bisect.uid, "inputs")
    nodenet.connect_flow_modules(bisect.uid, "outputs", double.uid, "inputs")

    nodenet.connect_flow_module_to_worldadapter(add.uid, "input1")
    nodenet.connect_flow_module_to_worldadapter(add.uid, "outputs")

    nodenet.connect_flow_modules(double.uid, "outputs", add.uid, "input2")

    netapi.link(source, 'gen', add, 'sub')
    assert len(nodenet.flowfuncs) == 1

    sources = np.zeros((5), dtype=nodenet.numpyfloatX)
    sources[:] = np.random.randn(*sources.shape)
    worldadapter.datasource_values = sources

    nodenet.step()
    assert np.all(worldadapter.datatarget_values == sources * 2)


@pytest.mark.engine("theano_engine")
def test_python_flowmodules(runtime, test_nodenet, default_world, resourcepath):
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, default_world, resourcepath)

    double = netapi.create_node("Double", None, "Double")
    py = netapi.create_node("Numpy", None, "Numpy")
    bisect = netapi.create_node("Bisect", None, "Bisect")

    source = netapi.create_node("Neuron", None)
    netapi.link(source, 'gen', source, 'gen')
    source.activation = 1

    netapi.connect_flow_module_to_worldadapter(double, "inputs")
    netapi.connect_flow_modules(double, "outputs", py, "inputs")
    netapi.connect_flow_modules(py, "outputs", bisect, "inputs")
    netapi.connect_flow_module_to_worldadapter(bisect, "outputs")

    sources = np.zeros((5), dtype=nodenet.numpyfloatX)
    sources[:] = np.random.randn(*sources.shape)
    worldadapter.datasource_values = sources

    nodenet.step()
    assert np.all(worldadapter.datatarget_values == 0)
    assert not hasattr(py, 'initfunction_ran')

    # netapi.link(source, 'gen', bisect, 'sub')

    nodenet.step()
    assert np.all(worldadapter.datatarget_values == 0)

    netapi.link(source, 'gen', bisect, 'sub')
    netapi.link(source, 'gen', py, 'sub')
    netapi.link(source, 'gen', double, 'sub')

    nodenet.step()
    # ((x * 2) + 1) / 2 == x + .5
    assert np.all(worldadapter.datatarget_values == sources + 0.5)
    assert py.initfunction_ran
