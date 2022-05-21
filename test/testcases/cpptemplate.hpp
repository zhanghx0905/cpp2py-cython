template <typename T>
class A {
public:
    T a;
    A(T a)
        : a(a)
    {
    }
    T get()
    {
        return a;
    }
    template <typename V>
    T addOne(V t)
    {
        return t + T(1);
    }
};

template <typename T>
T minusOne(T t)
{
    return t - T(1);
}