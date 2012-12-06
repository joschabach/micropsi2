#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Startup script for the MicroPsi service.
"""

__author__ = 'joscha'
__date__ = '06.07.12'

from micropsi_server import micropsi_app, user_api
from threading import Thread

from configuration import DEFAULT_API_PORT, DEFAULT_HOST, DEFAULT_ADMIN_PORT
import argparse


def main(host=DEFAULT_HOST, admin_port=DEFAULT_ADMIN_PORT, api_port=DEFAULT_API_PORT):
    adminapp = Thread(target=micropsi_app.main, args=(host, admin_port))
    adminapp.daemon = True
    adminapp.start()
    user_api.main(host, api_port)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start the MicroPsi server.")
    parser.add_argument('-d', '--host', type=str, default=DEFAULT_HOST)
    parser.add_argument('-admin', '--adminport', type=int, default=DEFAULT_ADMIN_PORT)
    parser.add_argument('-api', '--apiport', type=int, default=DEFAULT_API_PORT)
    args = parser.parse_args()
    main(host=args.host, admin_port=args.adminport, api_port=args.apiport)
