# -*- coding: utf-8 -*-

"""
Runtime API functionality for creating and maintaining activation monitors
"""

__author__ = 'dominik'
__date__ = '11.12.12'

import micropsi_core


def add_gate_monitor(nodenet_uid, node_uid, gate, name=None, color=None):
    """Adds a continuous monitor to the activation of a gate. The monitor will collect the activation
    value in every calculation step.
    Returns the uid of the new monitor."""
    nodenet = micropsi_core.runtime.get_nodenet(nodenet_uid)
    return nodenet.add_gate_monitor(node_uid, gate, name=name, color=color)


def add_slot_monitor(nodenet_uid, node_uid, slot, name=None, color=None):
    """Adds a continuous monitor to the activation of a slot. The monitor will collect the activation
    value in every calculation step.
    Returns the uid of the new monitor."""
    nodenet = micropsi_core.runtime.get_nodenet(nodenet_uid)
    return nodenet.add_slot_monitor(node_uid, slot, name=name, color=color)


def add_link_monitor(nodenet_uid, source_node_uid, gate_type, target_node_uid, slot_type, name, color=None):
    """Adds a continuous weightmonitor to a link. The monitor will record the linkweight in every calculation step.
    Returns the uid of the new monitor."""
    nodenet = micropsi_core.runtime.get_nodenet(nodenet_uid)
    return nodenet.add_link_monitor(source_node_uid, gate_type, target_node_uid, slot_type, name, color=color)


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


def get_monitor_data(nodenet_uid, step=0, from_step=0, count=-1, with_recorders=False):
    """Returns monitor and nodenet data for drawing monitor plots for the current step,
    if the current step is newer than the supplied calculation step."""
    nodenet = micropsi_core.runtime.get_nodenet(nodenet_uid)
    if nodenet is None:
        return {}
    data = {
        'nodenet_running': nodenet.is_active,
        'current_step': nodenet.current_step
    }
    if step > data['current_step']:
        return data
    else:
        monitor_data = {}
        if from_step == 0 and count > 0:
            count = min(nodenet.current_step + 1, count)
            from_step = max(0, nodenet.current_step + 1 - count)
        if from_step > 0:
            if count < 1:
                count = (nodenet.current_step + 1 - from_step)
            elif from_step + count > nodenet.current_step:
                from_step = max(nodenet.current_step + 1 - count, 0)
        monitor_data = nodenet.construct_monitors_dict()
        monitor_data.update(nodenet.construct_adhoc_monitors_dict())
        if from_step > 0 or count > 0:
            for uid in monitor_data:
                values = {}
                i = from_step
                while i < count + from_step:
                    values[i] = monitor_data[uid]['values'].get(i)
                    i += 1
                monitor_data[uid]['values'] = values
        data['monitors'] = monitor_data
        if with_recorders:
            data['recorders'] = nodenet.construct_recorders_dict()
        return data


def add_gate_activation_recorder(nodenet_uid, group_definition, name, interval=1):
    """ Adds an activation recorder to a group of nodes."""
    nodenet = micropsi_core.runtime.get_nodenet(nodenet_uid)
    rec = nodenet.add_gate_activation_recorder(group_definition, name, interval)
    return True, rec.uid


def add_node_activation_recorder(nodenet_uid, group_definition, name, interval=1):
    """ Adds an activation recorder to a group of nodes."""
    nodenet = micropsi_core.runtime.get_nodenet(nodenet_uid)
    rec = nodenet.add_node_activation_recorder(group_definition, name, interval)
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


def get_recorder(nodenet_uid, recorder_uid):
    return micropsi_core.runtime.get_nodenet(nodenet_uid).get_recorder(recorder_uid)


def export_recorders(nodenet_uid, recorder_uids):
    """ Returns a bytestream containing an npz export for the given recorders"""
    import numpy as np
    from io import BytesIO
    nodenet = micropsi_core.runtime.get_nodenet(nodenet_uid)
    data = {}
    stream = BytesIO()
    for uid in recorder_uids:
        recorder = nodenet.get_recorder(uid)
        data.update(recorder.export_data())
    np.savez(stream, **data)
    return stream.getvalue()
