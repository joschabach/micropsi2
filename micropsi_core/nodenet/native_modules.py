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
    nodetypes["GradientDescentLSTM"] = {
        "name": "GradientDescentLSTM",
        "engine": "theano_engine",
        "slottypes": ["trigger", "debug"],
        "gatetypes": ["e"],
        "nodefunction_name": "gradient_descent_lstm",
        "symbol": "↺",
        "category": "nn_learning",
        "path": os.path.abspath(__file__),
        "parameters": [
            "adadelta_rho",
            "adadelta_epsilon",
            "sequence_length",
            "links_io",
            "links_porpor",
            "links_porgin",
            "links_porgou",
            "links_porgfg",
            "bias_gin",
            "bias_gou",
            "bias_gfg",
            "group_t_nodes",
            "group_t_gates",
            "group_i_nodes",
            "group_i_gates",
            "group_c_nodes",
            "group_o_nodes",
            "group_o_gates"
        ],
        "parameter_values": {
            "links_io": ["true", "false"],
            "links_porpor": ["true", "false"],
            "links_porgin": ["true", "false"],
            "links_porgou": ["true", "false"],
            "links_porgfg": ["true", "false"],
            "bias_gin": ["true", "false"],
            "bias_gou": ["true", "false"],
            "bias_gfg": ["true", "false"]
        },
        "parameter_defaults": {
            "adadelta_rho": "0.95",
            "adadelta_epsilon": "0.000001",
            "sequence_length": "5",
            "links_io": "true",
            "links_porpor": "true",
            "links_porgin": "true",
            "links_porgou": "true",
            "links_porgfg": "true",
            "bias_gin": "true",
            "bias_gou": "true",
            "bias_gfg": "true",
            "group_t_nodes": "target",
            "group_t_gates": "gen",
            "group_i_nodes": "input",
            "group_i_gates": "gen",
            "group_c_nodes": "lstm",
            "group_o_nodes": "output",
            "group_o_gates": "gen"
        }
    }

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


def gradient_descent_lstm(netapi, node=None, **params):
    """
    Gradient Descent for LSTMs

    The following assumes a three-layer architecture, with hidden LSTM nodes.
    There is always a single LSTM cell per block (no multi-block cells are implemented).

    The following sets of weights are defined:
    input -> output
    input -> cell
    input -> input gate
    input -> output gate
    input -> forget gate
    cell -> output
    cell -> input gate
    cell -> output gate
    cell -> forget gate

    The cell's constant error carousel link is explicitly modelled (as a gen loop).
    Note that input, output and forget gate links aren't updated right now.

    Variable naming and implementation follows:
    Gers & al. 1999, Learning to Forget - Continual Prediction with LSTM

    Other helpful papers:
    Hochreiter & al. 1997, Long Short-Term Memory (introduces naming convention and most of the math)
    Graves & al. 2005, Framewise Phoneme Classification with Bidrectional LSTM and Other NN Architectures

    For the Graves paper, a minimal, almost readable python implementation can be found at:
    https://gist.github.com/neubig/ff2f97d91c9bed820c15

    The ADADELTA implemetation follows the original ADADELTA paper:
    Zeiler 2012, ADADELTA: An Adaptive Learning Rate Method

    A nice theano adadelta implementation is here:
    https://blog.wtf.sg/2014/08/28/implementing-adadelta/
    """

    from numbers import Number
    from theano import tensor as T

    SEQUENCE_LENGTH = 3
    sequence_length_string = node.get_parameter("sequence_length")
    if sequence_length_string is not None:
        SEQUENCE_LENGTH = int(sequence_length_string)

    target = node.get_parameter("group_t_nodes")
    target_gate = node.get_parameter("group_t_gates")
    output = node.get_parameter("group_o_nodes")
    output_gate = node.get_parameter("group_o_gates")
    input = node.get_parameter("group_i_nodes")
    input_gate = node.get_parameter("group_i_gates")
    lstm = node.get_parameter("group_c_nodes")
    lstm_gen = "%s_gen" % lstm
    lstm_por = "%s_por" % lstm
    lstm_gin = "%s_gin" % lstm
    lstm_gou = "%s_gou" % lstm
    lstm_gfg = "%s_gfg" % lstm

    nodespace = node.parent_nodespace

    if not hasattr(node, 'initialized'):

        # create the groups
        netapi.group_nodes_by_names(nodespace, node_name_prefix=target, gate=target_gate)
        netapi.group_nodes_by_names(nodespace, node_name_prefix=output, gate=output_gate)
        netapi.group_nodes_by_names(nodespace, node_name_prefix=input, gate=input_gate)

        netapi.group_nodes_by_names(nodespace, node_name_prefix=lstm, gate="gen", group_name=lstm_gen)
        netapi.group_nodes_by_names(nodespace, node_name_prefix=lstm, gate="por", group_name=lstm_por)
        netapi.group_nodes_by_names(nodespace, node_name_prefix=lstm, gate="gin", group_name=lstm_gin)
        netapi.group_nodes_by_names(nodespace, node_name_prefix=lstm, gate="gou", group_name=lstm_gou)
        netapi.group_nodes_by_names(nodespace, node_name_prefix=lstm, gate="gfg", group_name=lstm_gfg)

        len_output = len(netapi.get_activations(nodespace, output))
        len_input = len(netapi.get_activations(nodespace, input))
        len_hidden = len(netapi.get_activations(nodespace, lstm_por))

        # define a single LSTM-style backpropagation through time step, to be scanned over by theano
        def bpttstep(
                s, tgt, y_k, y_i, y_c, net_in, net_out, net_phi,
                error, drv_ci_prev, drv_cc_prev, drv_ini_prev, drv_inc_prev, drv_in1_prev, drv_phii_prev, drv_phic_prev, drv_phi1_prev,
                delta_w_ki, delta_w_kc, delta_w_outi, delta_w_outc, delta_w_ci, delta_w_cc, delta_w_ini, delta_w_inc, delta_w_phii, delta_w_phic,
                delta_theta_i, delta_theta_k, delta_theta_in, delta_theta_out, delta_theta_phi,
                w_kc, w_ci, w_cc, w_outc, w_outi, w_ini, w_inc, w_phii, w_phic):

            # calculate error
            e_k = tgt - y_k                         # (12) error per output element
            E = T.sum(T.square(e_k)) / 2.           # (12) squared sum to be minimized

            # Part I: standard (truncated) BPTT for links to output registers and lstm output gate slots
            # cell -> output
            # cell -> output gate
            # input -> output
            # input -> output gate

            # functions and derivatives
            y_in = T.nnet.sigmoid(net_in)           # (3) y_in = f(net_in)
            y_out = T.nnet.sigmoid(net_out)         # (3) y_out = f(net_out)
            y_phi = T.nnet.sigmoid(net_phi)         # (3) y_phi = f(net_phi)

            h_s = 2 * T.nnet.sigmoid(s) - 1         # (8)

            f_primed_net_k = y_k * (1. - y_k)       # f'(net_k) = f(net_k) * (1 - f(net_k)), f(net_k) provided as y_k
            f_primed_net_out = y_out * (1. - y_out)
            f_primed_net_in = y_in * (1. - y_in)
            f_primed_net_phi = y_phi * (1. - y_phi)
            # f_primed_net_i = y_i * (1. - y_i)
            h_primed_s = (2 * T.exp(s)) / T.square(T.exp(s) + 1)

            delta_k = f_primed_net_k * e_k                                                                       # (14) delta per output element
            delta_out = f_primed_net_out * h_s * T.sum(w_kc * T.reshape(delta_k, (len_output, 1)), axis=0)       # (15) delta per output gate

            # we use y_c and y_i here instead of y_i_prev because we have "flattened snapshots" to work with
            # i.e. the partial derivative of net_k(t) with respect to w_kc is delta_k(t) * y_c(t)
            # (y_c is what was propagated and created net_k)
            delta_w_kc += T.dot(T.reshape(delta_k, (len_output, 1)), T.reshape(y_c, (1, len_hidden)))       # (13) m = c
            delta_w_ki += T.dot(T.reshape(delta_k, (len_output, 1)), T.reshape(y_i, (1, len_input)))        # (13) m = i
            delta_w_outi += T.dot(T.reshape(delta_out, (len_hidden, 1)), T.reshape(y_i, (1, len_input)))    # (13) m = c
            delta_w_outc += T.dot(T.reshape(delta_out, (len_hidden, 1)), T.reshape(y_c, (1, len_hidden)))   # (13) m = i

            delta_theta_k += delta_k
            delta_theta_out += delta_out

            # Part II: RTRL-style updates
            # input -> cell
            # cell -> cell
            # input -> input gate
            # cell -> input gate
            # input -> forget gate
            # cell -> forget gate

            net_c = T.dot(w_ci, y_i)                                                        # ugly re-calculation of forward pass for net_c
            g_net_c = 4 * T.nnet.sigmoid(net_c) - 2                                         # (5)
            g_primed_net_c = (4 * T.exp(net_c)) / T.square(T.exp(net_c) + 1)

            e_s = y_out * h_primed_s * T.sum(w_kc * T.reshape(delta_k, (len_output, 1)), axis=0)                 # (17)

            drv_ci = drv_ci_prev * T.reshape(y_phi, (len_hidden, 1)) \
                + T.dot(T.reshape(g_primed_net_c * y_in, (len_hidden, 1)), T.reshape(y_i, (1, len_input)))       # (19) m = i
            drv_cc = drv_cc_prev * T.reshape(y_phi, (len_hidden, 1)) \
                + T.dot(T.reshape(g_primed_net_c * y_in, (len_hidden, 1)), T.reshape(y_c, (1, len_hidden)))      # (19) m = i

            drv_ini = drv_ini_prev * T.reshape(y_phi, (len_hidden, 1)) \
                + T.dot(T.reshape(g_net_c * f_primed_net_in, (len_hidden, 1)), T.reshape(y_i, (1, len_input)))   # (20) m = i
            drv_inc = drv_inc_prev * T.reshape(y_phi, (len_hidden, 1)) \
                + T.dot(T.reshape(g_net_c * f_primed_net_in, (len_hidden, 1)), T.reshape(y_c, (1, len_hidden)))  # (20) m = c
            drv_in1 = drv_in1_prev * y_phi + g_net_c * f_primed_net_in

            drv_phii = drv_phii_prev * T.reshape(y_phi, (len_hidden, 1)) \
                + T.dot(T.reshape(h_s * f_primed_net_phi, (len_hidden, 1)), T.reshape(y_i, (1, len_input)))      # (21) m = i
            drv_phic = drv_phic_prev * T.reshape(y_phi, (len_hidden, 1)) \
                + T.dot(T.reshape(h_s * f_primed_net_phi, (len_hidden, 1)), T.reshape(y_c, (1, len_hidden)))     # (21) m = c
            drv_phi1 = drv_phi1_prev * y_phi + h_s * f_primed_net_phi

            delta_w_ci += T.reshape(e_s, (len_hidden, 1)) * drv_ci
            delta_w_cc += T.reshape(e_s, (len_hidden, 1)) * drv_cc

            delta_w_ini += T.reshape(e_s, (len_hidden, 1)) * drv_ini
            delta_w_inc += T.reshape(e_s, (len_hidden, 1)) * drv_inc

            delta_w_phii += T.reshape(e_s, (len_hidden, 1)) * drv_phii
            delta_w_phic += T.reshape(e_s, (len_hidden, 1)) * drv_phic

            # delta_theta_i += 0
            delta_theta_in += e_s * drv_in1
            delta_theta_phi += e_s * drv_phi1

            error = E

            return error, drv_ci, drv_cc, drv_ini, drv_inc, drv_in1, drv_phii, drv_phic, drv_phi1, \
                delta_w_ki, delta_w_kc, delta_w_outi, delta_w_outc, delta_w_ci, delta_w_cc, delta_w_ini, delta_w_inc, delta_w_phii, delta_w_phic, \
                delta_theta_i, delta_theta_k, delta_theta_in, delta_theta_out, delta_theta_phi  # cumulate

        node.set_state('current_error', 0.)
        node.set_state('error', 0.)
        node.set_state('updates', 0)
        node.t = -1
        node.samples = 0

        t_a_i_matrix = node.t_a_i_matrix = np.zeros(shape=(SEQUENCE_LENGTH, len_input)).astype(T.config.floatX)
        t_a_t_matrix = node.t_a_t_matrix = np.zeros(shape=(SEQUENCE_LENGTH, len_output)).astype(T.config.floatX)
        t_a_o_matrix = node.t_a_o_matrix = np.zeros(shape=(SEQUENCE_LENGTH, len_output)).astype(T.config.floatX)
        t_a_h_gen_matrix = node.t_a_h_gen_matrix = np.zeros(shape=(SEQUENCE_LENGTH, len_hidden)).astype(T.config.floatX)
        t_a_h_por_matrix = node.t_a_h_por_matrix = np.zeros(shape=(SEQUENCE_LENGTH, len_hidden)).astype(T.config.floatX)
        t_a_h_gin_matrix = node.t_a_h_gin_matrix = np.zeros(shape=(SEQUENCE_LENGTH, len_hidden)).astype(T.config.floatX)
        t_a_h_gou_matrix = node.t_a_h_gou_matrix = np.zeros(shape=(SEQUENCE_LENGTH, len_hidden)).astype(T.config.floatX)
        t_a_h_gfg_matrix = node.t_a_h_gfg_matrix = np.zeros(shape=(SEQUENCE_LENGTH, len_hidden)).astype(T.config.floatX)

        w_oh_por_array = netapi.get_link_weights(nodespace, lstm_por, nodespace, output)
        w_oi_array = netapi.get_link_weights(nodespace, input, nodespace, output)
        w_h_por_i_array = netapi.get_link_weights(nodespace, input, nodespace, lstm_por)
        w_h_gou_h_por_array = netapi.get_link_weights(nodespace, lstm_por, nodespace, lstm_gou)
        w_h_gou_i_array = netapi.get_link_weights(nodespace, input, nodespace, lstm_gou)
        w_h_por_h_por_array = netapi.get_link_weights(nodespace, lstm_por, nodespace, lstm_por)
        w_h_gin_i_array = netapi.get_link_weights(nodespace, input, nodespace, lstm_gin)
        w_h_gin_h_por_array = netapi.get_link_weights(nodespace, lstm_por, nodespace, lstm_gin)
        w_h_gfg_i_array = netapi.get_link_weights(nodespace, input, nodespace, lstm_gfg)
        w_h_gfg_h_por_array = netapi.get_link_weights(nodespace, lstm_por, nodespace, lstm_gfg)

        theta_input_array = netapi.get_thetas(nodespace, input)
        theta_output_array = netapi.get_thetas(nodespace, output)
        theta_lstm_gin_array = netapi.get_thetas(nodespace, lstm_gin)
        theta_lstm_gou_array = netapi.get_thetas(nodespace, lstm_gou)
        theta_lstm_gfg_array = netapi.get_thetas(nodespace, lstm_gfg)

        steps = T.iscalar("steps")

        # adadelta hyperparameters
        rho = T.scalar("rho")
        epsilon = T.scalar("epsilon")

        # activations -- post node/gatefunction, i.e. post-nonlinearities: y
        # tgt t(t)
        tgt = node.tgt = theano.shared(value=t_a_t_matrix.astype(T.config.floatX), name="tgt", borrow=False)
        # output k(t)
        y_k = node.y_k = theano.shared(value=t_a_o_matrix.astype(T.config.floatX), name="y_k", borrow=False)
        # input i(t)
        y_i = node.y_i = theano.shared(value=t_a_i_matrix.astype(T.config.floatX), name="y_i", borrow=False)
        # cell state c(t)
        y_c = node.y_c = theano.shared(value=t_a_h_por_matrix.astype(T.config.floatX), name="y_c", borrow=False)
        # cell internal state (cec) s(t)
        s = node.s = theano.shared(value=t_a_h_gen_matrix.astype(T.config.floatX), name="s", borrow=False)

        # for the LSTM gates, no node/gatefunction has been calculated, so we get net sums, not post-nonlinearity values
        # output gate out(t)
        net_out = node.net_out = theano.shared(value=t_a_h_gou_matrix.astype(T.config.floatX), name="net_out", borrow=False)
        # input gate in(t)
        net_in = node.net_in = theano.shared(value=t_a_h_gin_matrix.astype(T.config.floatX), name="net_in", borrow=False)
        # forget gate phi(t)
        net_phi = node.net_phi = theano.shared(value=t_a_h_gfg_matrix.astype(T.config.floatX), name="net_phi", borrow=False)

        # weight sets to be updated
        # cell (c) -> output (k)
        w_kc = node.w_kc = theano.shared(value=w_oh_por_array.astype(T.config.floatX), name="w_kc", borrow=False)
        # input (i) -> output (k)
        w_ki = node.w_ki = theano.shared(value=w_oi_array.astype(T.config.floatX), name="w_ki", borrow=False)
        # cell (c) -> output gate (out)
        w_outc = node.w_outc = theano.shared(value=w_h_gou_h_por_array.astype(T.config.floatX), name="w_outc", borrow=False)
        # input (i) -> output gate (out)
        w_outi = node.w_outi = theano.shared(value=w_h_gou_i_array.astype(T.config.floatX), name="w_outi", borrow=False)
        # input (i) -> cell (c)
        w_ci = node.w_ci = theano.shared(value=w_h_por_i_array.astype(T.config.floatX), name="w_ci", borrow=False)
        # input (i) -> cell (c)
        w_cc = node.w_cc = theano.shared(value=w_h_por_h_por_array.astype(T.config.floatX), name="w_cc", borrow=False)
        # input (i) -> input gate (in)
        w_ini = node.w_ini = theano.shared(value=w_h_gin_i_array.astype(T.config.floatX), name="w_ini", borrow=False)
        # cell (c) -> input gate (in)
        w_inc = node.w_inc = theano.shared(value=w_h_gin_h_por_array.astype(T.config.floatX), name="w_inc", borrow=False)
        # input (i) -> forget gate (phi)
        w_phii = node.w_phii = theano.shared(value=w_h_gfg_i_array.astype(T.config.floatX), name="w_phii", borrow=False)
        # cell (c) -> forget gate (phi)
        w_phic = node.w_phic = theano.shared(value=w_h_gfg_h_por_array.astype(T.config.floatX), name="w_phic", borrow=False)

        # bias sets to be updated
        theta_i = node.theta_i = theano.shared(value=theta_input_array.astype(T.config.floatX), name="theta_i", borrow=False)
        theta_k = node.theta_k = theano.shared(value=theta_output_array.astype(T.config.floatX), name="theta_k", borrow=False)
        theta_in = node.theta_in = theano.shared(value=theta_lstm_gin_array.astype(T.config.floatX), name="theta_in", borrow=False)
        theta_out = node.theta_out = theano.shared(value=theta_lstm_gou_array.astype(T.config.floatX), name="theta_out", borrow=False)
        theta_phi = node.theta_phi = theano.shared(value=theta_lstm_gfg_array.astype(T.config.floatX), name="theta_phi", borrow=False)

        # adadelta gradients and delta accumulation variables
        node.accu_grad_w_kc = theano.shared(value=np.zeros_like(w_oh_por_array), name="accu_grad_w_kc", borrow=True)
        node.accu_delta_w_kc = theano.shared(value=np.zeros_like(w_oh_por_array), name="accu_delta_w_kc", borrow=True)
        node.accu_grad_w_ki = theano.shared(value=np.zeros_like(w_oi_array), name="accu_grad_w_ki", borrow=True)
        node.accu_delta_w_ki = theano.shared(value=np.zeros_like(w_oi_array), name="accu_delta_w_ki", borrow=True)
        node.accu_grad_w_outc = theano.shared(value=np.zeros_like(w_h_gou_h_por_array), name="accu_grad_w_outc", borrow=True)
        node.accu_delta_w_outc = theano.shared(value=np.zeros_like(w_h_gou_h_por_array), name="accu_delta_w_outc", borrow=True)
        node.accu_grad_w_outi = theano.shared(value=np.zeros_like(w_h_gou_i_array), name="accu_grad_w_outi", borrow=True)
        node.accu_delta_w_outi = theano.shared(value=np.zeros_like(w_h_gou_i_array), name="accu_delta_w_outi", borrow=True)
        node.accu_grad_w_ci = theano.shared(value=np.zeros_like(w_h_por_i_array), name="accu_grad_w_ci", borrow=True)
        node.accu_delta_w_ci = theano.shared(value=np.zeros_like(w_h_por_i_array), name="accu_delta_w_ci", borrow=True)
        node.accu_grad_w_cc = theano.shared(value=np.zeros_like(w_h_por_h_por_array), name="accu_grad_w_cc", borrow=True)
        node.accu_delta_w_cc = theano.shared(value=np.zeros_like(w_h_por_h_por_array), name="accu_delta_w_cc", borrow=True)
        node.accu_grad_w_ini = theano.shared(value=np.zeros_like(w_h_gin_i_array), name="accu_grad_w_ini", borrow=True)
        node.accu_delta_w_ini = theano.shared(value=np.zeros_like(w_h_gin_i_array), name="accu_delta_w_ini", borrow=True)
        node.accu_grad_w_inc = theano.shared(value=np.zeros_like(w_h_gin_h_por_array), name="accu_grad_w_inc", borrow=True)
        node.accu_delta_w_inc = theano.shared(value=np.zeros_like(w_h_gin_h_por_array), name="accu_delta_w_inc", borrow=True)
        node.accu_grad_w_phii = theano.shared(value=np.zeros_like(w_h_gfg_i_array), name="accu_grad_w_phii", borrow=True)
        node.accu_delta_w_phii = theano.shared(value=np.zeros_like(w_h_gfg_i_array), name="accu_delta_w_phii", borrow=True)
        node.accu_grad_w_phic = theano.shared(value=np.zeros_like(w_h_gfg_h_por_array), name="accu_grad_w_phic", borrow=True)
        node.accu_delta_w_phic = theano.shared(value=np.zeros_like(w_h_gfg_h_por_array), name="accu_delta_w_phic", borrow=True)
        node.accu_grad_theta_k = theano.shared(value=np.zeros_like(theta_output_array), name="accu_grad_theta_k", borrow=True)
        node.accu_delta_theta_k = theano.shared(value=np.zeros_like(theta_output_array), name="accu_delta_theta_k", borrow=True)
        node.accu_grad_theta_out = theano.shared(value=np.zeros_like(theta_lstm_gou_array), name="accu_grad_theta_out", borrow=True)
        node.accu_delta_theta_out = theano.shared(value=np.zeros_like(theta_lstm_gou_array), name="accu_delta_theta_out", borrow=True)
        node.accu_grad_theta_in = theano.shared(value=np.zeros_like(theta_lstm_gin_array), name="accu_grad_theta_in", borrow=True)
        node.accu_delta_theta_in = theano.shared(value=np.zeros_like(theta_lstm_gin_array), name="accu_delta_theta_in", borrow=True)
        node.accu_grad_theta_phi = theano.shared(value=np.zeros_like(theta_lstm_gfg_array), name="accu_grad_theta_phi", borrow=True)
        node.accu_delta_theta_phi = theano.shared(value=np.zeros_like(theta_lstm_gfg_array), name="accu_delta_theta_phi", borrow=True)

        [errors,
         deriv_ci_prev,
         deriv_cc_prev,
         deriv_ini_prev,
         deriv_inc_prev,
         deriv_in1_prev,
         deriv_phii_prev,
         deriv_phic_prev,
         deriv_phi1_prev,
         grad_w_ki,
         grad_w_kc,
         grad_w_outi,
         grad_w_outc,
         grad_w_ci,
         grad_w_cc,
         grad_w_ini,
         grad_w_inc,
         grad_w_phii,
         grad_w_phic,
         grad_theta_i,
         grad_theta_k,
         grad_theta_in,
         grad_theta_out,
         grad_theta_phi], updates = theano.scan(
            fn=bpttstep,
            sequences=[dict(input=s, taps=[-0]),
                       dict(input=tgt, taps=[-0]),
                       dict(input=y_k, taps=[-0]),
                       dict(input=y_i, taps=[-0]),
                       dict(input=y_c, taps=[-0]),
                       dict(input=net_in, taps=[-0]),
                       dict(input=net_out, taps=[-0]),
                       dict(input=net_phi, taps=[-0])],
            outputs_info=[0.,                                               # error
                          T.zeros_like(w_ci, dtype=T.config.floatX),        # deriv_ci_prev
                          T.zeros_like(w_cc, dtype=T.config.floatX),        # deriv_cc_prev
                          T.zeros_like(w_ini, dtype=T.config.floatX),       # deriv_ini_prev
                          T.zeros_like(w_inc, dtype=T.config.floatX),       # deriv_inc_prev
                          T.zeros_like(theta_in, dtype=T.config.floatX),    # deriv_in1_prev
                          T.zeros_like(w_phii, dtype=T.config.floatX),      # deriv_phii_prev
                          T.zeros_like(w_phic, dtype=T.config.floatX),      # deriv_phic_prev
                          T.zeros_like(theta_phi, dtype=T.config.floatX),   # deriv_phi1_prev
                          T.zeros_like(w_ki, dtype=T.config.floatX),        # delta_w_ki
                          T.zeros_like(w_kc, dtype=T.config.floatX),        # delta_w_kc
                          T.zeros_like(w_outi, dtype=T.config.floatX),      # delta_w_outi
                          T.zeros_like(w_outc, dtype=T.config.floatX),      # delta_w_outc
                          T.zeros_like(w_ci, dtype=T.config.floatX),        # delta_w_ci
                          T.zeros_like(w_cc, dtype=T.config.floatX),        # delta_w_cc
                          T.zeros_like(w_ini, dtype=T.config.floatX),       # delta_w_ini
                          T.zeros_like(w_inc, dtype=T.config.floatX),       # delta_w_inc
                          T.zeros_like(w_phii, dtype=T.config.floatX),      # delta_w_phii
                          T.zeros_like(w_phic, dtype=T.config.floatX),      # delta_w_phic
                          T.zeros_like(theta_i, dtype=T.config.floatX),     # delta_theta_i
                          T.zeros_like(theta_k, dtype=T.config.floatX),     # delta_theta_k
                          T.zeros_like(theta_in, dtype=T.config.floatX),    # delta_theta_in
                          T.zeros_like(theta_out, dtype=T.config.floatX),   # delta_theta_out
                          T.zeros_like(theta_phi, dtype=T.config.floatX)],  # delta_theta_phi
            non_sequences=[w_kc,
                           w_ci,
                           w_cc,
                           w_outc,
                           w_outi,
                           w_ini,
                           w_inc,
                           w_phii,
                           w_phic],
            go_backwards=True,
            n_steps=steps,
            strict=True)

        # adadelta momentum
        accu_grad_w_kc = rho * node.accu_grad_w_kc + (1. - rho) * (grad_w_kc[SEQUENCE_LENGTH - 1]**2)
        delta_w_kc = (T.sqrt(node.accu_delta_w_kc + epsilon) / T.sqrt(accu_grad_w_kc + epsilon)) * grad_w_kc[SEQUENCE_LENGTH - 1]
        accu_delta_w_kc = rho * node.accu_delta_w_kc + (1. - rho) * (delta_w_kc**2)

        accu_grad_w_ki = rho * node.accu_grad_w_ki + (1. - rho) * (grad_w_ki[SEQUENCE_LENGTH - 1]**2)
        delta_w_ki = (T.sqrt(node.accu_delta_w_ki + epsilon) / T.sqrt(accu_grad_w_ki + epsilon)) * grad_w_ki[SEQUENCE_LENGTH - 1]
        accu_delta_w_ki = rho * node.accu_delta_w_ki + (1. - rho) * (delta_w_ki**2)

        accu_grad_w_outc = rho * node.accu_grad_w_outc + (1. - rho) * (grad_w_outc[SEQUENCE_LENGTH - 1]**2)
        delta_w_outc = (T.sqrt(node.accu_delta_w_outc + epsilon) / T.sqrt(accu_grad_w_outc + epsilon)) * grad_w_outc[SEQUENCE_LENGTH - 1]
        accu_delta_w_outc = rho * node.accu_delta_w_outc + (1. - rho) * (delta_w_outc**2)

        accu_grad_w_outi = rho * node.accu_grad_w_outi + (1. - rho) * (grad_w_outi[SEQUENCE_LENGTH - 1]**2)
        delta_w_outi = (T.sqrt(node.accu_delta_w_outi + epsilon) / T.sqrt(accu_grad_w_outi + epsilon)) * grad_w_outi[SEQUENCE_LENGTH - 1]
        accu_delta_w_outi = rho * node.accu_delta_w_outi + (1. - rho) * (delta_w_outi**2)

        accu_grad_w_ci = rho * node.accu_grad_w_ci + (1. - rho) * (grad_w_ci[SEQUENCE_LENGTH - 1]**2)
        delta_w_ci = (T.sqrt(node.accu_delta_w_ci + epsilon) / T.sqrt(accu_grad_w_ci + epsilon)) * grad_w_ci[SEQUENCE_LENGTH - 1]
        accu_delta_w_ci = rho * node.accu_delta_w_ci + (1. - rho) * (delta_w_ci**2)

        accu_grad_w_cc = rho * node.accu_grad_w_cc + (1. - rho) * (grad_w_cc[SEQUENCE_LENGTH - 1]**2)
        delta_w_cc = (T.sqrt(node.accu_delta_w_cc + epsilon) / T.sqrt(accu_grad_w_cc + epsilon)) * grad_w_cc[SEQUENCE_LENGTH - 1]
        accu_delta_w_cc = rho * node.accu_delta_w_cc + (1. - rho) * (delta_w_cc**2)

        accu_grad_w_ini = rho * node.accu_grad_w_ini + (1. - rho) * (grad_w_ini[SEQUENCE_LENGTH - 1]**2)
        delta_w_ini = (T.sqrt(node.accu_delta_w_ini + epsilon) / T.sqrt(accu_grad_w_ini + epsilon)) * grad_w_ini[SEQUENCE_LENGTH - 1]
        accu_delta_w_ini = rho * node.accu_delta_w_ini + (1. - rho) * (delta_w_ini**2)

        accu_grad_w_inc = rho * node.accu_grad_w_inc + (1. - rho) * (grad_w_inc[SEQUENCE_LENGTH - 1]**2)
        delta_w_inc = (T.sqrt(node.accu_delta_w_inc + epsilon) / T.sqrt(accu_grad_w_inc + epsilon)) * grad_w_inc[SEQUENCE_LENGTH - 1]
        accu_delta_w_inc = rho * node.accu_delta_w_inc + (1. - rho) * (delta_w_inc**2)

        accu_grad_w_phii = rho * node.accu_grad_w_phii + (1. - rho) * (grad_w_phii[SEQUENCE_LENGTH - 1]**2)
        delta_w_phii = (T.sqrt(node.accu_delta_w_phii + epsilon) / T.sqrt(accu_grad_w_phii + epsilon)) * grad_w_phii[SEQUENCE_LENGTH - 1]
        accu_delta_w_phii = rho * node.accu_delta_w_phii + (1. - rho) * (delta_w_phii**2)

        accu_grad_w_phic = rho * node.accu_grad_w_phic + (1. - rho) * (grad_w_phic[SEQUENCE_LENGTH - 1]**2)
        delta_w_phic = (T.sqrt(node.accu_delta_w_phic + epsilon) / T.sqrt(accu_grad_w_phic + epsilon)) * grad_w_phic[SEQUENCE_LENGTH - 1]
        accu_delta_w_phic = rho * node.accu_delta_w_phic + (1. - rho) * (delta_w_phic**2)

        accu_grad_theta_k = rho * node.accu_grad_theta_k + (1. - rho) * (grad_theta_k[SEQUENCE_LENGTH - 1]**2)
        delta_theta_k = (T.sqrt(node.accu_delta_theta_k + epsilon) / T.sqrt(accu_grad_theta_k + epsilon)) * grad_theta_k[SEQUENCE_LENGTH - 1]
        accu_delta_theta_k = rho * node.accu_delta_theta_k + (1. - rho) * (delta_theta_k**2)

        accu_grad_theta_out = rho * node.accu_grad_theta_out + (1. - rho) * (grad_theta_out[SEQUENCE_LENGTH - 1]**2)
        delta_theta_out = (T.sqrt(node.accu_delta_theta_out + epsilon) / T.sqrt(accu_grad_theta_out + epsilon)) * grad_theta_out[SEQUENCE_LENGTH - 1]
        accu_delta_theta_out = rho * node.accu_delta_theta_out + (1. - rho) * (delta_theta_out**2)

        accu_grad_theta_in = rho * node.accu_grad_theta_in + (1. - rho) * (grad_theta_in[SEQUENCE_LENGTH - 1]**2)
        delta_theta_in = (T.sqrt(node.accu_delta_theta_in + epsilon) / T.sqrt(accu_grad_theta_in + epsilon)) * grad_theta_in[SEQUENCE_LENGTH - 1]
        accu_delta_theta_in = rho * node.accu_delta_theta_in + (1. - rho) * (delta_theta_in**2)

        accu_grad_theta_phi = rho * node.accu_grad_theta_phi + (1. - rho) * (grad_theta_phi[SEQUENCE_LENGTH - 1]**2)
        delta_theta_phi = (T.sqrt(node.accu_delta_theta_phi + epsilon) / T.sqrt(accu_grad_theta_phi + epsilon)) * grad_theta_phi[SEQUENCE_LENGTH - 1]
        accu_delta_theta_phi = rho * node.accu_delta_theta_phi + (1. - rho) * (delta_theta_phi**2)

        # update weights
        w_kc += delta_w_kc
        w_ki += delta_w_ki
        w_outc += delta_w_outc
        w_outi += delta_w_outi
        w_ci += delta_w_ci
        w_cc += delta_w_cc
        w_ini += delta_w_ini
        w_inc += delta_w_inc
        w_phii += delta_w_phii
        w_phic += delta_w_phic

        # update biases
        # theta_i += delta_theta_i
        theta_k += delta_theta_k
        theta_out += delta_theta_out
        theta_in += delta_theta_in
        theta_phi += delta_theta_phi

        # this will provide new w values to be written back to the node net,
        # as well as deriv_lm_prev values to be used in the next step
        node.get_updated_parameters = theano.function([rho, epsilon, steps],
                                                      errors,
                                                      updates=[(node.w_kc, w_kc),
                                                               (node.w_ki, w_ki),
                                                               (node.w_outc, w_outc),
                                                               (node.w_outi, w_outi),
                                                               (node.w_ci, w_ci),
                                                               (node.w_cc, w_cc),
                                                               (node.w_ini, w_ini),
                                                               (node.w_inc, w_inc),
                                                               (node.w_phii, w_phii),
                                                               (node.w_phic, w_phic),
                                                               (node.theta_i, theta_i),
                                                               (node.theta_k, theta_k),
                                                               (node.theta_in, theta_in),
                                                               (node.theta_out, theta_out),
                                                               (node.theta_phi, theta_phi),
                                                               (node.accu_grad_w_kc, accu_grad_w_kc),
                                                               (node.accu_delta_w_kc, accu_delta_w_kc),
                                                               (node.accu_grad_w_ki, accu_grad_w_ki),
                                                               (node.accu_delta_w_ki, accu_delta_w_ki),
                                                               (node.accu_grad_w_outc, accu_grad_w_outc),
                                                               (node.accu_delta_w_outc, accu_delta_w_outc),
                                                               (node.accu_grad_w_outi, accu_grad_w_outi),
                                                               (node.accu_delta_w_outi, accu_delta_w_outi),
                                                               (node.accu_grad_w_ci, accu_grad_w_ci),
                                                               (node.accu_delta_w_ci, accu_delta_w_ci),
                                                               (node.accu_grad_w_cc, accu_grad_w_cc),
                                                               (node.accu_delta_w_cc, accu_delta_w_cc),
                                                               (node.accu_grad_w_ini, accu_grad_w_ini),
                                                               (node.accu_delta_w_ini, accu_delta_w_ini),
                                                               (node.accu_grad_w_inc, accu_grad_w_inc),
                                                               (node.accu_delta_w_inc, accu_delta_w_inc),
                                                               (node.accu_grad_w_phii, accu_grad_w_phii),
                                                               (node.accu_delta_w_phii, accu_delta_w_phii),
                                                               (node.accu_grad_w_phic, accu_grad_w_phic),
                                                               (node.accu_delta_w_phic, accu_delta_w_phic),
                                                               (node.accu_grad_theta_k, accu_grad_theta_k),
                                                               (node.accu_delta_theta_k, accu_delta_theta_k),
                                                               (node.accu_grad_theta_out, accu_grad_theta_out),
                                                               (node.accu_delta_theta_out, accu_delta_theta_out),
                                                               (node.accu_grad_theta_in, accu_grad_theta_in),
                                                               (node.accu_delta_theta_in, accu_delta_theta_in),
                                                               (node.accu_grad_theta_phi, accu_grad_theta_phi),
                                                               (node.accu_delta_theta_phi, accu_delta_theta_phi)
                                                               ],
                                                      on_unused_input='warn')

        node.get_error = theano.function([], T.sum(T.square(tgt[SEQUENCE_LENGTH] - y_k[SEQUENCE_LENGTH])) / 2.)

        node.initialized = True

    # every step

    error_prev = node.get_state("current_error")
    if error_prev is None:
        error_prev = 0.
    node.get_gate('e').gate_function(error_prev)

    if netapi.step % 3 == 0 and node.get_slot("debug").activation > 0.5:
        netapi.logger.debug("%10i: lstm sample step" % netapi.step)

    if netapi.step % 3 != 1:
        return
    # every three steps, sample activation from LSTMs

    node.t += 1
    if node.t >= SEQUENCE_LENGTH:
        node.t = 0

    # roll time snapshots to the left
    node.t_a_i_matrix = np.roll(node.t_a_i_matrix, -1, 0)
    node.t_a_t_matrix = np.roll(node.t_a_t_matrix, -1, 0)
    node.t_a_o_matrix = np.roll(node.t_a_o_matrix, -1, 0)
    node.t_a_h_gen_matrix = np.roll(node.t_a_h_gen_matrix, -1, 0)
    node.t_a_h_por_matrix = np.roll(node.t_a_h_por_matrix, -1, 0)
    node.t_a_h_gin_matrix = np.roll(node.t_a_h_gin_matrix, -1, 0)
    node.t_a_h_gou_matrix = np.roll(node.t_a_h_gou_matrix, -1, 0)
    node.t_a_h_gfg_matrix = np.roll(node.t_a_h_gfg_matrix, -1, 0)

    # insert new snapshot at the end
    node.t_a_i_matrix[SEQUENCE_LENGTH - 1, :] = netapi.get_activations(nodespace, input)
    node.t_a_t_matrix[SEQUENCE_LENGTH - 1, :] = netapi.get_activations(nodespace, target)
    node.t_a_o_matrix[SEQUENCE_LENGTH - 1, :] = netapi.get_activations(nodespace, output)
    node.t_a_h_gen_matrix[SEQUENCE_LENGTH - 1, :] = netapi.get_activations(nodespace, lstm_gen)
    node.t_a_h_por_matrix[SEQUENCE_LENGTH - 1, :] = netapi.get_activations(nodespace, lstm_por)
    node.t_a_h_gin_matrix[SEQUENCE_LENGTH - 1, :] = netapi.get_activations(nodespace, lstm_gou)
    node.t_a_h_gou_matrix[SEQUENCE_LENGTH - 1, :] = netapi.get_activations(nodespace, lstm_gin)
    node.t_a_h_gfg_matrix[SEQUENCE_LENGTH - 1, :] = netapi.get_activations(nodespace, lstm_gfg)
    node.samples += 1

    if node.get_slot("debug").activation > 0.5:
        netapi.logger.debug("%10i: bp sample #%i t, i, c, k data: t[0]=%.6f i[0]=%.6f c[0]=%.6f k[0]=%.6f"
                            % (netapi.step, node.t, node.t_a_t_matrix[node.t, 0], node.t_a_i_matrix[node.t, 0],
                                node.t_a_h_por_matrix[node.t, 0], node.t_a_o_matrix[node.t, 0]))

    if node.t != SEQUENCE_LENGTH - 1 or node.samples < 3:
        return
    # every sequence length samples, do backpropagation-through-time for the sampled sequence

    # netapi.logger.debug("t=%.6f o=%.6f s=%.6f c=%.6f i=%.6f" % (node.t_a_t_matrix[0, 0], node.t_a_o_matrix[0, 0],
    #                     node.t_a_h_gen_matrix[0, 0], node.t_a_h_por_matrix[0, 0], node.t_a_i_matrix[0, 0]))
    # netapi.logger.debug("t=%.6f o=%.6f s=%.6f c=%.6f i=%.6f" % (node.t_a_t_matrix[1, 0], node.t_a_o_matrix[1, 0],
    #                     node.t_a_h_gen_matrix[1, 0], node.t_a_h_por_matrix[1, 0], node.t_a_i_matrix[1, 0]))
    # netapi.logger.debug("t=%.6f o=%.6f s=%.6f c=%.6f i=%.6f" % (node.t_a_t_matrix[2, 0], node.t_a_o_matrix[2, 0],
    #                     node.t_a_h_gen_matrix[2, 0], node.t_a_h_por_matrix[2, 0], node.t_a_i_matrix[2, 0]))

    # fill w and a variables with values from the Node Net
    node.w_kc.set_value(netapi.get_link_weights(nodespace, lstm_por, nodespace, output), borrow=True)
    node.w_ki.set_value(netapi.get_link_weights(nodespace, input, nodespace, output), borrow=True)
    node.w_outc.set_value(netapi.get_link_weights(nodespace, lstm_por, nodespace, lstm_gou), borrow=True)
    node.w_outi.set_value(netapi.get_link_weights(nodespace, input, nodespace, lstm_gou), borrow=True)
    node.w_ci.set_value(netapi.get_link_weights(nodespace, input, nodespace, lstm_por), borrow=True)
    node.w_cc.set_value(netapi.get_link_weights(nodespace, lstm_por, nodespace, lstm_por), borrow=True)
    node.w_ini.set_value(netapi.get_link_weights(nodespace, input, nodespace, lstm_gin), borrow=True)
    node.w_inc.set_value(netapi.get_link_weights(nodespace, lstm_por, nodespace, lstm_gin), borrow=True)
    node.w_phii.set_value(netapi.get_link_weights(nodespace, input, nodespace, lstm_gfg), borrow=True)
    node.w_phic.set_value(netapi.get_link_weights(nodespace, lstm_por, nodespace, lstm_gfg), borrow=True)

    node.theta_i.set_value(netapi.get_thetas(nodespace, input), borrow=True)
    node.theta_k.set_value(netapi.get_thetas(nodespace, output), borrow=True)
    node.theta_in.set_value(netapi.get_thetas(nodespace, lstm_gin), borrow=True)
    node.theta_out.set_value(netapi.get_thetas(nodespace, lstm_gou), borrow=True)
    node.theta_phi.set_value(netapi.get_thetas(nodespace, lstm_gfg), borrow=True)

    node.tgt.set_value(node.t_a_t_matrix, borrow=True)
    node.y_k.set_value(node.t_a_o_matrix, borrow=True)
    node.y_i.set_value(node.t_a_i_matrix, borrow=True)
    node.y_c.set_value(node.t_a_h_por_matrix, borrow=True)
    node.s.set_value(node.t_a_h_gen_matrix, borrow=True)
    node.net_out.set_value(node.t_a_h_gou_matrix, borrow=True)
    node.net_in.set_value(node.t_a_h_gin_matrix, borrow=True)
    node.net_phi.set_value(node.t_a_h_gfg_matrix, borrow=True)

    rho = float(node.get_parameter('adadelta_rho'))
    if not isinstance(rho, Number):
        rho = 0.95
        node.set_parameter('adadelta_rho', rho)

    epsilon = float(node.get_parameter('adadelta_epsilon'))
    if not isinstance(epsilon, Number):
        epsilon = 0.000001
        node.set_parameter('adadelta_epsilon', epsilon)

    len_output = len(netapi.get_activations(nodespace, output))
    len_input = len(netapi.get_activations(nodespace, input))
    len_hidden = len(netapi.get_activations(nodespace, lstm_por))

    # update the weights, all derivatives and weight update sums are 0 for the first step
    errors = node.get_updated_parameters(rho, epsilon, node.t + 1)

    if node.get_slot("debug").activation > 0.5:
        netapi.logger.debug("%10i: bp with error %.4f" % (netapi.step, errors[SEQUENCE_LENGTH - 1]))

    # write back changed weights to node net

    # netapi.set_thetas(nodespace, input, node.theta_i.get_value(borrow=True))
    if node.get_parameter("bias_gin") == "true":
        netapi.set_thetas(nodespace, lstm_gin, node.theta_in.get_value(borrow=True))
    if node.get_parameter("bias_gou") == "true":
        netapi.set_thetas(nodespace, lstm_gou, node.theta_out.get_value(borrow=True))
    if node.get_parameter("bias_gfg") == "true":
        netapi.set_thetas(nodespace, lstm_gfg, node.theta_phi.get_value(borrow=True))

    netapi.set_link_weights(nodespace, input, nodespace, lstm_gou, node.w_outi.get_value(borrow=True))
    netapi.set_link_weights(nodespace, input, nodespace, lstm_por, node.w_ci.get_value(borrow=True))
    netapi.set_link_weights(nodespace, input, nodespace, lstm_gin, node.w_ini.get_value(borrow=True))
    netapi.set_link_weights(nodespace, input, nodespace, lstm_gfg, node.w_phii.get_value(borrow=True))
    netapi.set_link_weights(nodespace, lstm_por, nodespace, output, node.w_kc.get_value(borrow=True))

    if node.get_parameter("links_io") == "true":
        netapi.set_link_weights(nodespace, input, nodespace, output, node.w_ki.get_value(borrow=True))
    if node.get_parameter("links_porpor") == "true":
        netapi.set_link_weights(nodespace, lstm_por, nodespace, lstm_por, node.w_cc.get_value(borrow=True))
    if node.get_parameter("links_porgin") == "true":
        netapi.set_link_weights(nodespace, lstm_por, nodespace, lstm_gin, node.w_inc.get_value(borrow=True))
    if node.get_parameter("links_porgou") == "true":
        netapi.set_link_weights(nodespace, lstm_por, nodespace, lstm_gou, node.w_outc.get_value(borrow=True))
    if node.get_parameter("links_porgfg") == "true":
        netapi.set_link_weights(nodespace, lstm_por, nodespace, lstm_gfg, node.w_phic.get_value(borrow=True))

    node.set_state('current_error', errors[SEQUENCE_LENGTH - 1])
    node.set_state('error', node.get_state('error') + errors[SEQUENCE_LENGTH - 1])
    if node.get_state('updates') % 100 == 0:
        netapi.logger.debug("Number of lstm backprop steps computed %d" % node.get_state('updates'))
        netapi.logger.debug("Error %.6f (Latest from loop: 0=%.6f)" % ((node.get_state('error') / 100), errors[SEQUENCE_LENGTH - 1]))
        node.set_state('error', 0.0)

    # after weight updates, reset gen loops of lstms
    netapi.substitute_activations(nodespace, lstm_gen, np.zeros_like(netapi.get_activations(nodespace, lstm_gen)))
    # netapi.substitute_activations(nodespace, "lstm_por", np.zeros_like(a_h_por_array))

    node.set_state('updates', node.get_state('updates') + 1)


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
