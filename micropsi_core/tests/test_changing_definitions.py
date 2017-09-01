
import pytest


@pytest.mark.engine("theano_engine")
def test_chaning_defs_theano(runtime, test_nodenet, default_world, resourcepath):
    import os
    os.makedirs(os.path.join(resourcepath, 'nodetypes'), exist_ok=True)

    def write_flowmodule(filename, name):
        with open(os.path.join(resourcepath, 'nodetypes', filename), 'w') as fp:
            fp.write("""
nodetype_definition = {
 'run_function_name': 'flowfunc',
 'name': '%s',
 'flow_module': True,
 'implementation': 'python',
 'inputs': ['Y'],
 'outputs': ['X'],
 'inputdims': ['2']
}

def flowfunc(Y, netapi, node, params):
    import numpy as np
    return np.ones((2,3))
""" % name)

    def write_nativemodule(filename, name):
        with open(os.path.join(resourcepath, 'nodetypes', filename), 'w') as fp:
            fp.write("""
nodetype_definition = {
 'nodefunction_name': 'nodefunc',
 'name': '%s',
 'slottypes': ['gen', 'foo', 'bar'],
 'gatetypes': ['gen', 'foo', 'bar']
}

def nodefunc(netapi, node, params):
    pass
""" % name)

    def removedefs(*filenames):
        for f in filenames:
            os.remove(os.path.join(resourcepath, 'nodetypes', f))

    write_flowmodule('foonode.py', 'foonode')
    write_flowmodule('foo2node.py', 'foo2node')
    write_nativemodule('barnode.py', 'barnode')
    runtime.reload_code()

    netapi = runtime.nodenets[test_nodenet].netapi
    foonode = netapi.create_node('foonode')
    barnode = netapi.create_node('barnode')
    neuron = netapi.create_node('Neuron')
    foo2node = netapi.create_node('foo2node')
    netapi.link(neuron, 'gen', foonode, 'gen')
    netapi.link(neuron, 'gen', foo2node, 'gen')
    netapi.link(neuron, 'gen', barnode, 'gen')
    runtime.set_nodenet_properties(nodenet_uid=test_nodenet, world_uid=default_world, worldadapter="DefaultArray")
    netapi.flow('worldadapter', 'vision', foonode, 'Y')
    netapi.flow(foonode, 'X', foo2node, 'Y')
    netapi.flow(foo2node, 'X', 'worldadapter', 'action')
    runtime.save_nodenet(test_nodenet)
    runtime.unload_nodenet(test_nodenet)

    # remove nativemodule
    removedefs('barnode.py')
    runtime.reload_code()
    net = runtime.get_nodenet(test_nodenet)
    assert type(net.netapi.get_node(foonode.uid)).__name__ == "FlowModule"
    with pytest.raises(KeyError):
        net.netapi.get_node(barnode.uid)
    write_nativemodule('barnode.py', 'barnode')
    runtime.unload_nodenet(test_nodenet)

    # remove a flowmodule
    removedefs('foonode.py')
    runtime.reload_code()
    net = runtime.get_nodenet(test_nodenet)
    foo2node = net.netapi.get_node(foo2node.uid)
    assert type(foo2node).__name__ == "FlowModule"
    assert type(net.netapi.get_node(barnode.uid)).__name__ == "TheanoNode"
    assert foonode.uid not in foo2node.inputmap['Y']
    with pytest.raises(KeyError):
        net.netapi.get_node(foonode.uid)
    runtime.unload_nodenet(test_nodenet)

    # change native module to flowmodule and vice versa
    write_flowmodule('barnode.py', 'barnode')
    write_nativemodule('foo2node.py', 'foo2node')
    runtime.reload_code()
    net = runtime.get_nodenet(test_nodenet)
    with pytest.raises(KeyError):
        foo2node = net.netapi.get_node(foo2node.uid)
    with pytest.raises(KeyError):
        barnode = net.netapi.get_node(barnode.uid)
    with pytest.raises(KeyError):
        net.netapi.get_node(foonode.uid)
    newbarnode = net.netapi.create_node("barnode")
    newfoo2node = net.netapi.create_node("foo2node")
    neuron = net.netapi.get_node(neuron.uid)
    net.netapi.link(neuron, 'gen', newbarnode, 'sub')
    net.netapi.link(neuron, 'gen', newfoo2node, 'foo')
    net.netapi.flow('worldadapter', 'vision', newbarnode, 'Y')
    net.netapi.flow(newbarnode, 'X', 'worldadapter', 'action')
