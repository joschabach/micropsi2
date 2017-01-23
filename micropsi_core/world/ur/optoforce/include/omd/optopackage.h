#ifndef OMD__OPTOPACKAGE_H
#define OMD__OPTOPACKAGE_H 
#include <stdint.h>
#include "omd/sensorconfig.h"
#include <stddef.h>
#include <stdlib.h>
enum opto_version {
    undefined_version = 0, _66, _67, _68, _94, _95, _31, _34, _64
};
struct OptoPackage {
  int s1;
  int s2;
  int s3;
  int s4;
  int s1c;
  int s2c;
  int s3c;
  int s4c;
  int x;
  int y;
  int z;
  int xc;
  int yc;
  int zc;
  int is1;
  int is2;
  int is3;
  int is4;
  int is1c;
  int is2c;
  int is3c;
  int is4c;
  int temp;
  SensorConfig config;
  int vs;
  OptoPackage ();
  ~OptoPackage();
  OptoPackage (opto_version v);
  bool isCorrect ();
  bool isRaw();
  void setInvariant();
  void saveInconsistent();
  void saveAsInconsistent();
  void setInvariant(const OptoPackage& offset);
  const OptoPackage& operator= (int pack);
  OptoPackage operator+(const OptoPackage& pack);
  OptoPackage operator-(const OptoPackage& pack);
  OptoPackage operator-(int value);
  OptoPackage operator*=(const OptoPackage& pack);
  OptoPackage operator/=(const int num);
  OptoPackage operator/=(const OptoPackage& pack);
};
#endif
