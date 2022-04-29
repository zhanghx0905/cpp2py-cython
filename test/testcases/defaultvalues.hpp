#include <string>

class MyClassA {
    int i;

public:
    MyClassA(int i = 5u)
        : i(i)
    {
    }
    int mult(int j = 6ull) { return i * j; }
    double multDouble(double d = -7.0) { return (double)i * d; }
    int half(bool b = false)
    {
        if (b)
            return i / 2;
        else
            return i;
    }
    std::string append(std::string s = "abc") { return s + "def"; }
    // Unsupported: nullptr
    int divide(int* c = nullptr)
    {
        if (c == nullptr) {
            return -1;
        }
        return i / *c;
    }
};