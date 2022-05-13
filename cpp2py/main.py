import os
from dataclasses import dataclass
from itertools import chain
from typing import List, Optional

import black

from .config import Config, Imports
from .generator import DeclGenerator, ImplGenerator, StubGenerator
from .parser import parse
from .process import Postprocessor
from .typesystem import init_converters
from .utils import render, suppress_stdout


@dataclass
class WrapperResult:
    source_content: str
    source_name: str
    header_content: str
    header_name: str
    setup_content: str
    setup_name: str

    stub_content: Optional[str] = None
    stub_name: Optional[str] = None

    def __iter__(self):
        yield self.header_name, self.header_content
        yield self.source_name, self.source_content
        yield self.setup_name, self.setup_content
        if self.stub_name is not None:
            yield self.stub_name, self.stub_content


def _derive_modname(headers: List[str]):
    name = headers[0].split(os.sep)[-1].split(".")[0]
    if len(headers) != 1 or name == "":
        raise ValueError("Can not determine valid module name")
    return name


def make_wrapper(config: Config):

    if not config.modulename:
        config.modulename = _derive_modname(config.headers)
    if not all(os.path.exists(path) for path in chain(config.incdirs, config.sources)):
        raise ValueError("Some include directories or source files do not exist.")

    pxd_header_name = f"{config.modulename}_header"
    init_converters(config.registered_converters)
    includes = Imports(pxd_header_name)
    parse_ret = parse(config, includes)

    postprocessor = Postprocessor(parse_ret, includes, config)
    process_ret = postprocessor.generate_output()

    # generate PXD
    decl_generator = DeclGenerator(parse_ret)
    pxd_content = decl_generator.generate()

    # generate PYX
    impl_generator = ImplGenerator(process_ret, config)
    pyx_content = impl_generator.generate()

    # add modules import
    pxd_content = includes.declarations_import() + pxd_content + config.additional_decls
    pyx_content = (
        includes.implementations_import() + pyx_content + config.additional_impls
    )

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
        f"{pxd_header_name}.pxd",
        setup_conetnt,
        config.setup_filename,
    )

    # generate PYI (optional)
    if config.generate_stub:
        results.stub_name = f"{config.modulename}.pyi"
        results.stub_content = black.format_str(
            StubGenerator(process_ret, config).generate(),
            mode=black.FileMode(is_pyi=True),
        )

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
    if not config.build:
        return
    cwd = os.getcwd()
    os.chdir(config.target)
    run_setup(config.setup_filename)
    os.chdir(cwd)
    if config.cleanup:
        targets = [
            results.source_name,
            results.header_name,
            results.setup_name,
            results.source_name.replace(".pyx", ".cpp"),
        ]
        for file in targets:
            os.remove(file)
