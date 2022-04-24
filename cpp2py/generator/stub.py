from ..utils import render
from .impl import BaseImplGenerator


def catch_type(literal: object):
    return str(type(literal)).removeprefix("<class '").removesuffix("'>")


class StubGenerator(BaseImplGenerator):
    def generate(self) -> str:
        constants = [
            f"{macro.name}: {catch_type(macro.literal)}" for macro in self.macros
        ]
        functions, classes = functions, classes = super()._generate_func_class(
            lambda generator: getattr(generator, "pysign")
        )
        return render(
            "stub",
            constants=constants,
            enums=self.enums,
            functions=functions,
            classes=classes,
        )
