#include "optoforce.h"
#include <unistd.h>

bool init() {
    OPort* portlist = ports.listPorts(true);

    if (ports.getLastSize() > 0) {
        daq.open(portlist[0]);

        SensorConfig sensorConfig;
        sensorConfig.setSpeed(1000);
        sensorConfig.setFilter(15);

        bool success = false;
        int attempts = 0;
        do {
            success = daq.sendConfig(sensorConfig);
            if (success) {
                 initialized = true;
                 return true;
             }
             attempts++;
             usleep(1000);
        } while (attempts < 10);

        return false;
    } else {
        return false;
    }
}

void shutdown() {
    daq.close();
    initialized = false;
}

void fill_ft(ft *result) {

    if(!initialized) {
        return;
    }

    daq.read6D(pack6D, false);
        
    result->fx = pack6D.Fx;
    result->fy = pack6D.Fy;
    result->fz = pack6D.Fz;
    result->tx = pack6D.Tx;
    result->ty = pack6D.Ty;
    result->tz = pack6D.Tz;
        
}


