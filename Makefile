# Makefile

venv: bin/activate

bin/activate: requirements.txt
	test -d bin || virtualenv ./ --python=python3
	. bin/activate; pip3 install -Ur requirements.txt
	touch bin/activate

