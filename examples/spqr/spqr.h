#include <stddef.h>

#define SuiteSparse_long long

typedef struct cholmod_sparse_struct {
    size_t nrow; /* the matrix is nrow-by-ncol */
    size_t ncol;
    size_t nzmax; /* maximum number of entries in the matrix */

    /* pointers to int or SuiteSparse_long: */
    void* p; /* p [0..ncol], the column pointers */
    void* i; /* i [0..nzmax-1], the row indices */

    /* pointers to double or float: */
    void* x; /* size nzmax or 2*nzmax, if present */

    int stype; /* Describes what parts of the matrix are considered:
                *
                * 0:  matrix is "unsymmetric": use both upper and lower triangular parts
                *     (the matrix may actually be symmetric in pattern and value, but
                *     both parts are explicitly stored and used).  May be square or
                *     rectangular.
                * >0: matrix is square and symmetric, use upper triangular part.
                *     Entries in the lower triangular part are ignored.
                * <0: matrix is square and symmetric, use lower triangular part.
                *     Entries in the upper triangular part are ignored.
                *
                * Note that stype>0 and stype<0 are different for cholmod_sparse and
                * cholmod_triplet.  See the cholmod_triplet data structure for more
                * details.
                */

    int itype; /* CHOLMOD_INT:     p, i, and nz are int.
                * CHOLMOD_INTLONG: p is SuiteSparse_long,
                *                  i and nz are int.
                * CHOLMOD_LONG:    p, i, and nz are SuiteSparse_long */

    int xtype; /* pattern, real, complex, or zomplex */
    int dtype; /* x and z are double or float */
    int sorted; /* TRUE if columns are sorted, FALSE otherwise */
    int packed; /* TRUE if packed (nz ignored), FALSE if unpacked
                 * (nz is required) */

} cholmod_sparse;

typedef struct cholmod_common_struct {

} cholmod_common;

int cholmod_l_start(cholmod_common*);

int cholmod_l_finish(cholmod_common*);

int cholmod_l_free_sparse(cholmod_sparse**, cholmod_common*);

#define CHOLMOD_REAL 1		/* a real matrix */
#define CHOLMOD_DOUBLE 0
#define CHOLMOD_LONG 2
/* ordering options */
#define SPQR_ORDERING_NATURAL 1
#define SPQR_ORDERING_DEFAULT 7 /* SuiteSparseQR default ordering */


/* Let [m n] = size of the matrix after pruning singletons.  The default
 * ordering strategy is to use COLAMD if m <= 2*n.  Otherwise, AMD(A'A) is
 * tried.  If there is a high fill-in with AMD then try METIS(A'A) and take
 * the best of AMD and METIS.  METIS is not tried if it isn't installed. */

/* tol options */
#define SPQR_DEFAULT_TOL (-2) /* if tol <= -2, the default tol is used */

/* [Q,R,E] = qr(A), returning Q as a sparse matrix */
SuiteSparse_long SuiteSparseQR_C_QR /* returns rank(A) est., (-1) if failure */
    (
        /* inputs: */
        int ordering, /* all, except 3:given treated as 0:fixed */
        double tol, /* columns with 2-norm <= tol treated as 0 */
        SuiteSparse_long econ, /* e = max(min(m,econ),rank(A)) */
        cholmod_sparse* A, /* m-by-n sparse matrix to factorize */
        /* outputs: */
        cholmod_sparse** Q, /* m-by-e sparse matrix */
        cholmod_sparse** R, /* e-by-n sparse matrix */
        SuiteSparse_long** E, /* size n column perm, NULL if identity */
        cholmod_common* cc /* workspace and parameters */
    );