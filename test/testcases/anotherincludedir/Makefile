CXX := c++
LIBNAME := libmylib.so

$(LIBNAME): somefunction.cpp somefunction.hpp
	$(CXX) somefunction.cpp -fPIC -shared -o $(LIBNAME)

clean:
	rm $(LIBNAME)
