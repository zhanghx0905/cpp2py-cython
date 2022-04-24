#include <string>
#include <map>
// #include <unordered_map>
// #include <set>
// #include <unordered_set>
// #include <utility>
// #include <deque>
// #include <queue>
// #include <stack>
// #include <forward_list>
// #include <list>
// #include <complex>

// struct A
// {
//     std::map<std::string, int> m;
//     std::unordered_map<std::string, double> um;
//     std::set<std::pair<int, int>> s;
//     std::unordered_set<bool> usp;
//     std::list<std::string> l;
//     std::complex<double> c;
// };

// int func1(int a[5]) {
//     return a[3];
// }
int lookup(std::map<std::string, int>& m)
{
    return m["test"];
}