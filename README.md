# Score Based Multi Assignment

A fast algorithm for optimizing multi-assignment problems at scale, capable of 
processing matrices of several GB while achieving near-optimal results. 

This project addresses the assignment optimization problem where items must be 
assigned to recipients based on a score matrix, with specific allocation 
counts per recipient. For more context on assignment problems, see 
[Wikipedia](https://en.wikipedia.org/wiki/Assignment_problem).

### The Core Assignment Problem:
Given an *n x m* score matrix (rows representing items, columns representing recipients) 
and assignment constraints, assign each item to exactly one recipient to maximize 
the total score while satisfying predetermined allocation counts per recipient.

```math
\begin{equation*}
S_{n,m} = 
\begin{pmatrix}
s_{1,1} & s_{1,2} & \cdots & s_{1,m} \\
s_{2,1} & s_{2,2} & \cdots & s_{2,m} \\
\vdots  & \vdots  & \ddots & \vdots  \\
s_{n,1} & s_{n,2} & \cdots & s_{n,m} 
\end{pmatrix}
\end{equation*}
```

An allocation counts array (of *integer*) of size *m* specifies
the number of items that must be assigned to each recipient.
The unique constraint is that all items must be assigned exactly once.
As a consequence, the sum of the elements in the allocation counts array is equal 
to the number of rows in the matrix, ensuring that all items are accounted for.

```math
\begin{equation*}
C_{m} = 
\begin{bmatrix}
c_{1}, & c_{2}, & \cdots & c_{m} \\
\end{bmatrix}
\end{equation*}
```

The objective is to maximize the total score across all assignments.
This is achieved by selecting the combination of items for each recipient that
results in the highest sum of scores from the input matrix.

Eg: given the score matrix (5 x 3):

| Item             | Recipient <sub>0</sub> | Recipient <sub>1</sub> | Recipient <sub>2</sub> | 
|:-----------------|:----------------------:|:----------------------:|:----------------------:|
| Item<sub>0</sub> |    s<sub>0,0</sub>     |    s<sub>0,1</sub>     |    s<sub>0,2</sub>     | 
| Item<sub>1</sub> |    s<sub>1,0</sub>     |    s<sub>1,1</sub>     |    s<sub>1,2</sub>     | 
| Item<sub>2</sub> |    s<sub>2,0</sub>     |    s<sub>2,1</sub>     |    s<sub>2,2</sub>     | 
| Item<sub>3</sub> |    s<sub>3,0</sub>     |    s<sub>3,1</sub>     |    s<sub>3,2</sub>     | 
| Item<sub>4</sub> |    s<sub>4,0</sub>     |    s<sub>4,1</sub>     |    s<sub>4,2</sub>     | 
| Item<sub>5</sub> |    s<sub>5,0</sub>     |    s<sub>5,1</sub>     |    s<sub>5,2</sub>     | 

and the allocation array $`[1, 3, 2]`$

Assuming the **best assigned scores** are the following:

| Item             | Recipient <sub>0</sub> | Recipient <sub>1</sub> | Recipient <sub>2</sub> | 
|:-----------------|:----------------------:|:----------------------:|:----------------------:|
| Item<sub>0</sub> |    s<sub>0,0</sub>     | ✅**s<sub>0,1</sub>**  |    s<sub>0,2</sub>     | 
| Item<sub>1</sub> | ✅**s<sub>1,0</sub>**  |    s<sub>1,1</sub>     |    s<sub>1,2</sub>     | 
| Item<sub>2</sub> |    s<sub>2,0</sub>     |    s<sub>2,1</sub>     | ✅**s<sub>2,2</sub>**  | 
| Item<sub>3</sub> |    s<sub>3,0</sub>     |    s<sub>3,1</sub>     | ✅**s<sub>3,2</sub>**  | 
| Item<sub>4</sub> |    s<sub>4,0</sub>     | ✅**s<sub>4,1</sub>**  |    s<sub>4,2</sub>     | 
| Item<sub>5</sub> |    s<sub>5,0</sub>     | ✅**s<sub>5,1</sub>**  |    s<sub>5,2</sub>     |

The final assignment would be:

**Recipient <sub>0</sub> &rarr; [s<sub>1,0</sub>]**<br>
**Recipient <sub>1</sub> &rarr; [s<sub>0,1</sub>, s<sub>4,1</sub>, s<sub>5,1</sub>]**<br>
**Recipient <sub>2</sub> &rarr; [s<sub>2,2</sub>, s<sub>3,2</sub>]**<br>

Expressed as python dictionary where the keys represent the column index and the values the row indexes:
```python
{0: array([1]), 1: array([0, 4, 5]), 2: array([2, 3])}
```

Although methods such as brute force or optimization libraries like Google OR-Tools
and Gurobi can yield exact solution(s) to this problem, they often come with a
high computational cost, especially for large-scale problems.

The algorithm proposed in this project finds an approximate and repeatable solution,
typically achieving a final sum of scores that is within 1% of the optimal solution,
but with significantly reduced computation time. For instance, solving a
1,000,000 x 500 matrix can be accomplished in less than 1 minute using the proposed algorithm,
compared to many hours with free / commercial solvers.

## Key Features

#### Technical Implementation:
- **Compiled Core:** C++ implementation with Python bindings for speed and usability
- **Memory Efficient:** Uses less than 5% of matrix size for internal calculations 
- **Hardware Optimized:** Leverages AVX2 instruction set when available

#### Performance Characteristics:
- **Robust Scaling:** Handles matrices over 200GB
- **Matrix Layout:** Works well with both row-major (C) and column-major (F) matrix layout (see benchmark)
 
#### Algorithm Approach:
1. **Initial Solution Phase:** Quick generation of initial assignments (optimized for C-contiguous arrays)
2. **Refinement Phase** (Optional): Iterative swapping to improve assignments (usually < 1% increase)

### Performance Benchmarks

```
Benchmark with Intel Core Ultra 7 155H (5 runs test case with random generated data)
========================================================================================================
Matrix Size             | Order | Initial Phase           | Refinement Phase         | Iters | Improve |
[rows x cols]    | [MB] |       | Time(ms)      | Score   | Time(ms)       | Score   |       |         |
--------------------------------------------------------------------------------------------------------
49,242 x 200     | 38   | C     | 38 ±6         | 48786   | 163 ±13        | 48927   | 6     | 0.2886% |
49,242 x 200     | 38   | F     | 48 ±3         | 48786   | 164 ±15        | 48927   | 6     | 0.2886% |
249,031 x 500    | 475  | C     | 399 ±6        | 248062  | 3296 ±127      | 248376  | 7     | 0.1269% |
249,031 x 500    | 475  | F     | 638 ±10       | 248062  | 3748 ±360      | 248376  | 7     | 0.1269% |
1,264,241 x 1000 | 4823 | C     | 3859 ±40      | 1261859 | 74186 ±4522    | 1262622 | 8     | 0.0605% |
1,264,241 x 1000 | 4823 | F     | 6675 ±120     | 1261859 | 78075 ±2347    | 1262622 | 8     | 0.0605% |
```

Where:
- *Order:* matrix layout, C-contiguous or F-contiguous
- *Score:* rounded sum of the scores selected
- *Iters:* number of iterations performed by the additional refinement step
- *Improve:* percentage increase in score after the refinement step, compared to the initial score

## Installation

You can clone the git repository and run the setup script.

```bash
$ git clone https://gitlab.com/valerio.maretti/sbma.git
$ cd sbma
$ pip install .
```

### Dependencies

- A C++ compiler (supports gcc, clang, or MSVC)
- NumPy

The core algorithm is written in C++ with Python bindings, requiring only `numpy` 
as a dependency, primarily for input checking and casting.

## Usage

The `solve` function expects:
- A `np.float32` score matrix (`NaN` are not allowed)
- A `np.int32/int64` assignment array

Eg

```python
import numpy as np
from sbma.solver import solve

np.random.seed(0)

# Define problem parameters
n_cols = 3  # Number of recipients
ar_counts = np.random.randint(1, 5, n_cols)  # Min and Max number of items each recipient get
n_rows = ar_counts.sum()  # Total number of items to assign

# Random score matrix (each cell represents score for assigning item i to recipient j)
mat = np.random.random((n_rows, n_cols)).astype(np.float32)

# Solve the assignment problem
results, status_msg, output_sum = solve(mat, ar_counts)

print(f"Assignment requirements:\n{ar_counts}")
array([2, 4, 1])  # First recipient gets 2 items, second gets 4, third gets 1

print(f"Number of rows: {n_rows}")
7  # Equal to the sum of the item to assign

print(f"Score matrix: {mat.round(3)}")  # Round for a better visualization
array([[0.933, 0.128, 0.999],
       [0.236, 0.397, 0.388],
       [0.67,  0.936, 0.846],
       [0.313, 0.525, 0.443],
       [0.23,  0.534, 0.914],
       [0.457, 0.431, 0.939],
       [0.778, 0.716, 0.803]])

print("Optimal assignments:\n", results)
{0: array([0, 6]), 1: array([1, 2, 3, 4]), 2: array([5])}
# Meaning: 
# - Recipient 0 gets items 0 and 6
# - Recipient 1 gets items 1, 2, 3 and 4
# - Recipient 2 gets item 5

print(f"Solution status:\n{status_msg}")  # Indicates runtime and iterations
'Stop condition reached in 0.000s after 1 iteration'

print(f"Total score achieved:\n{output_sum}")
5.041  # Sum of scores for all selected assignments
```

Check the `solve` docstring to see the optional parameters related to the stop
conditions and the verbosity.

## Benchmark against OR-Tools

To evaluate the performance of the solver, it is benchmarked against OR-Tools, 
the Google optimization library using randomly generated data.<br>
The solver completes in milliseconds compared to OR-Tools, which requires minutes 
for similar inputs. The final score achieved is nearly identical to OR-Tools,
with a difference of less than 1%.

The problem is reformulated for the linear solver as follows:

**Objective**: Maximize the total score of assignments:
```math
\begin{equation*}
\text{Maximize} \sum_{i=0}^{n_{\text{items}}-1} \sum_{j=0}^{n_{\text{recipients}}-1} \text{mat}[i, j] \cdot x[i, j]
\end{equation*}
```
  where `x[i, j]` is a binary variable indicating whether item `i` is assigned to recipient `j` (1 if assigned, 0 otherwise).

**Constraints**:
- Each item is assigned to exactly one recipient:
```math
\begin{equation*}
\sum_{j=0}^{n_{\text{recipients}}-1} x[i, j] = 1 \quad \text{for all} \quad i = 0, \dots, n_{\text{items}}-1
\end{equation*} 
```

- Each recipient receives exactly `ar_counts[j]` items:
```math
\begin{equation*}
\sum_{i=0}^{n_{\text{items}}-1} x[i, j] = \text{counts}_j \quad \text{for all} \quad j = 0, \dots, n_{\text{recipients}}-1
\end{equation*}
```

- Non-negativity and upper bound:
```math
\begin{equation*}
0 \leq x[i, j] \leq 1 \quad \text{for all} \quad i, j
\end{equation*}
```

The problem’s constraint matrix is totally unimodular, allowing continuous variables to yield integer solutions when solved as an LP, making it efficient for solvers like OR-Tools.

### Results
```
Benchmark against OR-tools (~5000 x 100 Input Matrix)
=================================================================================
Matrix Size    | Solver            | OR-tools          | Delta Score | Time Ratio
[rows x cols]  | Time(s) |  Score  | Time(s) |  Score  |     [%]     |     
---------------------------------------------------------------------------------
4785 x 100     | 0.0040  | 4720.75 |  46.7   | 4726.88 |   -0.13%    |  ~11670
4568 x 100     | 0.0025  | 4503.50 |  42.1   | 4509.85 |   -0.14%    |  ~16769
5492 x 100     | 0.0045  | 5421.23 |  58.8   | 5427.56 |   -0.12%    |  ~13041
4705 x 100     | 0.0040  | 4641.18 |  43.9   | 4647.40 |   -0.13%    |  ~10979
5179 x 100     | 0.0035  | 5111.92 |  54.6   | 5117.98 |   -0.12%    |  ~15534


Benchmark against OR-tools (~7500 x 150 Input Matrix)
=================================================================================
Matrix Size    | Solver            | OR-tools          | Delta Score | Time Ratio
[rows x cols]  | Time(s) |  Score  | Time(s) |  Score  |     [%]     |     
---------------------------------------------------------------------------------
7207 x 150     | 0.0061  | 7139.79 |  180.1  | 7148.01 |   -0.12%    |  ~29525
7208 x 150     | 0.0085  | 7136.76 |  179.6  | 7145.25 |   -0.12%    |  ~21129
8123 x 150     | 0.0065  | 8052.45 |  227.0  | 8060.10 |   -0.09%    |  ~34923
7074 x 150     | 0.0064  | 7006.99 |  213.3  | 7015.34 |   -0.12%    |  ~33328
7574 x 150     | 0.0071  | 7506.62 |  214.2  | 7514.61 |   -0.11%    |  ~30169

* Time Ratio approximates OR-Tools time divided by the SBMA solver time.
```
