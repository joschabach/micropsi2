# Makefile

venv: pip requirements.txt
	test -d bin || virtualenv ./ --python=python3
	source bin/activate; pip install -Ur requirements.txt
	touch bin/activate

pip:
	virtualenv --version >/dev/null || pip install virtualenv

run:
	./run.sh

all:
	venv pip

clean:
	rm -rf include lib .Python bin

tests:
	source bin/activate
	bin/py.test micropsi_server
	bin/py.test micropsi_core

.PHONY: run