// By-value return from a class with a private default constructor.
class MyClassA {
    MyClassA() { }

public:
    MyClassA(int a) { }
};

MyClassA factory() { return MyClassA(5); }
