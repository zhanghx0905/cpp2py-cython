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


# workaround for function pointer and pointer array
def _handle_spcase(arg: Variable, template):
    if "(*)" in arg.type.cppname:
        idx = arg.type.cppname.find("(*)") + 2
        return arg.type.name[:idx] + arg.name + arg.type.name[idx:]
    if "*[" in arg.type.cppname:
        idx = arg.type.cppname.find("*[") + 1
        return f"{arg.type.name[:idx]} {arg.name}{arg.type.name[idx:]}"
    return template % arg.__dict__


def _gen_args_decl(func: Function):
    return ", ".join(_handle_spcase(arg, ARG_DECL) for arg in func.args)


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
    return render("decl/enum", enum=enum)


def process_variable(var: Variable):
    return _handle_spcase(var, VAR_DECL)


def process_typedef(typedef: Typedef):
    return TYPEDEF_DECL % typedef.__dict__


def process_function(func: Function):
    return FUNC_DECL % {
        **func.__dict__,
        "args": _gen_args_decl(func),
    }


_MACRO_TYPES = {int: "int", str: "const char *", float: "double"}


def process_macro(macro: Macro):
    assert type(macro.literal) in _MACRO_TYPES
    return VAR_DECL % {"decl": macro.decl, "type": _MACRO_TYPES[type(macro.literal)]}


def process_class(class_: Class):
    fields = [_handle_spcase(field, VAR_DECL) for field in class_.fields]
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
    return render("decl/class", **class_decl)


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

        def drender(**kwargs):
            return render("decl/declarations", **kwargs)

        for key, group in self.objects:
            typedefs = []
            cppdecls = []
            cdecls = []

            for symbol in group:
                gen = _SYMBOL_HANDLER[symbol.__class__](symbol)
                if symbol.__class__ is Macro:
                    cdecls.append(gen)
                elif symbol.__class__ is Typedef:
                    typedefs.append(gen)
                else:
                    cppdecls.append(gen)
            # typedef must generate first
            outputs.insert(
                0,
                drender(
                    filename=key[0],
                    cppnamespace=key[1],
                    decls=typedefs,
                ),
            )
            outputs.extend(
                [
                    drender(
                        filename=key[0],
                        cppnamespace=key[1],
                        decls=cppdecls,
                    ),
                    drender(
                        filename=key[0],
                        decls=cdecls,
                    ),
                ]
            )

        return os.linesep.join(outputs)
