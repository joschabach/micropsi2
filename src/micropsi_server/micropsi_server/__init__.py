from pyramid.config import Configurator
from pyramid.response import Response


def hello(request):
    return Response('Hallo, Sie sehen gut aus heute!')


def main(global_config, **settings):
    """ Configure and create the main application. """
    config = Configurator(settings=settings)
    config.add_route('hello', '/')
    config.add_view(hello, route_name='hello')
    return config.make_wsgi_app()
