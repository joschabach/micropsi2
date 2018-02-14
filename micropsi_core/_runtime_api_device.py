from micropsi_core.device import devicemanager


def get_device_types():
    """ Return a dict with device types as keys and config dict as value """
    return dict((k, devicemanager.device_types[k].get_options()) for k in
                devicemanager.device_types)


def get_devices():
    """ Return a dict of devices with device uids
    as keys and config dict as a value """
    online_devs = devicemanager.get_online_devices()
    known_devs = devicemanager.get_known_devices()
    for d in known_devs:
        if d in online_devs:
            known_devs[d]['online'] = True
        else:
            known_devs[d]['online'] = False
    return known_devs


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
    return False, "This device is not online and can not be configured"
