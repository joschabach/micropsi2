from abc import ABCMeta, abstractmethod


class Device(metaclass=ABCMeta):
    """
    The Device abstract base class. Do not inherit from this class immediately,
    instead use one of the subclasses (InputDevice and OutputDevice),
    that further specify the direction of the data flow
    """
    def __init__(self, config):
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
        info['type'] = self.__class__.__name__
        info['config'] = config
        info['prefix'] = self.get_prefix()
        return info

    def set_config(self, config):
        for key in config:
            setattr(self, key, config[key])

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


class InputDevice(Device):
    def __init__(self, config):
        super().__init__(config)

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

    @abstractmethod
    def write_data(self, data):
        """
        Implementation should accept the array (of size get_data_size())
        with the data sent to the device
        """
        pass  # pragma: no cover
