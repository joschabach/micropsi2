about
-----
a Python implementation of the cognitive architecture MicroPsi.

For more information visit [micropsi.com](http://www.micropsi.com).


run
-----
* To just run the micropsi toolkit, copy `config.ini.template` to `config.ini` and adjust to your preferences
* run `./run.sh`
* view in browser at [http://localhost:6543/](http://localhost:6543/)


run with optional dependencies
-----
* To run micropsi with minecraft connectivity, you need to call `make` after checkout, and then follow the steps described above
(Minecraft connectivtiy has an additional dependency on pycrypto)
* Also see [micropsi_core/world/minecraft/README.md](/micropsi_core/world/minecraft/README.md) for setup instructions.


tests
-----
* to run the tests simply type `make tests`


attribution
-----
Python MicroPsi uses 

* [bottle](https://github.com/defnull/bottle)
* [spock](https://github.com/nickelpro/spock)
* [paperjs](http://github.com/paperjs/paper.js)