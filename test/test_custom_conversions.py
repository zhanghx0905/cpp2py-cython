import os

import numpy as np
import pytest
from cpp2py import AbstractTypeConverter, Config
from numpy.testing import assert_array_equal

from tools import cpp2py_tester

EIGEN3_INCDIR = "/usr/include/eigen3"


@pytest.mark.skipif(
    not os.path.exists(EIGEN3_INCDIR),
    reason=f"Eigen 3 include directory '{EIGEN3_INCDIR}' not found",
    # sudo apt install libeigen3-dev
)
def test_convert_vector():
    eigen_vector_decl = """

cdef extern from "Eigen/Dense" namespace "Eigen":
  cdef cppclass VectorXd:
    VectorXd()
    VectorXd(int rows)
    VectorXd(VectorXd&)
    double* data()
    int rows()
    double& get "operator()"(int rows)

"""

    class EigenConverter(AbstractTypeConverter):
        def _matches(self):
            return self.raw_cxxtype.plain_name == "VectorXd"

        def _add_includes(self, includes):
            includes.mods["numpy"] = True

        def python_to_cpp(self):
            return os.linesep.join(
                [
                    "cdef int %(py_argname)s_length = %(py_argname)s.shape[0]",
                    "cdef cpp.VectorXd %(cpp_argname)s = cpp.VectorXd(%(py_argname)s_length)",
                    "cdef int %(py_argname)s_idx",
                    "for %(py_argname)s_idx in range(%(py_argname)s_length):",
                    "    %(cpp_argname)s.data()[%(py_argname)s_idx] = %(py_argname)s[%(py_argname)s_idx]",
                ]
            ) % {"py_argname": self.py_argname, "cpp_argname": self.cpp_argname}

        def cpp_call_arg(self):
            return self.cpp_argname

        def return_output(self, cpp_call: str, **kwargs) -> str:
            return os.linesep.join(
                [
                    f"cdef cpp.VectorXd result = {cpp_call}",
                    "cdef int size = result.rows()",
                    "cdef int res_idx",
                    "cdef np.ndarray[double, ndim=1] res = np.ndarray(shape=(size,))",
                    "for res_idx in range(size):",
                    "    res[res_idx] = result.get(res_idx)",
                    "return res",
                ]
            )

        def input_type_decl(self) -> str:
            return "np.ndarray[double, ndim=1]"

    config = Config()
    config.registered_converters.append(EigenConverter)
    config.additional_decls = eigen_vector_decl

    @cpp2py_tester("eigen.hpp", config=config, incdirs=EIGEN3_INCDIR)
    def run():
        from eigen import make

        a = np.ones(5)
        assert_array_equal(make(a), a * 2.0)

    run()
