about Minecraft world
-----
Refresh-rate of the 3d visualization is directly bound to the world update cycle. Set it to somewhere below 110ms to get a smooth visualization. *

ReadMe for Running a Minecraft experiment under OS X (other OSes should also be fine, just make sure to install latest pylget (from repo) and pycrypto)

1. install http://brew.sh/

2. brew install python3

2.5. brew install mercurial *

[3. pip3 install pycrypto (might not be necessary anymore because new makefile installs it)]

4. pip3 install hg+https://pyglet.googlecode.com/hg/ (only for visualisation branch) *

5. git clone https://github.com/joschabach/micropsi2/

5.5. make

6. git clone https://github.com/jonasrk/minecraft_servers

7. git clone https://github.com/jonasrk/MicroPsi-2-Minecraft-Experiment [outdated!]

8. edit config.ini in a way, that it points to the data directory from point 7

9. Server: ./minecraft-servers/1.7.4/start_command

10. Micropsi ./run.sh

11. http://localhost:6543/ (you may need to login as admin/admin)

12. Select Minecraft World and Nodenet

13. Press "Play" next to the world. (Wait until you see something. *)

14. Press "Play" next to the nodenet. The minecraft bot will hopefully move.


* Only needed for visualisation which is not part of the current master.