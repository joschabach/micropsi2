
import pytest


@pytest.mark.xfail(reason="Theano removal broke this for unknown reasons. Works in production")
def test_code_reload(runtime, test_nodenet, resourcepath):
    import os
    os.makedirs(os.path.join(resourcepath, 'nodetypes', 'library'), exist_ok=True)
    os.makedirs(os.path.join(resourcepath, 'dummyworld'), exist_ok=True)
    os.makedirs(os.path.join(resourcepath, 'shared_utils'), exist_ok=True)

    nodetypef = os.path.join(resourcepath, 'nodetypes', 'testnode.py')
    foof = os.path.join(resourcepath, 'nodetypes', 'library', 'foo.py')
    barf = os.path.join(resourcepath, 'nodetypes', 'library', 'bar.py')

    worldjsonf = os.path.join(resourcepath, 'dummyworld', 'worlds.json')
    worldf = os.path.join(resourcepath, 'dummyworld', 'dummyworld.py')
    worldsharedf = os.path.join(resourcepath, 'shared_utils', 'stuff.py')
    open(os.path.join(resourcepath, 'shared_utils', '__init__.py'), 'w').close()

    def write_resources(nodevalues, datasource_name, datatarget_name, worldvalues):
        with open(nodetypef, 'w') as fp:
            fp.write("""
nodetype_definition = {
 'doc': 'calculates stuff',
 'nodefunction_name': 'testnode',
 'name': 'testnode',
 'slottypes': ['gen'],
 'gatetypes': ['gen'],
}

from nodetypes.library.foo import module_level


def testnode(netapi, node):
    from nodetypes.library.foo import inline, get_bar
    val = 1 + module_level + inline + get_bar()
    node.get_gate('gen').gate_function(val)
""")
        with open(foof, 'w') as fp:
            fp.write("""
module_level = %d
inline = %d
def get_bar():
    from nodetypes.library.bar import magicnumber
    return magicnumber
""" % (nodevalues[0], nodevalues[1]))
        with open(barf, 'w') as fp:
            fp.write("magicnumber=%d" % nodevalues[2])

        with open(worldjsonf, 'w') as fp:
            fp.write("""{"worlds": ["dummyworld.py"],"worldadapters": ["dummyworld.py"]}""")
        with open(worldf, 'w') as fp:
            fp.write("""from micropsi_core.world.world import World
from micropsi_core.world.worldadapter import WorldAdapter
from shared_utils.stuff import variable

class DummyWorld(World):
    supported_worldadapters=['DummyWA']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.var = variable
        self.inline = %d

class DummyWA(WorldAdapter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_datasource("foo")
        self.add_datasource("bar")
        self.add_datasource("%s")
        self.add_datatarget("%s")
    def update_data_sources_and_targets(self):
        from shared_utils.stuff import get_values
        values = get_values()
        self.datasources['foo'] = values[0]
        self.datasources['bar'] = values[1]
""" % (worldvalues[0], datasource_name, datatarget_name))
        with open(worldsharedf, 'w') as fp:
            fp.write("""variable = %d
def get_values():
    return %d, %d""" % (worldvalues[1], worldvalues[2], worldvalues[3]))

    write_resources([3, 5, 7], "source", "target", [13, 15, 17, 19])
    res, errors = runtime.reload_code()
    assert res

    res, wuid = runtime.new_world("dummyworld", "DummyWorld")
    runtime.set_nodenet_properties(test_nodenet, world_uid=wuid, worldadapter="DummyWA")

    net = runtime.nodenets[test_nodenet]
    netapi = net.netapi
    node = netapi.create_node('testnode')
    runtime.step_nodenet(test_nodenet)
    assert node.get_gate('gen').activation == 1 + 3 + 5 + 7
    world = runtime.worlds[wuid]
    assert world.inline == 13
    assert world.var == 15
    wa = net.worldadapter_instance
    assert "target" in wa.datatargets
    assert wa.get_datasource_value("foo") == 17
    assert wa.get_datasource_value("bar") == 19
    sensor = netapi.create_node("Sensor", None, "Sensor", datasource="source")
    actuator = netapi.create_node("Actuator", None, "Actuator", datatarget="target")

    write_resources([11, 13, 17], "foo", "bar", [1, 3, 5, 7])
    runtime.reload_code()
    node = netapi.get_node(node.uid)
    runtime.step_nodenet(test_nodenet)
    assert node.get_gate('gen').activation == 1 + 11 + 13 + 17
    world = runtime.worlds[wuid]
    assert world.inline == 1
    assert world.var == 3
    wa = net.worldadapter_instance
    assert "foo" in wa.datasources
    assert "bar" in wa.datatargets
    assert wa.get_datasource_value("foo") == 5
    assert wa.get_datasource_value("bar") == 7
    sensor = netapi.get_node(sensor.uid)
    actuator = netapi.get_node(actuator.uid)
    assert sensor.get_parameter('datasource') is None
    assert actuator.get_parameter('datatarget') is None


@pytest.mark.engine("theano_engine")
@pytest.mark.engine("numpy_engine")
def test_renaming_flow_datasources(runtime, test_nodenet, resourcepath):
    import os

    def write_resources(datasource_name, datatarget_name):
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
        self.add_flow_datasource("%s", shape=(5))
        self.add_flow_datatarget("%s", shape=(5))
        self.update_data_sources_and_targets()

    def update_data_sources_and_targets(self):
        for key in self.flow_datatargets:
            self.flow_datatarget_feedbacks[key] = np.copy(self.flow_datatargets[key])
        for key in self.flow_datasources:
            self.flow_datasources[key] = np.random.rand(len(self.flow_datasources[key]))
    """ % (datasource_name, datatarget_name))

    with open(os.path.join(resourcepath, "nodetypes", "Double.py"), 'w') as fp:
        fp.write("""nodetype_definition = {
    "flow_module": True,
    "implementation": "python",
    "name": "Double",
    "run_function_name": "double",
    "inputs": ["inputs"],
    "outputs": ["outputs"],
    "inputdims": [1]
}

def double(inputs, netapi, node, parameters):
    return inputs * 2""")

    write_resources("foo", "bar")
    runtime.reload_code()
    result, wuid = runtime.new_world("FlowWorld", "FlowWorld")
    runtime.set_nodenet_properties(test_nodenet, world_uid=wuid, worldadapter="SimpleArrayWA")
    nodenet = runtime.nodenets[test_nodenet]
    netapi = nodenet.netapi

    double = netapi.create_node("Double")
    netapi.flow("worldadapter", "foo", double, "inputs")
    netapi.flow(double, "outputs", "worldadapter", "bar")
    runtime.save_nodenet(test_nodenet)

    write_resources("source", "target")
    runtime.reload_code()

    double = netapi.get_node(double.uid)
    assert double.inputmap["inputs"] == tuple()
    assert double.outputmap["outputs"] == set()
    assert nodenet.flowgraph.edges() == []

    netapi.flow("worldadapter", "source", double, "inputs")
    netapi.flow(double, "outputs", "worldadapter", "target")

    runtime.save_nodenet(test_nodenet)
    write_resources("foo", "bar")
    runtime.reload_and_revert(test_nodenet)

    nodenet = runtime.nodenets[test_nodenet]
    netapi = nodenet.netapi

    double = netapi.get_node(double.uid)
    assert double.inputmap["inputs"] == tuple()
    assert double.outputmap["outputs"] == set()
    assert nodenet.flowgraph.edges() == []
