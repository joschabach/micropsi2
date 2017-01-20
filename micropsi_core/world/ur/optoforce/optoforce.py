import ctypes
import numpy as np
import os


class FT(ctypes.Structure):
    _fields_ = [('fx', ctypes.c_int),
                ('fy', ctypes.c_int),
                ('fz', ctypes.c_int),
                ('tx', ctypes.c_int),
                ('ty', ctypes.c_int),
                ('tz', ctypes.c_int)]

_optoforce = None
_ft = FT()
_ftbyteref = ctypes.byref(_ft)


def init():
    """
    Initializes the module and connects to the first OptoForce 6D sensor connected by USB
    """

    global _optoforce

    location = "./micropsi_core/world/ur/optoforce"
    _optoforce = ctypes.CDLL(os.path.join(location, "liboptoforce.so"))

    if not _optoforce.init():
        raise Exception("Could not initialize OptoForce 6D F/T sensor. Sensor connected to USB, permissions good?")


def shutdown():
    """
    Disconnects from the OptoForce sensor
    """
    _optoforce.shutdown()


def get_ft():
    """
    Returns an object with the fields fx, fy, fz, tx, ty, tz, filled with the current sensor readings.
    """
    _optoforce.fill_ft(_ftbyteref)
    return _ft


def get_ft_np():
    """
    Returns a 6-valued np array with current sensor readings
    """
    _optoforce.fill_ft(_ftbyteref)
    return np.array([_ft.fx, _ft.fy, _ft.fy, _ft.tx, _ft.ty, _ft.tz])
