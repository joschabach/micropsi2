#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""
Contains basic configuration information, especially path names to resource files
"""

__author__ = 'joscha'
__date__ = '03.12.12'

import os
import warnings
import configparser
from appdirs import AppDirs


def makedirs(path):
    if not os.access(path, os.W_OK):
        try:
            os.makedirs(path)
        except OSError as e:
            print("Fatal Error: Can not write to the configured data-directory")
            raise e


dirinfo = AppDirs("MicroPsi Runtime", appauthor=False, roaming=True)

configini = os.path.join(dirinfo.user_data_dir, "config.ini")
using_default = False

print("MicroPsi configuration directory: ", dirinfo.user_data_dir)

makedirs(dirinfo.user_data_dir)

if not os.path.isfile(configini):
    if os.path.isfile(os.path.abspath('config.ini')):
        configini = os.path.abspath('config.ini')
        print("Using local custom config")
    else:
        configini = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config.default.ini")
        using_default = True
        print("Using default configuration")
else:
    print("Using custom configuration")

try:
    config = configparser.ConfigParser()
    with open(configini) as fp:
        config.read_file(fp)
except OSError:
    warnings.warn('Can not read config from inifile %s' % configini)
    raise RuntimeError('Can not read config from inifile %s' % configini)

config['micropsi2']['version'] = "0.16-alpha14"
config['micropsi2']['apptitle'] = "MicroPsi"

data_path = os.path.expanduser(config['micropsi2']['data_directory'])
data_path = os.path.abspath(data_path)

config.add_section('paths')
config['paths']['usermanager_path'] = os.path.join(dirinfo.user_data_dir, 'user-db.json')
config['paths']['server_settings_path'] = os.path.join(dirinfo.user_data_dir, 'server-config.json')
config['paths']['device_settings_path'] = os.path.join(dirinfo.user_data_dir, 'devices.json')

for key in ['agent_directory', 'world_directory', 'persistency_directory']:
    if key in config['micropsi2']:
        path = os.path.expanduser(config['micropsi2'][key])
        config['paths'][key] = os.path.abspath(path)
    else:
        config['paths'][key] = data_path
    makedirs(config['paths'][key])
