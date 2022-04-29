class A {
public:
    void add_one(void* a)
    {
        long* ptr = (long*)a;
        *ptr += 1;
    }
};