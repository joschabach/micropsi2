# -*- coding: utf-8 -*-

"""
Runtime API functionality for creating and maintaining activation monitors
"""

__author__ = 'dominik'
__date__ = '11.12.12'

from micropsi_core.nodenet import monitor

import micropsi_core


def add_gate_monitor(nodenet_uid, node_uid, gate, sheaf=None, name=None, color=None):
    """Adds a continuous monitor to the activation of a gate. The monitor will collect the activation
    value in every simulation step.
    Returns the uid of the new monitor."""
    nodenet = micropsi_core.runtime.nodenets[nodenet_uid]
    mon = monitor.NodeMonitor(nodenet, node_uid, 'gate', gate, sheaf=sheaf, name=name, color=color)
    return mon.uid


def add_slot_monitor(nodenet_uid, node_uid, slot, sheaf=None, name=None, color=None):
    """Adds a continuous monitor to the activation of a slot. The monitor will collect the activation
    value in every simulation step.
    Returns the uid of the new monitor."""
    nodenet = micropsi_core.runtime.nodenets[nodenet_uid]
    mon = monitor.NodeMonitor(nodenet, node_uid, 'slot', slot, sheaf=sheaf, name=name, color=color)
    return mon.uid


def add_link_monitor(nodenet_uid, source_node_uid, gate_type, target_node_uid, slot_type, property, name, color=None):
    """Adds a continuous monitor to a link. You can choose to monitor either weight (default) or certainty
    The monitor will collect respective value in every simulation step.
    Returns the uid of the new monitor."""
    nodenet = micropsi_core.runtime.nodenets[nodenet_uid]
    mon = monitor.LinkMonitor(nodenet, source_node_uid, gate_type, target_node_uid, slot_type, property=property, name=name, color=color)
    return mon.uid


def add_modulator_monitor(nodenet_uid, modulator, name, color=None):
    """Adds a continuous monitor to a global modulator.
    The monitor will collect respective value in every simulation step.
    Returns the uid of the new monitor."""
    nodenet = micropsi_core.runtime.nodenets[nodenet_uid]
    mon = monitor.ModulatorMonitor(nodenet, modulator, property=property, name=name, color=color)
    return mon.uid


def add_custom_monitor(nodenet_uid, function, name, color=None):
    """Adds a continuous monitor, that evaluates the given python-code and collects the
    return-value for every simulation step.
    Returns the uid of the new monitor."""
    nodenet = micropsi_core.runtime.nodenets[nodenet_uid]
    mon = monitor.CustomMonitor(nodenet, function=function, name=name, color=color)
    return mon.uid


def remove_monitor(nodenet_uid, monitor_uid):
    """Deletes an activation monitor."""
    micropsi_core.runtime.nodenets[nodenet_uid]._unregister_monitor(monitor_uid)
    return True


def clear_monitor(nodenet_uid, monitor_uid):
    """Leaves the monitor intact, but deletes the current list of stored values."""
    micropsi_core.runtime.nodenets[nodenet_uid].get_monitor(monitor_uid).clear()
    return True


def export_monitor_data(nodenet_uid, monitor_uid=None):
    """Returns a string with all currently stored monitor data for the given nodenet."""
    if monitor_uid is not None:
        return micropsi_core.runtime.nodenets[nodenet_uid].construct_monitors_dict()[monitor_uid]
    else:
        return micropsi_core.runtime.nodenets[nodenet_uid].construct_monitors_dict()


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
