__author__ = 'rvuine'

import micropsi_core.tools
import math
from abc import ABCMeta, abstractmethod


class StepOperator(metaclass=ABCMeta):
    """
    A step operator will be executed once per net step on all nodes.
    """

    @property
    @abstractmethod
    def priority(self):
        """
        Returns a numerical priority value used to determine step operator order execution.
        Lower priority operators will be executed first.
        The lowest possible value 0 and 1 are reserved for the Propagate and Calculate operators to ensure all step
        operators will be executed after propagation and node function calculation.
        """
        pass  # pragma: no cover

    @abstractmethod
    def execute(self, nodenet, nodes, netapi):
        """
        Actually execute the operator.
        """
        pass  # pragma: no cover


class Propagate(StepOperator):
    """
    Every node net needs a propagate operator
    """
    @property
    def priority(self):
        return 0

    @abstractmethod
    def execute(self, nodenet, nodes, netapi):
        pass  # pragma: no cover


class Calculate(StepOperator):
    """
    Every node net needs a calculate operator
    """
    @property
    def priority(self):
        return 1

    def execute(self, nodenet, nodes, netapi):
        pass  # pragma: no cover


def gentle_sigmoid(x):
    return 2 * ((1 / (1 + math.exp(-0.5 * x))) - 0.5)


class DoernerianEmotionalModulators(StepOperator):
    """
    Implementation a doernerian emotional model based on global node net modulators.

    The following base values can and should be set from the node net:

    base_sum_importance_of_intentions           - Sum of importance of all current intentions
    base_sum_urgency_of_intentions              - Sum of urgency of all current intentions
    base_competence_for_intention               - Competence for currently selected intention
    base_importance_of_intention                - Importance of currently selected intention
    base_urgency_of_intention                   - Importance of currently selected intention
    base_number_of_active_motives               - Number of currently active motives
    base_number_of_expected_events              - Number of expected events in last cycle
    base_number_of_unexpected_events            - Number of unexpected events in last cycle
    base_urge_change                            - Sum of changes to urges in last cycle
    base_age_influence_on_competence            - Influence factor of node net age on competence (0: no influence)

    The following emotional parameters will be calculated:

    emo_pleasure                                - Pleasure (LUL in Dörner)
    emo_activation                              - General activation (ARAS in Dörner)
    emo_securing_rate                           - Tendency to check/re-check the environment
    emo_resolution                              - Thoroughness of perception
    emo_selection_threshold                     - Tendency to change selected motive
    emo_competence                              - Assumed predictability of events

    This code is experimental, various magic numbers / parameters will probably have to be
    introduced to make it work.

    """

    @property
    def priority(self):
        return 1000

    def execute(self, nodenet, nodes, netapi):

        COMPETENCE_DECAY_FACTOR = 0.1
        JOY_DECAY_FACTOR = 0.01

        base_sum_importance_of_intentions = netapi.get_modulator("base_sum_importance_of_intentions")
        base_sum_urgency_of_intentions = netapi.get_modulator("base_sum_urgency_of_intentions")
        base_competence_for_intention = netapi.get_modulator("base_competence_for_intention")
        base_importance_of_intention = netapi.get_modulator("base_importance_of_intention")
        base_urgency_of_intention = netapi.get_modulator("base_urgency_of_intention")

        base_number_of_active_motives = netapi.get_modulator("base_number_of_active_motives")
        base_number_of_unexpected_events = netapi.get_modulator("base_number_of_unexpected_events")
        base_number_of_expected_events = netapi.get_modulator("base_number_of_expected_events")
        base_urge_change = netapi.get_modulator("base_urge_change")
        base_age = netapi.get_modulator("base_age")
        base_age_influence_on_competence = netapi.get_modulator("base_age_influence_on_competence")
        base_unexpectedness_prev = netapi.get_modulator("base_unexpectedness")

        emo_competence_prev = netapi.get_modulator("emo_competence")
        emo_sustaining_joy_prev = netapi.get_modulator("emo_sustaining_joy")

        base_age += 1

        emo_activation = ((base_sum_importance_of_intentions + base_sum_urgency_of_intentions) /
                          ((base_number_of_active_motives * 2) + 1))

        base_unexpectedness = max(min(base_unexpectedness_prev + gentle_sigmoid((base_number_of_unexpected_events - base_number_of_expected_events) / 10), 1), 0)
        fear = 0                    # todo: understand the formula in Principles 185

        emo_securing_rate = (((1 - base_competence_for_intention) -
                              (0.5 * base_urgency_of_intention * base_importance_of_intention)) +
                               fear +
                               base_unexpectedness)

        emo_resolution = 1 - emo_activation

        emo_selection_threshold = emo_activation

        pleasure_from_expectation = gentle_sigmoid((base_number_of_expected_events - base_number_of_unexpected_events) / 10)
        pleasure_from_satisfaction = gentle_sigmoid(base_urge_change * 3)

        emo_pleasure = pleasure_from_expectation + pleasure_from_satisfaction        # ignoring fear and hope for now

        if emo_pleasure != 0:
            if math.copysign(1, emo_pleasure) == math.copysign(1, emo_sustaining_joy_prev):
                if abs(emo_pleasure) >= abs(emo_sustaining_joy_prev):
                    emo_sustaining_joy = emo_pleasure
                else:
                    emo_sustaining_joy = emo_sustaining_joy_prev
            else:
                emo_sustaining_joy = emo_pleasure
        else:
            if abs(emo_sustaining_joy_prev) < JOY_DECAY_FACTOR:
                emo_sustaining_joy = 0
            else:
                emo_sustaining_joy = emo_sustaining_joy_prev - math.copysign(JOY_DECAY_FACTOR, emo_sustaining_joy_prev)

        pleasurefactor = 1 if emo_pleasure >= 0 else -1
        divisorbaseline = 1 if emo_pleasure >= 0 else 2
        youthful_exuberance_term = 1 #base_age_influence_on_competence * (1 + (1 / math.sqrt(2 * base_age)))
        emo_competence = (((emo_competence_prev) + (emo_pleasure * youthful_exuberance_term)) /
                          (divisorbaseline + (pleasurefactor * emo_competence_prev*COMPETENCE_DECAY_FACTOR)))
        emo_competence = max(min(emo_competence, 0.99), 0.01)

        # setting technical parameters
        nodenet.set_modulator("base_age", base_age)
        nodenet.set_modulator("base_unexpectedness", base_unexpectedness)

        # resetting per-cycle base parameters
        nodenet.set_modulator("base_number_of_expected_events", 0)
        nodenet.set_modulator("base_number_of_unexpected_events", 0)
        nodenet.set_modulator("base_urge_change", 0)
        nodenet.set_modulator("base_porret_decay_factor", 1)

        # setting emotional parameters
        nodenet.set_modulator("emo_pleasure", emo_pleasure)
        nodenet.set_modulator("emo_activation", emo_activation)
        nodenet.set_modulator("emo_securing_rate", emo_securing_rate)
        nodenet.set_modulator("emo_resolution", emo_resolution)
        nodenet.set_modulator("emo_selection_threshold", emo_selection_threshold)
        nodenet.set_modulator("emo_competence", emo_competence)
        nodenet.set_modulator("emo_sustaining_joy", emo_sustaining_joy)
