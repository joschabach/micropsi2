#include "omd/opto.h"

static OptoDAQ daq;
static OptoPorts ports;
static OptoPackage6D pack6D;

bool initialized = false;

extern "C" {
    struct ft;

    typedef struct ft {
        int fx;
        int fy;
        int fz;
        int tx;
        int ty;
        int tz;
    } ft;

    bool init();
    void fill_ft(ft *result);
    void shutdown();
}
