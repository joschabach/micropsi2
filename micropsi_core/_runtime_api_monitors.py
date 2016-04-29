# -*- coding: utf-8 -*-

"""
Runtime API functionality for creating and maintaining activation monitors
"""

__author__ = 'dominik'
__date__ = '11.12.12'

import micropsi_core


def add_gate_monitor(nodenet_uid, node_uid, gate, sheaf=None, name=None, color=None):
    """Adds a continuous monitor to the activation of a gate. The monitor will collect the activation
    value in every calculation step.
    Returns the uid of the new monitor."""
    nodenet = micropsi_core.runtime.get_nodenet(nodenet_uid)
    return nodenet.add_gate_monitor(node_uid, gate, sheaf=sheaf, name=name, color=color)


def add_slot_monitor(nodenet_uid, node_uid, slot, sheaf=None, name=None, color=None):
    """Adds a continuous monitor to the activation of a slot. The monitor will collect the activation
    value in every calculation step.
    Returns the uid of the new monitor."""
    nodenet = micropsi_core.runtime.get_nodenet(nodenet_uid)
    return nodenet.add_slot_monitor(node_uid, slot, sheaf=sheaf, name=name, color=color)


def add_link_monitor(nodenet_uid, source_node_uid, gate_type, target_node_uid, slot_type, property, name, color=None):
    """Adds a continuous monitor to a link. You can choose to monitor either weight (default) or certainty
    The monitor will collect respective value in every calculation step.
    Returns the uid of the new monitor."""
    nodenet = micropsi_core.runtime.get_nodenet(nodenet_uid)
    return nodenet.add_link_monitor(source_node_uid, gate_type, target_node_uid, slot_type, property, name, color=color)


def add_modulator_monitor(nodenet_uid, modulator, name, color=None):
    """Adds a continuous monitor to a global modulator.
    The monitor will collect respective value in every calculation step.
    Returns the uid of the new monitor."""
    nodenet = micropsi_core.runtime.get_nodenet(nodenet_uid)
    return nodenet.add_modulator_monitor(modulator, name, color=color)


def add_custom_monitor(nodenet_uid, function, name, color=None):
    """Adds a continuous monitor, that evaluates the given python-code and collects the
    return-value for every calculation step.
    Returns the uid of the new monitor."""
    nodenet = micropsi_core.runtime.get_nodenet(nodenet_uid)
    return nodenet.add_custom_monitor(function, name, color=color)


def add_group_monitor(nodenet_uid, nodespace, name, node_name_prefix='', node_uids=[], gate='gen', color=None):
    """Adds a group monitor, that tracks the activations of the given group
    Returns the uid of the new monitor."""
    nodenet = micropsi_core.runtime.get_nodenet(nodenet_uid)
    return nodenet.add_group_monitor(nodespace, name, node_name_prefix=node_name_prefix, node_uids=node_uids, gate=gate, color=color)


def remove_monitor(nodenet_uid, monitor_uid):
    """Deletes an activation monitor."""
    micropsi_core.runtime.get_nodenet(nodenet_uid).remove_monitor(monitor_uid)
    return True


def clear_monitor(nodenet_uid, monitor_uid):
    """Leaves the monitor intact, but deletes the current list of stored values."""
    micropsi_core.runtime.get_nodenet(nodenet_uid).get_monitor(monitor_uid).clear()
    return True


def export_monitor_data(nodenet_uid, monitor_uid=None, monitor_from=0, monitor_count=-1):
    """Returns a string with all currently stored monitor data for the given nodenet."""
    nodenet = micropsi_core.runtime.get_nodenet(nodenet_uid)
    if monitor_from == 0 and monitor_count > 0:
        monitor_count = min(nodenet.current_step + 1, monitor_count)
        monitor_from = max(0, nodenet.current_step + 1 - monitor_count)
    if monitor_from > 0:
        if monitor_count < 1:
            monitor_count = (nodenet.current_step + 1 - monitor_from)
        elif monitor_from + monitor_count > nodenet.current_step:
            monitor_from = max(nodenet.current_step + 1 - monitor_count, 0)
    if monitor_uid is not None:
        data = nodenet.construct_monitors_dict()[monitor_uid]
        if monitor_from > 0 or monitor_count > 0:
            values = {}
            i = monitor_from
            while i < monitor_count + monitor_from:
                values[i] = data['values'].get(i)
                i += 1
            data['values'] = values
    else:
        data = nodenet.construct_monitors_dict()
        if monitor_from > 0 or monitor_count > 0:
            for uid in data:
                values = {}
                i = monitor_from
                while i < monitor_count + monitor_from:
                    values[i] = data[uid]['values'].get(i)
                    i += 1
                data[uid]['values'] = values
    return data


def get_monitor_data(nodenet_uid, step=0, monitor_from=0, monitor_count=-1):
    """Returns monitor and nodenet data for drawing monitor plots for the current step,
    if the current step is newer than the supplied calculation step."""
    nodenet = micropsi_core.runtime.get_nodenet(nodenet_uid)
    data = {
        'nodenet_running': nodenet.is_active,
        'current_step': nodenet.current_step
    }
    if step > data['current_step']:
        return data
    else:
        data['monitors'] = micropsi_core.runtime.export_monitor_data(nodenet_uid, None, monitor_from=monitor_from, monitor_count=monitor_count)
        return data


def add_activation_recorder(nodenet_uid, group_definition, name, interval=1):
    """ Adds an activation recorder to a group of nodes."""
    nodenet = micropsi_core.runtime.get_nodenet(nodenet_uid)
    rec = nodenet.add_activation_recorder(group_definition, name, interval)
    return True, rec.uid


def add_linkweight_recorder(nodenet_uid, from_group_definition, to_group_definition, name, interval=1):
    """ Adds a linkweight recorder to links between to groups."""
    nodenet = micropsi_core.runtime.get_nodenet(nodenet_uid)
    rec = nodenet.add_linkweight_recorder(from_group_definition, to_group_definition, name, interval)
    return True, rec.uid


def remove_recorder(nodenet_uid, recorder_uid):
    """Deletes a recorder."""
    micropsi_core.runtime.get_nodenet(nodenet_uid).remove_recorder(recorder_uid)
    return True


def clear_recorder(nodenet_uid, recorder_uid):
    """Leaves the recorder intact, but deletes the current list of stored values."""
    micropsi_core.runtime.get_nodenet(nodenet_uid).get_recorder(recorder_uid).clear()
    return True


def get_recorder_data(nodenet_uid):
    return True, micropsi_core.runtime.get_nodenet(nodenet_uid).construct_recorders_dict()
