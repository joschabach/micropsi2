#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Startup script for the MicroPsi service.
"""

__author__ = 'joscha'
__date__ = '06.07.12'

import micropsi_server.micropsi_app
import argparse


def main(host=None, port=None, console=True):
    micropsi_server.micropsi_app.main(host, port, console=console)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start the MicroPsi server.")
    parser.add_argument('-d', '--host', type=str, default=None)
    parser.add_argument('-p', '--port', type=int, default=None)
    parser.add_argument('--console', dest='console', action='store_true')
    parser.add_argument('--no-console', dest='console', action='store_false')
    parser.set_defaults(console=True)
    args = parser.parse_args()
    main(host=args.host, port=args.port, console=args.console)
