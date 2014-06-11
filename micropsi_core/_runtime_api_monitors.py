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
    value in every simulation step."""
    nodenet = micropsi_core.runtime.nodenets[nodenet_uid]
    monitor = Monitor(nodenet, node_uid, 'gate', gate, node_name=nodenet.nodes[node_uid].name)
    nodenet.monitors[monitor.uid] = monitor
    return monitor.data


def add_slot_monitor(nodenet_uid, node_uid, slot):
    """Adds a continuous monitor to the activation of a slot. The monitor will collect the activation
    value in every simulation step."""
    nodenet = micropsi_core.runtime.nodenets[nodenet_uid]
    monitor = Monitor(nodenet, node_uid, nodenet.nodes[node_uid].name, 'slot', slot, node_name=nodenet.nodes[node_uid].name)
    nodenet.monitors[monitor.uid] = monitor
    return monitor.data


def remove_monitor(nodenet_uid, monitor_uid):
    """Deletes an activation monitor."""
    del micropsi_core.runtime.nodenets[nodenet_uid].state['monitors'][monitor_uid]
    del micropsi_core.runtime.nodenets[nodenet_uid].monitors[monitor_uid]
    return True


def clear_monitor(nodenet_uid, monitor_uid):
    """Leaves the monitor intact, but deletes the current list of stored values."""
    micropsi_core.runtime.nodenets[nodenet_uid].monitors(monitor_uid).clear()
    return True


def export_monitor_data(nodenet_uid, monitor_uid=None):
    """Returns a string with all currently stored monitor data for the given nodenet."""
    if monitor_uid is not None:
        return micropsi_core.runtime.nodenets[nodenet_uid].state['monitors'][monitor_uid]
    else:
        return micropsi_core.runtime.nodenets[nodenet_uid].state.get('monitors', {})


def get_monitor_data(nodenet_uid, step):
    """Returns a dictionary of monitor_uid: [node_name/node_uid, slot_type/gate_type, activation_value] for
    the current step, it the current step is newer than the supplied simulation step."""
    pass
