import atexit
import numpy as np
from scipy import sparse

try:
    import spqr
except ImportError:
    import wrapper

    wrapper.build()
    import spqr


cholmod_sparse = spqr.cholmod_sparse_struct


def scipy_to_cholmod_sparse(mat: sparse.csc_matrix, view: cholmod_sparse):
    mat = mat.tocsc()
    mat.sort_indices()
    view.nrow, view.ncol = mat.shape
    view.nzmax = mat.nnz
    view.itype = spqr.CHOLMOD_LONG
    view.dtype = spqr.CHOLMOD_DOUBLE
    view.xtype = spqr.CHOLMOD_REAL
    view.sorted = 1
    view.packed = 1

    view.i = i = np.ascontiguousarray(mat.indices, np.int64)
    view.p = p = np.ascontiguousarray(mat.indptr, np.int64)
    view.x = x = np.ascontiguousarray(mat.data, np.float64)
    return mat, i, p, x


def qr(mat: sparse.csc_matrix):
    cc = spqr.cholmod_common_struct()
    spqr.cholmod_l_start(cc)

    A = cholmod_sparse()
    _ref = scipy_to_cholmod_sparse(mat, A)

    Q = cholmod_sparse.__new__(cholmod_sparse)
    R = cholmod_sparse.__new__(cholmod_sparse)

    E, rank = spqr.suite_sparse_qr_c_qr(
        spqr.SPQR_ORDERING_DEFAULT, spqr.SPQR_DEFAULT_TOL, mat.shape[0], A, Q, R, cc
    )
    Q = spqr.cholmod_to_scipy_sparse(Q, cc)
    R = spqr.cholmod_to_scipy_sparse(R, cc)

    atexit.register(lambda: spqr.cholmod_finish(cc))
    return Q, R, E, rank


def permutation_vector_to_matrix(E):
    n = len(E)
    return sparse.csc_matrix((np.ones(n), (E, np.arange(n))), shape=(n, n))


if __name__ == "__main__":
    print("Testing qr()")
    for _ in range(10):
        M = sparse.rand(10, 8, density=0.1)
        Q, R, E, rank = qr(M)
        print(abs(Q * R - M * permutation_vector_to_matrix(E)).sum())
