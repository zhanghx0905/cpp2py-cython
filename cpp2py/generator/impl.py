from ..utils import camel_to_snake, render
from ..postprocess import ProcessOutput


class ImplGenerator:
    def __init__(self, input: ProcessOutput) -> None:
        self.enums = input.objects.enums.values()
        self.macros = input.objects.macros.values()
        self.classes = input.classes
        self.functions = input.functions

    def generate(self) -> str:
        constants = [f"{macro.name} = cpp.{macro.name}" for macro in self.macros]
        enums = [render("enum", enum=enum) for enum in self.enums]

        functions = [func.generator.impl for func in self.functions]

        classes = []
        for class_ in self.classes:
            ctor = None
            if class_.ctor is not None:
                ctor = class_.ctor.generator.impl
            methods = [func.generator.impl for func in class_.methods]

            fields = []
            for field in class_.fields:
                field_dict = {
                    "name": camel_to_snake(field.field.name),
                    "getter": field.getter.impl,
                }
                if field.setter is not None:
                    field_dict["setter"] = field.setter.impl
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
        return render(
            "definitions",
            constants=constants,
            enums=enums,
            functions=functions,
            classes=classes,
        )
