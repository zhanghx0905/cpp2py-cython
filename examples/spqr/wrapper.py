import os
import re
from cpp2py import (
    Config,
    VoidPtrConverter,
)
from cpp2py.main import run_setup, write_files, make_wrapper

class DataConverter(VoidPtrConverter):
    def _matches(self):
        return super()._matches() and self.py_argname == "x"

    def real_type(self) -> str:
        return "double"


class IndexConverter(VoidPtrConverter):
    def _matches(self):
        return super()._matches() and self.py_argname in {"p", "i"}

    def real_type(self) -> str:
        return "long"


libdir = "/usr/include/suitesparse"
headers = [
    os.path.join(libdir, f)
    for f in ("cholmod.h", "cholmod_core.h", "SuiteSparseQR_C.h", "SuiteSparseQR_definitions.h")
]

config = Config(
    headers,
    modulename="spqr",
    incdirs=[libdir],
    libraries=["cholmod", "spqr"],
    registered_converters=[DataConverter, IndexConverter],
    generate_stub=True,
    cleanup=False,
    # build=False,
)

additional_impl = '''

from libc.stdlib cimport malloc
cimport numpy as np

import numpy as np
from scipy import sparse

np.import_array()

cdef class _CholmodSparseDestructor:
    """ Destructor for NumPy arrays based on sparse data of Cholmod """
    cdef cpp.cholmod_sparse_struct * _sparse
    cdef cpp.cholmod_common_struct * _common

    cdef init(self, cpp.cholmod_sparse_struct * m, cpp.cholmod_common_struct* common):
        self._sparse = m
        self._common = common

    def __dealloc__(self):
        cpp.cholmod_l_free_sparse(&self._sparse, self._common)


cpdef cholmod_to_scipy_sparse(cholmod_sparse_struct m, cholmod_common_struct common):
    cdef np.ndarray indptr = np.PyArray_SimpleNewFromData(1, [m.ncol + 1], np.NPY_INT64, m.thisptr.p)
    cdef np.ndarray indices = np.PyArray_SimpleNewFromData(1, [m.nzmax], np.NPY_INT64, m.thisptr.i)
    cdef np.ndarray data = np.PyArray_SimpleNewFromData(1, [m.nzmax], np.NPY_FLOAT64, m.thisptr.x)
    cdef _CholmodSparseDestructor base = _CholmodSparseDestructor()
    base.init(m.thisptr, common.thisptr)
    # base.__dealloc__ is called only when all 3 arrays are destructed
    for array in (indptr, indices, data):
        np.set_array_base(array, base)
    m.owner = False
    return sparse.csc_matrix((data, indices, indptr), shape=(m.nrow, m.ncol))

cpdef suite_sparse_qr_c_qr(int ordering, double tol, long econ, cholmod_sparse_struct A, cholmod_sparse_struct Q, cholmod_sparse_struct R, cholmod_common_struct cc):
    cdef long** c_E = <long **>malloc(sizeof(long*))
    cdef int rank = cpp.SuiteSparseQR_C_QR(ordering, tol, econ, A.thisptr, &Q.thisptr, &R.thisptr, c_E, cc.thisptr)
    cdef np.ndarray E = np.arange(A.ncol, dtype=np.int64)
    if c_E != NULL:
        E = np.PyArray_SimpleNewFromData(1, [A.ncol], np.NPY_INT64, deref(c_E))
    return E, rank
'''


config.additional_impls = additional_impl

def build():
    ret = make_wrapper(config)
    ret.header_content = re.sub(r'".+\.h"', '"SuiteSparseQR_C.h"', ret.header_content)
    write_files(ret)
    run_setup()




if __name__ == "__main__":
    build()
