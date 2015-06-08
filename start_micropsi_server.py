#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Startup script for the MicroPsi service.
"""

__author__ = 'joscha'
__date__ = '06.07.12'

import micropsi_server.micropsi_app
import argparse


def main(host=None, port=None):
    micropsi_server.micropsi_app.main(host, port)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start the MicroPsi server.")
    parser.add_argument('-d', '--host', type=str, default=None)
    parser.add_argument('-p', '--port', type=int, default=None)
    args = parser.parse_args()
    main(host=args.host, port=args.port)
