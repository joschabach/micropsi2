import pytest


tf = pytest.importorskip("tensorflow")
trt = pytest.importorskip("tensorrt")
uff = pytest.importorskip("uff")

engine_glob = ''


def create_dummy_engine(resourcepath):
    global engine_glob
    model = tf.placeholder(tf.float32, [None, 28, 28, 1], name='input')

    model = tf.layers.conv2d(model, 64, 5, 2, padding='SAME', activation=None, name='conv1', reuse=tf.AUTO_REUSE)
    model = tf.nn.relu(model, name='output')

    sess = tf.Session()
    sess.run(tf.global_variables_initializer())
    graphdef = tf.get_default_graph().as_graph_def()
    frozen_graph = tf.graph_util.convert_variables_to_constants(sess, graphdef,
                                                            ['output'])
    tf_model = tf.graph_util.remove_training_nodes(frozen_graph)

    uff_model = uff.from_tensorflow(tf_model, ['output'])
    uff_parser = trt.parsers.uffparser.create_uff_parser()
    uff_parser.register_input('input', (1, 28, 28), 0)
    uff_parser.register_output('output')

    G_LOGGER = trt.infer.ConsoleLogger(trt.infer.LogSeverity.ERROR)
    engine = trt.utils.uff_to_trt_engine(G_LOGGER, uff_model, uff_parser, 1, 1 << 20)

    uff_parser.destroy()
    engine_glob = engine


@pytest.mark.engine("theano_engine")
@pytest.mark.engine("numpy_engine")
def test_tensorrt_flowmodule(runtime, test_nodenet, resourcepath, default_world):
    if engine_glob is '':
        create_dummy_engine(resourcepath)
    import os
    os.makedirs(os.path.join(resourcepath, 'nodetypes'), exist_ok=True)
    filename = os.path.join(resourcepath, 'nodetypes', 'dummy.engine')
    trt.utils.write_engine_to_file(filename, engine_glob.serialize())

    res, errors = runtime.reload_code()
    assert res
    assert 'dummy.engine' in runtime.native_modules
    assert runtime.native_modules['flow_module']
    assert runtime.native_modules['is_tensorrt_engine']
    assert runtime.native_modules['name'] == ['dummy.engine']
    assert runtime.native_modules['inputs'] == ['input']
    assert runtime.native_modules['outputs'] == ['output']
    assert runtime.native_modules['path'] == filename
    assert runtime.native_modules['category'] == ''
    assert 'dummy.engine' in runtime.nodenets[test_nodenet].native_modules
    netapi = runtime.nodenets[test_nodenet].netapi
    dummy = netapi.create_node('dummy.engine')
    import numpy as np
    dummy._initfunction(netapi, dummy, {})
    res = dummy._flowfunction(np.zeros([1, 28, 28]), netapi, dummy)
    assert res.shape == (64, 14, 14)
