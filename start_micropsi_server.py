#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Startup script for the MicroPsi service.
"""

__author__ = 'joscha'
__date__ = '06.07.12'

DEFAULT_ADMIN_PORT = 6543
DEFAULT_API_PORT = 8080
DEFAULT_HOST = "localhost"

from micropsi_server import micropsi_app, user_api
import argparse
import os


def main(host=DEFAULT_HOST, admin_port=DEFAULT_ADMIN_PORT, api_port=DEFAULT_API_PORT):
    pid = os.fork()
    if pid == 0:
        micropsi_app.main(host, admin_port)
    else:
        user_api.main(host, api_port)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start the MicroPsi server.")
    parser.add_argument('-d', '--host', type=str, default=DEFAULT_HOST)
    parser.add_argument('-admin', '--adminport', type=int, default=DEFAULT_ADMIN_PORT)
    parser.add_argument('-api', '--apiport', type=int, default=DEFAULT_API_PORT)
    args = parser.parse_args()
    main(host=args.host, admin_port=args.adminport, api_port=args.apiport)
