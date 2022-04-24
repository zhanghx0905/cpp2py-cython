import warnings
from dataclasses import dataclass, field
from functools import partial
from typing import Callable

from .config import Imports
from .generator.func import (
    ConstructorGenerator,
    FunctionGenerator,
    GetterGenerator,
    MethodGenerator,
    SetterGenerator,
    StaticMethodGenerator,
)
from .parser import Class, Function, Method, ParseResult, Variable


@dataclass
class BindedFunc:
    func: Function
    generator: FunctionGenerator


@dataclass
class BindedField:
    field: Variable
    getter: GetterGenerator
    setter: SetterGenerator | None = None


@dataclass
class BindedClass:
    name: str
    ctor: BindedFunc | None = None
    methods: list[BindedFunc] = field(default_factory=list)
    fields: list[BindedField] = field(default_factory=list)


@dataclass
class ProcessOutput:
    objects: ParseResult
    classes: list[BindedClass] = field(default_factory=list)
    # functions remove overloaded
    functions: list[BindedFunc] = field(default_factory=list)


def _bind_overloaded_functions(
    funcs: list[Function], generator_builder: Callable[..., FunctionGenerator]
):
    for idx, func in enumerate(funcs):
        try:
            generator = generator_builder(func)
        except NotImplementedError as err:
            warnings.warn(f"{err} ignoring '{func.fullname}'")
        else:
            if idx != len(funcs) - 1:
                warnings.warn(
                    f"Ignoring overloaded {func.__class__.__name__}: {func.fullname}"
                )
            return func, generator
    return None


class Postprocessor:
    def __init__(self, objects: ParseResult, includes: Imports):
        self.objects = objects
        self.classnames = set(self.objects.classes.keys())
        self.includes = includes

    def generate_output(self):
        self.output = ProcessOutput(self.objects)
        self._handle_inheritance()
        self._handle_overloading_or_no_ctors()
        return self.output

    def _handle_inheritance(self):
        """Copies methods from base classes to subclasses."""
        class_dict = {node.fullname: node for node in self.objects.classes.values()}
        # class with out subclasses
        leaf_names = set(class_dict.keys()) - {
            clas.base for clas in class_dict.values()
        }

        def _copy_base_methods(leaf_class: Class):
            base = leaf_class.base
            chains: list[Class] = [leaf_class]
            while base is not None and base in class_dict:
                class_ = class_dict[base]
                chains.append(class_)
                base = class_.base
            chains.reverse()

            base_methods = chains[0].methods

            for class_ in chains[1:]:
                for method_name in base_methods:
                    if method_name not in class_.methods.keys():
                        # copy the method from base to subclass
                        added = base_methods[method_name][0]
                        class_.methods[method_name].append(added)
                base_methods = class_.methods

        for leaf_name in leaf_names:
            _copy_base_methods(class_dict[leaf_name])

    def _method_builder(self, m: Method, class_name: str):
        builder = StaticMethodGenerator if m.is_static else MethodGenerator
        return builder(
            m.name,
            m.args,
            m.ret_type,
            self.classnames,
            self.includes,
            class_name,
        )

    def _handle_overloading_or_no_ctors(self):
        for funcs in self.objects.functions.values():
            ret = _bind_overloaded_functions(
                funcs,
                lambda func: FunctionGenerator(
                    func.name, func.args, func.ret_type, self.classnames, self.includes
                ),
            )
            if ret is not None:
                self.output.functions.append(BindedFunc(*ret))

        for class_ in self.objects.classes.values():
            bclass = BindedClass(class_.name)

            # build functions
            method_builder = partial(self._method_builder, class_name=class_.name)
            for methods in class_.methods.values():
                ret = _bind_overloaded_functions(methods, method_builder)
                if ret is not None:
                    bclass.methods.append(BindedFunc(*ret))

            # build constructor
            ctors = []
            if not class_.is_abstract:
                if class_.ctors:
                    ctors = class_.ctors
                elif class_.auto_default_constructible:
                    ctors.append(Method(class_.name, args=[]))
            ret = _bind_overloaded_functions(
                ctors,
                lambda ctor: ConstructorGenerator(
                    ctor.args, self.classnames, self.includes, class_.name
                ),
            )
            if ret is not None:
                bclass.ctor = BindedFunc(*ret)

            # build fields
            for field in class_.fields:
                try:
                    bfield = BindedField(
                        field,
                        getter=GetterGenerator(
                            field.name,
                            field.type,
                            self.classnames,
                            self.includes,
                            class_.name,
                        ),
                    )
                    if not field.type.type.is_const_qualified():
                        bfield.setter = SetterGenerator(
                            field.name,
                            field.type,
                            self.classnames,
                            self.includes,
                            class_.name,
                        )
                except NotImplementedError as err:
                    warnings.warn(f"{err} ignoring field '{field.name}'")
                else:
                    bclass.fields.append(bfield)

            self.output.classes.append(bclass)
