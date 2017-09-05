
def no_exit(code):
    pass


def mesh_startup(port=7543):

    import sys
    sys.exit = no_exit

    import micropsi_server.micropsi_app
    micropsi_server.micropsi_app.main(None, port)
