"""Unit-test for brute force solver."""

from sbma.solver import generate_random_input


def test_brute_force():
    """Test brute force solver."""
    try:
        from sbma.brute_force_solver import solve as brute_solve
    except ImportError:
        return

    n_cols = 5

    for _ in range(10):
        mat, ar_counts = generate_random_input(n_cols, 4, seed=None, order="C")
        results, _sum = brute_solve(mat, ar_counts)

        keys = sorted(results)
        assert keys == list(range(n_cols))

        list_rows = list(range(mat.shape[0]))
        chk_rows = sorted(i for ii in results.values() for i in ii)
        assert list_rows == chk_rows
