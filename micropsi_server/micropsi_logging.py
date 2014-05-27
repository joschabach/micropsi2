"""
    Logging classes for storing log records in memory so browser clients
    can fetch them.
"""

__author__ = 'rvuine'

import logging


class RecordWebStorageHandler(logging.Handler):

    record_storage = None

    def __init__(self, record_storage=None):
        """
        Initialize the handler
        """
        logging.Handler.__init__(self)
        self.record_storage = record_storage

    def flush(self):
        """
        does nothing for this handler
        """

    def emit(self, record):
        # add record to self.record_storage
        pass


logging.getLogger("nodenet").addHandler(new RecordWebStorageHandler())