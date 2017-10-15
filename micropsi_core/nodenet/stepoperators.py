__author__ = 'rvuine'

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

    writeable_modulators = [
        'base_sum_importance_of_intentions',
        'base_sum_urgency_of_intentions',
        'base_competence_for_intention',
        'base_importance_of_intention',
        'base_urgency_of_intention',
        'base_number_of_active_motives',
        'base_number_of_expected_events',
        'base_number_of_unexpected_events',
        'base_urge_change',
        'base_age_influence_on_competence',
        'base_porret_decay_factor']
    readable_modulators = [
        'emo_pleasure',
        'emo_activation',
        'emo_securing_rate',
        'emo_resolution',
        'emo_selection_threshold',
        'emo_competence']

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
        base_sum_of_urges = netapi.get_modulator("base_sum_of_urges")

        emo_competence_prev = netapi.get_modulator("emo_competence")
        emo_sustaining_joy_prev = netapi.get_modulator("emo_sustaining_joy")

        base_age += 1

        emo_activation = max(0, ((base_sum_importance_of_intentions + base_sum_urgency_of_intentions) /
                          ((base_number_of_active_motives * 2) + 1)) + base_urge_change)

        base_unexpectedness = max(min(base_unexpectedness_prev + gentle_sigmoid((base_number_of_unexpected_events - base_number_of_expected_events) / 10), 1), 0)
        fear = 0                    # todo: understand the formula in Principles 185

        emo_securing_rate = (((1 - base_competence_for_intention) -
                              (0.5 * base_urgency_of_intention * base_importance_of_intention)) +
                               fear +
                               base_unexpectedness)

        emo_resolution = 1 - emo_activation

        emo_selection_threshold = emo_activation

        pleasure_from_expectation = gentle_sigmoid((base_number_of_expected_events - base_number_of_unexpected_events) / 10)
        pleasure_from_satisfaction = gentle_sigmoid(base_urge_change * -3)

        emo_pleasure = pleasure_from_expectation + pleasure_from_satisfaction        # ignoring fear and hope for now

        emo_valence = 0.5 - base_urge_change - base_sum_of_urges  # base_urge_change is inverse

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
        youthful_exuberance_term = 1  # base_age_influence_on_competence * (1 + (1 / math.sqrt(2 * base_age)))
        emo_competence = (((emo_competence_prev) + (emo_pleasure * youthful_exuberance_term)) /
                          (divisorbaseline + (pleasurefactor * emo_competence_prev * COMPETENCE_DECAY_FACTOR)))
        emo_competence = max(min(emo_competence, 0.99), 0.01)

        # setting technical parameters
        nodenet.set_modulator("base_age", base_age)
        nodenet.set_modulator("base_unexpectedness", base_unexpectedness)

        # resetting per-cycle base parameters
        nodenet.set_modulator("base_number_of_expected_events", 0)
        nodenet.set_modulator("base_number_of_unexpected_events", 0)
        nodenet.set_modulator("base_urge_change", 0)
        # nodenet.set_modulator("base_porret_decay_factor", 1)

        # setting emotional parameters
        nodenet.set_modulator("emo_pleasure", emo_pleasure)
        nodenet.set_modulator("emo_activation", emo_activation)
        nodenet.set_modulator("emo_securing_rate", emo_securing_rate)
        nodenet.set_modulator("emo_resolution", emo_resolution)
        nodenet.set_modulator("emo_selection_threshold", emo_selection_threshold)
        nodenet.set_modulator("emo_competence", emo_competence)
        nodenet.set_modulator("emo_sustaining_joy", emo_sustaining_joy)
        nodenet.set_modulator("emo_valence", emo_valence)


class CalculateFlowmodules(Propagate):

    @property
    def priority(self):
        return 0

    def __init__(self, nodenet):
        self.nodenet = nodenet

    def value_guard(self, value, source, name):
        if value is None:
            return None
        if self.nodenet.runner_config.get('runner_infguard'):
            if type(value) == list:
                for val in value:
                    self._guard(val, source, name)
            else:
                self._guard(value, source, name)
        return value

    def _guard(self, value, source, name):
        import numpy as np
        if np.isnan(np.sum(value)):
            raise ValueError("NAN value in flow datected: %s" % self.format_error(source, name))
        elif np.isinf(np.sum(value)):
            raise ValueError("INF value in flow datected: %s" % self.format_error(source, name))

    def format_error(self, source, name):
        if type(source) == dict:
            if len(source['members']) == 1:
                msg = "output %s of %s" % (name, source['members'][0])
            else:
                msg = "output %s of graph %s" % (name, str(source['members']))
        else:
            msg = "output %s of %s" % (name, str(source))
        return msg

    def execute(self, nodenet, nodes, netapi):
        if not nodenet.flow_module_instances:
            return
        for uid, item in nodenet.flow_module_instances.items():
            item.is_part_of_active_graph = False
            item.take_slot_activation_snapshot()
        flowio = {}
        if nodenet.worldadapter_instance:
            if 'datasources' in nodenet.worldadapter_flow_nodes:
                sourcenode = nodenet.get_node(nodenet.worldadapter_flow_nodes['datasources'])
                sourcenode.is_part_of_active_graph = True
                flowio[sourcenode.uid] = {}
                for key in sourcenode.outputs:
                    flowio[sourcenode.uid][key] = self.value_guard(nodenet.worldadapter_instance.get_flow_datasource(key), nodenet.worldadapter, key)

                    for target_uid, target_name in sourcenode.outputmap[key]:
                        datatarget_uid = nodenet.worldadapter_flow_nodes.get('datatargets')
                        if target_uid == datatarget_uid:
                            nodenet.flow_module_instances[datatarget_uid].is_part_of_active_graph = True
                            nodenet.worldadapter_instance.add_to_flow_datatarget(target_name, flowio[sourcenode.uid][key])

        for func in nodenet.flowfunctions:
            if any([node.is_requested() for node in func['endnodes']]):
                skip = False
                inputs = {}
                for node_uid, in_name in func['inputs']:
                    if not nodenet.get_node(node_uid).inputmap[in_name]:
                        raise RuntimeError("Missing Flow-input %s of node %s" % (in_name, str(nodenet.get_node(node_uid))))
                    source_uid, source_name = nodenet.get_node(node_uid).inputmap[in_name]
                    if flowio[source_uid][source_name] is None:
                        # netapi.logger.debug("Skipping graph bc. empty inputs")
                        skip = True
                        break
                    else:
                        inputs["%s_%s" % (node_uid, in_name)] = flowio[source_uid][source_name]
                if skip:
                    for node_uid, out_name in func['outputs']:
                        if node_uid not in flowio:
                            flowio[node_uid] = {}
                        flowio[node_uid][out_name] = None
                    continue
                out = func['callable'](**inputs)
                for n in func['members']:
                    n.is_part_of_active_graph = True
                for index, (node_uid, out_name) in enumerate(func['outputs']):
                    if node_uid not in flowio:
                        flowio[node_uid] = {}
                    if 'datatargets' in nodenet.worldadapter_flow_nodes:
                        targetnode = nodenet.get_node(nodenet.worldadapter_flow_nodes['datatargets'])
                        for uid, name in nodenet.get_node(node_uid).outputmap[out_name]:
                            if uid == targetnode.uid and node_uid != nodenet.worldadapter_flow_nodes.get('datasources', False):
                                targetnode.is_part_of_active_graph = True
                                nodenet.worldadapter_instance.add_to_flow_datatarget(name, out[index])
                    flowio[node_uid][out_name] = self.value_guard(out[index], func, out_name) if out is not None else None
