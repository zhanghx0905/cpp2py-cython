from itertools import chain
import os

from ..parser import Function, ParseResult
from ..utils import render


# declaration templates
TYPEDEF_DECL = """cdef extern from "%(filename)s" namespace "%(namespace)s":
    ctypedef %(underlying_type)s %(name)s"""
FUNC_DECL = """cdef extern from "%(filename)s" namespace "%(namespace)s":
    %(ret_type)s %(decl)s(%(args)s) except +"""
METHOD_DECL = "%(ret_type)s %(decl)s(%(args)s) except +"
CONSTRUCTOR_DECL = "%(class_name)s(%(args)s) except +"
VAR_DECL = "%(type)s %(name)s"
CONSTANT_DECL = """cdef extern from "%(filename)s":
    cdef enum:
        %(decl)s
"""


def _gen_args_decl(func: Function):
    return ", ".join(VAR_DECL % arg.__dict__ for arg in func.args)


class DeclGenerator:
    def __init__(self, objects: ParseResult) -> None:
        self.objects = objects

    def generate(self):
        enums = [render("enum_decl", enum=enum) for enum in self.objects.enums.values()]
        typedefs = [
            TYPEDEF_DECL % typedef.__dict__ for typedef in self.objects.typedefs
        ]
        funcs = [
            FUNC_DECL
            % {
                **func.__dict__,
                "args": _gen_args_decl(func),
            }
            for func in chain(*self.objects.functions.values())
        ]
        constants = [
            CONSTANT_DECL % macro.__dict__ for macro in self.objects.macros.values()
        ]
        classes = []
        for class_ in self.objects.classes.values():
            fields = [VAR_DECL % field.__dict__ for field in class_.fields]
            ctors = [
                CONSTRUCTOR_DECL
                % {"class_name": class_.name, "args": _gen_args_decl(ctor)}
                for ctor in class_.ctors
            ]
            methods = []
            for method in chain(*class_.methods.values()):
                mgen = METHOD_DECL % {**method.__dict__, "args": _gen_args_decl(method)}
                if method.is_static:
                    mgen = f"@staticmethod{os.linesep}{mgen}"
                methods.append(mgen)

            class_decl = {
                "fields": fields,
                "ctors": ctors,
                "methods": methods,
            }
            class_decl["empty"] = not any(class_decl.values())
            # items in class_decl will override these of class_.__dict__
            class_decl = {**class_.__dict__, **class_decl}
            classes.append(render("class_decl", **class_decl))
        return render(
            "declarations",
            enums=enums,
            functions=funcs,
            typedefs=typedefs,
            classes=classes,
            constants=constants,
        )
