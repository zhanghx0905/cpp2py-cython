"""Native regressions, run in CI or on a machine with a C++ toolchain."""

import subprocess
import sys
from pathlib import Path

import pytest

from cpp2py import Config, make_cython_extention

pytestmark = pytest.mark.integration


def test_native_ownership_buffers_and_string_arrays(tmp_path):
    header = Path(__file__).resolve().parents[1] / "testcases/native_memory.hpp"
    make_cython_extention(
        Config(
            headers=[str(header)],
            target=str(tmp_path),
            modulename="native_memory",
            return_policies={"make_owned": "owned"},
        )
    )
    # A subprocess avoids keeping a .pyd loaded during temporary-directory cleanup.
    program = """
import gc
import numpy as np
import native_memory as module

assert module.live_count() == 0
value = module.copy_value(7)
assert value.number == 7 and module.live_count() == 1
del value
gc.collect()
assert module.live_count() == 0

value = module.make_owned(8)
assert value.owner and module.live_count() == 1
alias = module.echo(value)
assert not alias.owner
del value
gc.collect()
assert alias.number == 8 and module.live_count() == 1
del alias
gc.collect()
assert module.live_count() == 0

parent = module.Owner(9)
child = parent.borrowed()
assert not child.owner
del parent
gc.collect()
assert child.number == 9 and module.live_count() == 1
del child
gc.collect()
assert module.live_count() == 0
assert module.null_value() is None
assert module.null_number() is None

values = np.array([1, 2, 3], dtype=np.int32)
values.flags.writeable = False
assert module.sum(values, 3) == 6
for invalid in (None, np.array([], dtype=np.int32), np.arange(6, dtype=np.int32)[::2]):
    try:
        module.sum(invalid, 0)
    except ValueError:
        pass
    else:
        raise AssertionError('invalid buffer must be rejected')
assert module.string_bytes(iter(['one', '二']), 2) == 6
assert module.string_bytes([], 0) == 0
for _ in range(20):
    try:
        module.fail_with_strings(['one'])
    except RuntimeError:
        pass
    else:
        raise AssertionError('C++ exception must reach Python')
"""
    process = subprocess.run(
        [sys.executable, "-X", "utf8", "-c", program],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        encoding="utf8",
    )
    assert process.returncode == 0, process.stdout + process.stderr
