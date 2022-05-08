from ..utils import render
from .impl import BaseImplGenerator


def catch_type(literal: object):
    # .removeprefix("<class '").removesuffix("'>")
    return str(type(literal))[8:-2]


class StubGenerator(BaseImplGenerator):
    def generate(self) -> str:
        self.template_dir = "stub"
        globals, functions, classes = super()._generate_func_class(
            lambda generator: getattr(generator, "pysign")
        )
        return self.render(
            "stub",
            globals=globals,
            enums=self.enums,
            functions=functions,
            classes=classes,
        )
