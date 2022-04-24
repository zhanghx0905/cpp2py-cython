from cpp2py import AbstractTypeConverter, Config

from tools import cpp2py_tester


@cpp2py_tester(["indeppart1.hpp", "indeppart2.hpp"], modulename="combined")
def test_independent_parts():
    from combined import ClassA, ClassB

    a = ClassA()
    assert not a.result()
    b = ClassB()
    assert b.result()


@cpp2py_tester(["deppart1.hpp", "deppart2.hpp"], modulename="depcombined")
def test_dependent_parts():
    from depcombined import A

    a = A()
    b = a.make()
    assert b.get_value() == 5


def test_register_custom_type_converter():
    class CustomTypeConverter(AbstractTypeConverter):
        def _matches(self):
            raise NotImplementedError()

        def python_to_cpp(self):
            raise NotImplementedError()

        def cpp_call_arg(self):
            raise NotImplementedError()

        def return_output(self, cpp_call: str, **kwargs) -> str:
            raise NotImplementedError()

        def input_type_decl(self):
            raise NotImplementedError()

        def _add_includes(self, includes):
            raise NotImplementedError()

    config = Config()
    config.registered_converters.append(CustomTypeConverter)

    @cpp2py_tester("boolinboolout.hpp", config=config, warnmsg=".* ignoring .*")
    def run():
        ...

    run()


@cpp2py_tester("addincludedir.hpp", incdirs=["anotherincludedir"])
def test_another_include_dir():
    from addincludedir import length

    assert length(3.0, 4.0) == 5.0
