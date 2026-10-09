import os
import subprocess
import sys
from pathlib import Path

import pytest

from cpp2py import BuildError, Config, make_cython_extention, make_wrapper, run_setup
from cpp2py import main as pipeline


def config_for(tmp_path, **kwargs):
    header = tmp_path / "input.hpp"
    header.write_text("int twice(int n);\n", encoding="utf8")
    return Config(
        headers=[str(header)], target=str(tmp_path / "output folder"), **kwargs
    )


def test_no_build_creates_directory_and_returns_result(tmp_path, monkeypatch):
    config = config_for(tmp_path, build=False)
    monkeypatch.setattr(
        pipeline, "run_setup", lambda *a, **k: pytest.fail("must not build")
    )
    result = make_cython_extention(config)
    assert (Path(config.target) / result.source_name).is_file()
    assert (Path(config.target) / result.stub_name).is_file()


def test_build_failure_preserves_files_and_working_directory(tmp_path, monkeypatch):
    config = config_for(tmp_path, cleanup=True)
    original_cwd = os.getcwd()

    def fail(*args, **kwargs):
        assert kwargs["cwd"] == config.target
        assert os.getcwd() == original_cwd
        raise BuildError("compiler is missing")

    monkeypatch.setattr(pipeline, "run_setup", fail)
    with pytest.raises(BuildError, match="compiler is missing"):
        make_cython_extention(config)
    assert os.getcwd() == original_cwd
    assert (Path(config.target) / "input.pyx").is_file()
    assert (Path(config.target) / "setup.py").is_file()


def test_success_cleanup_stays_in_output_directory(tmp_path, monkeypatch):
    config = config_for(tmp_path, cleanup=True)
    monkeypatch.chdir(tmp_path)
    sentinel = tmp_path / "input.pyx"
    sentinel.write_text("keep this original file", encoding="utf8")

    def succeed(*args, **kwargs):
        (Path(kwargs["cwd"]) / "input.cpp").write_text("generated", encoding="utf8")
        return 0

    monkeypatch.setattr(pipeline, "run_setup", succeed)
    result = make_cython_extention(config)
    assert sentinel.read_text(encoding="utf8") == "keep this original file"
    for filename in (
        result.source_name,
        result.header_name,
        result.setup_name,
        "input.cpp",
    ):
        assert not (Path(config.target) / filename).exists()
    assert (Path(config.target) / result.stub_name).is_file()


def test_run_setup_uses_current_python_and_handles_spaces(tmp_path, monkeypatch):
    calls = []

    def run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(subprocess, "run", run)
    assert run_setup("setup with spaces.py", cwd=str(tmp_path)) == 0
    command, options = calls[0]
    assert command == [sys.executable, "setup with spaces.py", "build_ext", "-i"]
    assert options["cwd"] == str(tmp_path)


def test_run_setup_reports_failed_process_output(monkeypatch):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda command, **kwargs: subprocess.CompletedProcess(
            command, 1, "Cython output", "SDK is missing"
        ),
    )
    with pytest.raises(BuildError, match="SDK is missing"):
        run_setup()


@pytest.mark.parametrize(
    "changes, message",
    [
        ({"headers": []}, "At least one"),
        ({"modulename": "invalid-name"}, "identifier"),
        ({"modulename": "class"}, "identifier"),
        ({"headers": ["nonexistent.hpp"]}, "Input file"),
        ({"pointer_return_policy": "copy"}, "return policy"),
        ({"return_policies": {"demo::factory": "copy"}}, "return policy"),
        ({"setup_filename": "../setup.py"}, "filename"),
    ],
)
def test_config_validation_before_parsing(tmp_path, changes, message):
    config = config_for(tmp_path, build=False)
    for key, value in changes.items():
        setattr(config, key, value)
    with pytest.raises(ValueError, match=message):
        make_wrapper(config)
