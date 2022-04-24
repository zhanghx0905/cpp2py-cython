import glob
import os
import os.path as osp

import clang
from clang import cindex

SUPPORTED_VERSIONS = ["12"]


def find_clang():
    """
    python-clang does not know where to find libclang, so we have to do this manually.
    """

    def _lib_exist(lib_path, clang_version):
        lib_names = {f"libclang-{clang_version}.so", f"libclang.so.{clang_version}"}
        return any(osp.exists(osp.join(lib_path, lib_name)) for lib_name in lib_names)

    def _find_include(lib_path, clang_version):
        patterns = {
            osp.join(lib_path, f"clang/{clang_version}.?/include/"),
            osp.join(lib_path, f"clang/{clang_version}.?.?/include/"),
        }
        for pattern in patterns:
            clang_incdir = glob.glob(pattern)
            if len(clang_incdir) == 1:
                return clang_incdir[0]

        raise ImportError("Could not find the clang include directory.")

    # remove pythonX.Y/site-packages/clang/__init__.py, get e.g. '$HOME/venv/lib'
    basepath = os.sep.join(clang.__file__.split(os.sep)[:-4])
    for clang_version in SUPPORTED_VERSIONS:
        search_paths = {
            f"/usr/lib/llvm-{clang_version}/lib",
            f"/usr/local/lib/llvm-{clang_version}/lib",
            basepath,
        }
        for path in search_paths:
            if not osp.exists(path):
                continue
            if not _lib_exist(path, clang_version):
                continue

            cindex.Config.set_library_path(path)
            return _find_include(path, clang_version)

    raise ImportError("Could not find a valid installation of libclang.")


CLANG_INCDIR = find_clang()

if __name__ == "__main__":
    print(CLANG_INCDIR)
