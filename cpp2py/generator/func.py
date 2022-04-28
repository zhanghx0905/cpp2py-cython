import os
import re
from typing import List, Set

from ..config import Imports
from ..parser import CXXType, Variable
from ..type_conversion import BaseTypeConverter, VarType, create_type_converter
from ..utils import camel_to_snake, render

# member definitions
FUNC_CALL = "cpp.%(name)s(%(call_args)s)"
CONSTRUCTOR_CALL = "self.thisptr = new cpp.%(class_name)s(%(call_args)s)"
METHOD_CALL = "self.thisptr.%(name)s(%(call_args)s)"
STATIC_METHOD_CALL = "cpp.%(class_name)s.%(name)s(%(call_args)s)"
SETTER_CALL = "self.thisptr.%(name)s = %(call_args)s"
GETTER_CALL = "self.thisptr.%(name)s"
PYSIGN = "def %(name)s(%(args)s) -> %(ret_type)s: ..."
_VOID = object()


class _VoidConverter(BaseTypeConverter):
    def __init__(self):
        ...

    def return_output(self, cpp_call: str, **kwargs) -> str:
        return cpp_call

    def pysign_type_decl(self, vtype: VarType):
        return "None"


class PostInitMeta(type):
    def __call__(cls, *args, **kwargs):
        obj = type.__call__(cls, *args, **kwargs)
        obj.__post_init__()
        return obj


class FunctionGenerator(metaclass=PostInitMeta):
    def __init__(
        self,
        name: str,
        args: List[Variable],
        ret_type: CXXType,
        typenames: Set[str],
        includes: Imports,
    ) -> None:
        def get_converter(type: CXXType, py_argname: str):
            return create_type_converter(type, py_argname, typenames, includes)

        self.name = name
        self.args = args

        self.arg_converters = [get_converter(arg.type, arg.name) for arg in args]
        if ret_type == _VOID:
            self.ret_converter = _VoidConverter()
        else:
            self.ret_converter = get_converter(ret_type, "")
        self.ret_copy = True

    def __post_init__(self):
        self.impl = self.generate_impl()
        self.pysign = self.generate_pysign()

    def _function_name(self):
        return camel_to_snake(self.name)

    def _function_prefix(self):
        return "cpdef"

    def _input_args(self):
        args = [f"{tc.input_type_decl()} {tc.py_argname}" for tc in self.arg_converters]
        # handle default values
        for idx in reversed(range(len(args))):
            arg = self.args[idx]
            if arg.value is None:
                break
            args[idx] += f" = {arg.value}"
        return ", ".join(args)

    def _cpp_call(self, args: str):
        return FUNC_CALL % {
            "name": self.name,
            "call_args": args,
        }

    def generate_impl(self):
        input_conversions = [tc.python_to_cpp() for tc in self.arg_converters]
        cpp_call_args = ", ".join(tc.cpp_call_arg() for tc in self.arg_converters)
        cpp_call = self._cpp_call(cpp_call_args)

        return render(
            "function",
            **{
                "name": self._function_name(),
                "def_prefix": self._function_prefix(),
                "args": self._input_args(),
                "input_conversions": input_conversions,
                "return_output": self.ret_converter.return_output(
                    cpp_call, copy=self.ret_copy
                ),
            },
        )

    def _pysign_input_args(self):
        args = [
            f"{tc.py_argname}: {tc.pysign_type_decl(VarType.PARAMETER)}"
            for tc in self.arg_converters
        ]
        # handle default values
        for idx in reversed(range(len(args))):
            arg = self.args[idx]
            if arg.value is None:
                break
            args[idx] += f" = {arg.value}"
        return ", ".join(args)

    def generate_pysign(self):
        return PYSIGN % {
            "name": self._function_name(),
            "args": self._pysign_input_args(),
            "ret_type": self.ret_converter.pysign_type_decl(VarType.RETURN),
        }


_MAGIC_METHOD_PATTERN = re.compile(r"__\w+__")


class MethodGenerator(FunctionGenerator):
    def __init__(
        self,
        name: str,
        args: List[Variable],
        ret_type: CXXType,
        typenames: Set[str],
        includes: Imports,
        class_name: str,
    ) -> None:
        super().__init__(name, args, ret_type, typenames, includes)
        self.class_name = class_name
        self.is_operator = _MAGIC_METHOD_PATTERN.match(name) is not None

    def _function_prefix(self):
        return "def" if self.is_operator else "cpdef"

    def _cpp_call(self, args: str):
        return METHOD_CALL % {"name": self.name, "call_args": args}

    def _input_args(self):
        args = super()._input_args()
        if args != "":
            return f"{self.class_name} self, {args}"
        return f"{self.class_name} self"

    def _pysign_input_args(self):
        args = super()._pysign_input_args()
        if args != "":
            return f"self, {args}"
        return "self"


class StaticMethodGenerator(MethodGenerator):
    def _function_prefix(self):
        return "def"

    def _cpp_call(self, args: str):
        return STATIC_METHOD_CALL % {
            "class_name": self.class_name,
            "name": self.name,
            "call_args": args,
        }

    def _input_args(self):
        return FunctionGenerator._input_args(self)

    def _pysign_input_args(self):
        return FunctionGenerator._pysign_input_args(self)

    def generate_impl(self):
        return f"@staticmethod{os.linesep}{super().generate_impl()}"

    def generate_pysign(self):
        return f"@staticmethod{os.linesep}{super().generate_pysign()}"


class ConstructorGenerator(MethodGenerator):
    def __init__(
        self,
        args: List[Variable],
        typenames: Set[str],
        includes: Imports,
        class_name: str,
    ) -> None:
        super().__init__("__init__", args, _VOID, typenames, includes, class_name)

    def _function_prefix(self):
        return "def"

    def _cpp_call(self, args: str):
        return CONSTRUCTOR_CALL % {
            "class_name": self.class_name,
            "call_args": args,
        }


class GetterGenerator(MethodGenerator):
    def __init__(
        self,
        field_name: str,
        field_type: CXXType,
        typenames: Set[str],
        includes: Imports,
        class_name: str,
    ) -> None:
        super().__init__(field_name, [], field_type, typenames, includes, class_name)
        self.ret_copy = False

    def _function_prefix(self):
        return "def"

    def _cpp_call(self, _args: str):
        return GETTER_CALL % {
            "name": self.name,
        }


class SetterGenerator(MethodGenerator):
    def __init__(
        self,
        field_name: str,
        field_type: CXXType,
        typenames: Set[str],
        includes: Imports,
        class_name: str,
    ) -> None:
        super().__init__(
            field_name,
            [Variable(f"_{field_name}", type=field_type)],
            _VOID,
            typenames,
            includes,
            class_name,
        )

    def _function_prefix(self):
        return "def"

    def _cpp_call(self, args: str):
        return SETTER_CALL % {
            "name": self.name,
            "call_args": args,
        }
