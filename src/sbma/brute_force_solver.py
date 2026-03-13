"""For benchmark purposes."""

import numpy as np
from sbma._brute_force_solver import solve as cpp_solve

__all__ = ["solve"]


def solve(mat: np.ndarray, ar_counts: np.ndarray):
    """Wrapper for brute force solver."""
    ar_result: np.ndarray = cpp_solve(mat, ar_counts)

    ret = {k: np.empty(v, dtype=np.int32) for k, v in enumerate(ar_counts)}

    counts = {k: 0 for k in range(len(ar_counts))}

    sum_: float = 0

    idx_row: int
    idx_col: int
    for idx_row, idx_col in enumerate(ar_result):
        idx = counts[idx_col]
        ret[idx_col][idx] = idx_row
        counts[idx_col] += 1
        v = mat[idx_row, idx_col]
        sum_ += v

    return ret, sum_
