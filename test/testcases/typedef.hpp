typedef double mytype;

typedef struct Student{
    int a;
} Stu;

typedef struct{
    int a;
} Stu1;

typedef Stu Stu2;

mytype fun(mytype d)
{
    return d + 1.0;
}