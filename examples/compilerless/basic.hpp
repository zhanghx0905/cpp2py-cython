// This header deliberately uses no C++ standard-library or platform SDK headers.
namespace sample {
struct Point {
    int x;
    int y;
    Point(int x = 0, int y = 0) : x(x), y(y) {}
};

int add(int a, int b) { return a + b; }
Point make_point(int x, int y) { return Point(x, y); }
}
