Additional Features
-----
For some of the more advanced features of the Micropsi2 runtime, additional manual configuration is necessary.
Support for the advanced features on Windows is experimental, see below.


OS X: Set up virtualenv
-----
Additional dependencies necessary for running the Toolkit with Minecraft connectivity or flow-engine support
require a working virtualenv on your machine.
To install virtualenv on OS X, you could:
* Install [homebrew](http://brew.sh/)
* Use homebrew to install python3 with pip3: `brew install python3`
* Use pip3 to install virtualenv: `pip3 install virtualenv`


OS X: Set up Minecraft connectivity
-----
* To run micropsi with minecraft connectivity, you need to call `make` after checkout and virtualenv setup


OS X: Set up flow-engine
-----
* To run micropsi with an optional flow engine implementation based on numpy and tensorflow, you need to install additional dependencies
* Call 'make' after checkout
* Call 'source bin/activate'
* When creating a new node net, you should now be able to chose the numpy engine that support flow nodes


Windows: Set up flow engine and Minecraft connectivity with winpython
-----
Windows support for advanced features is experimental.
* Install [WinPython 3.4.3.7](http://winpython.github.io/)
* From the installed folder, add the folders `python-3.4.3` and `python-3.4.3\Scripts` to your PATH environment variable
* Install GCC and C/C++ compilers via [mingw](mingw-w64.org)
* From the mingw Folder, add the `bin` Folder to your PATH environment variable
* Install pycrypto for python3.4. Get one of the [pycrypto windows binaries](https://github.com/axper/python3-pycrypto-windows-installer), open the WinPython Control Panel, click "Add Packages", select the downloaded pycrypto installer, and click "Install packages"
* now you can install our modified spock via
`pip install -e git+https://github.com/micropsi-industries/spock.git#egg=spock-dev`
* this should lead to a working MicroPsi with flow engine and minecraft support.
* install the optional packages with `pip install cherrypy pytest mock webtest`
* run `python start_micropsi_server.py`


Configuration
-----
* See `config.default.ini` for configuration options.
* Copy `config.default.ini` to `config.ini` to customize.


Tests
-----
* To run the tests type `make tests`
