To make regular, non-root users see the sensors, perform:

sudo chmod 666 /dev/ttyACM0

and create a file /etc/udev/rules.d/10-local.rules with the following content:

SUBSYSTEMS=="usb", ATTRS{product}=="OptoForce DAQ", GROUP="ftsensing"

Then add the user you want to run the MicroPsi runtime as to the group ftsensing.
