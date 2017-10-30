from micropsi_core.device.device import InputDevice


class Camera(InputDevice):
    def __init__(self, config):
        super().__init__(config)

    @classmethod
    def get_options(cls):
        options = super().get_options()
        options.extend([{
                        'name': 'mode',
                        'description': 'Image acquisition mode',
                        'default': 'color',
                        'options': ['mono', 'color', 'color/depth']},
                        {
                        'name': 'exposure',
                        'description': 'exposure time in microseconds',
                        'default': '5000'},
                        {
                        'name': 'xres',
                        'description': 'horizontal resolution',
                        'default': 'max'},
                        {
                        'name': 'yres',
                        'description': 'vertical resolution',
                        'default': 'max'}, ])
        return options
