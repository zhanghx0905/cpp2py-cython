import pytest

from tools import cpp2py_tester


@cpp2py_tester("fails.hpp", warnmsg=".* ignoring .*")
def test_fails():
    from fails import A

    assert not hasattr(A, "my_function")


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
