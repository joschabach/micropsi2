"""
World adapters provide an interface between agents (which are implemented in node nets) and environments,
such as the MicroPsi world simulator.

The type of an agent is characterized by its world adapter.
At each agent cycle, the activity of this actor nodes are written to data targets within the world adapter,
and the activity of sensor nodes is determined by the values exposed in its data sources.
At each world cycle, the value of the data targets is translated into operations performed upon the world,
and the value of the data sources is updated according to sensory data derived from the world.

Note that agent and world do not need to be synchronized, so agents will have to be robust against time lags
between actions and sensory confirmation (among other things).

During the initialization of the world adapter, it might want to register an agent body object within the
world simulation (for robotic bodies, the equivalent might consist in powering up/setup/boot operations.
Thus, world adapters should usually be imported by the world, inherit from a moving object class of some kind
and treated as parts of the world.
"""

__author__ = 'joscha'
__date__ = '10.05.12'

