#ifndef OMD__OPTOPORTS_H
#define OMD__OPTOPORTS_H 
#include <stddef.h>
#include <stdlib.h>
class OptoPorts_private;
struct OPort
{
    char name[25];
    char deviceName[25];
    char serialNumber[25];
    OPort();
    ~OPort();
};
class OptoPorts
{
    OptoPorts_private *d_ptr;
public:
    OptoPorts(int filterType=0, int baudRate=1000000);
    ~OptoPorts();
    OPort* listPorts(bool connectFilter);
    int getSize(bool connectFilter);
    int getLastSize();
    bool isNewPort(bool connectFilter);
    bool isLostPort(bool connectFilter);
    OPort getNewPort();
    OPort getLostPort();
    const char * getAPIversion();
};
#endif
