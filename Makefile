# convenience makefile to boostrap & run buildout

config = development.cfg
makes = https://raw.github.com/pyfidelity/makes/master/

all: tests



app: .installed.cfg

.installed.cfg:
	curl -s $(makes)/buildout | $(MAKE) -f- bootstrap_options=-d config=$(config)

tests: app
	bin/test

clean:
	rm -rf .installed.cfg .mr.developer.cfg buildout.cfg\
		bin downloads develop-eggs eggs fake-eggs parts
.PHONY: all  app tests clean
