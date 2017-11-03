from micropsi_core.device import devicemanager
from micropsi_core.tools import generate_uid


def get_device_types():
    """ Return a dict with device types as keys and config dict as value """
    return dict((k, devicemanager.device_types[k].get_options()) for k in
                devicemanager.device_types)


def get_devices():
    """ Return a dict with device uids as keys and config dict as value """
    return dict((k, devicemanager.devices[k].get_config()) for k in
                devicemanager.devices)


def add_device(device_type, config):
    """ Create a new device of the given type with the given configuration """
    if device_type in devicemanager.device_types:
        dev = devicemanager.device_types[device_type](config)
        uid = generate_uid()
        devicemanager.devices[uid] = dev
        return True, uid
    return False


def remove_device(device_uid):
    """ Remove the device specified by the uid """
    if device_uid in devicemanager.devices:
        del devicemanager.devices[device_uid]
        return True
    return False


def set_device_properties(device_uid, config):
    """ Reconfigure the device specified by the uid """
    if device_uid in devicemanager.devices:
        devicemanager.devices[device_uid].set_config(config)
        return True
    return False
