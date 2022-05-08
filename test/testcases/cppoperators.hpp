class Operators {
public:
    int v;
    bool b;

    Operators()
        : v(0)
        , b(false)
    {
    }

    int operator()(int a) { return 2 * a; }

    int operator[](int a) { return a; }

    int operator+(int a) { return 5 + a; }

    int operator-(int a) { return 5 - a; }

    int operator*(int a) { return 5 * a; }

    int operator/(int a) { return 5 / a; }

    int operator%(int a) { return 5 % a; }

    int operator&(int a) { return v & a; }

    int operator|(int a) { return v | a; }
    int operator~() { return ~v; }
    bool operator<(int a) { return v < a; }
    bool operator>(int a) { return v > a; }
    Operators& operator+=(int a)
    {
        v += a;
        return *this;
    }

    Operators& operator-=(int a)
    {
        v -= a;
        return *this;
    }

    Operators& operator*=(int a)
    {
        v *= a;
        return *this;
    }

    Operators& operator/=(int a)
    {
        v /= a;
        return *this;
    }

    Operators& operator%=(int a)
    {
        v %= a;
        return *this;
    }

    Operators& operator&=(int b)
    {
        this->v &= b;
        return *this;
    }

    Operators& operator|=(int b)
    {
        this->v |= b;
        return *this;
    }
};
