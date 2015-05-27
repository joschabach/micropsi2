# Makefile

venv: pip requirements.txt
	test -d bin || virtualenv ./ --python=python3
	bin/pip install -Ur requirements.txt

pip:
	virtualenv --version >/dev/null || pip install virtualenv

run:
	./run.sh

all:
	venv pip

clean:
	rm -rf include lib .Python bin

tests:
	bin/py.test

test-coverage:
	bin/py.test --cov micropsi_core --cov micropsi_server --cov-report html

.PHONY: run