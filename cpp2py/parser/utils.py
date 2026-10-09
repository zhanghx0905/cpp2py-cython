import operator
import re
from ast import literal_eval
from functools import lru_cache
from typing import Any, Callable, Dict, Union

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
    "operator&": "__and__",
    "operator|": "__or__",
    "operator~": "__invert__",
    "operator^": "__xor__",
    "operator<<": "__lshift__",
    "operator>>": "__rshift__",
    "operator<": "__lt__",
    "operator>": "__gt__",
    "operator<=": "__le__",
    "operator>=": "__ge__",
    "operator==": "__eq__",
    "operator!=": "__ne__",
    "operator+=": "__iadd__",
    "operator-=": "__isub__",
    "operator*=": "__imul__",
    "operator/=": "__itruediv__",
    "operator%=": "__imod__",
    "operator&=": "__iand__",
    "operator|=": "__ior__",
    "operator^=": "__ixor__",
    "operator<<=": "__ilshift__",
    "operator>>=": "__irshift__",
}


def _parse_bool_literal(literal: str):
    if literal == "true":
        return True
    if literal == "false":
        return False
    return None


def _parse_string_literal(literal: str):
    try:
        return literal_eval(literal)
    except (ValueError, SyntaxError):
        return None


def _parse_character_literal(literal: str):
    value = _parse_string_literal(literal)
    return ord(value) if isinstance(value, str) and len(value) == 1 else None


@lru_cache
def _parse_literal_digit(literal: str):
    # Hexadecimal digits can end in F, so stripping all suffix characters
    # corrupts values such as 0xFF. String contents must also remain intact.
    if literal.startswith('"'):
        return _parse_string_literal(literal)
    if literal.startswith("'"):
        return _parse_character_literal(literal)
    numeric = literal.replace("'", "").replace(" ", "")
    integer = re.fullmatch(
        r"([+-]?(?:0[xX][0-9a-fA-F]+|0[bB][01]+|[0-9]+))([uUlL]*)", numeric
    )
    if integer:
        digits = integer.group(1)
        unsigned = digits.lstrip("+-")
        base = (
            0
            if unsigned.lower().startswith(("0x", "0b"))
            else 8 if len(unsigned) > 1 and unsigned.startswith("0") else 10
        )
        try:
            return int(digits, base)
        except ValueError:
            return None
    numeric = numeric.rstrip("fFlL")
    try:
        if numeric.lower().startswith("0x") and "p" in numeric.lower():
            return float.fromhex(numeric)
        value = literal_eval(numeric)
        return value if isinstance(value, (int, float)) else None
    except (ValueError, SyntaxError):
        ...
    return None


_LITERAL_HANDLERS: Dict[CursorKind, Callable[[str], Any]] = {
    CursorKind.INTEGER_LITERAL: _parse_literal_digit,
    CursorKind.FLOATING_LITERAL: _parse_literal_digit,
    CursorKind.CHARACTER_LITERAL: _parse_character_literal,
    CursorKind.STRING_LITERAL: _parse_string_literal,
    CursorKind.CXX_BOOL_LITERAL_EXPR: _parse_bool_literal,
    # CursorKind.CXX_NULL_PTR_LITERAL_EXPR:
}


def parse_literal_cursor(
    cursor_kind: CursorKind, literal: str
) -> Union[int, float, str, bool, None]:
    return _LITERAL_HANDLERS.get(cursor_kind, lambda _: None)(literal)


def parse_literal_str(literal: str):
    for parser in [_parse_literal_digit, _parse_bool_literal]:
        ret = parser(literal)
        if ret is not None:
            return ret
    return None
