Additional Features
-----
For some of the more advanced features of the Micropsi2 runtime, additional manual configuration is necessary.


Set up virtualenv
-----
Additional dependencies necessary for running the Toolkit with Minecraft connectivity or theano_engine node nets
require a working virtualenv on your machine.
To install virtualenv on OS X, you could:
* Install [homebrew](http://brew.sh/)
* Use homebrew to install python3 with pip3: `brew install python3`
* Use pip3 to install virtualenv: `pip3 install virtualenv`


Set up Minecraft connectivity
-----
* To run micropsi with minecraft connectivity, you need to call `make` after checkout and virtualenv setup


Set up Theano-based theano_engine
-----
* To run micropsi with an optional and experimental node net implementation based on Theano, you need to install Theano
* Call 'make' after checkout
* Call 'source bin/activate'
* Follow Theano's "bleeding edge install instructions" directions [here](http://deeplearning.net/software/theano/install.html)
* When creating a new node net, you should now be able to chose theano_engine


Configuration
-----
* See `config.ini.template` for configuration options available in `config.ini`


Tests
-----
* To run the tests type `make tests`
