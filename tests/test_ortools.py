"""Unit-test for the OR-Tools implementation."""

import numpy as np
import pytest

from sbma.benchmarks.ortools_assignment import solve_with_ortools
from sbma.solver import assert_results, generate_random_input


@pytest.mark.parametrize("n_cols", [5, 10, 40])
@pytest.mark.parametrize("max_ms", [0, 1000])
def test_solve_with_ortools(n_cols: int, max_ms: int):
    """Test OR-Tools implementation."""
    avg_count = np.random.randint(3, 50)
    mat, ar_counts = generate_random_input(n_cols, avg_count, seed=None, order="C")
    results, _msg, score_sum = solve_with_ortools(mat, ar_counts, max_ms=max_ms)

    keys = sorted(results)
    assert keys == list(range(n_cols))

    list_rows = list(range(mat.shape[0]))
    chk_rows = sorted(i for ii in results.values() for i in ii)
    assert list_rows == chk_rows

    assert_results(mat, ar_counts, results, score_sum)
