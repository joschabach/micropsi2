# -*- coding: utf-8 -*-

"""
Tests for vizapi
"""

from micropsi_core import runtime as micropsi


def test_plot_activations(test_nodenet):
    from random import random
    nodenet = micropsi.get_nodenet(test_nodenet)
    vizapi = nodenet.netapi.vizapi
    activations = [random() for i in range(256)]
    plot = vizapi.NodenetPlot(plotsize=(2, 2))
    plot.add_activation_plot(activations)
    res = plot.to_base64(format="png")
    assert len(res) > 1000
    assert res.endswith('\n')


def test_plot_linkweights(test_nodenet):
    from random import random
    nodenet = micropsi.get_nodenet(test_nodenet)
    vizapi = nodenet.netapi.vizapi
    linkweights = []
    for i in range(16):
        linkweights.append([random() for i in range(16)])
    plot = vizapi.NodenetPlot(plotsize=(2, 2))
    plot.add_linkweights_plot(linkweights)
    res = plot.to_base64(format="png")
    assert len(res) > 1000
    assert res.endswith('\n')


def test_save_file(test_nodenet, resourcepath):
    from random import random
    import os
    nodenet = micropsi.get_nodenet(test_nodenet)
    vizapi = nodenet.netapi.vizapi
    activations = [random() for i in range(256)]
    plot = vizapi.NodenetPlot(plotsize=(2, 2))
    plot.add_activation_plot(activations)
    filepath = os.path.join(resourcepath, "plot.png")
    returnpath = plot.save_to_file(filepath)
    assert os.path.abspath(returnpath) == os.path.abspath(filepath)
    assert os.path.isfile(filepath)


def test_plot_from_nodefunc(test_nodenet, resourcepath, nodetype_def, nodefunc_def):
    import os
    from random import random
    from time import sleep
    nodenet = micropsi.get_nodenet(test_nodenet)
    vizapi = nodenet.netapi.vizapi
    activations = [random() for i in range(256)]
    plot = vizapi.NodenetPlot(plotsize=(2, 2))
    plot.add_activation_plot(activations)
    filepath = os.path.join(resourcepath, "plot.png")
    returnpath = plot.save_to_file(filepath)
    assert os.path.abspath(returnpath) == os.path.abspath(filepath)
    assert os.path.isfile(filepath)
    os.remove(filepath)
    with open(nodetype_def, 'w') as fp:
        fp.write("""{"Plotter": {
            "name": "Plotter",
            "slottypes": [],
            "nodefunction_name": "plotfunc",
            "gatetypes": [],
            "parameters": ["plotpath"]}}""")
    with open(nodefunc_def, 'w') as fp:
        fp.write("""
def plotfunc(netapi, node=None, **params):
    import os
    from random import random
    filepath = os.path.join(params['plotpath'], 'plot.png')
    activations = [random() for i in range(256)]
    plot = netapi.vizapi.NodenetPlot(plotsize=(2, 2))
    plot.add_activation_plot(activations)
    plot.save_to_file(filepath)
""")
    micropsi.reload_native_modules()
    node = nodenet.netapi.create_node("Plotter", None, name="Plotter")
    node.set_parameter("plotpath", resourcepath)
    micropsi.set_runner_properties(1000, 1)
    micropsi.start_nodenetrunner(test_nodenet)
    sleep(2)
    micropsi.stop_nodenetrunner(test_nodenet)
    print(micropsi.MicropsiRunner.last_nodenet_exception)
    assert micropsi.MicropsiRunner.last_nodenet_exception == {}
    assert os.path.isfile(os.path.join(resourcepath, "plot.png"))
