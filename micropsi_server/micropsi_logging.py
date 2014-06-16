"""
    Logging classes for storing log records in memory so browser clients
    can fetch them.
"""

__author__ = 'rvuine'

import logging
import time
from operator import itemgetter

MAX_RECORDS_PER_STORAGE = 1000


class RecordWebStorageHandler(logging.Handler):

    record_storage = None

    def __init__(self, record_storage):
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
        self.format(record)
        while len(self.record_storage) >= MAX_RECORDS_PER_STORAGE:
            del self.record_storage[0]
        dictrecord = {
            "logger": record.name,
            "time": int(round(record.created * 1000)),
            "level": record.levelname,
            "msg": record.message
        }
        self.record_storage.append(dictrecord)

nodenet_record_storage = []
world_record_storage = []
system_record_storage = []

logging.captureWarnings(True)

logging.getLogger("nodenet").addHandler(RecordWebStorageHandler(nodenet_record_storage))
logging.getLogger("world").addHandler(RecordWebStorageHandler(world_record_storage))

system_storage_handler = RecordWebStorageHandler(system_record_storage)
logging.getLogger("system").addHandler(system_storage_handler)
logging.getLogger("py.warnings").addHandler(system_storage_handler)

logging.getLogger("nodenet").debug("Nodenet logger ready.")
logging.getLogger("world").debug("World logger ready.")
logging.getLogger("world").debug("System logger ready.")


def get_logs(logger="*", after=0):
    """
        Returns a dict with the current time and a list of log entries,
        filtered by logger name and timestamp
    """
    logs = []
    if logger == "*":
        logs.extend(nodenet_record_storage)
        logs.extend(world_record_storage)
        logs.extend(system_record_storage)
        logs = sorted(logs, key=itemgetter('time'))
    elif logger == "nodenet":
        logs.extend(nodenet_record_storage)
    elif logger == "world":
        logs.extend( world_record_storage)
    elif logger == "system":
        logs.extend(system_record_storage)

    i = len(logs)-1
    while i >= 0:
        if logs[i]["time"] < after:
            del logs[i]
        i -= 1

    now = int(round(time.time() * 1000))
    return {
        "servertime": now,
        "logs": logs}
