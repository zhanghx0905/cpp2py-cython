class AbstractClass {
protected:
    AbstractClass() { }

public:
    virtual ~AbstractClass() { }
    virtual double square() = 0;
    virtual AbstractClass* clone() = 0;
};

class DerivedClass : public AbstractClass {
    double d;
    int a;

public:
    DerivedClass(double d, int a = -1)
        : d(d)
        , a(a)
    {
    }

    virtual double square() { return d * d; }
    virtual double product() { return a * d; }

    virtual AbstractClass* clone() { return new DerivedClass(d); }
};
