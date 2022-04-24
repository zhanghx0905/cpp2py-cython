from tools import cpp2py_tester


@cpp2py_tester("overloadmethod.hpp", warnmsg="Ignoring overloaded .*")
def test_overloading_method_is_not_possible():
    from overloadmethod import A

    a = A()
    assert a.plus_one(3.0) == 4.0


@cpp2py_tester("overloadfunction.hpp", warnmsg="Ignoring overloaded .*")
def test_overloading_function_is_not_possible():
    from overloadfunction import plus_one

    assert plus_one(3.0) == 4.0
