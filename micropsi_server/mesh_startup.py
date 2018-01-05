import os
import time

from micropsi_server.mesh_ipy import IPythonConnection
ipython_client = IPythonConnection()
console_termination_requested = False


def no_exit(code):
    pass


def start_runtime_and_console(port=7543):
    import micropsi_server
    import micropsi_server.micropsi_app
    import sys

    sys.exit = no_exit

    # make sure we have a kernel dir to write to
    import jupyter_core
    kernel_dir = jupyter_core.paths.jupyter_path('kernels')[0]
    if not os.path.isdir(kernel_dir):
        print("Creating IPython kernel dir: %s" % kernel_dir)
        try:
            os.makedirs(kernel_dir)
        except Exception as e:
            print(e)
            print("Cannot create IPython kernel dir, IPython console may not be available.")

    def client_daemon():
        while micropsi_server.micropsi_app.get_console_info() is None and console_termination_requested is False:
            time.sleep(0.1)

        if console_termination_requested:
            return

        ipython_client.ipy_connect(["--existing"])

    # Disable IPython client for now, does not start, find out if there's a way around that
    # ipython_client_thread = Thread(target=client_daemon)
    # ipython_client_thread.start()

    micropsi_server.micropsi_app.main(None, port, console=True)


def start_console(kernel_info=None):
    import tempfile
    import json

    if kernel_info is None:
        ipython_client.set_connection_args(["--existing"])
        while console_termination_requested is False:
            time.sleep(0.1)
    else:
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            temp.write(json.dumps(kernel_info).encode())
            temp.flush()
        ipython_client.set_connection_args(["--existing", temp.name])

        while console_termination_requested is False:
            time.sleep(0.1)


def request_termination():
    global console_termination_requested
    console_termination_requested = True
