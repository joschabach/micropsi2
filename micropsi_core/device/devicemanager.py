from micropsi_core.device.device import Device
import inspect
import importlib
import importlib.util
import os
import sys


ignore_list = ['__pycache__', '__init__.py']
device_types = {}
devices = {}


def reload_devices(path):
    global ignore_list, device_types
    if path not in sys.path:
        sys.path.append(path)
    device_types = {}
    for subdir in os.scandir(path):
        if subdir.is_dir() and subdir.name not in ignore_list:
            for sources in os.scandir(os.path.join(path, subdir.name)):
                if sources.is_file() and sources.name not in ignore_list:
                    try:
                        modpath = os.path.join(path, subdir.name, sources.name)
                        modname = subdir.name + '.' + sources.name.strip('.py')
                        if modname in sys.modules.keys():
                            del sys.modules[modname]
                        spec = importlib.util.spec_from_file_location(modname, modpath)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        sys.modules[modname] = module
                        for name, cls in inspect.getmembers(module, inspect.isclass):
                            if Device in inspect.getmro(cls) and not inspect.isabstract(cls):
                                device_types[name] = cls
                    except Exception as e:
                        raise e
