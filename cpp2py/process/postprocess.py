import warnings
from dataclasses import dataclass, field
from functools import partial
from itertools import chain
from typing import Callable, List, Optional, Set, Union

from ..config import Config, Imports
from ..typesystem import TypeNames
from .func import (
    AUTO,
    ConstructorGenerator,
    FunctionGenerator,
    GetterGenerator,
    MethodGenerator,
    SetterGenerator,
    StaticMethodGenerator,
)
from ..parser import Class, Function, Macro, Method, ParseResult, Variable
from ..utils import toposort


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
        self._rename_symbols()
        self._handle_inheritance()
        self._bind_generators()
        return self.output

    def _rename_symbols(self):
        namedict = {}
        for key, value in self.config.renames_dict.items():
            if len(key) > 1:
                key = (key[0], key[1].replace(" ", ""))
            namedict[key] = value

        def need_renamed(objects: ParseResult):
            yield from chain(*objects.functions.values())
            for class_ in objects.classes.values():
                # yield from class_.ctors
                yield from chain(*class_.methods.values())

        for func in need_renamed(self.objects):
            newname = func.name
            key = (func.fullname,)
            if key in namedict:
                newname = namedict[key]
            else:
                key = func.fullname, func.type.replace(" ", "")
                if key in namedict:
                    newname = namedict[key]
            func.name = newname

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
            for class_name in tset:
                _copy_from_supers(class_dict[class_name])

    def _bind_overloaded_functions(
        self, funcs: List[Function], generator_builder: Callable[..., FunctionGenerator]
    ):
        names: Set[str] = set()
        ret = []
        for func in funcs:
            if func.name in names:
                warnings.warn(
                    f"Ignoring overloaded {func.__class__.__name__}: {func.fullname}"
                )
                continue
            try:
                generator = generator_builder(func)
            except NotImplementedError as err:
                warnings.warn(f"{err} ignoring '{func.fullname}'")
            else:
                ret.append((func, generator))
                names.add(func.name)
        return ret

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
            for fun_gen in ret:
                self.output.functions.append(BindedFunc(*fun_gen))

        for class_ in self.objects.classes.values():
            bclass = BindedClass(class_.name)

            # build functions
            method_builder = partial(self._method_builder, class_name=class_.name)
            for methods in class_.methods.values():
                ret = self._bind_overloaded_functions(methods, method_builder)
                for fun_gen in ret:
                    bclass.methods.append(BindedFunc(*fun_gen))

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
            if ret:
                bclass.ctor = BindedFunc(*ret[0])

            # build fields
            for field in class_.fields:
                bfield = self._bind_var(field, class_.name, True)
                if bfield is not None:
                    bclass.fields.append(bfield)

            self.output.classes.append(bclass)
