from micropsi_server.mesh_ipy import IPythonConnection
ipython_client = IPythonConnection()


def no_exit(code):
    pass


def mesh_startup(port=7543, start_runtime=True):

    import sys
    sys.exit = no_exit

    import threading
    from threading import Thread
    main_thread = threading.current_thread()

    if start_runtime:
        def micropsi_runtime_main():
            import micropsi_server.micropsi_app
            micropsi_server.micropsi_app.main(None, port)

        main_thread = Thread(target=micropsi_runtime_main)
        main_thread.start()

    ipython_client.ipy_connect(["--existing"])
    #c.ipy_run(["print(\"Runtime is: \"+runtime.runtime_info())"])

    if main_thread != threading.current_thread():
        main_thread.join()
