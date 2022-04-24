import pytest
from tools import cpp2py_tester


@cpp2py_tester("subclass.hpp")
def test_ambiguous_method():
    from subclass import A, B

    a = A()
    assert a.afun() == 1
    b = B()
    assert b.afun() == 1
    assert b.bfun() == 2


@cpp2py_tester("complexhierarchy.hpp")
def test_complex_hierarchy():
    from complexhierarchy import A, B

    a = A()
    assert a.base1_method() == 1
    assert a.base2_method() == 2
    assert a.a_method() == 3
    b = B()
    assert b.base1_method() == 4
    assert b.base2_method() == 2
    assert b.b_method() == 5


@cpp2py_tester("inheritancewithnamespace.hpp")
def test_inheritance_with_namespace():
    from inheritancewithnamespace import ClassA, ClassB

    a = ClassA()
    assert a.method_a() == 1
    b = ClassB()
    assert b.method_a() == 1
    assert b.method_b() == 2


@cpp2py_tester("inheritancefromexternal.hpp")
def test_inheritance_from_external_header():
    from inheritancefromexternal import MyString

    s = MyString()
    assert s.myfun() == 13
