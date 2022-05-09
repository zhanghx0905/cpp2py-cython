import numpy as np
import pytest
from cpp2py import Config, VoidPtrConverter

from tools import cpp2py_tester


@cpp2py_tester(["deppart1.hpp", "deppart2.hpp"], modulename="depcombined")
def test_dependent_parts():
    from depcombined import A

    a = A()
    b = a.make()
    assert b.get_value() == 5


def test_voidptr():
    class LongConverter(VoidPtrConverter):
        def real_type(self) -> str:
            return "long"

    @cpp2py_tester("voidptr.hpp", config=Config(registered_converters=[LongConverter]))
    def run():
        from voidptr import A

        arr = np.array([2], dtype=np.int64)
        A().add_one(arr)
        assert arr[0] == 3

    run()


@cpp2py_tester("abstractclass.hpp")
def test_abstract_class():
    from abstractclass import AbstractClass, DerivedClass

    with pytest.raises(TypeError):
        AbstractClass()
    d = DerivedClass(5.0)
    a = d.clone()
    assert a.square() == 25.0


@cpp2py_tester("cppstruct.hpp")
def test_struct():
    from cppstruct import A, B, print_mystruct_a, print_mystruct_b

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
    op += 3
    assert op.v == 3
    assert 2 < op < 4
    op -= 1
    assert op.v == 2
    op *= 2
    assert op.v == 4
    op /= 4
    assert op.v == 1
    op %= 2
    assert op.v == 1
    op.v = 0b11
    assert op | 0b100 == 0b111
    assert op & 0b10 == 0b10
    assert ~op == ~0b11

    op |= 0b100
    assert op.v == 0b111
    op &= 0b10
    assert op.v == 0b10


@cpp2py_tester("typedef.hpp")
def test_typedef():
    from typedef import fun

    assert fun(1.0) == 2.0


@cpp2py_tester("complexfield.hpp")
def test_complex_field():
    from complexfield import A, B

    a = A()
    a.a = 5
    b = B()
    b.a = a
    b.b = a
    assert b.a.a == 5
    assert b.b.a == 5


@cpp2py_tester("cppenum.hpp")
def test_enum():
    from cppenum import Result, Suit, guess_card

    # assert issubclass(Suit, Enum)
    assert guess_card(Suit.Clubs) == Result.Hit
    assert guess_card(Suit.Hearts) == Result.Miss

    from cppenum import MyEnum, MyEnumClass

    assert MyEnum.FIRSTOPTION != MyEnum.SECONDOPTION
    assert MyEnum.SECONDOPTION != MyEnum.THIRDOPTION
    assert MyEnumClass.enum_to_string(MyEnum.FIRSTOPTION) == "first"
    assert MyEnumClass.enum_to_string(MyEnum.SECONDOPTION) == "second"
    assert MyEnumClass().enum_to_string(MyEnum.THIRDOPTION) == "third"


@cpp2py_tester("staticattr.hpp")
def test_static_attr():
    from staticattr import A, B, cvar

    assert A.get_count() == cvar.count
    cvar.count = 2
    assert A.get_count() == 2
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


@cpp2py_tester("throwexception.hpp")
def test_exceptions():
    # http://docs.cython.org/src/userguide/wrapping_CPlusPlus.html#exceptions
    from throwexception import (
        throw_bad_alloc,
        throw_bad_cast,
        throw_domain_error,
        throw_invalid_argument,
        throw_ios_base_failure,
        throw_other,
        throw_out_of_range,
        throw_overflow_error,
        throw_range_error,
        throw_underflow_error,
    )

    pytest.raises(MemoryError, throw_bad_alloc)
    pytest.raises(TypeError, throw_bad_cast)
    pytest.raises(ValueError, throw_domain_error)
    pytest.raises(ValueError, throw_invalid_argument)
    pytest.raises(IOError, throw_ios_base_failure)
    pytest.raises(IndexError, throw_out_of_range)
    pytest.raises(OverflowError, throw_overflow_error)
    pytest.raises(ArithmeticError, throw_range_error)
    pytest.raises(ArithmeticError, throw_underflow_error)
    pytest.raises(RuntimeError, throw_other)


@cpp2py_tester("globals.hpp")
def test_global_vars_macros():
    from globals import cvar, get_hello

    assert cvar.V == 5
    assert cvar.PI == np.float32(3.14159)
    assert cvar.T is False
    assert cvar.HELLO == get_hello()
    cvar.HELLO = "hello too"
    assert "hello too" == get_hello()

    with pytest.raises(AttributeError):
        cvar.V = 4
    with pytest.raises(AttributeError):
        cvar.PI = 4
    with pytest.raises(AttributeError):
        cvar.T = True
