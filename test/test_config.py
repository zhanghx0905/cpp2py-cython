import os
import shutil

import pytest
from cpp2py import Config

from tools import TESTCASES_PATH, cpp2py_tester


@cpp2py_tester("abstractclass.hpp")
def test_abstract_class():
    from abstractclass import AbstractClass, DerivedClass

    with pytest.raises(TypeError):
        AbstractClass()
    d = DerivedClass(5.0)
    a = d.clone()
    assert a.square() == 25.0


def test_external_library():
    """set LD_LIBRARY_PATH before test to find the shared liarary"""
    library_dir = os.path.abspath(os.path.join(TESTCASES_PATH, "externallib"))

    cwd = os.getcwd()
    try:
        os.chdir(library_dir)
        os.system("make")
    finally:
        os.chdir(cwd)
    shutil.copyfile(os.path.join(library_dir, "libmylib.so"), "./libmylib.so")
    config = Config()
    config.add_library_dir(library_dir)
    config.add_library("mylib")

    @cpp2py_tester("withexternallib.hpp", config=config, incdirs=["externallib"])
    def run():
        from withexternallib import get_number

        assert get_number() == 5

    try:
        run()
    finally:
        os.remove("./libmylib.so")
