"""
MicroPsi web server component, currently using the bottle framework for rendering content
"""

__author__ = 'joscha'
__date__ = '15.05.12'

from threading import Thread
import configuration as defaults


def main(global_config, **config):
    # evil monkeypath to inject the data path from config into the runtime...
    defaults.DATA_PATH = config.get('data_path', defaults.DATA_PATH)
    # ... before the api and app use them as side effect
    import user_api
    import micropsi_app
    adminapp = Thread(target=micropsi_app.main,
        args=(config.get('admin_api_host', defaults.DEFAULT_HOST),
            config.get('admin_api_port', defaults.DEFAULT_ADMIN_PORT)))
    adminapp.daemon = True
    adminapp.start()
    return user_api.api_app
