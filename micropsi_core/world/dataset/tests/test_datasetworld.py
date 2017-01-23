
import pytest

pytest.importorskip("numpy")


def test_datasetworld(runtime, resourcepath):
    import numpy as np
    import os
    data = {
        'input': np.array(np.random.randn(21, 23), dtype=np.float32),
        'target': np.array(np.random.randn(21, 23), dtype=np.float32)
    }
    filename = os.path.join(resourcepath, 'dataset.npz')
    np.savez(filename, **data)

    success, world_uid = runtime.new_world("Dataset", "Dataset", owner="tester", config={'path': filename})
    assert success
    world = runtime.load_world(world_uid)

    waconf = {
        'input_key': 'input',
        'target_key': 'target',
        'holdout_fraction': 0.7,
        'batch_size': 3
    }
    assert world.__class__.__name__ == 'Dataset'
    success, nodenet_uid = runtime.new_nodenet('testagent', 'theano_engine', worldadapter='SupervisedLearning', world_uid=world_uid, use_modulators=False, worldadapter_config=waconf)
    net = runtime.get_nodenet(nodenet_uid)
    wa = net.worldadapter_instance
    assert wa.__class__.__name__ == "SupervisedLearning"
    assert wa.N == 21
    assert wa.k == 23
    assert wa.l == 23
    assert wa.len_train == 14
    assert wa.batch_size == 3

    assert np.all(wa.get_flow_datasource('test_x') == data['input'][14:, :])
    assert np.all(wa.get_flow_datasource('test_y') == data['target'][14:, :])

    batches_per_epoch = int(wa.len_train / 3)

    xbatches = []
    ybatches = []

    for i in range(batches_per_epoch):
        runtime.step_nodenet(nodenet_uid)
        xbatches.append(wa.get_flow_datasource('train_x'))
        ybatches.append(wa.get_flow_datasource('train_y'))

    xbatches = np.vstack(xbatches)
    ybatches = np.vstack(ybatches)

    xrows = []
    yrows = []
    for i in range(xbatches.shape[0]):
        xrows.append(str(xbatches[i]))
        yrows.append(str(ybatches[i]))

    assert len(set(xrows)) == len(xrows)
    assert len(set(yrows)) == len(yrows)

    runtime.step_nodenet(net.uid)
    assert np.all(wa.get_flow_datasource('epoch_count') == [1])
