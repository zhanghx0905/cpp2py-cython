import os
from typing import Callable

from ..config import Config
from ..postprocess import ProcessOutput
from ..utils import render


class BaseImplGenerator:
    def __init__(self, process_ret: ProcessOutput, config: Config) -> None:
        self.config = config

        self.enums = process_ret.objects.enums.values()
        self.vars = process_ret.vars
        self.classes = process_ret.classes
        self.functions = process_ret.functions

        self.template_dir = ""

    def render(self, filename: str, **kwargs):
        return render(os.path.join(self.template_dir, filename), **kwargs)

    def _generate_func_class(self, getter: Callable[[object], str]):
        vars = []
        for var in self.vars:
            var_dict = {
                "name": var.name,
                "getter": getter(var.getter),
            }
            if var.setter is not None:
                var_dict["setter"] = getter(var.setter)
            vars.append(var_dict)
        globals = self.render("globals", name=self.config.global_vars, vars=vars)

        functions = [getter(func.generator) for func in self.functions]

        classes = []
        for class_ in self.classes:
            ctor = None
            if class_.ctor is not None:
                ctor = getter(class_.ctor.generator)
            methods = [getter(func.generator) for func in class_.methods]

            fields = []
            for field in class_.fields:
                field_dict = {
                    "name": field.name,
                    "getter": getter(field.getter),
                }
                if field.setter is not None:
                    field_dict["setter"] = getter(field.setter)
                fields.append(field_dict)

            classes.append(
                self.render(
                    "class",
                    ctor=ctor,
                    methods=methods,
                    fields=fields,
                    name=class_.name,
                )
            )
        return globals, functions, classes


class ImplGenerator(BaseImplGenerator):
    def generate(self) -> str:
        self.template_dir = "impl"
        enums = [self.render("enum", enum=enum) for enum in self.enums]
        globals, functions, classes = super()._generate_func_class(
            lambda generator: getattr(generator, "impl")
        )
        return self.render(
            "definitions",
            globals=globals,
            enums=enums,
            functions=functions,
            classes=classes,
        )
