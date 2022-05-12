/*
A <--- B   <--- D
  <--- C   <---
*/

class A {
public:
    A(int a)
        : m_a(a)
    {
    }
    int getMa() { return m_a; }
    int m_a;
};
class B : virtual public A {
public:
    B(int a, int b)
        : A(a)
        , m_b(b)
    {
    }
    int m_b;
};
class C : virtual public A {
public:
    C(int a, int c)
        : A(a)
        , m_c(c)
    {
    }
    int m_c;
};
class D : virtual public B, virtual public C {
public:
    D(int a, int b, int c, int d)
        : A(a)
        , B(a, b)
        , C(a, c)
        , m_d(d)
    {
    }
    int func()
    {
        return getMa();
    }
    int m_d;
};