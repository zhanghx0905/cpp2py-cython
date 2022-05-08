from __future__ import annotations

from dataclasses import dataclass, field
from typing import Set

from clang.cindex import Type, TypeKind

from .config import Imports
from .utils import remove_namespace

_PTR_TYPEKIND = {TypeKind.POINTER, TypeKind.LVALUEREFERENCE, TypeKind.RVALUEREFERENCE}


@dataclass
class CXXType:
    type: Type
    kind: TypeKind

    cppname: str
    name: str  # remove namespace and replace <> to []
    plain_name: str  # remove reference and const quailfier

    canonical: CXXType | None = None
    pointee: CXXType | None = None
    ele_type: CXXType | None = None  # for const length array
    template_args: list[CXXType] = field(default_factory=list)

    def get_canonical(self):
        return self if self.canonical is None else self.canonical

    def __str__(self) -> str:
        return self.name

    @classmethod
    def build(cls, type: Type, includes: Imports, cache: dict[str, CXXType]) -> CXXType:
        def recursive_build(type: Type):
            cppname = type.spelling
            if cppname in cache:
                return cache[cppname]
            includes.add_stl(cppname)

            kind = type.kind
            template_args = []
            pointee = canonical = ele_type = None
            if kind in _PTR_TYPEKIND:
                pointee = recursive_build(type.get_pointee())
            elif (num := type.get_num_template_arguments()) > 0:
                template_args = [
                    recursive_build(type.get_template_argument_type(i))
                    for i in range(num)
                ]
            else:
                try:
                    cpp_ele_type = type.element_type
                except Exception:
                    ...
                else:
                    ele_type = recursive_build(cpp_ele_type)

            if type != type.get_canonical():
                canonical = recursive_build(type.get_canonical())

            name = remove_namespace(type.spelling).replace("<", "[").replace(">", "]")
            plain_name = (
                name.replace("const ", "")
                .replace("*const", "*")
                .replace(" &", "")
                .replace(" &&", "")
            )
            ret = cls(
                type=type,
                kind=kind,
                cppname=cppname,
                name=name,
                plain_name=plain_name,
                canonical=canonical,
                pointee=pointee,
                ele_type=ele_type,
                template_args=template_args,
            )
            cache[cppname] = ret
            return ret

        return recursive_build(type)


@dataclass
class TypeNames:
    classes: Set[str]
    enums: Set[str]
