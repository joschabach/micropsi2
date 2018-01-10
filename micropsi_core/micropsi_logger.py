"""
    Logging classes for storing log records in memory so browser clients
    can fetch them.
"""

__author__ = 'rvuine'

import os
import logging
import time
from operator import itemgetter

MAX_RECORDS_PER_STORAGE = 1000

# optionally color log console log output
try:
    import coloredlogs
except ImportError:
    coloredlogs = None


class RecordWebStorageHandler(logging.Handler):

    def __init__(self, record_storage, name):
        """
        Initialize the handler
        """
        logging.Handler.__init__(self)
        self.name = name
        self.record_storage = record_storage

    def flush(self):
        """
        does nothing for this handler
        """

    def emit(self, record):
        self.format(record)
        while len(self.record_storage[self.name]) >= MAX_RECORDS_PER_STORAGE:
            del self.record_storage[self.name][0]
        dictrecord = {
            "logger": record.name,
            "time": record.created * 1000,
            "level": record.levelname,
            "function": record.funcName,
            "module": record.module,
            "msg": record.message,
            "step": None
        }
        if record.name.startswith('agent.'):
            from micropsi_core.runtime import nodenets
            uid = record.name.split('.').pop(1)
            if uid in nodenets:
                dictrecord['step'] = nodenets[uid].current_step
            else:
                dictrecord['step'] = 0
        self.record_storage[self.name].append(dictrecord)


class MicropsiLogger():

    logging_levels = {
        'CRITICAL': logging.CRITICAL,
        'ERROR': logging.ERROR,
        'WARNING': logging.WARNING,
        'INFO': logging.INFO,
        'DEBUG': logging.DEBUG
    }

    loggers = {}

    record_storage = {}

    handlers = {}

    default_format = '[%(name)8s] %(asctime)s - %(module)s:%(funcName)s() - %(levelname)s - %(message)s'

    def __init__(self, default_logging_levels={}, log_to_file=False):

        logging.basicConfig(
            level=self.logging_levels.get('logging_level', logging.INFO),
            format=self.default_format,
            datefmt='%d.%m. %H:%M:%S'
        )

        logging.getLogger().handlers = []

        self.log_to_file = log_to_file
        self.filehandler = None
        if log_to_file:
            if os.path.isfile(log_to_file):
                os.remove(log_to_file)
            self.filehandler = logging.FileHandler(self.log_to_file, mode='a')
            formatter = logging.Formatter(self.default_format)
            self.filehandler.setFormatter(formatter)
            self.filehandler.set_name('filehandler')

        self.register_logger("system", self.logging_levels.get(default_logging_levels.get('system', {}), logging.WARNING))
        self.register_logger("world", self.logging_levels.get(default_logging_levels.get('world', {}), logging.WARNING))

    def set_logfile(self, logfile=None):
        if logfile:
            self.log_to_file = logfile
            if os.path.isfile(logfile):
                os.remove(logfile)
            self.filehandler = logging.FileHandler(logfile, mode='a')
            formatter = logging.Formatter(self.default_format)
            self.filehandler.setFormatter(formatter)
            self.filehandler.set_name('filehandler')
            for name in self.loggers:
                self.loggers[name].addHandler(self.filehandler)
        elif self.log_to_file:
            self.log_to_file = False
            for name in self.loggers:
                self.loggers[name].handlers.remove(self.filehandler)

    def register_logger(self, name, level):
        self.loggers[name] = logging.getLogger(name)
        self.loggers[name].setLevel(level)
        self.loggers[name].propagate = False
        self.record_storage[name] = []
        self.handlers[name] = RecordWebStorageHandler(self.record_storage, name)
        formatter = logging.Formatter(self.default_format)
        self.handlers[name].setFormatter(formatter)
        logging.getLogger(name).addHandler(self.handlers[name])
        if self.filehandler:
            logging.getLogger(name).addHandler(self.filehandler)
        self.loggers[name].debug("Logger %s ready" % name)
        if coloredlogs is not None:
            coloredlogs.install(logger=self.loggers[name], level=level)

    def unregister_logger(self, name):
        logging.getLogger(name).removeHandler(self.handlers[name])
        if self.filehandler:
            logging.getLogger(name).removeHandler(self.filehandler)
        del self.handlers[name]
        del self.record_storage[name]
        del self.loggers[name]

    def clear_logs(self):
        for key in self.record_storage:
            self.record_storage[key] = []

    def set_logging_level(self, logger, level):
        logging.getLogger(logger).setLevel(self.logging_levels[level.upper()])

    def get_logs(self, logger=[], after=0):
        """
            Returns a dict with the current time and a list of log entries,
            filtered by logger name and timestamp
        """
        logs = []
        for key in logger:
            if key in self.record_storage:
                logs.extend(self.record_storage[key])

        logs = sorted(logs, key=itemgetter('time'))

        if after > 0:
            logs = [l for l in logs if l['time'] >= after]

        now = int(round(time.time() * 1000))
        return {
            "servertime": now,
            "logs": logs}
