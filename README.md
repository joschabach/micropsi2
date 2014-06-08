about
-----
a Python implementation of the cognitive architecture MicroPsi.
For more information visit [micropsi.com](http://www.micropsi.com).


run
-----
* to start the micropsi runtime, copy `config.ini.template` to `config.ini` and adjust to your preferences
* run `./start_micropsi_server.py`
* view in browser at [http://localhost:6543/](http://localhost:6543/)

Minecraft connectivtiy has an additional dependency on pycrypto. See [micropsi_core/world/minecraft/README.md](/micropsi_core/world/minecraft/README.md) for
information on setting up minecraft connectivity.


attribution
-----
Python MicroPsi uses [spock](https://github.com/nickelpro/spock) for minecraft connectivity.