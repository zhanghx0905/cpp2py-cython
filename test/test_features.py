from tools import cpp2py_tester


@cpp2py_tester("namespaces.hpp")
def test_namespaces():
    from namespaces import ClassA, ClassB


@cpp2py_tester("constructorargs.hpp")
def test_constructor_args():
    from constructorargs import A

    a = A(11, 7)
    assert 18 == a.sum()


@cpp2py_tester("function.hpp")
def test_function():
    from function import fun1, fun2

    assert fun1(0) == 0
    assert fun2() == 1


@cpp2py_tester("mystruct.hpp")
def test_struct():
    from mystruct import A, B, print_mystruct_a, print_mystruct_b

    a = A()
    a.a = 5
    a.b = [1.0, 2.0]
    assert a.a == 5
    assert a.b == [1.0, 2.0]
    assert print_mystruct_a(a) == "a = 5, b[0] = 1, b[1] = 2, "
    b = B()
    b.a = 10
    assert b.a == 10
    assert print_mystruct_b(b) == "a = 10"


@cpp2py_tester("vectorofstruct.hpp")
def test_vector_of_struct():
    from vectorofstruct import MyStruct, sum_of_activated_entries

    def make_struct(value, active):
        res = MyStruct()
        res.value = value
        res.active = active
        return res

    a = make_struct(5, False)
    b = make_struct(10, True)
    entries = [a, b]
    assert sum_of_activated_entries(entries) == 10
    a.active = True
    assert sum_of_activated_entries(entries) == 15


@cpp2py_tester("cppoperators.hpp")
def test_operators():
    from cppoperators import Operators

    op = Operators()
    assert op(2) == 4
    assert op[2] == 2
    assert op + 1 == 6
    assert op - 1 == 4
    assert op * 2 == 10
    assert op / 5 == 1
    assert op % 2 == 1
    assert op and True == True
    op += 3
    assert op.v == 3
    op -= 1
    assert op.v == 2
    op *= 2
    assert op.v == 4
    op /= 4
    assert op.v == 1
    op %= 2
    assert op.v == 1
    op |= True
    assert op.b == True
    op &= True
    assert op.b == True


@cpp2py_tester("typedef.hpp")
def test_typedef():
    from typedef import fun, Student, Stu1

    assert fun(1.0) == 2.0
    stu = Student()
    stu.a = 10
    assert stu.a == 10
    stu = Stu1()
    stu.a = 10
    assert stu.a == 10


# FIXME
# @cpp2py_tester("complexfield.hpp")
# def test_complex_field():
#     from complexfield import A, B

#     a = A()
#     a.a = 5
#     b = B()
#     b.a = a
#     b.b = a
#     assert b.a.a == 5
#     assert b.b.a == 5


@cpp2py_tester("cppenum.hpp")
def test_enum():
    from cppenum import MyEnum, enum_to_string

    assert MyEnum.FIRSTOPTION != MyEnum.SECONDOPTION
    assert MyEnum.SECONDOPTION != MyEnum.THIRDOPTION
    assert enum_to_string(MyEnum.FIRSTOPTION) == "first"
    assert enum_to_string(MyEnum.SECONDOPTION) == "second"
    assert enum_to_string(MyEnum.THIRDOPTION) == "third"


@cpp2py_tester("enuminclass.hpp")
def test_enum_in_class():
    from enuminclass import MyEnum, MyEnumClass

    assert MyEnum.FIRSTOPTION != MyEnum.SECONDOPTION
    assert MyEnum.SECONDOPTION != MyEnum.THIRDOPTION
    assert MyEnumClass.enum_to_string(MyEnum.FIRSTOPTION) == "first"
    assert MyEnumClass.enum_to_string(MyEnum.SECONDOPTION) == "second"
    assert MyEnumClass().enum_to_string(MyEnum.THIRDOPTION) == "third"


@cpp2py_tester("staticmethod.hpp")
def test_static_method():
    from staticmethod import A, B

    assert A.plus1(1) == 2
    assert B.plus2(1) == 3


@cpp2py_tester("defaultvalues.hpp")
def test_defaultvalues():
    from defaultvalues import MyClassA

    a = MyClassA()
    assert a.mult() == 30
    assert a.mult(9) == 45
    assert a.mult_double() == -35.0
    assert a.half() == 5
    assert a.half(True) == 2
    assert a.append() == "abcdef"
    assert a.append("hello'") == "hello'def"
