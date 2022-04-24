from typing import Callable

from ..utils import camel_to_snake, render
from ..postprocess import ProcessOutput


class BaseImplGenerator:
    def __init__(self, process_ret: ProcessOutput) -> None:
        self.enums = process_ret.objects.enums.values()
        self.macros = process_ret.objects.macros.values()
        self.classes = process_ret.classes
        self.functions = process_ret.functions

    def _generate_func_class(self, getter: Callable[[object], str]):
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
                    "name": camel_to_snake(field.field.name),
                    "getter": getter(field.getter),
                }
                if field.setter is not None:
                    field_dict["setter"] = getter(field.setter)
                fields.append(field_dict)

            classes.append(
                render(
                    "class",
                    ctor=ctor,
                    methods=methods,
                    fields=fields,
                    name=class_.name,
                )
            )
        return functions, classes


class ImplGenerator(BaseImplGenerator):
    def generate(self) -> str:
        constants = [f"{macro.name} = cpp.{macro.name}" for macro in self.macros]
        enums = [render("enum", enum=enum) for enum in self.enums]
        functions, classes = super()._generate_func_class(
            lambda generator: getattr(generator, "impl")
        )
        return render(
            "definitions",
            constants=constants,
            enums=enums,
            functions=functions,
            classes=classes,
        )
