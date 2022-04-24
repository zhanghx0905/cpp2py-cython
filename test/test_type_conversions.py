import numpy as np
import pytest

from tools import cpp2py_tester


@cpp2py_tester("boolinboolout.hpp")
def test_bool_in_bool_out():
    from boolinboolout import A

    a = A()
    b = False
    assert True == a.neg(b)


@cpp2py_tester("doubleindoubleout.hpp")
def test_double_in_double_out():
    from doubleindoubleout import A

    a = A()
    d = 3.213
    assert d + 2.0 == a.plus2(d)


@cpp2py_tester("complexarg.hpp")
def test_complex_arg():
    from complexarg import A, B

    a = A()
    b = B(a)
    assert b.get_string() == "test"


@cpp2py_tester("map.hpp")
def test_map():
    from map import lookup

    m = {"test": 0}
    assert lookup(m) == 0


@cpp2py_tester("vector.hpp")
def test_vector():
    from vector import A

    a = A()
    v = np.array([2.0, 1.0, 3.0])
    n = a.norm(v, len(v))
    assert n == 14.0


@cpp2py_tester("stringinstringout.hpp")
def test_string_in_string_out():
    from stringinstringout import A

    a = A()
    s = "This is a sentence"
    sout = "This is a sentence."
    assert sout == a.end(s)


@cpp2py_tester("stringvector.hpp")
def test_string_vector():
    from stringvector import A

    a = A()
    substrings = ["AB", "CD", "EF"]
    res = a.concat(substrings)
    assert res == "ABCDEF"


@cpp2py_tester("complexptrarg.hpp")
def test_complex_ptr_arg():
    from complexptrarg import A, B

    a = A()
    b = B(a)
    assert b.get_string() == "test"


@cpp2py_tester("factory.hpp")
def test_factory():
    from factory import AFactory

    factory = AFactory()
    a = factory.make()
    assert 5 == a.get()


@cpp2py_tester("primitivepointers.hpp")
def test_primitive_pointers():
    from primitivepointers import fun1

    ptr = np.array([5], np.int32)
    assert fun1(ptr) == 6


@cpp2py_tester("cstring.hpp")
def test_cstring():
    from cstring import helloworld, length

    assert length("test") == 4
    assert helloworld() == "hello world"


@cpp2py_tester("fixedarray.hpp")
def test_fixed_length_array():
    from fixedarray import to_string

    assert to_string([1, 2, 3, 4, 5]) == "[1, 2, 3, 4, 5]"
    pytest.raises(ValueError, to_string, [1, 2, 3, 4])
    pytest.raises(TypeError, to_string, [1, 2, 3, 4, "a"])


@cpp2py_tester("missingdefaultctor.hpp")
def test_missing_default_ctor():
    with pytest.raises(ImportError):
        import missingdefaultctor


@cpp2py_tester("missingassignmentop.hpp")
def test_missing_assignment():
    with pytest.raises(ImportError):
        import missingassignmentop


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
