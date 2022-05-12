import warnings
from dataclasses import dataclass, field
from functools import partial
from itertools import chain
from typing import Callable, List, Optional, Union

from .config import Config, Imports
from .cxxtypes import TypeNames
from .generator.func import (
    AUTO,
    ConstructorGenerator,
    FunctionGenerator,
    GetterGenerator,
    MethodGenerator,
    SetterGenerator,
    StaticMethodGenerator,
)
from .parser import Class, Function, Macro, Method, ParseResult, Variable
from .utils import toposort


@dataclass
class BindedFunc:
    func: Function
    generator: FunctionGenerator


@dataclass
class BindedVar:
    name: str
    getter: GetterGenerator
    setter: Optional[SetterGenerator] = None


@dataclass
class BindedClass:
    name: str
    ctor: Optional[BindedFunc] = None
    methods: List[BindedFunc] = field(default_factory=list)
    fields: List[BindedVar] = field(default_factory=list)


@dataclass
class ProcessOutput:
    objects: ParseResult
    vars: List[BindedVar] = field(default_factory=list)
    classes: List[BindedClass] = field(default_factory=list)
    # functions remove overloaded
    functions: List[BindedFunc] = field(default_factory=list)


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
        """Copies methods/fields from base classes to subclasses."""
        class_dict = {node.fullname: node for node in self.objects.classes.values()}
        dep_map = {
            class_.fullname: {class_dict[name].fullname for name in class_.bases}
            for class_ in self.objects.classes.values()
        }
        toposets = toposort(dep_map)

        def _copy_from_supers(leaf_class: Class):
            supers = dep_map[leaf_class.fullname]
            for superclass_name in supers:
                superclass = class_dict[superclass_name]
                for method_name, methods in superclass.methods.items():
                    if method_name not in leaf_class.methods.keys():
                        # copy the method from base to subclass
                        leaf_class.methods[method_name].extend(methods)
                class_fields = {field.name for field in leaf_class.fields}
                for field in superclass.fields:
                    if field.name not in class_fields:
                        leaf_class.fields.append(field)

        for tset in toposets:
            for leaf_class_name in tset:
                _copy_from_supers(class_dict[leaf_class_name])

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

    def _bind_var(self, var: Union[Variable, Macro], class_name: str, is_field: bool):
        if isinstance(var, Macro):
            vtype = AUTO
            no_setter = True
        else:
            vtype = var.type
            no_setter = var.type.get_canonical().type.is_const_qualified()
        prefix = "self.thisptr" if is_field else "cpp"
        try:
            getter = GetterGenerator(
                var.name, vtype, self.typenames, self.includes, class_name, prefix
            )
        except NotImplementedError as err:
            warnings.warn(f"{err} ignoring field '{var.name}'")
            return None
        setter = None
        if not no_setter:
            try:
                setter = SetterGenerator(
                    var.name,
                    vtype,
                    self.typenames,
                    self.includes,
                    class_name,
                    prefix,
                )
            except NotImplementedError as err:
                warnings.warn(f"{err} ignoring field '{var.name}' setter")
        return BindedVar(var.name, getter, setter)

    def _method_builder(self, m: Method, class_name: str):
        builder = StaticMethodGenerator if m.is_static else MethodGenerator
        return builder(
            m.name,
            m.args,
            m.ret_type,
            self.typenames,
            self.includes,
            class_name,
        )

    def _bind_generators(self):
        # bind global variables and macros
        for var in chain(self.objects.variables.values(), self.objects.macros.values()):
            bvar = self._bind_var(var, f"_{self.config.global_vars}", False)
            if bvar is not None:
                self.output.vars.append(bvar)

        # bind functions
        for funcs in self.objects.functions.values():
            ret = self._bind_overloaded_functions(
                funcs,
                lambda func: FunctionGenerator(
                    func.name, func.args, func.ret_type, self.typenames, self.includes
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
                    ctor.args, self.typenames, self.includes, class_.name
                ),
            )
            if ret is not None:
                bclass.ctor = BindedFunc(*ret)

            # build fields
            for field in class_.fields:
                bfield = self._bind_var(field, class_.name, True)
                if bfield is not None:
                    bclass.fields.append(bfield)

            self.output.classes.append(bclass)
