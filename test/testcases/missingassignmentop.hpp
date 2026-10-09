class MyClassA {
    void operator=(const MyClassA& other) { }

public:
    int value;
    MyClassA(int n = 0) : value(n) { }
};

MyClassA factory() { return MyClassA(5); }
