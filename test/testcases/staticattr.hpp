class A {
public:
    static int count;
    static int getCount() { return count; }
};

int A::count = 0;

namespace MyNamespace {

class B {
public:
    static int plus2(int a) { return a + 2; }
};

} // namespace MyNamespace
