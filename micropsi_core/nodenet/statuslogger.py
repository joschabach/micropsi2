
import copy
import logging

from micropsi_core.runtime import logger


class StatusLogger(object):

    INACTIVE = "inactive"
    ACTIVE = "active"
    SUCCESS = "success"
    FAILURE = "failure"

    def __init__(self, name):
        """ Logger that accepts non-string data """
        self.name = name
        self._logger = logging.getLogger(name)
        logger.register_logger(name, logging.DEBUG)
        self.status_dict = {}
        self.states = [self.INACTIVE, self.ACTIVE, self.SUCCESS, self.FAILURE]

    def log(self, level, key, state, msg="", progress=None):
        """ Log the given message

        Params
            level: log level
                can be given as integer (e.g. logging.DEBUG) or
                as the corresponding string (e.g. 'DEBUG').

            key: string, namespaced via '.'

            msg: a message

            progress: optional progress tuple

        """
        try:
            intlevel = getattr(logging, level.upper())
        except AttributeError:
            raise Exception('%s is not a known log level' % level)

        if state not in self.states:
            logging.getLogger("system").warning("unknown state for status logger: %s" % state)

        self._track_status(level, intlevel, key, state, msg, progress)

        log_msg = "STATUS: %s: %s " % (key, state)
        if progress:
            log_msg += "- %d/%d completed. " % progress
        log_msg += msg
        self._logger.log(intlevel, log_msg)

    def remove(self, key):
        path = key.split('.')
        if len(path) == 1:
            del self.status_dict[path[0]]
        else:
            item = self.status_dict
            for x in path[:-1]:
                item = item[x]['children']
            del item[path[-1]]

    def _track_status(self, level, intlevel, key, state, msg, progress):
        path = key.split('.')
        data = {
            'level': level,
            'intlevel': intlevel,
            'state': state,
            'msg': msg,
            'progress': progress or '',
        }
        template = {
            'level': level,
            'intlevel': intlevel,
            'state': '',
            'msg': '',
            'progress': '',
            'children': {}
        }

        if len(path) == 1:
            if path[0] not in self.status_dict:
                self.status_dict[path[0]] = copy.deepcopy(template)
            self.status_dict[path[0]].update(data)
        else:
            # import pdb; pdb.set_trace()
            if path[0] not in self.status_dict:
                self.status_dict[path[0]] = copy.deepcopy(template)
            node = self.status_dict[path[0]]
            for key in path[1:]:
                if key not in node['children']:
                    node['children'][key] = copy.deepcopy(template)
                node = node['children'][key]
            node.update(data)

    def get_status_tree(self, logging_level="debug"):
        intlevel = getattr(logging, logging_level.upper())
        data = {}
        for key in self.status_dict:
            if self.status_dict[key]['intlevel'] >= intlevel:
                data[key] = self.status_dict[key]
        return data

    def critical(self, *args, **kwargs):
        self.log('critical', *args, **kwargs)

    def error(self, *args, **kwargs):
        self.log('error', *args, **kwargs)

    def warning(self, *args, **kwargs):
        self.log('warning', *args, **kwargs)

    def info(self, *args, **kwargs):
        self.log('info', *args, **kwargs)

    def debug(self, *args, **kwargs):
        self.log('debug', *args, **kwargs)
