
import os
import pytest


@pytest.mark.engine("theano_engine")
def test_activation_recorder(runtime, test_nodenet, resourcepath):
    nodenet = runtime.nodenets[test_nodenet]
    netapi = nodenet.netapi
    nodespace = netapi.get_nodespace(None)
    nodes = []
    for i in range(10):
        runtime.step_nodenet(test_nodenet)
        node = netapi.create_node('Neuron', None, "testnode_%d" % i)
        nodes.append(node)
        if i > 0:
            netapi.link(nodes[i - 1], 'gen', node, 'gen')
    source = netapi.create_node("Neuron", None, "Source")
    netapi.link(source, 'gen', source, 'gen')
    netapi.link(source, 'gen', nodes[0], 'gen')
    source.activation = 1
    recorder = netapi.add_gate_activation_recorder(group_definition={'nodespace_uid': nodespace.uid, 'node_name_prefix': 'testnode'}, name="recorder", interval=2)
    assert recorder.name == 'recorder'
    assert recorder.interval == 2
    for i in range(5):
        runtime.step_nodenet(test_nodenet)
    assert recorder.first_step == 12
    assert recorder.current_index == 1
    filename = os.path.join(resourcepath, 'recorder.npz')
    recorder.save(filename=filename)
    assert os.path.isfile(filename)
    assert recorder.values['activations'][1].tolist() == [1, 1, 1, 1, 0, 0, 0, 0, 0, 0]
    runtime.save_nodenet(test_nodenet)
    runtime.revert_nodenet(test_nodenet)
    recorder = netapi.get_recorder(recorder.uid)
    assert recorder.values['activations'][1].tolist() == [1, 1, 1, 1, 0, 0, 0, 0, 0, 0]


@pytest.mark.engine("theano_engine")
def test_nodeactivation_recorder(runtime, test_nodenet):
    import numpy as np
    nodenet = runtime.nodenets[test_nodenet]
    netapi = nodenet.netapi
    nodes = []
    source = netapi.create_node("Neuron", None, 'source')
    source.activation = 1
    for i in range(10):
        node = netapi.create_node('Pipe', None, "testnode_%d" % i)
        netapi.link(source, 'gen', node, 'sub')
        nodes.append(node)

    recorder = netapi.add_node_activation_recorder(group_definition={'nodespace_uid': None, 'node_name_prefix': 'testnode'}, name="recorder")

    gatecount = len(nodes[0].get_gate_types())
    runtime.step_nodenet(test_nodenet)
    values = recorder.values['activations'][0]

    assert values.shape == (gatecount, 10)
    assert np.all(values[5] == 1)
    assert np.all(values[3] == 1)
    assert np.all(values[0] == 0)


@pytest.mark.engine("theano_engine")
def test_linkweight_recorder(runtime, test_nodenet):
    nodenet = runtime.nodenets[test_nodenet]
    netapi = nodenet.netapi
    nodespace = netapi.get_nodespace(None)
    layer1 = []
    layer2 = []
    for i in range(10):
        layer1.append(netapi.create_node('Neuron', None, "l1_%d" % i))
        layer2.append(netapi.create_node('Neuron', None, "l2_%d" % i))
    for i in range(10):
        for j in range(10):
            netapi.link(layer1[i], 'gen', layer2[j], 'gen', weight=0.89)

    recorder = netapi.add_linkweight_recorder(
        from_group_definition={'nodespace_uid': nodespace.uid, 'node_name_prefix': 'l1'},
        to_group_definition={'nodespace_uid': nodespace.uid, 'node_name_prefix': 'l2'},
        name="recorder", interval=1)

    runtime.step_nodenet(test_nodenet)
    values = recorder.values
    assert set(["%.2f" % item for row in values['linkweights'][0] for item in row]) == {"0.89"}
    assert len(values['from_bias'][0]) == 10
    assert len(values['to_bias'][0]) == 10
    runtime.save_nodenet(test_nodenet)
    runtime.revert_nodenet(test_nodenet)
    recorder = netapi.get_recorder(recorder.uid)
    assert set(["%.2f" % item for row in recorder.values['linkweights'][0] for item in row]) == {"0.89"}
    assert len(values['from_bias'][0]) == 10
    assert len(values['to_bias'][0]) == 10


@pytest.mark.engine("theano_engine")
def test_clear_recorder(runtime, test_nodenet):
    nodenet = runtime.nodenets[test_nodenet]
    netapi = nodenet.netapi
    nodespace = netapi.get_nodespace(None)
    for i in range(5):
        netapi.create_node('Neuron', None, "testnode_%d" % i)
    recorder = netapi.add_gate_activation_recorder(group_definition={'nodespace_uid': nodespace.uid, 'node_name_prefix': 'testnode'}, name="recorder")
    for i in range(3):
        runtime.step_nodenet(test_nodenet)
    assert len(recorder.values['activations'].tolist()[3]) == 5
    recorder.clear()
    assert recorder.values == {}


@pytest.mark.engine("theano_engine")
def test_remove_recorder(runtime, test_nodenet):
    nodenet = runtime.nodenets[test_nodenet]
    netapi = nodenet.netapi
    nodespace = netapi.get_nodespace(None)
    for i in range(5):
        netapi.create_node('Neuron', None, "testnode_%d" % i)
    recorder = netapi.add_gate_activation_recorder(group_definition={'nodespace_uid': nodespace.uid, 'node_name_prefix': 'testnode'}, name="recorder")
    for i in range(3):
        runtime.step_nodenet(test_nodenet)
    netapi.remove_recorder(recorder.uid)
    assert netapi.get_recorder(recorder.uid) is None


@pytest.mark.engine("theano_engine")
def test_grow_recorder_values(runtime, test_nodenet):
    from micropsi_core.nodenet.recorder import Recorder
    nodenet = runtime.nodenets[test_nodenet]
    netapi = nodenet.netapi
    nodespace = netapi.get_nodespace(None)
    for i in range(5):
        netapi.create_node('Neuron', None, "testnode_%d" % i)
    Recorder.initial_size = 5
    recorder = netapi.add_gate_activation_recorder(group_definition={'nodespace_uid': nodespace.uid, 'node_name_prefix': 'testnode'}, name="recorder")
    runtime.step_nodenet(test_nodenet)
    assert len(recorder.values['activations']) == 5
    for i in range(20):
        runtime.step_nodenet(test_nodenet)
    assert len(recorder.values['activations'] == 25)


@pytest.mark.engine("theano_engine")
def test_export_recorders(runtime, test_nodenet):
    from micropsi_core.nodenet.recorder import Recorder
    import numpy as np
    from io import BytesIO
    nodenet = runtime.nodenets[test_nodenet]
    netapi = nodenet.netapi
    for i in range(4):
        runtime.step_nodenet(test_nodenet)
    nodespace = netapi.get_nodespace(None)
    for i in range(5):
        netapi.create_node('Neuron', None, "testnode_%d" % i)
    Recorder.initial_size = 5
    recorder = netapi.add_gate_activation_recorder(group_definition={'nodespace_uid': nodespace.uid, 'node_name_prefix': 'testnode'}, interval=2, name="recorder")
    runtime.step_nodenet(test_nodenet)
    runtime.step_nodenet(test_nodenet)
    data = runtime.export_recorders(test_nodenet, [recorder.uid])
    stream = BytesIO(data)
    loaded = np.load(stream)
    assert 'recorder_activations' in loaded
    assert 'recorder_meta' in loaded
    assert np.all(loaded['recorder_meta'] == [6, 2])
    assert loaded['recorder_activations'][0][0] == 0
