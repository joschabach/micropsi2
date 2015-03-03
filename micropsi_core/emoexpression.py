__author__ = 'rvuine'


def calc_emoexpression_parameters(nodenet):

    emoexpression = dict()

    exp_pain = 0
    exp_activation = 0
    exp_surprise = 0
    exp_anger = 0
    exp_sadness = 0
    exp_joy = 0
    exp_fear = 0
    exp_helplessness = 0

    emoexpression["exp_pain"] = exp_pain
    emoexpression["exp_activation"] = exp_activation
    emoexpression["exp_surprise"] = exp_surprise
    emoexpression["exp_anger"] = exp_anger
    emoexpression["exp_sadness"] = exp_sadness
    emoexpression["exp_joy"] = exp_joy
    emoexpression["exp_fear"] = exp_fear
    emoexpression["exp_helplessness"] = exp_helplessness

    return emoexpression