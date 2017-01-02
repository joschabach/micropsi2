#include <omd/optopackage.h>
#ifndef OPTOPACKAGE6D_H
#define OPTOPACKAGE6D_H 
struct OptoPackage6D
{
int Fx;
int Fy;
int Fz;
int Tx;
int Ty;
int Tz;
OptoPackage Sensor1;
OptoPackage Sensor2;
OptoPackage Sensor3;
OptoPackage Sensor4;
OptoPackage6D();
~OptoPackage6D();
void setInvariant(const OptoPackage6D& offset);
const OptoPackage6D& operator= (int pack);
const OptoPackage6D& operator= (const OptoPackage6D& pack);
OptoPackage6D operator+(const OptoPackage6D& pack);
OptoPackage6D operator-(const OptoPackage6D& pack);
OptoPackage6D operator-(int value);
OptoPackage6D operator*=(const OptoPackage6D& pack);
OptoPackage6D operator/=(const int num);
OptoPackage6D operator/=(const OptoPackage6D& pack);
};
#endif
