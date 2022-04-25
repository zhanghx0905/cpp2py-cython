import os
from functools import partial
from time import perf_counter

import numpy as np
from numpy.testing import assert_allclose
from pytest import mark
from scipy import sparse
from scipy.io import mmread

from pyspqr import qr

assert_allclose = partial(assert_allclose, rtol=1e-5, atol=1e-8)

_TESTDIR = os.path.join(os.path.dirname(__file__), "test_data")


def mm_matrix(name: str) -> sparse.csc_matrix:
    matrix = mmread(os.path.join(_TESTDIR, f"{name}.mtx"))
    assert sparse.issparse(matrix)
    matrix = matrix.tocsc()
    assert matrix.indices.dtype == np.int32
    return matrix


def perm_vec_to_mat(E: np.ndarray) -> sparse.csc_matrix:
    n = len(E)
    return sparse.csc_matrix((np.ones(n), (E, np.arange(n))), shape=(n, n))


def test_correctness():
    testcases = [mm_matrix(f"case{problem}") for problem in range(1, 5)]

    for case in testcases:
        Q, R, E, _ = qr(case)
        P = perm_vec_to_mat(E)
        assert_allclose((Q @ R).todense(), (case @ P).todense())


@mark.skip
def test_performance():
    testcases = {"ted_B": 10, "s3rmt3m3": 5}
    for case, trial in testcases.items():
        mat = mm_matrix(case)
        elapsed = 1e5
        for _ in range(trial):
            start = perf_counter()
            qr(mat)
            elapsed = min(elapsed, perf_counter() - start)
        print(f"Py Overall time elasped:  {elapsed:12.6f} s")
        ctest = os.popen(f"./qr_c_test -f ./test_data/{case}.mtx -t{trial} ")
        print(ctest.read())


if __name__ == "__main__":
    test_correctness()
    test_performance()
