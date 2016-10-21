#!/usr/local/bin/python
# -*- coding: utf-8 -*-


import pytest
# skip these tests if numpy is not installed
pytest.importorskip("numpy")

import numpy as np
from micropsi_core.nodenet.node import Nodetype
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
        "flowmodule": true,
        "name": "Double",
        "flowfunction_name" : "double",
        "inputs": ["inputs"],
        "outputs": ["outputs"]
    },
    "Add": {
        "flowmodule": true,
        "name": "Add",
        "flowfunction_name" : "add",
        "inputs": ["input1", "input2"],
        "outputs": ["outputs"]
    },
    "Bisect": {
        "flowmodule": true,
        "name": "Bisect",
        "flowfunction_name" : "bisect",
        "inputs": ["inputs"],
        "outputs": ["outputs"]
    }}""")
    with open(os.path.join(resourcepath, 'nodefunctions.py'), 'w') as fp:
        fp.write("""
def double(inputs):
    return inputs * 2

def add(input1, input2):
    return input1 + input2

def bisect(inputs):
    return inputs / 2
""")

    nodenet = runtime.nodenets[test_nodenet]
    netapi = nodenet.netapi
    worldadapter = SimpleArrayWA(runtime.worlds[default_world])
    nodenet.worldadapter_instance = worldadapter
    runtime.reload_native_modules()
    return nodenet, netapi, worldadapter


@pytest.mark.engine("theano_engine")
def test_flowmodule_definition(runtime, test_nodenet, default_world, resourcepath):
    import numpy as np
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, default_world, resourcepath)

    assert nodenet.get_available_flow_module_inputs() == ["datasources"]

    flowmodule = netapi.create_flow_module("Double", None, "Double")
    nodenet.link_flow_module_to_worldadapter(flowmodule.uid, "inputs")
    nodenet.link_flow_module_to_worldadapter(flowmodule.uid, "outputs")

    assert nodenet.get_available_flow_module_inputs() == ["datasources", "%s:outputs" % flowmodule.uid]

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

    # # step & assert that the flowfunction ran
    nodenet.step()
    assert np.all(worldadapter.datatarget_values == sources * 2)


@pytest.mark.engine("theano_engine")
def test_multiple_flowgraphs(runtime, test_nodenet, default_world, resourcepath):
    import numpy as np
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, default_world, resourcepath)

    double = netapi.create_flow_module("Double", None, "Double")
    add = netapi.create_flow_module("Add", None, "Add")
    bisect = netapi.create_flow_module("Bisect", None, "Bisect")

    # create a first graph
    # link datasources to double & add
    nodenet.link_flow_module_to_worldadapter(double.uid, "inputs")
    nodenet.link_flow_module_to_worldadapter(add.uid, "input2")
    # link double to add:
    nodenet.link_flow_modules(double.uid, "outputs", add.uid, "input1")
    # link add to datatargets
    nodenet.link_flow_module_to_worldadapter(add.uid, "outputs")

    # create a second graph
    nodenet.link_flow_module_to_worldadapter(bisect.uid, "inputs")
    nodenet.link_flow_module_to_worldadapter(bisect.uid, "outputs")

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
def test_unlink_flowmodules(runtime, test_nodenet, default_world, resourcepath):
    nodenet, netapi, worldadapter = prepare(runtime, test_nodenet, default_world, resourcepath)

    double = netapi.create_flow_module("Double", None, "Double")
    add = netapi.create_flow_module("Add", None, "Add")
    # bisect = netapi.create_flow_module("Bisect", None, "Bisect")

    # link datasources to double & add
    nodenet.link_flow_module_to_worldadapter(double.uid, "inputs")
    nodenet.link_flow_module_to_worldadapter(add.uid, "input2")
    # link double to add:
    nodenet.link_flow_modules(double.uid, "outputs", add.uid, "input1")
    # link add to datatargets
    nodenet.link_flow_module_to_worldadapter(add.uid, "outputs")

    # have one connected graph
    assert len(nodenet.flow_graphs) == 1

    # unlink double from add
    nodenet.unlink_flow_modules(double.uid, "outputs", add.uid, "input1")
    assert double.uid not in nodenet.flow_modules[add.uid].dependencies

    # have two seperated graphs again
    assert len(nodenet.flow_graphs) == 2

    # unlink add from datatargets
    nodenet.unlink_flow_module_from_worldadapter(add.uid, "outputs")
    assert len(nodenet.flow_graphs) == 2
    assert set([g.endnode_uid for g in nodenet.flow_graphs]) == set([double.uid, add.uid])
    assert set([g.write_datatargets for g in nodenet.flow_graphs]) == {False}
