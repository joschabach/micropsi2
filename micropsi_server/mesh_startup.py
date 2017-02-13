
def no_exit(code):
    pass


def mesh_startup(port=7543):

    import sys
    from os import walk

    path = sys.path.copy()
    for p in path:
        for root,dirs,files in walk(p):
            if p is not root:
                sys.path.append(root)

    sys.exit = no_exit

    import micropsi_server.micropsi_app

    micropsi_server.micropsi_app.main(None, port)