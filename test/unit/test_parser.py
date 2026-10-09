import subprocess
import sys
from pathlib import Path

import pytest
from clang.cindex import Diagnostic

from cpp2py import ClangError, Config, make_wrapper
from cpp2py.config import Imports
from cpp2py.parser import parse
from cpp2py.parser.parser import _check_diagnostics
from cpp2py.parser.utils import parse_literal_str


class FakeDiagnostic:
    def __init__(self, severity):
        self.severity = severity

    def __str__(self):
        return "diagnostic"


def test_warning_does_not_abort_parsing():
    with pytest.warns(UserWarning, match="diagnostic"):
        _check_diagnostics([FakeDiagnostic(Diagnostic.Warning)])


@pytest.mark.parametrize("severity", [Diagnostic.Error, Diagnostic.Fatal])
def test_error_aborts_parsing(severity):
    with pytest.raises(ClangError, match="diagnostic"):
        _check_diagnostics([FakeDiagnostic(severity)])


def parse_text(tmp_path, source):
    header = tmp_path / "input.hpp"
    header.write_text(source, encoding="utf8")
    return parse(Config(headers=[str(header)]), Imports("input"))


def test_anonymous_declaration_does_not_hide_following_functions(tmp_path):
    objects = parse_text(tmp_path, "enum { HIDDEN = 1 };\nint after_enum(int n);\n")
    assert "after_enum" in objects.functions


def test_forward_declaration_does_not_hide_definition(tmp_path):
    objects = parse_text(tmp_path, "struct Value;\nstruct Value { int number; };\n")
    assert objects.classes["Value"].fields[0].name == "number"


def test_deleted_constructor_and_method_are_ignored(tmp_path):
    objects = parse_text(
        tmp_path, "struct Value { Value() = delete; void run() = delete; };\n"
    )
    value = objects.classes["Value"]
    assert not value.ctors
    assert not value.auto_default_constructible
    assert not value.methods


def test_same_basename_and_relative_nested_include(tmp_path):
    headers = []
    for folder, name in (("a", "one"), ("b", "two")):
        directory = tmp_path / folder
        directory.mkdir()
        (directory / "nested.hpp").write_text("#pragma once\n", encoding="utf8")
        header = directory / "same.hpp"
        header.write_text(
            f'#include "nested.hpp"\nint {name}(int n);\n', encoding="utf8"
        )
        headers.append(str(header))
    objects = parse(Config(headers=headers), Imports("input"))
    assert set(objects.functions) == {"one", "two"}


def test_same_name_in_different_namespaces_keeps_first(tmp_path):
    with pytest.warns(UserWarning, match="name conflicts"):
        objects = parse_text(
            tmp_path,
            "namespace a { struct Value { int one; }; }\nnamespace b { struct Value { int two; }; }\n",
        )
    assert objects.classes["Value"].namespace == "a"
    assert objects.classes["Value"].fields[0].name == "one"


def test_namespace_base_is_resolved_by_full_name(tmp_path):
    header = tmp_path / "input.hpp"
    header.write_text(
        "namespace demo { struct Base { int x; }; struct Derived : Base { int y; }; }\n",
        encoding="utf8",
    )
    result = make_wrapper(Config(headers=[str(header)]))
    assert "cdef class Derived" in result.source_content
    assert "def x(Derived self)" in result.source_content


def test_missing_included_base_has_actionable_error(tmp_path):
    (tmp_path / "base.hpp").write_text("struct Base { int x; };\n", encoding="utf8")
    header = tmp_path / "derived.hpp"
    header.write_text(
        '#include "base.hpp"\nstruct Derived : Base {};\n', encoding="utf8"
    )
    with pytest.raises(ValueError, match="Config.headers"):
        make_wrapper(Config(headers=[str(header)]))


def test_gbk_input_remains_supported(tmp_path):
    header = tmp_path / "input.hpp"
    header.write_text("// 中文注释\nint twice(int n);\n", encoding="gbk")
    result = make_wrapper(Config(headers=[str(header)], encoding="gbk"))
    assert "cpdef twice" in result.source_content


def test_import_does_not_load_native_library():
    process = subprocess.run(
        [
            sys.executable,
            "-c",
            "import cpp2py; from clang.cindex import Config; assert not Config.loaded",
        ],
        capture_output=True,
        text=True,
    )
    assert process.returncode == 0, process.stderr


@pytest.mark.parametrize(
    "source, value",
    [
        ("0xFF", 255),
        ("0xFFUL", 255),
        ("0123", 83),
        ("0b101ULL", 5),
        ("- 0xFF", -255),
        ("-0123", -83),
        ("1'234", 1234),
        ("3.5f", 3.5),
        ("0x1.8p1", 3.0),
        ('"don\'t"', "don't"),
        ("'x'", 120),
        ("false", False),
    ],
)
def test_cpp_literal_values(source, value):
    assert parse_literal_str(source) == value
