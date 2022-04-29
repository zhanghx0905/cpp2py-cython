import numpy as np
import pytest

from tools import cpp2py_tester


@cpp2py_tester("basictypes.hpp")
def test_basic_types():
    from basictypes import A, fun1, helloworld, length, lookup

    a = A()
    assert True == a.neg(False)

    d = 3.213
    assert d + 2.0 == a.plus2(d)

    s = "This is a sentence"
    assert s + "." == a.end(s)

    substrings = ["AB", "CD", "EF"]
    assert a.concat(substrings) == "ABCDEF"

    ptr = np.array([5], np.int32)
    assert fun1(ptr) == 6

    assert length("test") == 4
    assert helloworld() == "hello world"

    m = {"test": -1}
    assert lookup(m) == m["test"]


@cpp2py_tester("complexarg.hpp")
def test_complex_arg():
    from complexarg import A, B, C

    a = A()
    b = B(a)
    assert b.get_string() == "test"

    a = A()
    c = C(a)
    assert c.get_string() == "test"


@cpp2py_tester("fixedarray.hpp")
def test_fixed_length_array():
    from fixedarray import to_string

    assert to_string([1, 2, 3, 4, 5]) == "[1, 2, 3, 4, 5]"
    pytest.raises(ValueError, to_string, [1, 2, 3, 4])
    pytest.raises(TypeError, to_string, [1, 2, 3, 4, "a"])


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


@cpp2py_tester("lref.hpp")
def test_left_reference():
    from lref import A, change_a

    a = A()
    a.a, a.b = -1, True
    change_a(a)
    assert a.a == 99
    assert a.b == False
