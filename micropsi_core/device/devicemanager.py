from micropsi_core.device.device import Device
from micropsi_core.tools import generate_uid, post_mortem
import inspect
import importlib
import importlib.util
import os
import sys
import json
import logging
import shutil


ignore_list = ['__init__.py']
device_types = {}
devices = {}
device_json_path = None


def reload_device_types(path):
    global ignore_list, device_types
    if not os.path.isdir(path):
        return []
    if path not in sys.path:
        sys.path.append(path)
    device_types = {}
    errors = []
    for subdir in os.scandir(path):
        if subdir.is_dir() and subdir.name not in ignore_list:
            # first, remove pycache folders
            for entry in os.scandir(os.path.join(path, subdir.name)):
                if entry.is_dir() and entry.name == '__pycache__':
                    shutil.rmtree(os.path.join(path, subdir.name, entry.name))
            # then, load modules
            for sources in os.scandir(os.path.join(path, subdir.name)):
                if sources.is_file() and sources.name not in ignore_list and sources.name.endswith('.py'):
                    try:
                        modpath = os.path.join(path, subdir.name, sources.name)
                        modname = 'devices.' + subdir.name + '.' + sources.name.strip('.py')
                        spec = importlib.util.spec_from_file_location(modname, modpath)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        sys.modules[modname] = module
                        for name, cls in inspect.getmembers(module, inspect.isclass):
                            if Device in inspect.getmro(cls) and not inspect.isabstract(cls):
                                device_types[name] = cls
                    except Exception as e:
                        post_mortem(ignore_types=[ImportError])
                        errors.append("%s when importing device file %s: %s" % (e.__class__.__name__, modpath, str(e)))
    return errors


def get_devices():
    return dict((k, devices[k].get_config()) for k in devices)


def add_device(device_type, config, dev_uid=None):
    if device_type in device_types:
        dev = device_types[device_type](config)
        if dev_uid is None:
            uid = generate_uid()
        else:
            uid = dev_uid
        devices[uid] = dev
        with open(device_json_path, 'w', encoding='utf-8') as devices_json:
            devices_json.write(json.dumps(get_devices()))
        return True, uid
    return False, "Unknown device type"


def remove_device(device_uid):
    if device_uid in devices:
        del devices[device_uid]
        with open(device_json_path, 'w', encoding='utf-8') as devices_json:
            devices_json.write(json.dumps(get_devices()))
        return True
    return False


def reload_devices(json_path):
    global device_json_path, devices
    device_json_path = json_path
    devices = {}
    try:
        with open(json_path) as devices_json:
            data = json.load(devices_json)
            for k in data:
                if data[k]['type'] not in device_types:
                    logging.getLogger('system').warning("Device type %s not found!" % data[k]['type'])
                    continue
                devices[k] = device_types[data[k]['type']](data[k]['config'])
    except FileNotFoundError:
        logging.getLogger('system').info("Device persistency file not found: %s" % json_path)
    except ValueError:
        raise ValueError("Malforfmed JSON file: %s" % json_path)
