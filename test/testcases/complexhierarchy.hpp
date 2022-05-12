/*
Base1 <---- Base2 <---- A
                  <---- B
*/
class Base1 {
public:
    int a;
    virtual ~Base1() { }
    virtual int base1Method() { return 1; }
};

class Base2 : public Base1 {
public:
    int b;
    virtual int base2Method() { return 2; };
};

class A : public Base2 {
public:
    int c;
    virtual int aMethod() { return 3; }
};

namespace NA {
class B : public Base2 {
public:
    int d;
    virtual int base1Method() { return 4; }

    virtual int bMethod() { return 5; }
};
}