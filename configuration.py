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

dirinfo = AppDirs("MicroPsi Runtime")

configini = os.path.join(dirinfo.user_data_dir, "config.ini")
using_default = False

if not os.path.isdir(dirinfo.user_data_dir):
    os.makedirs(dirinfo.user_data_dir)

if not os.path.isfile(configini):
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

config['micropsi2']['version'] = "0.9-alpha7-dev"
config['micropsi2']['apptitle'] = "MicroPsi"

if using_default:
    data_path = os.path.join(os.path.expanduser('~'), config['micropsi2']['data_directory'])
else:
    data_path = os.path.expanduser(config['micropsi2']['data_directory'])
    data_path = os.path.abspath(data_path)

if not os.access(data_path, os.W_OK):
    try:
        os.makedirs(data_path)
    except OSError as e:
        print("Fatal Error: Can not write to the configured data-directory")
        raise e

if 'logging' not in config:
    config['logging'] = {}

for level in ['level_agent', 'level_system', 'level_world']:
    if level not in config['logging']:
        warnings.warn('logging level for %s not set in config.ini - defaulting to WARNING' % level)
        config['logging'][level] = 'WARNING'

config.add_section('paths')
config['paths']['data_directory'] = data_path
config['paths']['usermanager_path'] = os.path.join(dirinfo.user_data_dir, 'user-db.json')
config['paths']['server_settings_path'] = os.path.join(dirinfo.user_data_dir, 'server-config.json')
