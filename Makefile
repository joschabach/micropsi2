# convenience makefile to boostrap & run buildout

config = development.cfg

all: tests

app: .installed.cfg
	bin/buildout -c $(config)

.installed.cfg:
	python bootstrap.py -c $(config)

tests: app
	bin/test

clean:
	rm -rf .installed.cfg .mr.developer.cfg buildout.cfg\
		bin downloads develop-eggs eggs fake-eggs parts
.PHONY: all  app tests clean
