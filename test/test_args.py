import os
import subprocess

import pytest

from cpp2py import Config

from tools import TESTCASES_PATH, cpp2py_tester

pytestmark = pytest.mark.integration


def test_external_library():
    """set LD_LIBRARY_PATH before test to find the shared liarary"""
    EXTERNAL_DIR = "anotherincludedir"
    library_dir = os.path.abspath(os.path.join(TESTCASES_PATH, EXTERNAL_DIR))

    subprocess.run(["make"], cwd=library_dir, check=True)

    config = Config()
    config.add_library_dir(library_dir)
    config.add_library("mylib")

    @cpp2py_tester(
        "withincludedir.hpp",
        modulename="external_library",
        config=config,
        incdirs=[EXTERNAL_DIR],
    )
    def run():
        from external_library import length

        assert length(3.0, 4.0) == 5.0

    run()


@cpp2py_tester(
    "withincludedir.hpp",
    incdirs=["anotherincludedir"],
    sources=["anotherincludedir/somefunction.cpp"],
)
def test_another_include_dir():
    from withincludedir import length

    assert length(3.0, 4.0) == 5.0
