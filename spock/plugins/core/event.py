import signal
import copy
from spock.mcp import mcdata
from spock.utils import pl_announce

class EventCore:
    def __init__(self, register_kill_signal_handlers=True):
        self.kill_event = False
        self.event_handlers = {}
        self.register_kill_signal_handlers = register_kill_signal_handlers

    def event_loop(self):
        if self.register_kill_signal_handlers:
            signal.signal(signal.SIGINT, self.kill)
            signal.signal(signal.SIGTERM, self.kill)
        while not self.kill_event:
            self.emit('tick')
        self.emit('kill')

    def reg_event_handler(self, event, handler):
        if event not in self.event_handlers:
            self.event_handlers[event] = []
        self.event_handlers[event].append(handler)

    def unreg_event_handler(self, event, handler):
        if event in self.event_handlers and handler in self.event_handlers[event]:
            self.event_handlers[event].remove(handler)

    def emit(self, event, data = None):
        if event not in self.event_handlers:
            self.event_handlers[event] = []
        for handler in self.event_handlers[event]:
            handler(event, (data.clone() if hasattr(data, 'clone')
                else copy.deepcopy(data)
            ))

    def kill(self, *args):
        self.kill_event = True

@pl_announce('Event')
class EventPlugin:
    def __init__(self, ploader, settings):
        register_kill_signal_handlers = settings is None or 'killsignals' not in settings.keys() or \
            settings['killsignals'] is True
        ploader.provides('Event', EventCore(register_kill_signal_handlers))