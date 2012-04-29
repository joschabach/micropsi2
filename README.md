install 
-----
( s.a. docs/installation.rst )

	python2.7 bootstrap.py -c development.cfg
	bin/buildout -c development.cfg

run 
-----

	./bin/pserve ./etc/micropsi_server.ini
	view in browser at http://0.0.0.0:6543/
