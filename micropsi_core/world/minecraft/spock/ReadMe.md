Based on NickelPros Python Bot Framework for Minecraft. I added a webinteface.

Usage

1. Start Minecraft 1.5.2 server (online-mode: False) on localhost:25565

2. Launch (python3) demo.py . The bot will connect to the Minecraft server.

3. Launch (python3) psicraft/psicraft.py . The webserver will start.

4. In your browser go to localhost:8080/bot .

5. Play around with x+, x-, z+, z-, draw chunk, draw chunk continously and stop drawing chunk continously .

6. To properly shut down the bot, press "kill bot"-button on the webinterface.

If bot was not killed via the "kill"-button of the webinterface, the port will usually not close. To workaround the "address in use" bug, change the global port variables in psicraft.py and client.py .

NOTE: If you run psicraft.py from the commandline you need to actually start it from INSIDE the psicraft folder. Otherwise bottle won't find the .tpl file.
