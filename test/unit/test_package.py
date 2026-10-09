import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def wheel(tmp_path_factory):
    target = tmp_path_factory.mktemp("distribution")
    process = subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            str(ROOT),
            "--wheel",
            "--no-isolation",
            "--outdir",
            str(target),
        ],
        capture_output=True,
        text=True,
        encoding="utf8",
    )
    assert process.returncode == 0, process.stdout + process.stderr
    return next(target.glob("*.whl"))


def test_wheel_includes_all_templates_and_dependencies(wheel):
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        expected = {
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "cpp2py/template_data").rglob("*.j2")
        }
        assert expected <= names
        metadata_file = next(
            name for name in names if name.endswith(".dist-info/METADATA")
        )
        metadata = archive.read(metadata_file).decode("utf8")
        for dependency in (
            "libclang",
            "Cython",
            "black",
            "Jinja2",
            "more-itertools",
            "numpy",
        ):
            assert f"Requires-Dist: {dependency}".lower() in metadata.lower()
        entrypoints = next(
            name for name in names if name.endswith(".dist-info/entry_points.txt")
        )
        assert "cpp2py = cpp2py.cli:main" in archive.read(entrypoints).decode("utf8")


def test_installed_wheel_works_outside_source_checkout(wheel, tmp_path):
    installed = tmp_path / "installed"
    process = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-deps",
            "--target",
            str(installed),
            str(wheel),
        ],
        capture_output=True,
        text=True,
        encoding="utf8",
    )
    assert process.returncode == 0, process.stdout + process.stderr
    header = tmp_path / "input.hpp"
    header.write_text("int twice(int n);\n", encoding="utf8")
    program = """
from pathlib import Path
import cpp2py
from cpp2py import Config, make_wrapper
assert Path(cpp2py.__file__).resolve().is_relative_to(Path('installed').resolve())
result = make_wrapper(Config(headers=['input.hpp'], build=False))
assert 'cpdef twice' in result.source_content
assert result.setup_content and result.stub_content
"""
    process = subprocess.run(
        [sys.executable, "-X", "utf8", "-c", program],
        cwd=str(tmp_path),
        env={**os.environ, "PYTHONPATH": str(installed)},
        capture_output=True,
        text=True,
        encoding="utf8",
    )
    assert process.returncode == 0, process.stdout + process.stderr
