from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum as pyEnum
from functools import cached_property
from keyword import iskeyword

from clang.cindex import CursorKind

from ..cxxtypes import CXXType
from .utils import OPERATORS_MAPPER


@dataclass
class _BaseSymbol:
    name: str
    filename: str = ""
    namespace: str = ""

    def __post_init__(self):
        if iskeyword(self.name):
            self.decl = f' _{self.name} "{self.name}"'
            self.name = f"_{self.name}"
        else:
            self.decl = self.name

    @cached_property
    def fullname(self) -> str:
        """name with namespace"""
        if self.namespace == "":
            return self.name
        return f"{self.namespace}::{self.name}"


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
    ret_type: CXXType = None
    args: list[Variable] = field(default_factory=list)


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
            self.decl = f'{pyname} "{self.name}"'
            self.name = pyname


@dataclass
class Record(_BaseSymbol):
    def __post_init__(self):
        if iskeyword(self.name):
            raise NotImplementedError("Unsupported: type name collide with keywords")


class RecordType(pyEnum):
    CLASS = 0
    STRUCT = 1
    # ENUM = 2
    UNION = 3

    def __str__(self) -> str:
        return self.name.lower()

    @classmethod
    def build(cls, kind: CursorKind):
        if kind == CursorKind.CLASS_DECL:
            return cls.CLASS
        if kind == CursorKind.STRUCT_DECL:
            return cls.STRUCT
        if kind == CursorKind.UNION_DECL:
            return cls.UNION
        raise NotImplementedError()


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

    rtype: RecordType = RecordType.CLASS
    base: str | None = None
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
