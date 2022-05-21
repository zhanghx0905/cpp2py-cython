from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from functools import cached_property
from keyword import iskeyword

from ..typesystem import CXXType
from .utils import OPERATORS_MAPPER


@dataclass
class _BaseSymbol:
    name: str
    filename: str = ""
    namespace: str = ""
    old_name: str = ""

    @property
    def decl(self):
        if self.name == self.old_name:
            return self.name
        return f'{self.name} "{self.old_name}"'

    def __post_init__(self):
        self.old_name = self.name
        if iskeyword(self.name):
            self.name = f"_{self.name}"

    @cached_property
    def fullname(self) -> str:
        """name with namespace"""
        if self.namespace == "":
            return self.old_name
        return f"{self.namespace}::{self.old_name}"


@dataclass
class Macro(_BaseSymbol):
    literal: object = None


@dataclass
class Variable(_BaseSymbol):
    """class's field or function's argument"""

    type: CXXType = None
    is_const: bool = False

    value: object = None  # default value


@dataclass
class Function(_BaseSymbol):
    type: str = ""
    ret_type: CXXType = None
    args: list[Variable] = field(default_factory=list)
    is_variadic: bool = False  # C variadic parameter like "int printf(char *, ...)"


@dataclass
class Method(Function):
    is_const: bool = False
    is_static: bool = False
    is_pure_virtual: bool = False
    is_operator: bool = False

    def __post_init__(self):
        super().__post_init__()
        if (pyname := OPERATORS_MAPPER.get(self.name, None)) is not None:
            self.is_operator = True
            self.name = pyname


@dataclass
class Record(_BaseSymbol):
    def __post_init__(self):
        super().__post_init__()
        if iskeyword(self.old_name):
            raise NotImplementedError("Unsupported: type name collide with keywords")


@dataclass
class Typedef(Record):
    underlying_type: str = ""


@dataclass
class Enum(Record):
    constants: list[Variable] = field(default_factory=list)


@dataclass
class Class(Record):
    methods: dict[str, list[Method]] = field(default_factory=lambda: defaultdict(list))
    ctors: list[Method] = field(default_factory=list)
    fields: list[Variable] = field(default_factory=list)

    bases: set[str] = field(default_factory=set)
    is_abstract: bool = False
    # Whether there is an implicitly generated default constructor
    auto_default_constructible: bool = True


@dataclass
class ParseResult:
    macros: dict[str, Macro] = field(default_factory=dict)
    variables: dict[str, Variable] = field(default_factory=dict)
    enums: dict[str, Enum] = field(default_factory=dict)
    classes: dict[str, Class] = field(default_factory=dict)
    functions: dict[str, list[Function]] = field(
        default_factory=lambda: defaultdict(list)
    )
    typedefs: list[Typedef] = field(default_factory=list)
