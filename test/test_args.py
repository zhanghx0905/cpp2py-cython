import os

from cpp2py import Config

from tools import TESTCASES_PATH, cpp2py_tester


def test_external_library():
    """set LD_LIBRARY_PATH before test to find the shared liarary"""
    EXTERNAL_DIR = "anotherincludedir"
    library_dir = os.path.abspath(os.path.join(TESTCASES_PATH, EXTERNAL_DIR))

    cwd = os.getcwd()
    try:
        os.chdir(library_dir)
        os.system("make")
    finally:
        os.chdir(cwd)

    config = Config()
    config.add_library_dir(library_dir)

    @cpp2py_tester("withincludedir.hpp", config=config, incdirs=[EXTERNAL_DIR])
    def run():
        from withincludedir import length

        assert length(3.0, 4.0) == 5.0

    run()


@cpp2py_tester("withincludedir.hpp", incdirs=["anotherincludedir"])
def test_another_include_dir():
    from withincludedir import length

    assert length(3.0, 4.0) == 5.0
