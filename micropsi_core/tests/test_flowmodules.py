#!/usr/local/bin/python
# -*- coding: utf-8 -*-


import pytest


@pytest.mark.engine('theano_engine')
@pytest.mark.engine('numpy_engine')
def test_flow_start_stop_hooks(runtime, test_nodenet, resourcepath):
    import os
    from time import sleep
    with open(os.path.join(resourcepath, 'nodetypes', 'foobar.py'), 'w') as fp:
        fp.write("""
nodetype_definition = {
    "name": "foobar",
    "flow_module": True,
    "inputs": [],
    "inputdims": [],
    "outputs": ["gen"],
    "implementation": "python",
    "init_function_name": "foobar_init",
    "run_function_name": "foobar",
}

def hook(node):
    node.hook_runs += 1

def antihook(node):
    node.hook_runs -= 1

def foobar_init(netapi, node, prams):
    node.hook_runs = 0
    node.on_start = hook
    node.on_stop = antihook

def foobar(gen, netapi, node, **_):
    return gen
""")

    res, errors = runtime.reload_code()
    assert res
    netapi = runtime.nodenets[test_nodenet].netapi
    foobar = netapi.create_node('foobar')
    neuron = netapi.create_node('Neuron')
    netapi.link(neuron, 'gen', foobar, 'sub')
    runtime.start_nodenetrunner(test_nodenet)
    sleep(0.001)
    assert foobar.hook_runs == 1
    runtime.stop_nodenetrunner(test_nodenet)
    assert foobar.hook_runs == 0


@pytest.mark.engine("theano_engine")
@pytest.mark.engine("numpy_engine")
def test_malformed_flownodetype_defintion(runtime, test_nodenet, resourcepath):
    import os
    nodetype_file = os.path.join(resourcepath, 'nodetypes', 'Test', 'testnode.py')
    with open(nodetype_file, 'w') as fp:
        fp.write("""nodetype_definition = {
            "flow_module": True,
            "name": "broken"}""")
    res, errors = runtime.reload_code()
    assert not res
    assert "run_function_name" in errors[0]
