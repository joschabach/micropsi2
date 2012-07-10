#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Startup script for the MicroPsi service.
"""

__author__ = 'joscha'
__date__ = '06.07.12'

DEFAULT_PORT = 6543
DEFAULT_HOST = "localhost"

import micropsi_server.micropsi_app, argparse

def main(host=DEFAULT_HOST, port=DEFAULT_PORT):
    micropsi_server.micropsi_app.main(host, port)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start the MicroPsi server.")
    parser.add_argument('-d', '--host', type=str, default=DEFAULT_HOST)
    parser.add_argument('-p', '--port', type=int, default=DEFAULT_PORT)
    args = parser.parse_args()
    main(host = args.host, port = args.port)

