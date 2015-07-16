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

try:
    config = configparser.ConfigParser()
    config.read_file(open('config.ini'))
except OSError:
    warnings.warn('config.ini not found - please copy config.template.ini to config.ini and edit according to your preferences')
    raise RuntimeError("config.ini not found")

config['micropsi2']['version'] = "0.5-alpha3"
config['micropsi2']['apptitle'] = "MicroPsi"

homedir = config['micropsi2']['data_directory'].startswith('~')

if homedir:
    data_path = os.path.expanduser(config['micropsi2']['data_directory'])
else:
    data_path = config['micropsi2']['data_directory']

config.add_section('paths')
config['paths']['resource_path'] = os.path.join(os.path.dirname(__file__), data_path)
config['paths']['usermanager_path'] = os.path.join(os.path.dirname(__file__), 'resources', 'user-db.json')
config['paths']['server_settings_path'] = os.path.join(os.path.dirname(__file__), 'resources', 'server-config.json')
