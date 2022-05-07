import os
from itertools import chain, groupby

from ..parser import Class, Enum, Function, Macro, ParseResult, Typedef, Variable
from ..utils import render

# declaration templates
TYPEDEF_DECL = """ctypedef %(underlying_type)s %(name)s"""
FUNC_DECL = """%(ret_type)s %(decl)s(%(args)s) except +"""
CONSTRUCTOR_DECL = "%(class_name)s(%(args)s) except +"
VAR_DECL = "%(type)s %(decl)s"
ARG_DECL = "%(type)s %(name)s"
MACRO_DECL = """cdef enum:
    %(decl)s"""


def _gen_args_decl(func: Function):
    return ", ".join(ARG_DECL % arg.__dict__ for arg in func.args)


def split_symbols(objects: ParseResult):
    symbols = list(
        chain(
            objects.macros.values(),
            objects.variables.values(),
            objects.typedefs,
            *objects.functions.values(),
            objects.enums.values(),
            objects.classes.values(),
        )
    )

    def keyfunc(symbol):
        return (symbol.filename, symbol.namespace)

    symbols.sort(key=keyfunc)
    yield from groupby(symbols, keyfunc)


def process_enum(enum: Enum):
    return render("enum_decl", enum=enum)


def process_variable(var: Variable):
    return VAR_DECL % var.__dict__


def process_typedef(typedef: Typedef):
    return TYPEDEF_DECL % typedef.__dict__


def process_function(func: Function):
    return FUNC_DECL % {
        **func.__dict__,
        "args": _gen_args_decl(func),
    }


def process_macro(macro: Macro):
    return MACRO_DECL % macro.__dict__


def process_class(class_: Class):
    fields = [VAR_DECL % field.__dict__ for field in class_.fields]
    ctors = [
        CONSTRUCTOR_DECL % {"class_name": class_.name, "args": _gen_args_decl(ctor)}
        for ctor in class_.ctors
    ]
    methods = []
    for method in chain(*class_.methods.values()):
        mgen = FUNC_DECL % {**method.__dict__, "args": _gen_args_decl(method)}
        if method.is_static:
            mgen = f"@staticmethod{os.linesep}{mgen}"
        methods.append(mgen)

    class_decl = {
        "name": class_.name,
        "fields": fields,
        "ctors": ctors,
        "methods": methods,
    }
    return render("class_decl", **class_decl)


_SYMBOL_HANDLER = {
    Macro: process_macro,
    Variable: process_variable,
    Typedef: process_typedef,
    Function: process_function,
    Enum: process_enum,
    Class: process_class,
}


class DeclGenerator:
    def __init__(self, objects: ParseResult) -> None:
        self.objects = split_symbols(objects)

    def generate(self):
        outputs = []
        for key, group in self.objects:
            cppdecls = []
            cdecls = []

            for symbol in group:
                gen = _SYMBOL_HANDLER[symbol.__class__](symbol)
                if symbol.__class__ is Macro:
                    cdecls.append(gen)
                else:
                    cppdecls.append(gen)
            outputs.append(
                render(
                    "declarations",
                    **{
                        "filename": key[0],
                        "namespace": key[1],
                        "cppdecls": cppdecls,
                        "cdecls": cdecls,
                    },
                )
            )
        return os.linesep.join(outputs)
