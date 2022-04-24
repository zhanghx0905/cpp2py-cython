import operator
import re
from functools import lru_cache
from ast import literal_eval

from clang.cindex import CursorKind

_OPERATOR_PATTERN = re.compile(r"operator\W+")


def unary_operators(op: str):
    if op == "-":
        return operator.neg
    if op == "+":
        return operator.pos
    return lambda _: None


def join_namespace(parent: str, namespace: str):
    return f"{parent}::{namespace}" if parent else namespace


def split_namespace(namespace: str):
    names = namespace.split("::")
    return "::".join(names[:-1]), names[-1]


@lru_cache
def is_operator(name: str) -> bool:
    return _OPERATOR_PATTERN.match(name) is not None


OPERATORS_MAPPER = {
    "operator()": "__call__",
    "operator[]": "__getitem__",
    "operator+": "__add__",
    "operator-": "__sub__",
    "operator*": "__mul__",
    "operator/": "__truediv__",
    "operator%": "__mod__",
    "operator&&": "__and__",
    "operator&": "__and__",
    "operator||": "__or__",
    "operator|": "__or__",
    "operator+=": "__iadd__",
    "operator-=": "__isub__",
    "operator*=": "__imul__",
    "operator/=": "__itruediv__",
    "operator%=": "__imod__",
    "operator&=": "__iand__",
    "operator|=": "__ior__",
}


@lru_cache
def parse_literal_digit(literal: str):
    literal = literal.replace("'", "").rstrip("lLfFuU")
    try:
        return literal_eval(literal)
    except (ValueError, SyntaxError):
        ...
    return None


_LITERAL_HANDLERS = {
    CursorKind.INTEGER_LITERAL: parse_literal_digit,
    CursorKind.FLOATING_LITERAL: parse_literal_digit,
    CursorKind.CHARACTER_LITERAL: ord,
    CursorKind.STRING_LITERAL: lambda x: x,
    CursorKind.CXX_BOOL_LITERAL_EXPR: lambda x: x == "true",
    # CursorKind.CXX_NULL_PTR_LITERAL_EXPR:
}


def parse_literal_cursor(
    cursor_kind: CursorKind, literal: str
) -> int | float | str | bool | None:
    return _LITERAL_HANDLERS.get(cursor_kind, lambda _: None)(literal)
