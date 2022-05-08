import warnings
from dataclasses import dataclass, field
from functools import partial
from typing import Callable, List, Optional, Set

from enum import Enum as pyEnum

from .config import Config, Imports
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
    setter: Optional[SetterGenerator] = None


@dataclass
class BindedClass:
    name: str
    ctor: Optional[BindedFunc] = None
    methods: List[BindedFunc] = field(default_factory=list)
    fields: List[BindedField] = field(default_factory=list)


@dataclass
class ProcessOutput:
    objects: ParseResult
    vars: List[BindedField] = field(default_factory=list)
    classes: List[BindedClass] = field(default_factory=list)
    # functions remove overloaded
    functions: List[BindedFunc] = field(default_factory=list)


@dataclass
class TypeNames:
    classes: Set[str]
    enums: Set[str]


class VarType(pyEnum):
    FIELD = 0
    GLOBAL_VAR = 1
    MACRO = 2


class Postprocessor:
    def __init__(self, objects: ParseResult, includes: Imports, config: Config):
        self.objects = objects
        self.typenames = TypeNames(
            set(self.objects.classes.keys()), set(self.objects.enums.keys())
        )
        self.includes = includes
        self.config = config

    def generate_output(self):
        self.output = ProcessOutput(self.objects)
        self._handle_inheritance()
        self._bind_generators()
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
            chains: List[Class] = [leaf_class]
            while base is not None and base in class_dict:
                class_ = class_dict[base]
                chains.append(class_)
                base = class_.base
            chains.reverse()

            base_methods = chains[0].methods
            base_fields = chains[0].fields
            for class_ in chains[1:]:
                for method_name, methods in base_methods.items():
                    if method_name not in class_.methods.keys():
                        # copy the method from base to subclass
                        class_.methods[method_name].extend(methods)
                class_fields = {field.name for field in class_.fields}
                for field in base_fields:
                    if field.name not in class_fields:
                        class_.fields.append(field)

                base_methods = class_.methods
                base_fields = class_.fields

        for leaf_name in leaf_names:
            _copy_base_methods(class_dict[leaf_name])

    def _bind_overloaded_functions(
        self, funcs: List[Function], generator_builder: Callable[..., FunctionGenerator]
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

    def _bind_var(self, var: Variable, class_name: str, vartype: VarType):

        try:
            getter = GetterGenerator(
                var.name,
                var.type,
                self.classnames,
                self.includes,
                class_name,
            )
        except NotImplementedError as err:
            warnings.warn(f"{err} ignoring field '{var.name}'")
            return None

        if not var.type.type.is_const_qualified():
            try:
                setter = SetterGenerator(
                    var.name,
                    var.type,
                    self.classnames,
                    self.includes,
                    class_name,
                )
            except NotImplementedError as err:
                warnings.warn(f"{err} ignoring field '{var.name}' setter")
        # return bfield

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

    def _bind_generators(self):
        vars = []
        for var in self.objects.variables.values():
            bvar = self._bind_var(var, self.config.global_vars, VarType.GLOBAL_VAR)
            if bvar is not None:
                vars.append(bvar)

        for funcs in self.objects.functions.values():
            ret = self._bind_overloaded_functions(
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
                ret = self._bind_overloaded_functions(methods, method_builder)
                if ret is not None:
                    bclass.methods.append(BindedFunc(*ret))

            # build constructor
            ctors = []
            if not class_.is_abstract:
                if class_.ctors:
                    ctors = class_.ctors
                elif class_.auto_default_constructible:
                    ctors.append(Method(class_.name, args=[]))
            ret = self._bind_overloaded_functions(
                ctors,
                lambda ctor: ConstructorGenerator(
                    ctor.args, self.classnames, self.includes, class_.name
                ),
            )
            if ret is not None:
                bclass.ctor = BindedFunc(*ret)

            # build fields
            for field in class_.fields:
                bfield = self._bind_var(field, class_.name, VarType.FIELD)
                if bfield is not None:
                    bclass.fields.append(bfield)

            self.output.classes.append(bclass)
