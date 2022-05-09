
#include <stdio.h>
// A normal function with an int parameter
// and void return type
void fun(int a, int (*bfun)(int, int))
{
    printf("Value of a is %d\n", a);
    printf("Result of bfun(1, 2) %d\n", bfun(1, 2));
}

int add(int a, int b)
{
    return a + b;
}

int (*bfun)(int, int) = &add;

struct A {
    void (*error_handler)(int status, const char* file,
        int line, const char* message);
};
