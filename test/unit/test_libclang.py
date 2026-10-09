import pytest
from clang import cindex

from cpp2py.parser import libclang


def test_explicit_missing_library_is_rejected_before_loading(tmp_path):
    with pytest.raises(ValueError, match="does not exist"):
        libclang.create_index(str(tmp_path / "missing.dll"))


def test_builtin_headers_can_be_found_from_compiler_installation(tmp_path, monkeypatch):
    binary = tmp_path / "llvm/bin/clang"
    binary.parent.mkdir(parents=True)
    binary.write_text("", encoding="utf8")
    include = tmp_path / "llvm/lib/clang/18/include"
    include.mkdir(parents=True)
    monkeypatch.setattr(libclang.shutil, "which", lambda command: str(binary))
    monkeypatch.setattr(
        cindex.conf, "get_filename", lambda: str(tmp_path / "native/libclang.dll")
    )
    assert libclang.resource_include_dirs() == [str(include)]


def test_missing_library_has_actionable_message(monkeypatch):
    def fail():
        raise cindex.LibclangError("missing library")

    monkeypatch.setattr(cindex.Index, "create", fail)
    with pytest.raises(ImportError, match="pip install libclang"):
        libclang.create_index()
