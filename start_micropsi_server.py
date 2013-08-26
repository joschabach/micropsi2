#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Startup script for the MicroPsi service.
"""

__author__ = 'joscha'
__date__ = '06.07.12'

from configuration import DEFAULT_PORT, DEFAULT_HOST
import micropsi_server.micropsi_app
import argparse


def main(host=DEFAULT_HOST, port=DEFAULT_PORT):
    micropsi_server.micropsi_app.main(host, port)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start the MicroPsi server.")
    parser.add_argument('-d', '--host', type=str, default=DEFAULT_HOST)
    parser.add_argument('-p', '--port', type=int, default=DEFAULT_PORT)
    args = parser.parse_args()
    main(host=args.host, port=args.port)
