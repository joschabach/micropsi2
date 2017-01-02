liboptoforce.so: optoforce.cpp
	$(CXX) -std=c++11 -Iinclude -fPIC -c optoforce.cpp -o optoforce.o
	$(CXX) -shared -Wl,-soname,liboptoforce.so -Wl,--no-as-needed -Wl,-rpath,lib -o liboptoforce.so -Llib -lOMD optoforce.o

clean:
	rm *.o *.so
