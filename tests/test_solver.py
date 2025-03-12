import numpy as np
import pytest

from sbma import *


def _assert(mat, ar_counts, results, notes, output_sum):
    assert isinstance(results, dict)
    assert isinstance(notes, str)
    assert isinstance(output_sum, float)

    assigned_rows = []
    for col_idx, row_indices in results.items():
        assert len(row_indices) == ar_counts[col_idx]
        assigned_rows.extend(row_indices)
    assert sorted(assigned_rows) == list(range(mat.shape[0]))
    assert_results(mat, ar_counts, results, output_sum)


class TestInvalidInput:
    """Test class for invalid inputs to assignment function."""

    @staticmethod
    def test_invalid_matrix_dimensions():
        """Test invalid matrix dimensions."""
        ar_counts = np.arange(10)
        # Test 1D matrix
        mat = np.random.random(9).astype(np.float32)
        with pytest.raises(DimensionError):
            solve(mat, ar_counts)

        # Test 3D matrix
        mat = np.random.random((3, 3, 3)).astype(np.float32)
        with pytest.raises(DimensionError):
            solve(mat, ar_counts)

    @staticmethod
    def test_invalid_matrix_dtype():
        """Test invalid matrix data type."""
        mat = np.random.random((10, 5)).astype(np.float64)
        with pytest.raises(TypeError):
            solve(mat, np.arange(5))

    @staticmethod
    def test_invalid_counts_dimensions():
        """Test invalid counts array dimensions."""
        mat = np.random.random((10, 2)).astype(np.float32)
        ar_counts = np.array([[1, 2], [3, 4]], dtype=np.int32)
        with pytest.raises(DimensionError):
            solve(mat, ar_counts)

    @staticmethod
    def test_invalid_counts_dtype():
        """Test invalid counts data type."""
        mat = np.random.random((10, 3)).astype(np.float32)
        ar_counts = np.array([6.0, 2.0, 2.0], dtype=np.float32)
        with pytest.raises(TypeError):
            solve(mat, ar_counts)

    @staticmethod
    def test_negative_counts():
        """Test negative values in counts array."""
        mat = np.random.random((4, 3)).astype(np.float32)
        ar_counts = np.array([-1, 2, 3], dtype=np.int32)
        with pytest.raises(ValueError):
            solve(mat, ar_counts)

    @staticmethod
    def test_zero_counts():
        """Test zero values in counts array."""
        mat = np.random.random((4, 3)).astype(np.float32)
        ar_counts = np.array([0, 2, 2], dtype=np.int32)
        with pytest.raises(ValueError):
            solve(mat, ar_counts)

    @staticmethod
    def test_mismatched_dimensions():
        """Test mismatched dimensions between matrix and counts."""
        mat = np.random.random((4, 3)).astype(np.float32)
        ar_counts = np.array([2, 1], dtype=np.int32)  # Wrong length
        with pytest.raises(ShapeError):
            solve(mat, ar_counts)

    @staticmethod
    def test_invalid_counts_sum():
        """Test when sum of counts doesn't match matrix rows."""
        mat = np.random.random((4, 3)).astype(np.float32)
        ar_counts = np.array([1, 1, 1], dtype=np.int32)  # Sum = 3, but need 4
        with pytest.raises(ShapeError):
            solve(mat, ar_counts)

    @staticmethod
    def test_insufficient_columns():
        """Test matrix with less than 2 columns."""
        with pytest.raises(ShapeError):
            mat = np.random.random((4, 1)).astype(np.float32)
            ar_counts = np.array([4], dtype=np.int32)
            solve(mat, ar_counts)

    @staticmethod
    def test_negative_process_time():
        """Test negative max process time."""
        mat = np.random.random((3, 2)).astype(np.float32)
        ar_counts = np.array([1, 2]).astype(np.int32)
        with pytest.raises(ValueError):
            solve(mat, ar_counts, max_process_time=-1.0)

    @staticmethod
    def test_negative_error_threshold_abs():
        """Test negative absolute error threshold."""
        mat = np.random.random((3, 2)).astype(np.float32)
        ar_counts = np.array([1, 2]).astype(np.int32)
        with pytest.raises(ValueError):
            solve(mat, ar_counts, error_threshold_abs=-1.0)

    @staticmethod
    def test_negative_error_threshold_pct():
        """Test negative percentage error threshold."""
        mat = np.random.random((3, 2)).astype(np.float32)
        ar_counts = np.array([1, 2]).astype(np.int32)
        with pytest.raises(ValueError):
            solve(mat, ar_counts, error_threshold_pct=-1.0)

    @staticmethod
    def test_negative_max_iterations():
        """Test negative max iterations."""
        mat = np.random.random((4, 3)).astype(np.float32)
        ar_counts = np.array([1, 2, 1]).astype(np.int32)
        with pytest.raises(ValueError):
            solve(mat, ar_counts, max_iterations=-1)

    @staticmethod
    def test_nan():
        """Test a matrix with a nan."""
        mat = np.random.random((3, 2)).astype(np.float32)
        mat[0, 0] = np.nan
        ar_counts = np.array([1, 2]).astype(np.int32)
        with pytest.raises(ValueError):
            solve(mat, ar_counts)


@pytest.mark.parametrize("verbose", [True, False])
@pytest.mark.parametrize("skip_first_phase", [True, False])
@pytest.mark.parametrize("max_iterations", [0, 1, 1000])
def test_assign_basic(max_iterations, skip_first_phase, verbose):
    """Test basic functionality with small input."""
    n_cols = 3
    ar_counts = np.array([2, 1, 1], dtype=np.int32)
    n_rows = ar_counts.sum()
    mat = np.random.random((n_rows, n_cols)).astype(np.float32)

    results, notes, output_sum = solve(
        mat,
        ar_counts,
        max_iterations=max_iterations,
        skip_first_phase=skip_first_phase,
        verbose=verbose
    )
    _assert(mat, ar_counts, results, notes, output_sum)


@pytest.mark.parametrize("verbose", [True, False])
@pytest.mark.parametrize("skip_first_phase", [True, False])
@pytest.mark.parametrize("max_iterations", [0, 1, 1000])
def test_two_columns(max_iterations, skip_first_phase, verbose):
    """Test basic functionality with small input."""
    n_cols = 2
    ar_counts = np.array([2, 1], dtype=np.int32)
    n_rows = ar_counts.sum()
    mat = np.random.random((n_rows, n_cols)).astype(np.float32)

    results, notes, output_sum = solve(
        mat,
        ar_counts,
        max_iterations=max_iterations,
        skip_first_phase=skip_first_phase,
        verbose=verbose
    )
    _assert(mat, ar_counts, results, notes, output_sum)


@pytest.mark.parametrize("skip_first_phase", [True, False])
def test_assign_optimality(skip_first_phase):
    """Test that assign produces better results than random allocation."""
    n_cols = 4
    ar_counts = np.array([2, 2, 1, 1], dtype=np.int32)
    n_rows = ar_counts.sum()
    mat = np.random.random((n_rows, n_cols)).astype(np.float32)

    results, _, output_sum = solve(mat, ar_counts, skip_first_phase=skip_first_phase)

    assert_results(mat, ar_counts, results, output_sum)

    random_scores = []
    for _ in range(100):
        random_results = {}
        available_rows = set(range(n_rows))

        for col in range(n_cols):
            n_items = ar_counts[col]
            rows = np.random.choice(list(available_rows), size=n_items, replace=False)
            random_results[col] = rows
            available_rows -= set(rows)

        score = sum(mat[rows, col].sum() for col, rows in random_results.items())
        random_scores.append(score)

    # Check that the solver performs better than random
    assert output_sum > np.mean(random_scores)


@pytest.mark.parametrize("order", ["C", "F"])
def test_array_contiguity(order):
    """Ensure the solver works with both C and F contiguous arrays."""
    mat, ar_counts = generate_random_input(4, 3, order=order)

    assert mat.flags["C_CONTIGUOUS"] == (order == "C")
    assert mat.flags["F_CONTIGUOUS"] == (order == "F")

    results, notes, output_sum = solve(mat, ar_counts)
    _assert(mat, ar_counts, results, notes, output_sum)


@pytest.mark.parametrize("order", ["C", "F"])
@pytest.mark.parametrize("c_cols, max_counts", [(6, 3), (200, 500)])
@pytest.mark.parametrize("skip_first_phase", [True, False])
def test_deterministic(c_cols, max_counts, order, skip_first_phase):
    """Ensure the solver produces consistent results with same input.

    Tests both memory layouts and small/large matrices to cover AVX2 cases.
    """
    mat, ar_counts = generate_random_input(c_cols, max_counts, order=order)

    assert mat.flags["C_CONTIGUOUS"] == (order == "C")
    assert mat.flags["F_CONTIGUOUS"] == (order == "F")

    # Run twice
    results1, _, sum1 = solve(mat, ar_counts, skip_first_phase=skip_first_phase)
    results2, _, sum2 = solve(mat, ar_counts, skip_first_phase=skip_first_phase)

    res_list1 = {k: v.tolist() for k, v in results1.items()}
    res_list2 = {k: v.tolist() for k, v in results2.items()}

    assert sum1 == sum2
    assert res_list1 == res_list2
    assert_results(mat, ar_counts, results1, sum1)


def test_hardcoded():
    """Test against known results."""
    mat, ar_counts = generate_random_input(200, 500, seed=1)

    results, notes, output_sum = solve(mat, ar_counts, skip_first_phase=False)
    _assert(mat, ar_counts, results, notes, output_sum)

    sum_exp = 50810.37109375

    err = abs(sum_exp - output_sum) / sum_exp
    assert err < 0.00001


class TestTimeAndIterations:
    """Test class for time and iteration limits."""

    @staticmethod
    def test_zero_max_time():
        """Test with max_time=0"""
        mat, ar_counts = generate_random_input(200, 500)

        results, notes, output_sum = solve(
            mat,
            ar_counts,
            max_process_time=0.0,
            error_threshold_abs=0.0,
            error_threshold_pct=0.0,
            max_iterations=100,
        )
        _assert(mat, ar_counts, results, notes, output_sum)
        assert "Max process time reached" in notes

    @staticmethod
    def test_zero_max_iterations():
        """Test with max_iterations=0"""
        mat, ar_counts = generate_random_input(200, 500)

        results, notes, output_sum = solve(
            mat,
            ar_counts,
            max_process_time=300.0,
            error_threshold_abs=0.0,
            error_threshold_pct=0.0,
            max_iterations=0,
            verbose=False,
        )
        _assert(mat, ar_counts, results, notes, output_sum)

    @staticmethod
    @pytest.mark.parametrize("the_abs, thr_pct", [(0, 1000), (1000, 0)])
    def test_tolerance(the_abs, thr_pct):
        """Ensure a threshold is reached at the first iteration."""
        mat, ar_counts = generate_random_input(200, 500)

        results, notes, output_sum = solve(
            mat,
            ar_counts,
            max_process_time=300.0,
            error_threshold_abs=the_abs,
            error_threshold_pct=thr_pct,
            max_iterations=100,
            verbose=False,
        )
        _assert(mat, ar_counts, results, notes, output_sum)
        assert "after 1 iteration" in notes
