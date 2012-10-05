#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Startup script for the MicroPsi service.
"""

__author__ = 'joscha'
__date__ = '06.07.12'

DEFAULT_PORT = 6543
DEFAULT_HOST = "localhost"

import micropsi_server.micropsi_app
import argparse
import multiprocessing


def main(host=DEFAULT_HOST, port=DEFAULT_PORT):
    runner = multiprocessing.Process(target=runner_deamon, args=(port,))
    runner.daemon = True
    runner.start()
    micropsi_server.micropsi_app.main(host, port)


def runner_deamon(port):
    import time
    import warnings
    from urllib2 import urlopen, URLError
    from datetime import datetime, timedelta
    interval = timedelta(milliseconds=100)
    errcount = 0
    while True:
        start = datetime.now()
        try:
            urlopen('http://127.0.0.1:%s/rpc/runner_step()' % port)
            errcount = 0
        except URLError:
            errcount += 1
            if errcount > 4:
                # five consecutive fails: give up
                warnings.warn('Runner gave up after 5 failed attempts')
                return False
        left = interval - (datetime.now() - start)
        time.sleep(left.microseconds / 1000000.0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start the MicroPsi server.")
    parser.add_argument('-d', '--host', type=str, default=DEFAULT_HOST)
    parser.add_argument('-p', '--port', type=int, default=DEFAULT_PORT)
    args = parser.parse_args()
    main(host=args.host, port=args.port)
