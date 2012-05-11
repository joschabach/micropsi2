from pyramid.view import view_config
from kotti import base_configure

@view_config(route_name="nodenet", renderer='micropsi_server:templates/nodespaceviewer.pt')
def start(request):
    return dict(title='Hallo, Sie sehen gut aus heute!')


def main(global_config, **settings):
    """ Configure and create the main application. """
    config = base_configure(global_config, **settings)
    config.add_static_view('static', 'micropsi_server:static')
    config.add_route('nodenet', '/nodenet')
    config.scan()
    return config.make_wsgi_app()
