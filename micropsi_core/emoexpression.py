__author__ = 'rvuine'

import math


def gentle_sigmoid(x):
    return 2 * ((1 / (1 + math.exp(-0.5 * x))) - 0.5)


def calc_emoexpression_parameters(nodenet):

    emoexpression = dict()

    emo_selection_threshold	= nodenet.get_modulator("emo_selection_threshold")
    emo_securing_rate = nodenet.get_modulator("emo_securing_rate")
    emo_resolution = nodenet.get_modulator("emo_resolution")
    emo_pleasure = nodenet.get_modulator("emo_pleasure")
    emo_joy = nodenet.get_modulator("emo_sustaining_joy")
    emo_competence = nodenet.get_modulator("emo_competence")
    emo_activation = nodenet.get_modulator("emo_activation")
    base_unexpectedness = nodenet.get_modulator("base_unexpectedness")

    integrity = 1
    if nodenet.world is not None and "health" in nodenet.worldadapter_instance.get_available_datasources():
        if nodenet.worldadapter_instance.get_datasource_value("health"):
            integrity = nodenet.worldadapter_instance.get_datasource_value("health")

    exp_pain = 1 - integrity
    exp_activation = emo_activation
    exp_surprise = base_unexpectedness
    exp_anger = (1 - emo_competence) * emo_activation
    exp_sadness = (1 - emo_competence) * (1 - emo_activation)
    exp_joy = emo_joy + 0.3     # baseline
    exp_fear = 0                # todo: get fear from emo once we know how to calculate it
    exp_helplessness = 0        # todo: probably introduce base_ parameter to be set by motivation

    emoexpression["exp_pain"] = exp_pain
    emoexpression["exp_activation"] = exp_activation
    emoexpression["exp_surprise"] = exp_surprise
    emoexpression["exp_anger"] = exp_anger
    emoexpression["exp_sadness"] = exp_sadness
    emoexpression["exp_joy"] = exp_joy
    emoexpression["exp_fear"] = exp_fear
    emoexpression["exp_helplessness"] = exp_helplessness

    return emoexpression