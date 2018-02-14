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
online_devices = {}  # holds instances of active devices
known_devices = {}  # holds config-dicts of all devices
device_json_path = None


def reload_device_types(path):
    global ignore_list, device_types
    device_types = {}
    errors = []
    if not os.path.isdir(path):
        return errors
    if path not in sys.path:
        sys.path.append(path)
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
                        modname = 'devices.' + subdir.name + '.' + sources.name[:-3]  # remove ".py" from name
                        spec = importlib.util.spec_from_file_location(modname, modpath)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        sys.modules[modname] = module
                        for name, cls in inspect.getmembers(module, inspect.isclass):
                            if Device in inspect.getmro(cls) and not inspect.isabstract(cls):
                                device_types[name] = cls
                    except ImportError as e:
                        logging.getLogger("system").error("%s when importing device file %s: %s" % (e.__class__.__name__, modpath, str(e)))
                    except Exception as e:
                        errors.append("%s when importing device file %s: %s" % (e.__class__.__name__, modpath, str(e)))
                        post_mortem()
    return errors


def get_known_devices():
    """ Returns a dict of all known devices"""
    return known_devices


def get_online_devices():
    """ Returns a dict of online device instances"""
    return dict((k, online_devices[k].get_config()) for k in online_devices)


def add_device(device_type, config, dev_uid=None):
    if device_type in device_types:
        dev = device_types[device_type](config)
        if dev_uid is None:
            uid = generate_uid()
        else:
            uid = dev_uid
        known_devices[uid] = dev.get_config()
        online_devices[uid] = dev
        with open(device_json_path, 'w', encoding='utf-8') as devices_json:
            devices_json.write(json.dumps(get_known_devices()))
        return True, uid
    return False, "Unknown device type"


def remove_device(device_uid):
    if device_uid in known_devices:
        del known_devices[device_uid]
        if device_uid in online_devices:
            online_devices[device_uid].deinit()
            del online_devices[device_uid]
        with open(device_json_path, 'w', encoding='utf-8') as devices_json:
            devices_json.write(json.dumps(get_known_devices()))
        return True
    return False


def read_persistence(json_path):
    try:
        with open(json_path) as fp:
            data = json.load(fp)
    except FileNotFoundError:
        logging.getLogger('system').info("Device persistency file not found: %s" % json_path)
        return None
    except ValueError:
        logging.getLogger('system').error("Malforfmed JSON file: %s" % json_path)
        return None
    return data


def reload_devices(json_path):
    global device_json_path, known_devices, online_devices
    device_json_path = json_path

    for d in list(online_devices.keys()):
        online_devices[d].deinit()
        del online_devices[d]

    known_devices = {}
    online_devices = {}
    data = read_persistence(json_path)
    if data is None:
        return
    known_devices = data.copy()
    for k in data:
        if data[k]['type'] not in device_types:
            logging.getLogger('system').warning("Device type %s not found!" % data[k]['type'])
            continue
        try:
            online_devices[k] = device_types[data[k]['type']](data[k]['config'])
        except Exception as e:
            logging.getLogger('system').error("Error when loading device %s with uid %s: %s" % (data[k]['type'], k, e))


def shutdown():
    for d in list(online_devices.keys()):
        online_devices[d].deinit()
