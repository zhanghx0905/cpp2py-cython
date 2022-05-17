namespace foo {
int fact(int n)
{
    int prod = 1;
    for (int i = 2; i <= n; i++) {
        prod *= i;
    }
    return prod;
};
namespace A::B {
    struct Vector {
        double x, y, z;
    };
};
};