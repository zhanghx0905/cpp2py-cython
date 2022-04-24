/* CE: C++ class must have a nullary constructor to be stack allocated */
class MyClassA
{
    MyClassA() {}
public:
    MyClassA(int a) {}
};


MyClassA factory()
{
    return MyClassA(5);
}
