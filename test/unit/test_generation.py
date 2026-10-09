"""Exercise real libclang + Cython translation without invoking a C++ compiler."""

import ast
import subprocess
import sys
from pathlib import Path

import pytest

from cpp2py import Config, make_wrapper, write_files
from cpp2py.config import Imports
from cpp2py.generator import DeclGenerator, ImplGenerator, StubGenerator
from cpp2py.main import WrapperResult
from cpp2py.parser import Function, Variable, parse
from cpp2py.process import Postprocessor
from cpp2py.typesystem import CXXType, init_converters
from clang.cindex import TypeKind

TESTCASES = Path(__file__).resolve().parents[1] / "testcases"


def translate(result, target):
    write_files(result, str(target))
    process = subprocess.run(
        [
            sys.executable,
            "-m",
            "cython",
            "--cplus",
            result.source_name,
            "-o",
            "generated.cpp",
        ],
        cwd=str(target),
        capture_output=True,
        text=True,
        encoding="utf8",
    )
    assert process.returncode == 0, process.stdout + process.stderr
    assert (target / "generated.cpp").is_file()
    ast.parse(result.stub_content)
    ast.parse(result.setup_content)
    return (target / "generated.cpp").read_text(encoding="utf8")


@pytest.mark.parametrize(
    "name",
    [
        "cppnamespaces",
        "abstractclass",
        "complexhierarchy",
        "vinheritance",
        "overload",
        "cppoperators",
        "pythonkeywords",
        "sgetternameclash",
        "nodefaultctor",
        "twoctors",
        "lref",
        "staticattr",
        "vectorofstruct",
        "native_memory",
        "missingdefaultctor",
        "missingassignmentop",
    ],
)
def test_portable_existing_headers_translate_to_cpp(tmp_path, name):
    header = TESTCASES / f"{name}.hpp"
    # This suite intentionally uses headers that do not need an installed SDK.
    if "#include <" in header.read_text(encoding="utf8"):
        pytest.skip("This original fixture requires C++ standard-library headers")
    result = make_wrapper(
        Config(headers=[str(header)], target=str(tmp_path), build=False)
    )
    translate(result, tmp_path)


@pytest.fixture
def wrapper(tmp_path):
    header = tmp_path / "fixture.hpp"
    header.write_text(
        """
namespace demo {
enum class Color { RED, BLUE };
Color identity(Color color);
struct Value {
    int number;
    Value(int n = 3) : number(n) {}
    Value clone() const;
    Value* borrowed();
    static Value* allocate();
};
struct Owner {
    Value child;
    Value* pointer;
};
Value make_value();
Value* borrow(Value* value);
Value* create_owned();
Value* use_result(Value* result, Value* obj, Value* _cpp2py_result);
int sum(const int* values);
int* first(int* values);
int strings(char** words);
long long_value(long n);
char character(char c = 'x');
int defaults(bool enabled = true, const char* text = "a\\\"b");
const char* greeting();
}
#define ENABLED true
""",
        encoding="utf8",
    )
    return make_wrapper(
        Config(
            headers=[str(header)],
            target=str(tmp_path),
            return_policies={
                "demo::create_owned": "owned",
                "demo::Value::allocate": "owned",
            },
        )
    )


def test_pointer_policy_and_value_copy_translate_without_compiler(wrapper, tmp_path):
    source = wrapper.source_content
    assert "new cpp.Value(cpp.make_value())" in source
    assert "malloc" not in source
    assert "_cpp2py_object._keepalive = self" in source
    assert "_cpp2py_object._keepalive = (value,)" in source
    assert "_cpp2py_object.owner = True" in source
    assert "_cpp2py_object.owner = False" in source
    assert "cdef cpp.Value * _cpp2py_result_" in source
    assert "Optional[Value]" in wrapper.stub_content
    generated = translate(wrapper, tmp_path)
    assert "new demo::Value" in generated
    assert "__Pyx_Optional_Type<demo::Value>" in generated
    assert "this->emplace(std::forward<U>(rhs))" in generated


def test_buffers_and_string_pointer_storage_are_guarded(wrapper):
    source = wrapper.source_content
    assert "const int[::1] values" in source
    assert "values.shape[0] == 0" in source
    assert "vector[char*] _words_pointers" in source
    assert "_words_strings" in source
    assert "malloc" not in source
    assert "if _cpp2py_result == NULL:" in source


def test_default_literals_and_platform_numeric_widths(wrapper):
    assert "enabled = True" in wrapper.source_content
    assert "char c = 120" in wrapper.source_content
    assert "np.float128" not in wrapper.stub_content
    expected = "np.int32" if sys.platform == "win32" else "np.int64"
    assert f"n: {expected}" in wrapper.stub_content


def test_setup_paths_are_valid_python_strings(tmp_path):
    directory = tmp_path / "include folder"
    directory.mkdir()
    header = directory / "input.hpp"
    header.write_text("int f(int n);\n", encoding="utf8")
    result = make_wrapper(
        Config(
            headers=[str(header)],
            target=str(tmp_path / "output"),
            sources=[str(header)],
            incdirs=[str(directory)],
            library_dirs=[str(directory)],
            compiler_flags=('quoted="value"',),
        )
    )
    tree = ast.parse(result.setup_content)
    literals = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]
    expected_include = str(Path("..") / "include folder")
    assert expected_include in literals
    assert 'quoted="value"' in literals


def test_class_vector_template_initializes_cpp_local(tmp_path):
    # Test the converter's intermediate model without pretending to supply
    # real STL headers to libclang. Native STL parsing remains an integration test.
    header = tmp_path / "value.hpp"
    header.write_text("struct Value { int number; };\n", encoding="utf8")
    config = Config(headers=[str(header)], modulename="class_vector", build=False)
    includes = Imports("class_vector_header")
    objects = parse(config, includes)
    value_type = CXXType(None, TypeKind.RECORD, "Value", "Value", "Value")
    vector_type = CXXType(
        None,
        TypeKind.RECORD,
        "std::vector<Value>",
        "vector[Value]",
        "vector[Value]",
        template_args=[value_type],
    )
    void_type = CXXType(None, TypeKind.VOID, "void", "void", "void")
    objects.functions["consume"].append(
        Function(
            name="consume",
            filename=header.as_posix(),
            ret_type=void_type,
            args=[Variable(name="entries", type=vector_type)],
        )
    )
    includes.add_stl("std::vector")
    init_converters([])
    processed = Postprocessor(objects, includes, config).generate_output()
    source = (
        "# cython: cpp_locals=True\n"
        + includes.implementations_import()
        + ImplGenerator(processed, config).generate()
    )
    declarations = includes.declarations_import() + DeclGenerator(objects).generate()
    result = WrapperResult(
        source,
        "class_vector.pyx",
        declarations,
        "class_vector_header.pxd",
        "",
        "setup.py",
        StubGenerator(processed, config).generate(),
        "class_vector.pyi",
    )
    assert "_entries = vector[cpp.Value]()" in source
    assert "entries_element.thisptr == NULL" in source
    translate(result, tmp_path)
