import os
import re
from dataclasses import dataclass, field
from typing import Callable, List, Optional


@dataclass
class Config:
    headers: List[str] = field(default_factory=list)
    modulename: Optional[str] = None
    target: str = "."
    sources: List[str] = field(default_factory=list)
    incdirs: List[str] = field(default_factory=list)
    compiler_flags: tuple = ("-O3",)
    encoding: str = "utf8"
    verbose: int = 0
    build: bool = True
    clear_files: bool = True
    generate_stub: bool = True
    decl_filename: str = "_declarations"
    setup_filename: str = "setup"

    global_vars: str = "cvar"

    before_build_handlers: Callable[..., None] = lambda: None
    registered_converters: List[type] = field(default_factory=list)
    additional_declarations: List[str] = field(default_factory=list)

    libraries: List[str] = field(default_factory=list)
    library_dirs: List[str] = field(default_factory=list)

    def add_declaration(self, decl: str):
        self.additional_declarations.append(decl)

    def export_declaration(self):
        return os.linesep.join(self.additional_declarations)

    def add_library_dir(self, library_dir: str):
        self.library_dirs.append(library_dir)

    def add_library(self, library: str):
        self.libraries.append(library)

    def add_converter(self, converter):
        self.registered_converters.append(converter)


_STL_MODES_DECL = {
    "pair": "from libcpp.utility cimport pair",
    "map": "from libcpp.map cimport map",
    "set": "from libcpp.set cimport set",
    "list": "from libcpp.list cimport list",
    "vector": "from libcpp.vector cimport vector",
    "string": "from libcpp.string cimport string",
    "unordered_map": "from libcpp.unordered_map cimport unordered_map",
    "unordered_set": "from libcpp.unordered_set cimport unordered_set",
    "complex": "from libcpp.complex cimport complex",
    "unique_ptr": "from libcpp.memory cimport unique_ptr",
    "shared_ptr": "from libcpp.memory cimport shared_ptr",
}

_OTHER_MODS_DECL = {
    "numpy": "cimport numpy as np\nimport numpy as np",
    "deref": "from cython.operator cimport dereference as deref",
    "malloc": "from libc.stdlib cimport malloc",
    "move": "from libcpp.utility cimport move",
}
_STL_PATTERN = re.compile(r"std::(\w+)")


class Imports:
    """Cython Modules need to be imported from numpy/libc/libcpp/..."""

    def __init__(self, config: Config):
        self.config = config
        self.mods = {mod: False for mod in _OTHER_MODS_DECL}
        self.stl = {container: False for container in _STL_MODES_DECL}

    def add_stl(self, tname: str):
        for match in _STL_PATTERN.finditer(tname):
            container_name = match.group(1)

            if container_name in self.stl:
                self.stl[container_name] = True

    def _stl_import(self):
        includes = ["from libcpp cimport bool"]
        includes += [
            _STL_MODES_DECL[tname] for tname, cimport in self.stl.items() if cimport
        ]
        return includes

    def declarations_import(self):
        return os.linesep.join(self._stl_import())

    def implementations_import(self):
        includes = self._stl_import()

        includes += [
            _OTHER_MODS_DECL[name] for name, cimport in self.mods.items() if cimport
        ]
        includes += ["cimport _declarations as cpp"]
        return os.linesep.join(includes)
