from devices.device import Device
from devices import *
from devices.cameras import *
from micropsi_core.tools import itersubclasses
import inspect


def get_device_types():
    devtypes = []
    for a in itersubclasses(Device):
        if not inspect.isabstract(a):
            devtypes.append()
    return devtypes
