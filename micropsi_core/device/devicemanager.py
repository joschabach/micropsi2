from micropsi_core.device.device import Device
from micropsi_core.tools import itersubclasses
import inspect


def get_device_types():
    devtypes = []
    for a in itersubclasses(Device):
        if not inspect.isabstract(a):
            devtypes.append()
    return devtypes
