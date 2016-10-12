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


@pytest.mark.engine("theano_engine")
def test_flowmodule_definition(runtime, test_nodenet, default_world, resourcepath):
    import os
    import numpy as np

    nodenet = runtime.nodenets[test_nodenet]
    netapi = nodenet.netapi
    worldadapter = SimpleArrayWA(runtime.worlds[default_world])
    nodenet.worldadapter_instance = worldadapter

    with open(os.path.join(resourcepath, 'nodetypes.json'), 'w') as fp:
        fp.write("""
    {"Flow": {
        "flowmodule": true,
        "name": "Flow",
        "flowfunction_name" : "flow",
        "inputs": ["in"],
        "outputs": ["out"]

    }}""")
    with open(os.path.join(resourcepath, 'nodefunctions.py'), 'w') as fp:
        fp.write("""
def flow(inputs):
    out = inputs * 2
    return out
""")

    runtime.reload_native_modules()
    assert nodenet.get_available_flow_module_inputs() == ["datasources"]
    flowmodule = netapi.create_flow_module("Flow", None, "flow")

    nodenet.link_flow_module_to_worldadapter(flowmodule.uid, "in")
    nodenet.link_flow_module_to_worldadapter(flowmodule.uid, "out")

    assert nodenet.get_available_flow_module_inputs() == ["datasources", "%s:out" % flowmodule.uid]

    # step & assert that nothing happened without sub-activatio
    nodenet.step()
    assert np.all(worldadapter.datatarget_values == np.zeros(5))

    # create activation source:
    source = netapi.create_node("Neuron", None)
    netapi.link(source, 'gen', flowmodule, 'sub')

    # # step & assert that the flowfunction ran
    nodenet.step()
    assert np.all(worldadapter.datatargets == worldadapter.datasources * 2)
