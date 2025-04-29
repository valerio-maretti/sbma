"""OR-Tools implementation."""

from time import time

import numpy as np
from ortools.linear_solver import pywraplp

from sbma import generate_random_input, solve

__all__ = [
    "solve_with_ortools",
]


def solve_with_ortools(
        mat: np.ndarray,
        ar_counts: np.ndarray,
        max_ms: int = 0
) -> tuple[dict[int, list[int]], str, float]:
    """Solve the assignment problem to maximize total score using OR-Tools.

    Args:
        mat (np.ndarray):
            2D NumPy array where mat[i, j] is the score of assigning
            item i to recipient j.
        ar_counts (np.ndarray):
            1D NumPy array where ar_counts[j] is the number of items
            recipient j should receive.
        max_ms (int):
            Set the maximum solver time in milliseconds. If 0 run till the
            optimal solution. Defaults to 0.

    Returns (tuple(dict(int, list(int)), str, float)):
        - Dictionary mapping recipient indices to arrays of assigned item indices.
        - Status message.
        - Total score.
    """
    if not np.issubdtype(mat.dtype, np.floating):
        mat = mat.astype(np.float64)

    # Get problem dimensions
    n_items, n_recipients = mat.shape

    solver = pywraplp.Solver.CreateSolver('GLOP')
    if not solver:
        raise RuntimeError("Solver not created.")

    if max_ms:
        solver.SetTimeLimit(max_ms)

    x = [[solver.NumVar(0.0, 1.0, f'x_{i}_{j}') for j in range(n_recipients)]
         for i in range(n_items)]

    # Set objective: Maximize total score
    objective = solver.Objective()
    for i in range(n_items):
        for j in range(n_recipients):
            # Explicitly cast to float to ensure compatibility
            objective.SetCoefficient(x[i][j], float(mat[i, j]))
    objective.SetMaximization()

    # Constraint 1: Each item is assigned to exactly one recipient
    for i in range(n_items):
        constraint = solver.Constraint(1.0, 1.0)
        for j in range(n_recipients):
            constraint.SetCoefficient(x[i][j], 1.0)

    # Constraint 2: Each recipient gets exactly ar_counts[j] items
    for j in range(n_recipients):
        constraint = solver.Constraint(float(ar_counts[j]), float(ar_counts[j]))
        for i in range(n_items):
            constraint.SetCoefficient(x[i][j], 1.0)

    status = solver.Solve()

    if status == pywraplp.Solver.OPTIMAL:
        notes = "Optimal solution found."
    else:
        notes = "!!! No optimal solution found. !!!"

    solution = np.array([[x[i][j].solution_value() for j in range(n_recipients)]
                         for i in range(n_items)])
    assignment = np.argmax(solution, axis=1)

    assignment_dict = {j: [] for j in range(n_recipients)}
    for i, j in enumerate(assignment):
        assignment_dict[j].append(i)

    total_score = objective.Value()

    return assignment_dict, notes, total_score


def benchmark_against_ortools(n_cols: int = 100, max_count: int = 50):
    """Benchmark against OR-tools."""
    benchmark = []
    for seed in range(5):
        print(f"{seed=}")
        mat, ar_counts = generate_random_input(n_cols, max_count, seed=seed, order="C")
        shape = mat.shape

        start = time()
        _results, _msg, score_sum = solve(mat, ar_counts)
        end = time() - start

        start = time()
        _results_ortools, _msg, score_ortools = solve_with_ortools(mat, ar_counts, max_ms=0)
        end_ortools = time() - start

        benchmark.append((shape, score_sum, end, score_ortools, end_ortools))

    table = [
        "Benchmark against OR-tools",
        "=" * 81,
        "Matrix Size    | Solver            | OR-tools          | Delta Score | Time Ratio",
        "[rows x cols]  | Time(s) |  Score  | Time(s) |  Score  |     [%]     |    [*]",
        "-" * 81
    ]

    for shape, score_sum, t_cpp, score_ortools, t_ortools in benchmark:
        matrix_size = f"{shape[0]} x {shape[1]}"
        delta = ((score_sum - score_ortools) / score_ortools * 100) if score_ortools != 0 else 0.0
        speedup = round(t_ortools / t_cpp) if t_cpp else 0
        speedup_str = f"{speedup}" if speedup else " N/A"

        row_str = (f"{matrix_size:<14} | {t_cpp:>6.4f}  | {score_sum:>7.2f} | "
                   f"  {t_ortools:<4.1f}  | {score_ortools:>7.2f} |"
                   f" {delta:>7.2f}%    |  {speedup_str:>3s}")
        table.append(row_str)

    return "\n".join(table)


if __name__ == "__main__":
    result_benchmark = benchmark_against_ortools(n_cols=100, max_count=100)
    print(result_benchmark)
