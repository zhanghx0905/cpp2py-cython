"""Load libclang only when parsing, including the library bundled by PyPI libclang."""

import os
import shutil
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import clang
from clang import cindex


def create_index(library_file=None):
    explicit = library_file or os.environ.get("CPP2PY_LIBCLANG_LIBRARY")
    if explicit:
        library = Path(explicit).resolve()
        if not library.is_file():
            raise ValueError(f"libclang library does not exist: {library}")
        if cindex.Config.loaded:
            configured = Path(cindex.conf.get_filename()).resolve()
            if library != configured:
                raise ValueError("libclang is already loaded from a different location")
        else:
            cindex.Config.set_library_file(str(library))
    elif not cindex.Config.loaded and not (
        cindex.Config.library_file or cindex.Config.library_path
    ):
        # The bundled distribution sets library_path itself. These candidates
        # also support installations of the unbundled LLVM Python bindings.
        candidates = [Path(clang.__file__).parent / "native"]
        if os.name == "nt":
            candidates.append(
                Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "LLVM/bin"
            )
        else:
            candidates.extend(sorted(Path("/usr/lib").glob("llvm-*/lib"), reverse=True))
            candidates.extend([Path("/usr/local/lib"), Path("/usr/lib")])
        for directory in candidates:
            libraries = [
                directory / name
                for name in ("libclang.dll", "libclang.dylib", "libclang.so")
            ]
            libraries.extend(sorted(directory.glob("libclang-*.so*"), reverse=True))
            library = next((path for path in libraries if path.is_file()), None)
            if library:
                cindex.Config.set_library_file(str(library))
                break
    try:
        return cindex.Index.create()
    except cindex.LibclangError as error:
        raise ImportError(
            "Cannot load libclang. Install the bundled library with "
            "'python -m pip install libclang', or set CPP2PY_LIBCLANG_LIBRARY "
            "to a compatible libclang.dll/.so/.dylib file. Do not install the "
            "clang and libclang Python distributions together."
        ) from error


def resource_include_dirs():
    """Locate optional Clang builtin headers; C++ STL/SDK headers are separate."""
    library = Path(cindex.conf.get_filename()).resolve()
    roots = [library.parent / "clang", library.parent.parent / "lib/clang"]
    compiler = shutil.which("clang") or shutil.which("clang-cl")
    if compiler:
        roots.append(Path(compiler).resolve().parent.parent / "lib/clang")
    if os.name == "nt":
        roots.append(
            Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "LLVM/lib/clang"
        )
    else:
        roots.extend([Path("/usr/lib/clang"), Path("/usr/local/lib/clang")])
        roots.extend(sorted(Path("/usr/lib").glob("llvm-*/lib/clang"), reverse=True))
    candidates = []
    for root in roots:
        for include in sorted(root.glob("*/include"), reverse=True):
            if include.is_dir():
                candidates.append(include)
    try:
        major = version("libclang").split(".")[0]
    except PackageNotFoundError:
        major = None
    preferred = next(
        (path for path in candidates if path.parent.name.split(".")[0] == major), None
    )
    include = preferred or next(iter(candidates), None)
    return [str(include)] if include else []
