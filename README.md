About
-----
A Python implementation of the cognitive architecture MicroPsi.

For more information visit [micropsi.com](http://www.micropsi.com), for instance, the [publications ](http://www.micropsi.com/publications/publications.html) page. For a one-paper introduction see [The AEP Toolkit for Agent Design and Simulation](http://www.micropsi.com/publications/assets/BachVuineMates2003.pdf)


Prerequisites
-----
* Python3


Run
-----
* To run the micropsi toolkit, copy `config.ini.template` to `config.ini` and adjust to your preferences
* Run `./run.sh`
* View in browser at [http://localhost:6543/](http://localhost:6543/)


Run with Minecraft
-----
* To run micropsi with minecraft connectivity, you need to call `make` after checkout, and then follow the steps described above
(Minecraft connectivtiy has an additional dependency on pycrypto)
* Also see [micropsi_core/world/minecraft/README.md](/micropsi_core/world/minecraft/README.md) for setup instructions.


Tests
-----
* To run the tests type `make tests`


Attribution
-----
[micropsi2](https://github.com/joschabach/micropsi2) uses 

* [bottle](https://github.com/defnull/bottle)
* [spock](https://github.com/nickelpro/spock)
* [paperjs](http://github.com/paperjs/paper.js)
* [three.js](https://github.com/mrdoob/three.js)
