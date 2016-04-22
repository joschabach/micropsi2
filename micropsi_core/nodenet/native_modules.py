"""
Builtin native modules

Currently contains
 * GradientDescent for 3 layers (input, hidden, outpu)
 * GradientDescent for LSTMS
"""

import os

nodetypes = {}

try:
    import numpy as np
    import theano
    numpy_installed = True
except ImportError:
    numpy_installed = False


if numpy_installed:
    # only register these native modules if we
    # have theano and numpy installed.
    nodetypes["GradientDescent"] = {
        "name": "GradientDescent",
        "engine": "theano_engine",
        "slottypes": ["gen"],
        "gatetypes": ["gen"],
        "nodefunction_name": "gradient_descent",
        "symbol": "☲",
        "category": "nn_learning",
        "path": os.path.abspath(__file__),
        "parameters": [
            "ae_type",
            "adadelta_rho",
            "adadelta_eps",
            "check_grad",
            "weight_decay",
            "tied_weights",
            "sparsity_value",
            "sparsity_penalty",
            "t",
            "ctr",
            "input_prefix",
            "hidden_prefix",
            "output_prefix",
            "input_nodespace"
        ],
        "parameter_values": {
            "ae_type": ["sparse", "denoising"],
            "tied_weights": ["True", "False"],
            "check_grad": ["yes", "no"]
        },
        "parameter_defaults": {
            "ae_type": "denoising",
            "tied_weights": "True",
            "hidden_prefix": "hidden_1",
            "output_prefix": "output_1"
        }
    }


def gradient_descent(netapi, node=None, **params):
    """
    Online gradient descent with backpropagation for three layers (input, hidden,
    and output layer) and AdaDelta for adapting the learning rate per parameter.

    References:
    [1] Werbos, PJ. "Beyond Regression:  New Tools for Prediction and Analysis
        in the Behavioral Sciences." (1974).
    [2] Zeiler, MD. "ADADELTA: An adaptive learning rate method." (2012).
    [3] Vincent, P. "Extracting and Composing Robust Features with Denoising
        Autoencoders." (2008).
    """

    # To be able to switch this native module on and off, require positive
    # activation on the gen slot for its code to be run.
    if node.get_slot('gen').activation > 0:

        import theano
        import theano.tensor as T

        # get shared name prefix of nodes in input, hidden, and output layers
        input_ = node.get_parameter('input_prefix')
        hidden = node.get_parameter('hidden_prefix')
        output = node.get_parameter('output_prefix')

        # get the name of the nodespace where the input lives
        ns_input_name = node.get_parameter('input_nodespace')

        # get nodespace uids of nodes in input, hidden, and output layers
        # assumption: if the input layer consists of sensor nodes, they have their
        # own nodespace, all other nodes are in this node's nodespace
        ns_input_uid = None
        for ns in netapi.get_nodespaces():
            if ns.name == ns_input_name:
                ns_input_uid = ns.uid
                break
        ns_hidden_uid = node.parent_nodespace
        ns_output_uid = node.parent_nodespace

        # initialization
        if not hasattr(node, 'initialized'):

            node.set_state('cumulative_error', 0)

            sparse = str(node.get_parameter('ae_type')) == "sparse"
            # denoising = str(node.get_parameter('ae_type')) == "denoising"
            tied_weights = str(node.get_parameter('tied_weights')) == "True"

            # group nodes
            netapi.group_nodes_by_names(ns_input_uid, node_name_prefix=input_)
            netapi.group_nodes_by_names(ns_hidden_uid, node_name_prefix=hidden)
            netapi.group_nodes_by_names(ns_output_uid, node_name_prefix=output)

            # get activation values
            a_i_array = netapi.get_activations(ns_input_uid, input_)
            a_h_array = netapi.get_activations(ns_hidden_uid, hidden)
            a_o_array = netapi.get_activations(ns_output_uid, output)

            node.set_parameter('error', 0.0)  # store error values to observe how training develops

            len_input = len(a_i_array)
            len_hidden = len(a_h_array)
            len_output = len(a_o_array)

            if len_input == 0:
                netapi.logger.warn("Node net has no input nodes whose names start with '%s'", input_)
                node.set_parameter('ctr', 0)
                return
            elif len_hidden == 0:
                netapi.logger.warn("Node net has no hidden nodes whose names start with '%s'.", hidden)
                node.set_parameter('ctr', 0)
                return
            elif len_output == 0:
                netapi.logger.warn("Node net has no output names whose names start with '%s'.", output)
                node.set_parameter('ctr', 0)
                return
            else:
                netapi.logger.info("Initializing theano-based autoencoder backprop with layout: %i -> %i -> %i",
                                   len_input, len_hidden, len_output)

            # get parameter values from node net
            b_h_array = netapi.get_thetas(ns_hidden_uid, hidden)
            b_o_array = netapi.get_thetas(ns_output_uid, output)
            w_hi_array = netapi.get_link_weights(ns_input_uid, input_, ns_hidden_uid, hidden)
            w_oh_array = netapi.get_link_weights(ns_hidden_uid, hidden, ns_output_uid, output)

            # declare shared variables ( shared b/w theano and node nets )
            a_i = node.a_i = theano.shared(value=a_i_array.astype(T.config.floatX), name="a_i", borrow=False)
            a_h = node.a_h = theano.shared(value=a_h_array.astype(T.config.floatX), name="a_h", borrow=False)
            a_o = node.a_o = theano.shared(value=a_o_array.astype(T.config.floatX), name="a_o", borrow=False)
            b_h = node.b_h = theano.shared(value=b_h_array.astype(T.config.floatX), name="b_h", borrow=False)
            b_o = node.b_o = theano.shared(value=b_o_array.astype(T.config.floatX), name="b_o", borrow=False)
            w_hi = node.w_hi = theano.shared(value=w_hi_array.astype(T.config.floatX), name="w_hi", borrow=False)
            w_oh = node.w_oh = theano.shared(value=w_oh_array.astype(T.config.floatX), name="w_oh", borrow=False)

            # write initial parameter values to shared variables
            node.b_h.set_value(b_h_array, borrow=True)
            node.b_o.set_value(b_o_array, borrow=True)
            node.w_hi.set_value(w_hi_array, borrow=True)
            node.w_oh.set_value(w_oh_array, borrow=True)

            # initialize accumulation variables for AdaDelta, ie. mean square gradients and mean square deltas
            ms_grad_b_o = node.ms_grad_b_o = theano.shared(value=np.zeros_like(b_o_array), name="ms_grad_b_o", borrow=True)
            ms_grad_w_oh = node.ms_grad_w_oh = theano.shared(value=np.zeros_like(w_oh_array), name="ms_grad_w_oh", borrow=True)
            ms_grad_b_h = node.ms_grad_b_h = theano.shared(value=np.zeros_like(b_h_array), name="ms_grad_b_h", borrow=True)
            ms_grad_w_hi = node.ms_grad_w_hi = theano.shared(value=np.zeros_like(w_hi_array), name="ms_grad_w_hi", borrow=True)

            ms_delta_b_o = node.ms_delta_b_o = theano.shared(value=np.zeros_like(b_o_array), name="ms_delta_b_o", borrow=True)
            ms_delta_w_oh = node.ms_delta_w_oh = theano.shared(value=np.zeros_like(w_oh_array), name="ms_delta_w_oh", borrow=True)
            ms_delta_b_h = node.ms_delta_b_h = theano.shared(value=np.zeros_like(b_h_array), name="ms_delta_b_h", borrow=True)
            ms_delta_w_hi = node.ms_delta_w_hi = theano.shared(value=np.zeros_like(w_hi_array), name="ms_delta_w_hi", borrow=True)

            # make function parameters theano compatible
            weight_decay = T.scalar("weight_decay", dtype=T.config.floatX)
            sparsity_value = T.scalar("sparsity_value", dtype=T.config.floatX)
            sparsity_penalty = T.scalar("sparsity_penalty", dtype=T.config.floatX)
            ada_rho = T.scalar("ada_rho", dtype=T.config.floatX)
            ada_eps = T.scalar("ada_eps", dtype=T.config.floatX)

            # declare the reconstruction error
            error_term = T.sum(T.square(a_o - a_i)) / 2.  # squared error
            # error_term = -T.sum(a_i * T.log(a_o) + (1. - a_i) * T.log(1. - a_o))  # cross-entropy

            # use a weight constraint as a regularizer
            weight_constraint = (weight_decay / 2.) * (T.sum(T.square(w_hi)) + T.sum(T.square(w_oh)))

            if sparse:  # training criterion for a sparse autoencoder

                # save the average activation of hidden units; initialize to first activation received
                avg_a_h = node.avg_a_h = theano.shared(value=a_h_array, name="avg_a_h", borrow=False)
                new_avg_a_h = 0.95 * avg_a_h + (1 - 0.95) * a_h  # for gradient checking, set new_avg_a_h = a_h

                rho = sparsity_value
                information_gain = rho * T.log(rho / new_avg_a_h) + (1. - rho) * T.log((1. - rho) / (1. - new_avg_a_h))

                sparsity_constraint = sparsity_penalty * T.sum(information_gain)
                cost = error_term + weight_constraint + sparsity_constraint

            else:  # training criterion for a denoising autoencoder

                cost = error_term + weight_constraint

            node.cost = theano.function([weight_decay, sparsity_value, sparsity_penalty], cost, on_unused_input='ignore')
            node.error = theano.function([], error_term / len(b_h_array))

            # compute gradients
            sigmoid_deriv_a_o = a_o * (1. - a_o)
            grad_o = (a_o - a_i) * sigmoid_deriv_a_o  # squared error  # T.grad(cost, z_o)
            # grad_o = ((a_i - a_o) / (a_o - a_o**2)) * sigmoid_deriv_a_o  # cross-entropy

            sigmoid_deriv_a_h = a_h * (1. - a_h)

            if sparse:

                grad_w_oh = T.dot(T.reshape(grad_o, (len_input, 1)), T.reshape(a_h, (1, len_hidden))) + weight_decay * w_oh
                grad_sparsity = (- rho / new_avg_a_h + (1. - rho) / (1. - new_avg_a_h)).T
                grad_h = (T.dot(w_oh.T, grad_o) + sparsity_penalty * grad_sparsity) * sigmoid_deriv_a_h
                grad_w_hi = T.dot(T.reshape(grad_h, (len_hidden, 1)), T.reshape(a_i, (1, len_input))) + weight_decay * w_hi

            else:  # denoising

                grad_w_oh = T.dot(T.reshape(grad_o, (len_input, 1)), T.reshape(a_h, (1, len_hidden))) + weight_decay * w_oh
                grad_h = T.dot(w_oh.T, grad_o) * sigmoid_deriv_a_h
                grad_w_hi = T.dot(T.reshape(grad_h, (len_hidden, 1)), T.reshape(a_i, (1, len_input))) + weight_decay * w_hi

            if tied_weights:
                grad_w_oh = grad_w_oh + grad_w_hi.T
                gradients = [grad_o, grad_w_oh, grad_h]
                ms_grad = [ms_grad_b_o, ms_grad_w_oh, ms_grad_b_h]
                ms_delta = [ms_delta_b_o, ms_delta_w_oh, ms_delta_b_h]
            else:
                gradients = [grad_o, grad_w_oh, grad_h, grad_w_hi]
                ms_grad = [ms_grad_b_o, ms_grad_w_oh, ms_grad_b_h, ms_grad_w_hi]
                ms_delta = [ms_delta_b_o, ms_delta_w_oh, ms_delta_b_h, ms_delta_w_hi]

            # update accumulation variables for AdaDelta and compute new deltas
            # compute an exponentially decaying average of squared gradients
            # ie. recent gradients are more important and the quantity doesn't continue to grow
            # thereby allowing the learning rate to grow or shrink as time progresses ( rather than just shrink as in AdaGrad )
            new_ms_grad = [ada_rho * ms_g + (1 - ada_rho) * (g**2) for ms_g, g in zip(ms_grad, gradients)]
            # Note: the square root of the mean squared gradients plus epsilon is effectively the RMS of the gradients
            # epsilon is added ~"to start off the first iteration and to ensure progress when previous updates become small"
            deltas = [(T.sqrt(ms_d + ada_eps) / T.sqrt(ms_g + ada_eps)) * g for ms_d, ms_g, g in zip(ms_delta, new_ms_grad, gradients)]
            # compute an exponentially decaying average of squared deltas -- this is to ensure correct units
            new_ms_delta = [ada_rho * ms_d + (1 - ada_rho) * (d**2) for ms_d, d in zip(ms_delta, deltas)]

            # update parameters, ie. old_value - learning_rate * delta_value
            if tied_weights:
                new_b_o, new_w_oh, new_b_h = (old - update for old, update in zip([b_o, w_oh, b_h], deltas))
                new_w_hi = new_w_oh.T
                new_ms_grad.append(new_ms_grad[1].T)
                new_ms_delta.append(new_ms_delta[1].T)
                gradients.append(gradients[1].T)
            else:
                new_b_o, new_w_oh, new_b_h, new_w_hi = (old - update for old, update in zip([b_o, w_oh, b_h, w_hi], deltas))

            if sparse:

                update_function = theano.function([weight_decay, sparsity_value, sparsity_penalty, ada_rho, ada_eps],
                                                  None,
                                                  updates=[(b_o, new_b_o),
                                                           (w_oh, new_w_oh),
                                                           (b_h, new_b_h),
                                                           (w_hi, new_w_hi),
                                                           (avg_a_h, new_avg_a_h),
                                                           (ms_grad_b_o, new_ms_grad[0]),
                                                           (ms_grad_w_oh, new_ms_grad[1]),
                                                           (ms_grad_b_h, new_ms_grad[2]),
                                                           (ms_grad_w_hi, new_ms_grad[3]),
                                                           (ms_delta_b_o, new_ms_delta[0]),
                                                           (ms_delta_w_oh, new_ms_delta[1]),
                                                           (ms_delta_b_h, new_ms_delta[2]),
                                                           (ms_delta_w_hi, new_ms_delta[3])],
                                                  on_unused_input='ignore')

            else:  # denoising

                update_function = theano.function([weight_decay, sparsity_value, sparsity_penalty, ada_rho, ada_eps],
                                                  None,
                                                  updates=[(b_o, new_b_o),
                                                           (w_oh, new_w_oh),
                                                           (b_h, new_b_h),
                                                           (w_hi, new_w_hi),
                                                           (ms_grad_b_o, new_ms_grad[0]),
                                                           (ms_grad_w_oh, new_ms_grad[1]),
                                                           (ms_grad_b_h, new_ms_grad[2]),
                                                           (ms_grad_w_hi, new_ms_grad[3]),
                                                           (ms_delta_b_o, new_ms_delta[0]),
                                                           (ms_delta_w_oh, new_ms_delta[1]),
                                                           (ms_delta_b_h, new_ms_delta[2]),
                                                           (ms_delta_w_hi, new_ms_delta[3])],
                                                  on_unused_input='ignore')

            node.get_updated_parameters = update_function

            # for gradient checking use the following function:
            node.get_gradients = theano.function([weight_decay, sparsity_value, sparsity_penalty, ada_rho, ada_eps],
                                                 [gradients[0], gradients[1], gradients[2], gradients[3]], on_unused_input='ignore')

            node.initialized = True

        # get input activations from node net
        a_i_array = netapi.get_activations(ns_input_uid, input_)

        # learn only if activation on the input layer has been persistent for as many steps as your neural net has layers
        # Note: since we're currently using denoising autoencoders, this means persistent up to Bernoulli noise
        try:
            # check if activation has changed since the last step ( by testing if there's any different activation value )
            bool_idx = node.prev_a_i != a_i_array
            input_changed = np.any(bool_idx)

            # if deviating activations were 0 ( i.e most likely the effect of Bernoulli noising ), assume no change
            is_zero = node.prev_a_i[bool_idx] == 0
            # if is_zero contains elements but not all input activations and their values are all zero, assume no change
            if len(is_zero) and len(is_zero) < len(a_i_array) and np.all(is_zero):
                input_changed = False
        except:
            input_changed = True

        node.prev_a_i = a_i_array

        if input_changed:
            node.set_parameter('ctr', 1)
        else:
            node.set_parameter('ctr', int(node.get_parameter('ctr')) + 1)

        # until counter equals number of layers, ie. the same activation has reached all layers, don't compute
        if node.get_parameter('ctr') < 3:
            return

        # get other activations from node net
        a_h_array = netapi.get_activations(ns_hidden_uid, hidden)
        a_o_array = netapi.get_activations(ns_output_uid, output)

        # define learning parameters
        param = node.get_parameter('weight_decay')
        if param is None:
            weight_decay = netapi.floatX(4e-06)  # 0.0001 . 1e-07 assuming batches of size 1000 . 4e-06 assuming batches of size 256
            node.set_parameter('weight_decay', str(weight_decay))  # store as regular float to appease the serializer
        else:
            weight_decay = netapi.floatX(param)

        param = node.get_parameter('sparsity_value')
        if param is None:
            sparsity_value = netapi.floatX(0.05)
            node.set_parameter('sparsity_value', str(sparsity_value))
        else:
            sparsity_value = netapi.floatX(param)

        param = node.get_parameter('sparsity_penalty')
        if param is None:
            sparsity_penalty = netapi.floatX(0.001)  # 3.0 . 0.003 assuming batches of size 1000 . 0.01 assuming batches of size 256
            node.set_parameter('sparsity_penalty', str(sparsity_penalty))
        else:
            sparsity_penalty = netapi.floatX(param)

        param = node.get_parameter('adadelta_rho')
        if param is None:
            ada_rho = netapi.floatX(0.95)
            node.set_parameter('adadelta_rho', str(ada_rho))
        else:
            ada_rho = netapi.floatX(param)

        param = node.get_parameter('adadelta_eps')
        if param is None:
            ada_eps = netapi.floatX(1e-6)
            node.set_parameter('adadelta_eps', str(ada_eps))
        else:
            ada_eps = netapi.floatX(param)

        param = node.get_parameter('ae_type')
        if param is None:
            ae_type = 'sparse'  # options: 'sparse', 'denoising'
            node.set_parameter('ae_type', 'sparse')
        else:
            ae_type = str(param)

        param = node.get_parameter('t')
        if param is None:
            t = 0
            node.set_parameter('t', t)
        else:
            t = int(param)

        # gradient checking
        # Note: use double precision when running gradient checks
        if node.get_parameter('check_grad') == 'yes':

            # get values of biases and weights from node net
            b_h_array = netapi.get_thetas(ns_hidden_uid, hidden)
            b_o_array = netapi.get_thetas(ns_output_uid, output)
            w_hi_array = netapi.get_link_weights(ns_input_uid, input_, ns_hidden_uid, hidden)
            w_oh_array = netapi.get_link_weights(ns_hidden_uid, hidden, ns_output_uid, output)

            # compute the analytical gradient
            anal_grad = compute_analytic_gradient(
                netapi, node, a_i_array, a_h_array, a_o_array, b_h_array, b_o_array, w_hi_array, w_oh_array,
                weight_decay, sparsity_value, sparsity_penalty, ada_rho, ada_eps)

            # compute the numerical gradient
            num_grad = compute_numeric_gradient(
                netapi, node, a_i_array, a_h_array, a_o_array, b_h_array, b_o_array, w_hi_array, w_oh_array,
                weight_decay, sparsity_value, sparsity_penalty)

            # compare them
            diff = np.linalg.norm(num_grad - anal_grad) / np.linalg.norm(num_grad + anal_grad)
            print("Gradient difference: %e" % diff)  # %.10f" % diff
            print("The norm of the difference between numerical and analytical gradient should be < 1e-9\n")

        # write values to shared variables
        node.a_i.set_value(a_i_array, borrow=True)
        node.a_h.set_value(a_h_array, borrow=True)
        node.a_o.set_value(a_o_array, borrow=True)

        # update values in shared variables ( using backpropgation of the gradients )
        node.get_updated_parameters(weight_decay, sparsity_value, sparsity_penalty, ada_rho, ada_eps)

        # write new parameter values to node net
        netapi.set_thetas(ns_output_uid, output, node.b_o.get_value(borrow=True))
        netapi.set_link_weights(ns_hidden_uid, hidden, ns_output_uid, output, node.w_oh.get_value(borrow=True))
        netapi.set_thetas(ns_hidden_uid, hidden, node.b_h.get_value(borrow=True))
        netapi.set_link_weights(ns_input_uid, input_, ns_hidden_uid, hidden, node.w_hi.get_value(borrow=True))

        error = float(node.error())
        # save current error as node parameter
        node.set_parameter('error', error)
        node.set_state('cumulative_error', node.get_state('cumulative_error') + error)

        t = int(node.get_parameter('t'))
        if t % 1000 == 0:
            netapi.logger.debug("Number of backprop steps computed %d" % t)
            netapi.logger.debug("Average Error %.6f (Latest: 0=%.6f)" % ((node.get_state('cumulative_error') / 1000), error))
            node.set_state('cumulative_error', 0.0)

        # reset counter after successful backprop step; cf. must wait for new sensory activation to reach output layer
        node.set_parameter('ctr', 0)
        node.set_parameter('t', t + 1)


def sigmoid(z):
    """ The sigmoid ( activation ) function. """
    return 1. / (1. + np.exp(-z))


def compute_analytic_gradient(netapi, node, a_i, a_h, a_o, b_h, b_o, w_hi, w_oh, weight_decay,
                              sparsity_value, sparsity_penalty, ada_rho, ada_eps):

    # make sure borrow is False here because otherwise the buffers are overwritten and
    # compute_numerical_gradient(..) still needs these same input values for proper comparison
    node.a_i.set_value(a_i, borrow=False)
    node.a_h.set_value(a_h, borrow=False)
    node.a_o.set_value(a_o, borrow=False)
    node.b_h.set_value(b_h, borrow=False)
    node.b_o.set_value(b_o, borrow=False)
    node.w_hi.set_value(w_hi, borrow=False)
    node.w_oh.set_value(w_oh, borrow=False)

    delta_o, delta_w_oh, delta_h, delta_w_hi = \
        node.get_gradients(weight_decay, sparsity_value, sparsity_penalty, ada_rho, ada_eps)

    gradient = np.concatenate((delta_o, np.ravel(delta_w_oh), delta_h, np.ravel(delta_w_hi)))

    return gradient


def compute_numeric_gradient(netapi, node, a_i, a_h, a_o, b_h, b_o, w_hi, w_oh, weight_decay, sparsity_value, sparsity_penalty):
    """ Compute numerical gradient for validating backprop implementation above. """

    from copy import deepcopy

    # helper variables
    epsilon = netapi.floatX(1e-4)
    ni = len(b_o)
    nh = len(b_h)
    nih = ni * nh

    theta = np.concatenate((b_o, np.ravel(w_oh), b_h, np.ravel(w_hi)))

    n = theta.shape[0]
    I = np.eye(n, dtype=netapi.floatX)
    gradient = np.zeros(theta.shape, dtype=netapi.floatX)

    for i in range(n):

        eps_vec = np.array(I[:, i] * epsilon, dtype=netapi.floatX)
        eps_plus = theta + eps_vec
        eps_minus = theta - eps_vec

        # split theta into parts, recompute activations, update shared variables, compute cost
        b_o_plus = eps_plus[: ni]
        w_oh_plus = eps_plus[ni: ni + nih].reshape((ni, nh))
        b_h_plus = eps_plus[ni + nih: ni + nih + nh]
        w_hi_plus = eps_plus[ni + nih + nh:].reshape((nh, ni))
        a_i_plus = deepcopy(a_i)
        a_h_plus = np.ravel(sigmoid(w_hi_plus.dot(a_i_plus) + b_h_plus))
        a_o_plus = np.ravel(sigmoid(w_oh_plus.dot(a_h_plus) + b_o_plus))

        node.a_i.set_value(a_i_plus, borrow=True)
        node.a_h.set_value(a_h_plus, borrow=True)
        node.a_o.set_value(a_o_plus, borrow=True)
        node.b_h.set_value(b_h_plus, borrow=True)
        node.b_o.set_value(b_o_plus, borrow=True)
        node.w_hi.set_value(w_hi_plus, borrow=True)
        node.w_oh.set_value(w_oh_plus, borrow=True)

        cost = node.cost(weight_decay, sparsity_value, sparsity_penalty)

        # split theta into parts, recompute activations, update shared variables, compute cost
        b_o_minus = eps_minus[: ni]
        w_oh_minus = eps_minus[ni: ni + nih].reshape((ni, nh))
        b_h_minus = eps_minus[ni + nih: ni + nih + nh]
        w_hi_minus = eps_minus[ni + nih + nh:].reshape((nh, ni))
        a_i_minus = deepcopy(a_i)
        a_h_minus = np.ravel(sigmoid(w_hi_minus.dot(a_i_minus) + b_h_minus))
        a_o_minus = np.ravel(sigmoid(w_oh_minus.dot(a_h_minus) + b_o_minus))

        node.a_i.set_value(a_i_minus, borrow=True)
        node.a_h.set_value(a_h_minus, borrow=True)
        node.a_o.set_value(a_o_minus, borrow=True)
        node.b_h.set_value(b_h_minus, borrow=True)
        node.b_o.set_value(b_o_minus, borrow=True)
        node.w_hi.set_value(w_hi_minus, borrow=True)
        node.w_oh.set_value(w_oh_minus, borrow=True)

        cost_ = node.cost(weight_decay, sparsity_value, sparsity_penalty)

        # compute cost difference
        gradient[i] = (cost - cost_) / (2. * epsilon)

        if i % 1000 == 0:
            print("Computed numeric gradient for %d parameters" % i)

    return gradient
