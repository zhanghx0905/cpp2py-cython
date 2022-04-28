from ..utils import render
from .impl import BaseImplGenerator


def catch_type(literal: object):
    # .removeprefix("<class '").removesuffix("'>")
    return str(type(literal))[8:-2]


class StubGenerator(BaseImplGenerator):
    def generate(self) -> str:
        constants = [
            f"{macro.name}: {catch_type(macro.literal)}" for macro in self.macros
        ]
        functions, classes = functions, classes = super()._generate_func_class(
            lambda generator: getattr(generator, "pysign"), "class_stub"
        )
        return render(
            "stub",
            constants=constants,
            enums=self.enums,
            functions=functions,
            classes=classes,
        )
