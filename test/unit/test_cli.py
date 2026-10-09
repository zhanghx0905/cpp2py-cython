import os
import subprocess
import sys


def run_cli(*args, env=None):
    return subprocess.run(
        [sys.executable, "-X", "utf8", "-m", "cpp2py", *args],
        env=env,
        capture_output=True,
        text=True,
        encoding="utf8",
    )


def test_help_does_not_need_a_native_library():
    process = run_cli(
        "--help", env={**os.environ, "CPP2PY_LIBCLANG_LIBRARY": "missing.dll"}
    )
    assert process.returncode == 0, process.stderr
    assert "--nobuild" in process.stdout


def test_cli_generates_sources_in_unicode_output_directory(tmp_path):
    header = tmp_path / "input.hpp"
    header.write_text("int twice(int n);\n", encoding="utf8")
    output = tmp_path / "输出 folder"
    process = run_cli(str(header), "--outdir", str(output), "--nobuild", "--genstub")
    assert process.returncode == 0, process.stderr
    assert (output / "input.pyx").is_file()
    assert (output / "input.pyi").is_file()
    assert not list(output.glob("*.pyd"))


def test_cli_invalid_header_exits_with_error(tmp_path):
    header = tmp_path / "broken.hpp"
    header.write_text("int broken( ;", encoding="utf8")
    process = run_cli(str(header), "--nobuild", "--outdir", str(tmp_path / "output"))
    assert process.returncode != 0
    assert "error:" in process.stderr
    assert "Traceback" not in process.stderr
