from micropsi_core.device import devicemanager


def get_device_types():
    """ Return a dict with device types as keys and config dict as value """
    return dict((k, devicemanager.device_types[k].get_options()) for k in
                devicemanager.device_types)


def get_devices():
    """ Return a dict of online devices
    with device uids as keys and config dict as value """
    return devicemanager.get_online_devices()


def add_device(device_type, config):
    """ Create a new device of the given type with the given configuration """
    return devicemanager.add_device(device_type, config)


def remove_device(device_uid):
    """ Remove the device specified by the uid """
    return devicemanager.remove_device(device_uid)


def set_device_properties(device_uid, config):
    """ Reconfigure the device specified by the uid """
    if device_uid in devicemanager.online_devices:
        devtype = devicemanager.online_devices[device_uid].__class__.__name__
        devicemanager.remove_device(device_uid)
        devicemanager.add_device(devtype, config, device_uid)
        return True
    return False
