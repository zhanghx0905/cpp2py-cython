import pytest

from tools import cpp2py_tester


@cpp2py_tester("overload.hpp", warnmsg="Ignoring overloaded .*")
def test_overloading_is_not_possible():
    from overload import A, plus_one

    a = A()
    assert a.plus_one(3.0) == 4.0
    assert plus_one(3.0) == 4.0


@cpp2py_tester("twoctors.hpp", warnmsg="Ignoring overloaded .*")
def test_twoctors():
    from twoctors import A

    A()
    with pytest.raises(TypeError):
        A(2)


@cpp2py_tester("nodefaultctor.hpp")
def test_no_default_constructor():
    from nodefaultctor import A

    a = A()
    a.set_member(5)


@cpp2py_tester("pythonkeywords.hpp")
def test_python_keyword_conversion():
    from pythonkeywords import _def

    assert _def(2, 3) == 6


@cpp2py_tester("sgetternameclash.hpp")
def test_name_clash():
    from sgetternameclash import A

    a = A()
    a.n = 20
    assert a.n == 20
    a.set_n(30)
    assert a.get_n() == 30


@cpp2py_tester("missingdefaultctor.hpp")
def test_missing_default_ctor():
    with pytest.raises(ImportError):
        import missingdefaultctor


@cpp2py_tester("missingassignmentop.hpp")
def test_missing_assignment():
    with pytest.raises(ImportError):
        import missingassignmentop
