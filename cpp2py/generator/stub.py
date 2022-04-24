from ..utils import camel_to_snake, render
from ..postprocess import ProcessOutput


def catch_type(literal: object):
    return str(type(literal)).removeprefix("<class '").removesuffix("'>")


class StubGenerator:
    def __init__(self, input: ProcessOutput) -> None:
        self.enums = input.objects.enums.values()
        self.macros = input.objects.macros.values()
        self.classes = input.classes
        self.functions = input.functions

    def generate(self) -> str:
        constants = [
            f"{macro.name}: {catch_type(macro.literal)}" for macro in self.macros
        ]
        functions = [func.generator.pysign for func in self.functions]

        classes = []
        for class_ in self.classes:
            ctor = None
            if class_.ctor is not None:
                ctor = class_.ctor.generator.pysign

            methods = [func.generator.pysign for func in class_.methods]

            fields = []
            for field in class_.fields:
                field_dict = {
                    "name": camel_to_snake(field.field.name),
                    "getter": field.getter.pysign,
                }
                if field.setter is not None:
                    field_dict["setter"] = field.setter.pysign
                fields.append(field_dict)

            classes.append(
                render(
                    "class_stub",
                    ctor=ctor,
                    methods=methods,
                    fields=fields,
                    name=class_.name,
                )
            )
        return render(
            "stub",
            constants=constants,
            enums=self.enums,
            functions=functions,
            classes=classes,
        )
