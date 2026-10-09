"""Command-line interface shared by console scripts and python -m cpp2py."""

import sys
from argparse import ArgumentParser

from . import BuildError, ClangError, Config, make_cython_extention


def parse_args(argv=None):
    parser = ArgumentParser(description="Generate Cython wrappers from C/C++ headers")
    parser.add_argument("header", nargs="+", help="C++ header files")
    parser.add_argument(
        "--sources", nargs="*", default=[], help="C++ implementation files"
    )
    parser.add_argument("--modname", default=None, help="Name of the extension module")
    parser.add_argument("--outdir", default=".", help="Output directory")
    parser.add_argument("--incdirs", nargs="*", default=[], help="Include directories")
    parser.add_argument(
        "--globals", default="cvar", help="Object holding global variables"
    )
    parser.add_argument(
        "--nobuild", action="store_true", help="Generate sources without a C++ compiler"
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Remove intermediate files after successful compilation",
    )
    parser.add_argument(
        "--genstub", action="store_true", help="Generate a Python stub (.pyi)"
    )
    parser.add_argument("--encoding", default="utf8", help="Encoding of input files")
    parser.add_argument(
        "--libclang-library", help="Explicit libclang shared library filename"
    )
    parser.add_argument(
        "--pointer-return-policy", choices=["borrowed", "owned"], default="borrowed"
    )
    parser.add_argument("--verbose", "-v", action="count", default=0)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    config = Config(
        headers=args.header,
        modulename=args.modname,
        target=args.outdir,
        sources=args.sources,
        incdirs=args.incdirs,
        encoding=args.encoding,
        libclang_library=args.libclang_library,
        pointer_return_policy=args.pointer_return_policy,
        verbose=args.verbose,
        build=not args.nobuild,
        cleanup=args.cleanup,
        global_vars=args.globals,
        generate_stub=args.genstub,
    )
    try:
        make_cython_extention(config)
    except (BuildError, ClangError, ValueError, OSError, ImportError) as error:
        print(f"cpp2py: {error}", file=sys.stderr)
        return 1
    return 0
