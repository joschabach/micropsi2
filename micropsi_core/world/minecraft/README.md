about Minecraft world
-----
Refresh-rate of the 3d visualization is directly bound to the world update cycle. Set it to somewhere below 110ms to get a smooth visualization. *

ReadMe for Running a Minecraft experiment under OS X (other OSes should also be fine, just make sure to install latest pylget (from repo) and pycrypto)

1. install http://brew.sh/

2. brew install python3

2.5.* brew install mercurial

[3. pip3 install pycrypto (might not be necessary anymore because new makefile installs it)]

4. pip3 install hg+https://pyglet.googlecode.com/hg/ (only for visualisation branch) *

5. git clone https://github.com/joschabach/micropsi2/

5.5. make

6. git clone https://github.com/jonasrk/minecraft_servers

7. git clone https://github.com/jonasrk/MicroPsi-2-Minecraft-Experiment [outdated!]

8. edit config.ini in a way, that it points to the data directory from point 7

9. Server: ./minecraft_servers/1.7.4/start.command

10. Micropsi ./run.sh

11. http://localhost:6543/ (you may need to login as admin/admin)

12. Select Minecraft World and Nodenet

13. Press "Play" next to the world. (Wait until you see something. *)

14. Press "Play" next to the nodenet. The minecraft bot will hopefully move.


\* Only needed for visualisation which is not part of the current master.



# Known working Minecraft experiments:
## With Pyglet Visualisation, 1.5.2 Server, Diamond finding experiment

* https://github.com/joschabach/micropsi2/tree/minecraft_with_visualisation

commit b62a506dc42dafc8bb661e5af59073833eaa4cc8

* https://github.com/jonasrk/minecraft_servers

commit 75e2cf65ba38efce8b8328106201df94a9e1a3ae
cd 'minecraft server 1.5.2'; ./start.command

* https://github.com/jonasrk/MicroPsi-2-Minecraft-Experiment

commit 21e114f72364bfd4818debf1be28959b6424255a
./micropsi2_data


## Without Visualisation, 1.7.4 Server, Diamond finding experiment with jumping and gravity

* https://github.com/joschabach/micropsi2/tree/master

commit 0bf90d110ab24f22ccb07dc938cec6484475ac81

* https://github.com/jonasrk/minecraft_servers

commit e3c7ea937e027f1d87d5036ef07a3e73124fd8e8
cd 1.7.4; ./start.command

* https://github.com/jonasrk/MicroPsi-2-Minecraft-Experiment
commit 9d7cb90f7420850afe13735e094501b9b72830a5
./micropsi2_data/micropsi2_data_for_new_spock

## Without Visualisation, 1.7.4 Server, Ground Types experiment with jumping and gravity

* https://github.com/joschabach/micropsi2/tree/master

commit ae8d9a378aa6a927ac923db2c0fca8267262da1c

* https://github.com/jonasrk/minecraft_servers

commit 53ac1b904e0ac7f85a36ef97f19123c1bc9159ed
cd 1.7.4; ./start.command

* https://github.com/jonasrk/MicroPsi-2-Minecraft-Experiment
commit cc98943adbf3e82b99899e8ed6d3f2cbfb925993
./micropsi2_data/micropsi2_data_for_new_spock

## Without Visualisation, 1.7.4 Server, Obstacle experiment with jumping and gravity

* https://github.com/joschabach/micropsi2/tree/master

commit 88ce9c205451b2dffb39a156fbbd305719c0f3f6

* https://github.com/jonasrk/minecraft_servers

commit 268f9621bcfa95304600ed6fcbffb57674e0d153
cd 1.7.4; ./start.command

* https://github.com/jonasrk/MicroPsi-2-Minecraft-Experiment
commit 1fad259cd1043983f4af8c3facd9730d1d7603dd
./micropsi2_data/micropsi2_data_for_new_spock
