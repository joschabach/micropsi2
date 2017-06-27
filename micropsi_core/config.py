"""
Maintain configuration data for the MicroPsi service

The configuration manager takes care of persisting config data for the different MicroPsi components.
At the moment, persistence is achieved with a simple file, into which config data is dumped in json format.

All configuration data is simply stored as a dictionary, with keys to reference them. The items may be strings,
arrays or dictionaries. Every change prompts a saving of the config data to disk.

Example usage:

>>> configs = ConfigurationManager("my_configuration_data.json")
>>> configs["fontsize"] = 12
>>> configs["lineparameters"] = { "weight" : "2pt", "color" : "blue" }
>>> print configs["lineparameters"]["color"]
blue
"""

__author__ = 'joscha'
__date__ = '04.07.12'

import json
import os
import micropsi_core.tools
import logging


class ConfigurationManager(object):
    """The configuration manager creates, deletes and persists configuration data.

    It should be a singleton, because all config managers would use the same resources for maintaining persistence.

    Attributes:
        users: a dictionary of user_ids to user objects (containing session tokens, access role and hashed passwords)
        sessions: a dictionary of active sessions for faster reference
        user_file: the handle for the user data file
    """

    instances = []

    def __init__(self, config_path="config-data.json", auto_save=True):
        """initialize configuration management.

        If no config data are found, a new resource file is created.

        Parameters:
            config (optional): a path to store config data permanently.
            auto_save: if set to True, then the config data will be saved after every change.
        """

        # check if we already have a configuration manager with this resource file
        absolute_path = os.path.abspath(config_path)
        if absolute_path in ConfigurationManager.instances:
            logging.getLogger("system").warning("A configuration manager with this resource path already exists!")
            # raise RuntimeError("A configuration manager with this resource path already exists!")

        ConfigurationManager.instances.append(absolute_path)
        self.key = absolute_path

        # set up persistence
        dirpath = os.path.dirname(config_path)
        if not os.path.isdir(dirpath):
            os.makedirs(dirpath, exist_ok=True)

        self.config_file_name = config_path
        self.auto_save = auto_save
        self.data = {}
        self.load_configs()

    def __del__(self):
        """shut down user management"""
        if hasattr(self, "key"):
            if ConfigurationManager:
                ConfigurationManager.instances.remove(self.key)

    def load_configs(self):
        """load configuration data"""
        try:
            with open(self.config_file_name, encoding="utf-8") as file:
                self.data = json.load(file)
            return True
        except ValueError:
            logging.getLogger("system").warning("Could not read config data at %s" % self.config_file_name)
        except IOError:
            logging.getLogger("system").info("No readable config data file, attempting to create one")
        return False

    def save_configs(self):
        """saves the config data to a file"""
        with open(self.config_file_name, mode='w+', encoding="utf-8") as file:
            json.dump(self.data, file, indent=4)

    def __setitem__(self, key, value):
        self.data[key] = value
        if self.auto_save:
            self.save_configs()

    def __delitem__(self, key):
        del self.data[key]
        if self.auto_save:
            self.save_configs()

    def __getitem__(self, key):
        return self.data[key]

    def __contains__(self, key):
        return key in self.data
