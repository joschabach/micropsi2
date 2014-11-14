# -*- coding: utf-8 -*-

"""
Runtime API functionality for creating and maintaining activation monitors
"""

__author__ = 'dominik'
__date__ = '11.12.12'

from micropsi_core.nodenet.monitor import Monitor

import micropsi_core


def add_gate_monitor(nodenet_uid, node_uid, gate):
    """Adds a continuous monitor to the activation of a gate. The monitor will collect the activation
    value in every simulation step.
    Returns the uid of the new monitor."""
    nodenet = micropsi_core.runtime.nodenets[nodenet_uid]
    monitor = Monitor(nodenet, node_uid, 'gate', gate, node_name=nodenet.nodes[node_uid].name)
    nodenet.monitors[monitor.uid] = monitor
    return monitor.uid


def add_slot_monitor(nodenet_uid, node_uid, slot):
    """Adds a continuous monitor to the activation of a slot. The monitor will collect the activation
    value in every simulation step.
    Returns the uid of the new monitor."""
    nodenet = micropsi_core.runtime.nodenets[nodenet_uid]
    monitor = Monitor(nodenet, node_uid, 'slot', slot, node_name=nodenet.nodes[node_uid].name)
    nodenet.monitors[monitor.uid] = monitor
    return monitor.uid


def remove_monitor(nodenet_uid, monitor_uid):
    """Deletes an activation monitor."""
    del micropsi_core.runtime.nodenets[nodenet_uid].state['monitors'][monitor_uid]
    del micropsi_core.runtime.nodenets[nodenet_uid].monitors[monitor_uid]
    return True


def clear_monitor(nodenet_uid, monitor_uid):
    """Leaves the monitor intact, but deletes the current list of stored values."""
    micropsi_core.runtime.nodenets[nodenet_uid].monitors[monitor_uid].clear()
    return True


def export_monitor_data(nodenet_uid, monitor_uid=None):
    """Returns a string with all currently stored monitor data for the given nodenet."""
    if monitor_uid is not None:
        return micropsi_core.runtime.nodenets[nodenet_uid].state['monitors'][monitor_uid]
    else:
        return micropsi_core.runtime.nodenets[nodenet_uid].state.get('monitors', {})


def get_monitor_data(nodenet_uid, step=0):
    """Returns monitor and nodenet data for drawing monitor plots for the current step,
    if the current step is newer than the supplied simulation step."""
    data = {
        'nodenet_running': micropsi_core.runtime.nodenets[nodenet_uid].is_active,
        'current_step': micropsi_core.runtime.nodenets[nodenet_uid].current_step
    }
    if step > data['current_step']:
        return data
    else:
        data['monitors'] = micropsi_core.runtime.export_monitor_data(nodenet_uid)
        return data
