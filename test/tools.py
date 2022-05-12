import glob
import os
import sys
from functools import wraps
from typing import List, Optional

import pytest
from cpp2py import Config
from cpp2py.main import make_wrapper, run_setup, write_files

TESTCASES_PATH = os.path.join(os.path.dirname(__file__), "testcases")
sys.path.insert(0, os.getcwd())
SETUPPY_NAME = "setup_test.py"


def remove_files(filenames):
    """Remove files if they exist."""
    for f in filenames:
        if os.path.exists(f):
            os.remove(f)
        else:
            files = glob.glob(f)
            if len(files) == 1:
                os.remove(files[0])


def full_path(filenames: List[str]):
    if isinstance(filenames, str):
        filenames = [filenames]
    paths = [os.path.join(TESTCASES_PATH, file) for file in filenames]
    assert all(os.path.exists(path) for path in paths)
    return paths


def cpp2py_tester(
    headers,
    modulename=None,
    incdirs=None,
    sources=None,
    cleanup=True,
    warnmsg=None,
    config: Optional[Config] = None,
):
    def inner(func):
        @wraps(func)
        def wrapper():
            nonlocal incdirs
            if incdirs is None:
                incdirs = []
            nonlocal sources
            if sources is None:
                sources = []
            args = {}
            if config is not None:
                args.update(config.__dict__)
            args.update(
                {
                    "headers": full_path(headers),
                    "modulename": modulename,
                    "incdirs": full_path(incdirs),
                    "sources": full_path(sources),
                    "compiler_flags": ("-O0",),
                    "setup_filename": SETUPPY_NAME,
                    "generate_stub": False,  # True,
                }
            )
            _config = Config(**args)
            if warnmsg is None:
                results = make_wrapper(_config)
            else:
                with pytest.warns(UserWarning, match=warnmsg):
                    results = make_wrapper(_config)
            write_files(results)
            run_setup(results.setup_name)
            try:
                func()
            finally:
                if cleanup:
                    targets = [
                        results.source_name,
                        results.header_name,
                        results.setup_name,
                        results.source_name.replace(".pyx", ".cpp"),
                        results.source_name.replace(".pyx", ".*.so"),
                    ]
                    remove_files(targets)

        return wrapper

    return inner
