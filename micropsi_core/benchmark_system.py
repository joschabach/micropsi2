#!/usr/bin/env python3


def benchmark_system(n=1000, repeat=100):

    import numpy as np
    import tensorflow as tf
    import scipy
    import timeit

    result = [""]

    result.append("numpy version: {:>12}".format(np.__version__))
    result.append("scipy version: {:>12}".format(scipy.__version__))
    result.append("tensorflow version: {:>6}".format(tf.__version__))
    result.append("")

    # numpy dot
    setup = "import numpy as np; x = np.random.random(({0}, {0})).astype(np.float32)".format(n)
    statement = "np.dot(x, x.T)"
    timer = timeit.Timer(statement, setup=setup)
    t = timer.timeit(repeat) / repeat
    f = 2 * n ** 3 / t / 1e9
    result.append("numpy dot      {:.4f} seconds; flop rate = {: 7.2f} Gflops/s".format(t, f))

    # scipy dot
    setup = "import scipy; import numpy as np; x = np.random.random(({0}, {0})).astype(np.float32)".format(n)
    statement = "scipy.dot(x, x.T)"
    timer = timeit.Timer(statement, setup=setup)
    t = timer.timeit(repeat) / repeat
    f = 2 * n ** 3 / t / 1e9
    result.append("scipy dot      {:.4f} seconds; flop rate = {: 7.2f} Gflops/s".format(t, f))

    # Fortran dot
    setup = "from scipy import linalg; import numpy as np; x = np.random.random(({0}, {0})).astype(np.float32)".format(n)
    statement = "linalg.blas.dgemm(1.0, x, x.T)"
    timer = timeit.Timer(statement, setup=setup)
    t = timer.timeit(repeat) / repeat
    f = 2 * n ** 3 / t / 1e9
    result.append("scipy dgemm    {:.4f} seconds; flop rate = {: 7.2f} Gflops/s".format(t, f))

    # tensorflow matmul
    setup = "import numpy as np; import tensorflow as tf; \
             xs = tf.placeholder(dtype=np.float64); \
             dot = tf.matmul(xs, tf.transpose(xs)); \
             func = lambda x: tf.Session().run(dot, feed_dict={xs: x}); \
             x = np.random.random((%s, %s))" % (n, n)
    statement = "func(x)"
    timer = timeit.Timer(statement, setup=setup)
    t = timer.timeit(repeat) / repeat
    f = 2 * n ** 3 / t / 1e9
    result.append("tf matmul      {:.4f} seconds; flop rate = {: 7.2f} Gflops/s".format(t, f))

    # tensorflow using a (shared) variable
    setup = "import tensorflow as tf; import numpy as np; \
             x = np.random.random((%s, %s)); \
             X = tf.Variable(x); init_op = tf.global_variables_initializer(); \
             z = tf.matmul(X, tf.transpose(X)); \
             g = lambda s: s.run(init_op); f = lambda s: s.run(z)" % (n, n)
    statement = "sess = tf.Session(); g(sess); f(sess)"
    timer = timeit.Timer(statement, setup=setup)
    # theano_times_list = timer.repeat(num_repeats, 1)
    t = timer.timeit(repeat) / repeat
    f = 2 * n ** 3 / t / 1e9
    result.append("tf variable    {:.4f} seconds; flop rate = {: 7.2f} Gflops/s".format(t, f))

    result.append("")

    return "\n".join(result)


if __name__ == "__main__":  # pragma: no cover

    results = benchmark_system()
    print(results)
