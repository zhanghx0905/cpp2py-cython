#include <map>
#include <sstream>
#include <string>
#include <vector>

class A {
public:
    bool neg(bool b) { return !b; }

    double plus2(double d) { return d + 2.0; }

    double norm(double* vec, unsigned size)
    {
        double norm = 0.0;
        for (unsigned i = 0; i < size; i++)
            norm += vec[i] * vec[i];
        return norm;
    }

    std::string end(const std::string& s) { return s + "."; }

    std::string concat(const std::vector<std::string>& substrings)
    {
        std::stringstream ss;
        for (unsigned i = 0; i < substrings.size(); i++)
            ss << substrings[i];
        return ss.str();
    }
};

int fun1(int* i) { return *i + 1; }

int length(char const* const input)
{
    int i = 0;
    while (input[i] != 0)
        i++;
    return i;
}

char const* helloworld() { return "hello world"; }

int lookup(std::map<std::string, int>& m) { return m["test"]; }