struct A {
    int a;
    bool b;
};

void changeA(A& aobj)
{
    aobj.a += 100;
    aobj.b = !aobj.b;
}