import os
import re
from itertools import count, tee
from typing import Dict, List
from warnings import warn

from clang import cindex
from clang.cindex import Cursor, CursorKind
from more_itertools import ilen, last, partition, split_at

from ..config import Config, Imports
from ..typesystem import CXXType
from ..utils import remove_namespace
from .libclang import CLANG_INCDIR
from .parser_types import (
    Class,
    Enum,
    Function,
    Macro,
    Method,
    ParseResult,
    RecordType,
    Typedef,
    Variable,
)
from .utils import (
    OPERATORS_MAPPER,
    is_operator,
    join_namespace,
    parse_literal_cursor,
    parse_literal_digit,
    split_namespace,
    unary_operators,
)


class ClangError(Exception):
    def __init__(self, diags):
        super().__init__(os.linesep.join(str(diag) for diag in diags))


def _check_diagnostics(diagnostics: List[cindex.Diagnostic]):
    critical, non_critical = partition(
        lambda d: d.severity <= cindex.Diagnostic.Warning,
        diagnostics,
    )
    for diag in non_critical:
        warn(f"Diagnostic: {diag}")
    c1, c2 = tee(critical, 2)
    if ilen(c1):
        raise ClangError(c2)


def is_ignored_method(cur: Cursor):
    """unpublic or deleted method"""
    return (
        cur.access_specifier != cindex.AccessSpecifier.PUBLIC
        or last(cur.get_tokens(), "") == "delete"
    )


def set_when_missing(dic: dict, symbol):
    if symbol.name in dic:
        warn(
            f"Ignoring {symbol.__class__.__name__} {dic[symbol.name].fullname} "
            f"for name conflicts with {symbol.fullname}."
        )
    dic[symbol.name] = symbol


class ClangParser:
    def __init__(
        self, cursor: Cursor, headers_mapper: Dict[str, str], includes: Imports
    ):
        self.root_cursor = cursor
        self.fmapper = headers_mapper
        self.objects = ParseResult()
        self.includes = includes
        self.cxxtypes: Dict[str, CXXType] = {}

    def get_filename(self, cur: Cursor):
        return self.fmapper[cur.location.file.name]

    def build_cxxtype(self, type: cindex.Type):
        return CXXType.build(type, self.includes, self.cxxtypes)

    def parse(self):
        for ac in self.root_cursor.walk_preorder():
            if ac.location.file is None or ac.location.file.name not in self.fmapper:
                continue
            if ac.kind == CursorKind.MACRO_DEFINITION:
                self._process_macro(ac)
        self._process_namespace(self.root_cursor, "")
        return self.objects

    def _process_namespace(self, cursor: Cursor, namespace: str):
        for cur in cursor.get_children():
            if (
                cur.location.file is not None
                and cur.location.file.name not in self.fmapper
            ):
                continue
            if cur.kind == CursorKind.UNEXPOSED_DECL:  # extern "C" {}
                self._process_namespace(cur, namespace)
            elif cur.kind == CursorKind.NAMESPACE:
                subns = join_namespace(namespace, cur.spelling)
                self._process_namespace(cur, subns)
            elif cur.kind == CursorKind.FUNCTION_DECL:
                self._process_function(cur, namespace)
            elif cur.kind == CursorKind.ENUM_DECL:
                if cur.is_anonymous():
                    return
                self._process_enum(cur)
            elif cur.kind in {
                CursorKind.CLASS_DECL,
                CursorKind.STRUCT_DECL,
                CursorKind.UNION_DECL,
            }:
                if cur.is_anonymous():
                    return
                self._process_class(cur)
            elif cur.kind in {CursorKind.TYPEDEF_DECL, CursorKind.TYPE_ALIAS_DECL}:
                self._process_typedef(cur, namespace)
            elif cur.kind == CursorKind.VAR_DECL:
                self._process_variable(cur, namespace)

    def _process_variable(self, cur: Cursor, namespace: str):
        if cur.semantic_parent != cur.lexical_parent:
            return
        type = self.build_cxxtype(cur.type)

        var = Variable(
            name=cur.spelling,
            filename=self.get_filename(cur),
            type=type,
            namespace=namespace,
            is_const=type.get_canonical().type.is_const_qualified(),
        )
        set_when_missing(self.objects.variables, var)

    def _process_parameter(self, cur: Cursor, func: Function, default_name: str):
        var = Variable(
            # if the argument has no name, we need a default one
            name=cur.spelling or default_name,
            filename=self.get_filename(cur),
            type=self.build_cxxtype(cur.type),
        )

        tokens = list(
            split_at(cur.get_tokens(), lambda token: token.spelling == "=", maxsplit=1)
        )
        if len(tokens) == 2:
            var.value = self._parse_var_literal(tokens[1])
        func.args.append(var)

    def _process_function(self, cur: Cursor, namespace: str):
        if is_operator(cur.spelling):
            # only support operator overloading in methods
            return
        arg_counter = count()
        func = Function(
            name=cur.spelling,
            filename=self.get_filename(cur),
            namespace=namespace,
            ret_type=self.build_cxxtype(cur.result_type),
        )
        for ac in cur.get_arguments():
            self._process_parameter(ac, func, f"arg{next(arg_counter)}")
        self.objects.functions[func.name].append(func)

    UNDERLYING_TYPE_PATTERN = re.compile(r"^(struct|enum|union|class) ")

    def _process_typedef(self, cur: Cursor, namespace: str):
        uname = cur.underlying_typedef_type.spelling
        uname = self.UNDERLYING_TYPE_PATTERN.sub("", uname)
        uname = remove_namespace(uname)
        if uname == cur.spelling:
            return
        typedef = Typedef(
            name=cur.spelling,
            filename=self.get_filename(cur),
            namespace=namespace,
            underlying_type=uname,
        )
        self.objects.typedefs.append(typedef)

    def _process_enum(self, cur: Cursor):
        constant_namespace = cur.type.spelling
        namespace, name = split_namespace(constant_namespace)
        enum = Enum(
            name=name,
            filename=self.get_filename(cur),
            namespace=namespace,
            constants=[
                Variable(
                    name=i.spelling, namespace=constant_namespace, value=i.enum_value
                )
                for i in cur.get_children()
            ],
        )
        set_when_missing(self.objects.enums, enum)

    def _process_class(self, cur: Cursor):
        class_namespace, class_name = split_namespace(cur.type.spelling)
        class_ = Class(
            name=class_name,
            filename=self.get_filename(cur),
            namespace=class_namespace,
            rtype=RecordType.build(cur.kind),
            is_abstract=cur.is_abstract_record(),
        )
        self._process_class_children(cur, class_)
        set_when_missing(self.objects.classes, class_)

    def _process_class_children(self, cur: Cursor, class_: Class):
        child_namespace = cur.type.spelling
        for ac in cur.get_children():
            if ac.kind == CursorKind.CXX_BASE_SPECIFIER:
                if ac.access_specifier != cindex.AccessSpecifier.PUBLIC:
                    continue
                class_.bases.add(ac.type.spelling)
            elif ac.kind == CursorKind.CXX_METHOD:
                self._process_method(ac, class_)
            elif ac.kind == CursorKind.CONSTRUCTOR:
                self._process_ctor(ac, class_)
            elif ac.kind == CursorKind.FIELD_DECL:
                if (
                    ac.access_specifier != cindex.AccessSpecifier.PUBLIC
                    or ac.is_anonymous()
                ):
                    continue
                self._process_field(ac, class_)
            elif ac.kind == CursorKind.VAR_DECL:
                if (
                    ac.access_specifier != cindex.AccessSpecifier.PUBLIC
                    or ac.is_anonymous()
                ):
                    continue
                self._process_variable(ac, child_namespace)
            elif ac.kind == CursorKind.ENUM_DECL:
                if ac.is_anonymous():
                    continue
                self._process_enum(ac)
            elif ac.kind in {
                CursorKind.CLASS_DECL,
                CursorKind.STRUCT_DECL,
                CursorKind.UNION_DECL,
            }:
                if ac.is_anonymous():
                    continue
                self._process_class(ac)
            elif ac.kind in {CursorKind.TYPEDEF_DECL, CursorKind.TYPE_ALIAS_DECL}:
                self._process_typedef(ac, cur.type.spelling)

    def _process_field(self, cur: Cursor, class_: Class):
        var = Variable(
            name=cur.spelling,
            filename=self.get_filename(cur),
            type=self.build_cxxtype(cur.type),
        )
        class_.fields.append(var)

    def _process_method(self, cur: Cursor, class_: Class):
        if is_ignored_method(cur):
            return
        if is_operator(cur.spelling) and cur.spelling not in OPERATORS_MAPPER:
            warn(f"{cur.location} {cur.spelling} is not supported.")
            return
        arg_counter = count()
        func = Method(
            name=cur.spelling,
            ret_type=self.build_cxxtype(cur.result_type),
            is_const=cur.is_const_method(),
            is_static=cur.is_static_method(),
            is_pure_virtual=cur.is_pure_virtual_method(),
        )

        for ac in cur.get_arguments():
            self._process_parameter(ac, func, f"arg{next(arg_counter)}")
        class_.methods[func.name].append(func)

    def _process_ctor(self, cur: Cursor, class_: Class):
        if not cur.is_default_constructor():
            # has constructor other than default constructor
            class_.auto_default_constructible = False
        if is_ignored_method(cur):
            if cur.is_default_constructor():
                # explicitly deleted default constructor
                class_.auto_default_constructible = False
            return
        if cur.is_copy_constructor() or cur.is_move_constructor():
            return

        arg_counter = count()
        func = Method(
            name=cur.spelling,
            ret_type=self.build_cxxtype(cur.result_type),
        )

        for ac in cur.get_arguments():
            self._process_parameter(ac, func, f"arg{next(arg_counter)}")
        class_.ctors.append(func)

    @staticmethod
    def _parse_var_literal(expressions: List[cindex.Token]):
        # only support: literal/ unary_operator literal
        if len(expressions) not in [1, 2]:
            return None
        l = expressions[-1]
        literal = parse_literal_cursor(l.cursor.kind, l.spelling)
        if len(expressions) == 1:
            return literal
        if len(expressions) == 2 and isinstance(literal, (int, float)):
            unary_op = unary_operators(expressions[0].spelling)
            return unary_op(literal)
        return None

    def _process_macro(self, c: Cursor):
        tokens = c.get_tokens()
        next(tokens)
        definition = " ".join(i.spelling for i in tokens)
        literal = parse_literal_digit(definition)
        if literal is None:
            return
        m = Macro(name=c.spelling, filename=self.get_filename(c), literal=literal)
        set_when_missing(self.objects.macros, m)


def parse(config: Config, includes: Imports):
    args = [
        "-Wno-pragma-once-outside-header",
        f"-I{CLANG_INCDIR}",
        *[f"-I{include}" for include in config.incdirs],
        *[flag for flag in config.libclang_flags],
    ]

    headers = [path.split(os.sep)[-1] for path in config.headers]
    dummy_name = "./__dummy.cxx"
    dummy_content = os.linesep.join(f'#include "{h}"' for h in headers)
    # https://stackoverflow.com/questions/60311504/clang-cindex-cant-find-header-in-unsaved-files
    headers = [f"./{h}" for h in headers]
    headers_mapper = dict(zip(headers, config.headers))

    unsaved_files = [[dummy_name, dummy_content]]
    for header, path in headers_mapper.items():
        with open(path, encoding=config.encoding) as f:
            unsaved_files.append([header, f.read()])

    idx = cindex.Index.create()
    root = idx.parse(
        path=dummy_name,
        args=args,
        unsaved_files=unsaved_files,
        options=(
            cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD
            | cindex.TranslationUnit.PARSE_SKIP_FUNCTION_BODIES
        ),
    )
    _check_diagnostics(root.diagnostics)

    parser = ClangParser(root.cursor, headers_mapper, includes)
    ret = parser.parse()
    return ret
