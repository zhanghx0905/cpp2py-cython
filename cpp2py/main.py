import os
import keyword
import subprocess
import sys
from dataclasses import dataclass
from itertools import chain
from pathlib import Path
from typing import List, Optional

import black

from .config import Config, Imports
from .generator import DeclGenerator, ImplGenerator, StubGenerator
from .parser import parse
from .process import Postprocessor
from .typesystem import init_converters
from .utils import render


class BuildError(RuntimeError):
    """Compilation failed; generated files are retained for diagnosis."""


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
    if len(headers) != 1:
        raise ValueError("Can not determine valid module name")
    return Path(headers[0]).stem


def _build_path(filename, target):
    absolute = os.path.abspath(filename)
    try:
        return os.path.relpath(absolute, start=target)
    except ValueError:  # Paths on different Windows drives cannot be relative.
        return absolute


def _validate_config(config):
    if not config.headers:
        raise ValueError("At least one C/C++ header is required")
    if not config.modulename:
        config.modulename = _derive_modname(config.headers)
    if not config.modulename.isidentifier() or keyword.iskeyword(config.modulename):
        raise ValueError("Module name must be a valid Python identifier")
    if Path(config.setup_filename).name != config.setup_filename:
        raise ValueError(
            "setup_filename must be a filename within the output directory"
        )
    for filename in chain(config.headers, config.sources):
        if not Path(filename).is_file():
            raise ValueError(f"Input file does not exist: {filename}")
    for directory in chain(config.incdirs, config.library_dirs):
        if not Path(directory).is_dir():
            raise ValueError(
                f"Include or library directory does not exist: {directory}"
            )
    if config.pointer_return_policy not in {"borrowed", "owned"} or any(
        policy not in {"borrowed", "owned"}
        for policy in config.return_policies.values()
    ):
        raise ValueError("Pointer return policy must be 'borrowed' or 'owned'")


def make_wrapper(config: Config):

    _validate_config(config)

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
        "# cython: language_level=3, cpp_locals=True, c_string_type=str, c_string_encoding=default\n"
        + includes.implementations_import()
        + pyx_content
        + config.additional_impls
    )

    # generate setup
    sourcedir = _build_path(".", config.target)
    source_relpaths = [
        _build_path(filename, config.target) for filename in config.sources
    ]
    setup_conetnt = render(
        "setup",
        filenames=source_relpaths,
        module=config.modulename,
        sourcedir=sourcedir,
        incdirs=[_build_path(directory, config.target) for directory in config.incdirs],
        compiler_flags=config.compiler_flags,
        library_dirs=[
            _build_path(directory, config.target) for directory in config.library_dirs
        ],
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
    Path(target).mkdir(parents=True, exist_ok=True)
    for file, content in results:
        ofilename = os.path.join(target, file)
        with open(ofilename, "w", encoding="utf8", newline="\n") as outf:
            outf.write(content)


def run_setup(setup_name: str = "setup.py", *, cwd=None, verbose: int = 0):
    command = [sys.executable, setup_name, "build_ext", "-i"]
    process = subprocess.run(
        command,
        cwd=cwd,
        capture_output=not verbose,
        text=True,
        encoding="utf8",
        errors="replace",
        env={**os.environ, "PYTHONIOENCODING": "utf8"},
    )
    if process.returncode:
        output = "\n".join(part for part in (process.stdout, process.stderr) if part)
        raise BuildError(
            f"Cython extension build failed (exit code {process.returncode}). "
            "Generated files have been retained. A C++ compiler and its SDK/standard "
            "library are required to build an extension. Use Config(build=False) "
            "or --nobuild to generate wrapper sources without compiling.\n" + output
        )
    return process.returncode


def make_cython_extention(config: Config):
    results = make_wrapper(config)
    write_files(results, config.target)
    if not config.build:
        return results
    run_setup(config.setup_filename, cwd=config.target, verbose=config.verbose)
    if config.cleanup:
        targets = [
            results.source_name,
            results.header_name,
            results.setup_name,
            results.source_name.replace(".pyx", ".cpp"),
        ]
        for file in targets:
            Path(config.target, file).unlink(missing_ok=True)
    return results
