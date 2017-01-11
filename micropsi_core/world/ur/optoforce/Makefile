liboptoforce.so: optoforce.cpp
	$(CXX) -std=c++11 -Iinclude -fPIC -c optoforce.cpp -o optoforce.o
	$(CXX) -shared -Wl,-soname,liboptoforce.so -Wl,-rpath,./micropsi_core/world/ur/optoforce/lib/ -Wl,--no-as-needed -o liboptoforce.so -Llib -lOMD optoforce.o

clean:
	rm *.o *.so
