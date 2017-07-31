

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

    def write_resources(nodevalues, datatarget_name, worldvalues):
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
        self.add_datatarget("%s")
    def update_data_sources_and_targets(self):
        from shared_utils.stuff import get_values
        values = get_values()
        self.datasources['foo'] = values[0]
        self.datasources['bar'] = values[1]
""" % (worldvalues[0], datatarget_name))
        with open(worldsharedf, 'w') as fp:
            fp.write("""variable = %d
def get_values():
    return %d, %d""" % (worldvalues[1], worldvalues[2], worldvalues[3]))

    write_resources([3, 5, 7], "target", [13, 15, 17, 19])
    res, errors = runtime.reload_code()
    # assert res

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

    write_resources([11, 13, 17], "foobar", [1, 3, 5, 7])
    runtime.reload_code()
    node = netapi.get_node(node.uid)
    runtime.step_nodenet(test_nodenet)
    assert node.get_gate('gen').activation == 1 + 11 + 13 + 17
    world = runtime.worlds[wuid]
    assert world.inline == 1
    assert world.var == 3
    wa = net.worldadapter_instance
    assert "foobar" in wa.datatargets
    assert wa.get_datasource_value("foo") == 5
    assert wa.get_datasource_value("bar") == 7
