from .impl import BaseImplGenerator


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
