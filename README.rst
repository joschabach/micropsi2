about
=====

a Python version of the cognitive architecture MicroPsi

run 
===

For development, just use the hardcoded runtime::

	./start_micropsi_server.py
	view in browser at http://localhost:6543/


For deployment, use the Makefile::

    make

then start supervisord::

    bin/supervisord


History
=======

1.2 - 2013-01-17
================

 * First public release on EC2
