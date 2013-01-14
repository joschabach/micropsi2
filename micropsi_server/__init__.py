"""
MicroPsi web server component, currently using the bottle framework for rendering content
"""

__author__ = 'joscha'
__date__ = '15.05.12'

import user_api
import micropsi_app
from threading import Thread
from configuration import DEFAULT_ADMIN_PORT, DEFAULT_HOST


def main(global_config, **config):
    adminapp = Thread(target=micropsi_app.main,
        args=(config.get('admin_api_host', DEFAULT_HOST),
            config.get('admin_api_port', DEFAULT_ADMIN_PORT)))
    adminapp.daemon = True
    adminapp.start()
    return user_api.api_app
