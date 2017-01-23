#ifndef OMD__SENSORCONFIG_H
#define OMD__SENSORCONFIG_H 
#include <stdint.h>
enum sensor_state:unsigned int { no_sensor = 0, overload_x, overload_y, overload_z, sensor_failure, sensor_ok, conn_faliure };
enum sensor_speed:unsigned int { speed_1000hz = 0, speed_333hz, speed_100hz, speed_30hz };
enum sensor_filter:unsigned int { no_filter = 0, filter_150hz, filter_50hz, filter_15hz };
enum sensor_mode:unsigned int { mode_raw = 0, mode_comp };
struct SensorConfig {
    sensor_mode mode: 1;
    sensor_filter filter: 2;
    sensor_speed speed: 2;
    sensor_state state: 3;
    SensorConfig (sensor_state st, sensor_speed sp, sensor_filter ft, sensor_mode rf);
    SensorConfig ();
    void set(sensor_state st, sensor_speed sp, sensor_filter ft, sensor_mode rf);
    SensorConfig null_sensor();
    static SensorConfig from_uint8_t (uint8_t c) {
        int i = c;
        return * (SensorConfig*) (&i);
    }
    static uint8_t to_uin8_t (SensorConfig c) {
        return *(uint8_t*)(&c);
    }
    uint8_t to_uin8_t () const;
    int getState ();
    int getSpeed ();
    int getFilter ();
    int getMode ();
    void setSpeed(int sp);
    void setFilter(int ft);
    void setMode(int md);
};
#endif
