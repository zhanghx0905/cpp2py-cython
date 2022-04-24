import os
from dataclasses import dataclass
from itertools import chain

import autopep8

from .config import Config, Imports
from .generator import DeclGenerator, ImplGenerator, StubGenerator
from .parser import parse
from .postprocess import Postprocessor
from .type_conversion import init_converters
from .utils import print_header, render, suppress_stdout


@dataclass
class WrapperResult:
    source_content: str
    source_name: str
    header_content: str
    header_name: str
    setup_content: str
    setup_name: str

    stub_content: str = ""
    stub_name: str | None = None

    def __post_init__(self):
        self.header_content = autopep8.fix_code(self.header_content)
        self.source_content = autopep8.fix_code(self.source_content)
        if self.stub_name is not None:
            self.stub_content = autopep8.fix_code(self.stub_content)

    def __iter__(self):
        yield self.header_name, self.header_content
        yield self.source_name, self.source_content
        yield self.setup_name, self.setup_content
        if self.stub_name is not None:
            yield self.stub_name, self.stub_content


def _derive_modname(headers: list[str]):
    name = headers[0].split(os.sep)[-1].split(".")[0]
    if len(headers) != 1 or name == "":
        raise ValueError("Can not determine valid module name")
    return name


def make_wrapper(config: Config):

    if not config.modulename:
        config.modulename = _derive_modname(config.headers)
    if not all(os.path.exists(path) for path in chain(config.incdirs, config.sources)):
        raise ValueError("Some include directories or source files do not exist.")

    init_converters(config.registered_converters)
    includes = Imports(config)
    parse_ret = parse(config.headers, config.incdirs, config.encoding, includes)

    postprocessor = Postprocessor(parse_ret, includes)
    process_ret = postprocessor.generate_output()

    # generate PXD
    decl_generator = DeclGenerator(parse_ret)
    pxd_content = decl_generator.generate() + config.export_declaration()

    # generate PYX
    impl_generator = ImplGenerator(process_ret)
    pyx_content = impl_generator.generate()

    # add modules import
    pxd_content = includes.declarations_import() + pxd_content
    pyx_content = includes.implementations_import() + pyx_content

    # generate setup
    sourcedir = os.path.relpath(".", start=config.target)
    source_relpaths = [
        os.path.relpath(filename, start=config.target) for filename in config.sources
    ]
    setup_conetnt = render(
        "setup",
        filenames=source_relpaths,
        module=config.modulename,
        sourcedir=sourcedir,
        incdirs=config.incdirs,
        compiler_flags=config.compiler_flags,
        library_dirs=config.library_dirs,
        libraries=config.libraries,
    )

    results = WrapperResult(
        pyx_content,
        f"{config.modulename}.pyx",
        pxd_content,
        f"{config.decl_filename}.pxd",
        setup_conetnt,
        f"{config.setup_filename}.py",
    )

    # generate PYI (optional)
    if config.generate_stub:
        results.stub_name = f"{config.modulename}.pyi"
        results.stub_content = StubGenerator(process_ret).generate()

    if config.verbose >= 1:
        for file, content in results:
            print_header(file)
            print(content)
    return results


def write_files(results: WrapperResult, target: str = "."):
    for file, content in results:
        ofilename = os.path.join(target, file)
        with open(ofilename, "w", encoding="utf8") as outf:
            outf.write(content)


def run_setup(setup_name: str = "setup.py"):
    cmd = f"python {setup_name} build_ext -i"
    with suppress_stdout():
        return os.system(cmd)


def make_cython_extention(config: Config):
    results = make_wrapper(config)
    write_files(results, config.target)
    config.before_build_handlers()
    if not config.build:
        return
    cwd = os.getcwd()
    os.chdir(config.target)
    run_setup()
    os.chdir(cwd)
    if config.clear_files:
        targets = [
            results.source_name,
            results.header_name,
            results.setup_name,
            results.source_name.replace(".pyx", ".cpp"),
        ]
        for file in targets:
            os.remove(file)
