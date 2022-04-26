import re
from abc import ABCMeta, abstractmethod
from enum import Enum

from clang.cindex import TypeKind

from .config import Imports
from .cxxtypes import CXXType
from .utils import render


class VarType(Enum):
    PARAMETER = 0
    RETURN = 1


class AbstractTypeConverter(metaclass=ABCMeta):
    """
    mytype func(mytype arg);

    cpdef func({{ python_type_decl }} arg):
        {{ python_to_cpp }}
        (cdef {{ cpp_type_decl }} result = ) c_func({{ call_cpp_arg }})
        {{ return_output }}
    """

    def __init__(
        self,
        type: CXXType,
        argname: str,
        classnames: set[str],
        includes: Imports,
    ):
        self.classnames = classnames
        self.raw_cxxtype = type
        self.cxxtype = type.get_canonical()

        self.py_argname = argname
        self.cpp_argname = f"_{self.py_argname}"

        self.match = self._matches()  # like cached property
        if self.match:
            self._add_includes(includes)

    @abstractmethod
    def _matches(self) -> bool:
        """Is the type converter applicable to the type?"""

    @abstractmethod
    def _add_includes(self, includes: Imports):
        """Add includes for this conversion."""

    @abstractmethod
    def python_to_cpp(self) -> str:
        """Convert Cython object to C++ object."""

    @abstractmethod
    def cpp_call_arg(self) -> str:
        """Representation for C++ function call."""

    @abstractmethod
    def input_type_decl(self) -> str:
        """Python type decleration."""

    @abstractmethod
    def return_output(self, cpp_call: str, **kwargs) -> str:
        """return output"""

    def pysign_type_decl(self, vtype: VarType):
        """used in stub files,"""
        return "Any"


class BaseTypeConverter(AbstractTypeConverter):
    def __init__(
        self, type: CXXType, argname: str, classnames: set[str], includes: Imports
    ):
        if type.kind in {TypeKind.LVALUEREFERENCE, TypeKind.RVALUEREFERENCE}:
            type = type.pointee
        super().__init__(type, argname, classnames, includes)

    def _matches(self) -> bool:
        return False

    def _add_includes(self, includes: Imports):
        """do nothing"""

    def input_type_decl(self):
        return self.cxxtype.name

    def python_to_cpp(self):
        return ""

    def cpp_call_arg(self):
        return self.py_argname

    def return_output(self, cpp_call: str, **kwargs) -> str:
        return f"return {cpp_call}"


class VoidConverter(BaseTypeConverter):
    def _matches(self):
        return self.cxxtype.kind == TypeKind.VOID

    def input_type_decl(self):
        raise NotImplementedError("Unsupported: void as parameter")

    def python_to_cpp(self):
        raise NotImplementedError("Unsupported: void as parameter")

    def cpp_call_arg(self):
        raise NotImplementedError("Unsupported: void as parameter")

    def return_output(self, cpp_call: str, **kwargs) -> str:
        return cpp_call

    def pysign_type_decl(self, vtype: VarType):
        if vtype == VarType.RETURN:
            return "None"
        raise NotImplementedError("Unsupported: void as parameter")


# on 64-bit
NUMERIC_TYPEKINDS = {
    TypeKind.BOOL: "bool",
    TypeKind.UCHAR: "np.uint8",
    TypeKind.USHORT: "np.uint16",
    TypeKind.UINT: "np.uint32",
    TypeKind.ULONG: "np.uint64",
    TypeKind.ULONGLONG: "np.uint64",
    TypeKind.CHAR_S: "np.int8",
    TypeKind.SHORT: "np.int16",
    TypeKind.INT: "np.int32",
    TypeKind.LONG: "np.int64",
    TypeKind.LONGLONG: "np.int64",
    TypeKind.FLOAT: "np.float32",
    TypeKind.DOUBLE: "np.float64",
    TypeKind.LONGDOUBLE: "np.float128",
}


class NumericConverter(BaseTypeConverter):
    def _matches(self):
        return self.cxxtype.kind in NUMERIC_TYPEKINDS

    def pysign_type_decl(self, vtype: VarType):
        return NUMERIC_TYPEKINDS[self.cxxtype.kind]


class CStringConverter(BaseTypeConverter):
    def _matches(self) -> bool:
        return (
            self.cxxtype.kind == TypeKind.POINTER
            and self.cxxtype.pointee.kind == TypeKind.CHAR_S
        )

    def input_type_decl(self):
        return "str"

    def pysign_type_decl(self, vtype: VarType):
        return "str"


class StringConverter(CStringConverter):
    def _matches(self) -> bool:
        return self.cxxtype.plain_name == "basic_string[char]"


class CStringArrayConverter(BaseTypeConverter):
    def _matches(self) -> bool:
        return (
            self.cxxtype.kind == TypeKind.POINTER
            and self.cxxtype.pointee.kind == TypeKind.POINTER
            and self.cxxtype.pointee.pointee.kind == TypeKind.CHAR_S
        )

    def _add_includes(self, includes):
        includes.mods["malloc"] = True

    def python_to_cpp(self):
        return f"""cdef char** {self.cpp_argname} = <char **>malloc(sizeof(char *)*len({self.py_argname}))
cdef unsigned int {self.py_argname}_idx
for {self.py_argname}_idx in range(len({self.py_argname})):
    {self.cpp_argname}[{self.py_argname}_idx] = {self.py_argname}[{self.py_argname}_idx]
"""

    def input_type_decl(self):
        return "object"

    def cpp_call_arg(self):
        return self.cpp_argname

    def pysign_type_decl(self, vtype: VarType):
        return "Iterable[str]"

    def return_output(self, cpp_call: str, **kwargs) -> str:
        raise NotImplementedError


class FixedSizeArrayConverter(BaseTypeConverter):
    def _matches(self):
        if self.cxxtype.kind == TypeKind.CONSTANTARRAY:
            self.size = self.cxxtype.type.element_count
            self.ele_type = self.cxxtype.ele_type
            return True
        return False

    def python_to_cpp(self):
        return render(
            "convert_fixed_array",
            py_argname=self.py_argname,
            cpp_argname=self.cpp_argname,
            size=self.size,
            ele_type=self.ele_type,
        )

    def cpp_call_arg(self):
        return self.cpp_argname

    def input_type_decl(self):
        return "object"

    def pysign_type_decl(self, vtype: VarType):
        return "Iterable"


class EnumConverter(BaseTypeConverter):
    def _matches(self):
        return self.cxxtype.kind == TypeKind.ENUM

    def return_output(self, cpp_call: str, **kwargs) -> str:
        return f"return {self.cxxtype.plain_name}({cpp_call})"

    def pysign_type_decl(self, vtype: VarType):
        return self.cxxtype.plain_name


class NumericPtrConverter(BaseTypeConverter):
    def _matches(self):
        self.pointee = self.cxxtype.pointee
        return (
            self.cxxtype.kind == TypeKind.POINTER
            and self.pointee.kind in NUMERIC_TYPEKINDS
        )

    def _add_includes(self, includes):
        includes.mods["deref"] = True

    def input_type_decl(self):
        return f"{self.pointee.name}[:]"

    def cpp_call_arg(self):
        return f"&{self.py_argname}[0]"

    def return_output(self, cpp_call: str, **kwargs) -> str:
        return f"return deref({cpp_call})"

    def pysign_type_decl(self, vtype: VarType):
        pointee_typing = NUMERIC_TYPEKINDS[self.pointee.kind]
        if vtype == VarType.PARAMETER:
            return f"np.ndarray[Any, np.dtype[{pointee_typing}]]"
        return pointee_typing


class VoidPtrConverter(BaseTypeConverter):
    def _matches(self):
        return (
            self.cxxtype.kind == TypeKind.POINTER
            and self.cxxtype.pointee.kind == TypeKind.VOID
        )

    def _add_includes(self, includes):
        includes.mods["deref"] = True

    def input_type_decl(self):
        return f"{self.real_type()}[:]"

    def cpp_call_arg(self):
        return f"<void *>&{self.py_argname}[0]"

    def return_output(self, cpp_call: str, **kwargs) -> str:
        return f"return deref(<{self.real_type()} *> {cpp_call})"

    @abstractmethod
    def real_type(self) -> str:
        """Need to specify"""


class ClassConverter(BaseTypeConverter):
    def _matches(self):
        return self.cxxtype.plain_name in self.classnames

    def _add_includes(self, includes):
        includes.mods["deref"] = True
        includes.mods["malloc"] = True

    def cpp_call_arg(self):
        return f"deref({self.py_argname}.thisptr)"

    def return_output(self, cpp_call: str, **kwargs) -> str:
        return render("convert_class", name=self.cxxtype.plain_name, cpp_call=cpp_call)

    def input_type_decl(self):
        return self.cxxtype.plain_name

    def pysign_type_decl(self, vtype: VarType):
        return self.cxxtype.plain_name


class ClassPtrConverter(BaseTypeConverter):
    def _matches(self):
        self.pointee = self.cxxtype.pointee
        return (
            self.cxxtype.kind == TypeKind.POINTER
            and self.pointee.plain_name in self.classnames
        )

    def cpp_call_arg(self):
        return f"{self.py_argname}.thisptr.get()"

    def return_output(self, cpp_call: str, **kwargs) -> str:
        return render(
            "convert_class_ptr",
            name=self.pointee.plain_name,
            copy=kwargs["copy"],
            cpp_call=cpp_call,
        )

    def input_type_decl(self):
        return self.pointee.plain_name

    def pysign_type_decl(self, vtype: VarType):
        return self.pointee.plain_name


class ClassPtrPtrConverter(BaseTypeConverter):
    def _matches(self) -> bool:
        if (
            self.cxxtype.kind == TypeKind.POINTER
            and self.cxxtype.pointee.kind == TypeKind.POINTER
        ):
            self.pointee = self.cxxtype.pointee.pointee
            return self.pointee.plain_name in self.classnames
        return False

    def cpp_call_arg(self):
        return f"&{self.py_argname}.thisptr.get()"

    def input_type_decl(self):
        return self.pointee.plain_name

    def pysign_type_decl(self, vtype: VarType):
        return self.pointee.plain_name

    def return_output(self, cpp_call: str, **kwargs) -> str:
        raise NotImplementedError


_SUPPORTED_STL_PATTERN = re.compile(
    r"^(?:const )?std::(map|unordered_map|set|unordered_set|vector|list|complex|pair)<"
)
_IDENTIFIER_PATTERN = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*")
_STL_PYTYPING = {
    "map": ("Mapping", "dict"),
    "unordered_map": ("Mapping", "dict"),
    "set": ("Iterable", "set"),
    "unordered_set": ("Iterable", "set"),
    "pair": ("Iterable", "tuple"),
    "vector": ("Iterable", "list"),
    "list": ("Iterable", "list"),
    "complex": ("complex", "complex"),
}


class STLConverter(BaseTypeConverter):
    def _matches(self):
        match = _SUPPORTED_STL_PATTERN.match(self.cxxtype.cppname)
        if match is not None:
            self.stl = match.group(1)
            typenames = {
                m.group(0)
                for m in _IDENTIFIER_PATTERN.finditer(self.cxxtype.plain_name)
            }
            return all(typename not in self.classnames for typename in typenames)
        return False

    def input_type_decl(self):
        return "object"

    def pysign_type_decl(self, vtype: VarType):
        return _STL_PYTYPING[self.stl][vtype.value]


class ClassVectorConverter(STLConverter):
    def _matches(self):
        match = _SUPPORTED_STL_PATTERN.match(self.cxxtype.cppname)
        if match is not None and match.group(1) == "vector":
            subtype = self.cxxtype.template_args[0]
            if subtype.plain_name in self.classnames:
                self.subtype = subtype
                self.impl_name = f"vector[cpp.{subtype.plain_name}]"
                return True
        return False

    def _add_includes(self, includes):
        includes.mods["deref"] = True

    def python_to_cpp(self):
        return render(
            "convert_vector",
            python_argname=self.py_argname,
            cpp_tname=self.subtype,
            cpp_type_decl=self.impl_name,
            cython_argname=self.cpp_argname,
        )

    def pysign_type_decl(self, vtype: VarType):
        if vtype == VarType.PARAMETER:
            return f"list[{self.subtype.plain_name}]"
        raise NotImplementedError()

    def cpp_call_arg(self):
        return self.cpp_argname

    def return_output(self, cpp_call: str, **kwargs) -> str:
        raise NotImplementedError()


DEFAULT_CONVERTERS: list[type] = [
    VoidConverter,
    CStringConverter,
    NumericConverter,
    NumericPtrConverter,
    CStringArrayConverter,
    FixedSizeArrayConverter,
    EnumConverter,
    ClassConverter,
    ClassPtrConverter,
    ClassPtrPtrConverter,
    StringConverter,
    ClassVectorConverter,
    STLConverter,
]
CONVERTERS = DEFAULT_CONVERTERS


def init_converters(custom_converters: list[type]):
    global CONVERTERS
    CONVERTERS = custom_converters + DEFAULT_CONVERTERS


def create_type_converter(
    type: CXXType, argname: str, classnames: set[str], includes: Imports
) -> AbstractTypeConverter:
    for converter_type in CONVERTERS:
        converter: AbstractTypeConverter = converter_type(
            type, argname, classnames, includes
        )
        if converter.match:
            return converter
    raise NotImplementedError(f'No type converter available for type "{type}"')
