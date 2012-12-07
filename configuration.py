#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""
Contains basic configuration information, especially path names to resource files
"""

__author__ = 'joscha'
__date__ = '03.12.12'

import os

VERSION = "0.2"

APPTITLE = "PSI Cortex"

RESOURCE_PATH = os.path.join(os.path.dirname(__file__), "resources")
USERMANAGER_PATH = os.path.join(RESOURCE_PATH, "user-db.json")

DEFAULT_PORT = 6543
DEFAULT_HOST = "localhost"
