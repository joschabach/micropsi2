from threading import Thread
import time
from micropsi_server.mesh_ipy import IPythonConnection
ipython_client = IPythonConnection()


def no_exit(code):
    pass


def mesh_startup(port=7543, start_runtime=True):

    import sys
    sys.exit = no_exit

    runtime_thread = None

    if start_runtime:
        def micropsi_runtime_main():
            import micropsi_server.micropsi_app
            micropsi_server.micropsi_app.main(None, port)

        runtime_thread = Thread(target=micropsi_runtime_main)
        runtime_thread.start()

    ipython_client.ipy_connect(["--existing"])

    if runtime_thread is not None:
        runtime_thread.join()
    else:
        while ipython_client is not None:
            time.sleep(0.1)


def request_termination():
    global ipython_client
    ipython_client = None
