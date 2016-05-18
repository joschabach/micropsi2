# V-REP interface

vrep_world.py provides an interface to the Virtual Robot Experimentation platform (V-REP) by Coppelia Robotics GmbH.
V-REP is free for academic use.

To create a V-REP world in the toolkit, please:

- download and install V-REP from http://www.coppeliarobotics.com/downloads.html
- get the vrep.py and vrepConst.py files from the V-REP folder, in programming/remoteApiBindings/python/python, and add them to your virtualenv
- get the dylib/dll/so file for your platform from the V-REP folder, the file should be in programming/remoteApiBindings/lib/lib, and put it next to vrep.py
- make sure your firewalls aren't blocking local connections to port 19999
 

    portNumber = 19999
    status, info, serverVersion, clientVersion, clientIp=simExtRemoteApiStatus(portNumber)
    if status < 0 then
        simExtRemoteApiStart(portNumber)
    end

When instatiating the V-REP world in the toolkit, you will be able to specify the name of the robot that will
be controlled.

If a camera called "Observer" is present in the V-REP scene, pixel data will be provided to connected node nets.
