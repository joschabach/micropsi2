#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""
Contains basic configuration information, especially path names to resource files
"""

__author__ = 'joscha'
__date__ = '03.12.12'

import os
import configparser
import warnings

configini = os.path.dirname(os.path.realpath(__file__)) + "/config.ini"
defaultconfigini = os.path.dirname(os.path.realpath(__file__)) + "/default.config.ini"

if os.path.isfile(configini):
    filename = configini
else:
    filename = defaultconfigini
try:
    config = configparser.ConfigParser()
    with open(filename) as fp:
        config.read_file(fp)
except OSError:
    warnings.warn('Can not read config from inifile %s' % filename)
    raise RuntimeError('Can not read config from inifile %s' % filename)

config['micropsi2']['version'] = "0.9-alpha7-dev"
config['micropsi2']['apptitle'] = "MicroPsi"

homedir = config['micropsi2']['data_directory'].startswith('~')

if homedir:
    data_path = os.path.expanduser(config['micropsi2']['data_directory'])
else:
    data_path = config['micropsi2']['data_directory']

if 'logging' not in config:
    config['logging'] = {}

for level in ['level_agent', 'level_system', 'level_world']:
    if level not in config['logging']:
        warnings.warn('logging level for %s not set in config.ini - defaulting to WARNING' % level)
        config['logging'][level] = 'WARNING'

config.add_section('paths')
config['paths']['data_directory'] = os.path.join(os.path.dirname(__file__), data_path)
config['paths']['usermanager_path'] = os.path.join(os.path.dirname(__file__), 'resources', 'user-db.json')
config['paths']['server_settings_path'] = os.path.join(os.path.dirname(__file__), 'resources', 'server-config.json')
