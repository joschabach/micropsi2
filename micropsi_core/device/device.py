from abc import ABCMeta, abstractmethod
from threading import Thread, current_thread
import logging
import time


class Device(metaclass=ABCMeta):
    """
    The Device abstract base class. Do not inherit from this class immediately,
    instead use one of the subclasses (InputDevice and OutputDevice),
    that further specify the direction of the data flow
    """
    def __init__(self, config):
        self.logger = logging.getLogger("world")
        for item in self.__class__.get_options():
            if item['name'] not in config:
                config[item['name']] = item.get('default')
        for key in config:
            setattr(self, key, config[key])

    def get_config(self):
        config = dict()
        info = dict()
        for item in self.__class__.get_options():
            config[item['name']] = getattr(self, item['name'])
        if isinstance(self, InputDevice):
            info['nature'] = "InputDevice"
        elif isinstance(self, OutputDevice):
            info['nature'] = "OutputDevice"
        else:
            raise TypeError("Devices must inherit from either InputDevice or OutputDevice")
        info['type'] = self.__class__.__name__
        info['config'] = config
        info['prefix'] = self.get_prefix()
        info['data_size'] = self.get_data_size()
        return info

    @classmethod
    def get_options(cls):
        """
        In case the device has further options they should be added by overriding
        this method
        """
        options = [{
                        'name': 'name',
                        'description': 'device name',
                        'default': 'Device'}, ]
        return options

    @abstractmethod
    def get_data_size(self):
        """
        Should be implemented to return the size of the data that can be
        read/written from/to devices in one iteration
        """
        pass  # pragma: no cover

    @abstractmethod
    def get_prefix(self):
        """
        Should be implemented to return the prefix used for mapping devices
        to datasources/datatargets
        """
        pass  # pragma: no cover

    def deinit(self):
        """
        Should be implemented in case the device requires specific
        deinitialization sequence
        """
        pass  # pragma: no cover


class InputDevice(Device):
    def __init__(self, config):
        super().__init__(config)

    def get_data(self):
        """
        Aks the implementation to read data from the device and returns it to
        the world adapter. Do not override, implement read_data().
        """
        return self.read_data()

    @abstractmethod
    def read_data(self):
        """
        Implementation should return the array (of size get_data_size())
        with the data from the device
        """
        pass  # pragma: no cover


class OutputDevice(Device):
    def __init__(self, config):
        super().__init__(config)

    def set_data(self, data):
        """
        Passes data on to the device from the world adapter.
        Do not override, implement write_data(data).
        """
        self.write_data(data)

    @abstractmethod
    def write_data(self, data):
        """
        Implementation should accept the array (of size get_data_size())
        with the data sent to the device
        """
        pass  # pragma: no cover


class InputDeviceAsync(InputDevice):
    def __init__(self, config):
        super().__init__(config)
        self.initialized = False
        self.running = False
        self.thread = Thread(target=self.read_data_continuously)
        self.thread.daemon = True
        self.data = None

    def read_data_continuously(self):
        try:
            self.running = True
            while self.running:
                self.data = self.read_data()
                time.sleep(0.05)
        except Exception as e:
            self.logger.error("Async input device thread crashed: %s", e)

    @abstractmethod
    def read_data(self):
        """
        Implementation should return the array (of size get_data_size())
        with the data from the device
        """
        pass  # pragma: no cover

    def get_data(self):
        if not self.initialized:
            self.initialized = True
            self.thread.start()
            attempt_counter = 0
            while self.data is None and attempt_counter < 1000:
                time.sleep(0.05)
                attempt_counter += 1
        return self.data

    def deinit(self):
        if self.running:
            self.running = False
            self.thread.join()
