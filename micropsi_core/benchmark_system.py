#!/usr/bin/env python3


def benchmark_system(n=1000, repeat=100):

    import numpy as np
    import theano
    import scipy
    import timeit

    result = [""]

    result.append("numpy version: %s" % np.__version__)
    result.append("scipy version: %s" % scipy.__version__)
    result.append("theano version: %s" % theano.__version__)
    result.append("")
    result.append("theano device: %s" % theano.config.device)
    result.append("theano blas: %s" % theano.config.blas.ldflags)
    result.append("")

    # numpy dot
    setup = "import numpy as np; x = np.random.random(({0}, {0})).astype(np.float32)".format(n)
    statement = "np.dot(x, x.T)"
    timer = timeit.Timer(statement, setup=setup)
    t = timer.timeit(repeat) / repeat
    f = 2 * n ** 3 / t / 1e9
    result.append("numpy dot      %.4f seconds; flop rate = %.2f Gflops/s" % (t, f))

    # scipy dot
    setup = "import scipy; import numpy as np; x = np.random.random(({0}, {0})).astype(np.float32)".format(n)
    statement = "scipy.dot(x, x.T)"
    timer = timeit.Timer(statement, setup=setup)
    t = timer.timeit(repeat) / repeat
    f = 2 * n ** 3 / t / 1e9
    result.append("scipy dot      %.4f seconds; flop rate = %.2f Gflops/s" % (t, f))

    # Fortran dot
    setup = "from scipy import linalg; import numpy as np; x = np.random.random(({0}, {0})).astype(np.float32)".format(n)
    statement = "linalg.blas.dgemm(1.0, x, x.T)"
    timer = timeit.Timer(statement, setup=setup)
    t = timer.timeit(repeat) / repeat
    f = 2 * n ** 3 / t / 1e9
    result.append("scipy dgemm    %.4f seconds; flop rate = %.2f Gflops/s" % (t, f))

    # theano dot
    setup = "import theano; import theano.tensor as T; x = T.matrix(); \
             dot = x.dot(x.T); func = theano.function([x], dot); \
             import numpy as np; x = np.random.random(({0}, {0})).astype(np.float32)".format(n)
    statement = "func(x)"
    timer = timeit.Timer(statement, setup=setup)
    t = timer.timeit(repeat) / repeat
    f = 2 * n ** 3 / t / 1e9
    result.append("theano dot     %.4f seconds; flop rate = %.2f Gflops/s" % (t, f))

    # theano using a shared variable
    setup = "import theano; import numpy as np; x = np.random.random(({0}, {0})).astype(np.float32); \
             X = theano.shared(x); z = theano.tensor.dot(X, X.T); f = theano.function([], z)".format(n)
    statement = "f()"
    timer = timeit.Timer(statement, setup=setup)
    # theano_times_list = timer.repeat(num_repeats, 1)
    t = timer.timeit(repeat) / repeat
    f = 2 * n ** 3 / t / 1e9
    result.append("theano shared  %.4f seconds; flop rate = %.2f Gflops/s" % (t, f))

    result.append("")

    return "\n".join(result)


if __name__ == "__main__":  # pragma: no cover

    results = benchmark_system()
    print(results)
