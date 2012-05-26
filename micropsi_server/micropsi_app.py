#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MicroPsi server application.

This version of MicroPsi is meant to be deployed as a web server, and accessed through a browser.
For local use, simply start this server and point your browser to "http://localhost:6543".
The latter parameter is the default port and can be changed as needed.
"""

__author__ = 'joscha'
__date__ = '15.05.12'

from bottle import route, run, template, static_file
import argparse
import os

DEFAULT_PORT = 6543
DEFAULT_HOST = "localhost"

APP_PATH = os.path.dirname(__file__)

@route("/")
def index():
    return template("view/nodenet")

@route('/static/<filepath:path>')
def server_static(filepath):
    return static_file(filepath, root='static')

def main(host = DEFAULT_HOST, port = DEFAULT_PORT):
    # run(host=host, port=port)
    run(host=host, port=port, reloader=True) # debug version

if __name__=="__main__":
    parser = argparse.ArgumentParser(description="Start the MicroPsi server.")
    parser.add_argument('-d', '--host', type=str, default=DEFAULT_HOST)
    parser.add_argument('-p', '--port', type=int, default=DEFAULT_PORT)
    args = parser.parse_args()
    main(host = args.host, port = args.port)


