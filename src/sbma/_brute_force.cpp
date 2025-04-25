#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <numpy/arrayobject.h>
#include <vector>
#include <algorithm>
#include <limits>
#include <cstddef> // for size_t

size_t* brute_force_solver(const float* mat, const size_t n_rows, const size_t n_cols, const int* ar_counts) {
    // Create initial assignment array
    std::vector<size_t> assignment;
    assignment.reserve(n_rows); // Pre-allocate to avoid reallocations
    for (size_t rec = 0; rec < n_cols; rec++) {
        int count = ar_counts[rec];
        for (int i = 0; i < count; i++) {
            assignment.push_back(rec);
        }
    }

    // Sort to ensure std::next_permutation starts correctly
    std::sort(assignment.begin(), assignment.end());

    // Initialize tracking for best assignment
    double max_score = -std::numeric_limits<double>::infinity();
    std::vector<size_t> best_assignment;

    do {
        double score = 0.0;
        for (size_t i = 0; i < n_rows; i++) {
            size_t rec = assignment[i];
            score += static_cast<double>(mat[i * n_cols + rec]);
        }
        if (score > max_score) {
            max_score = score;
            best_assignment = assignment;
        }
    } while (std::next_permutation(assignment.begin(), assignment.end()));

    size_t* result = new size_t[n_rows];
    std::copy(best_assignment.begin(), best_assignment.end(), result);

    return result;
}


extern "C" {

static PyObject* solve(PyObject* self, PyObject* args) {
    PyArrayObject *py_mat, *py_allocation_counts;

    if (!PyArg_ParseTuple(args, "O!O!",
                          &PyArray_Type, &py_mat,
                          &PyArray_Type, &py_allocation_counts)) {
        return nullptr;
    }

    size_t n_rows = (size_t)PyArray_DIM(py_mat, 0);
    size_t n_cols = (size_t)PyArray_DIM(py_mat, 1);

    float* mat = (float*)PyArray_DATA(py_mat);
    int* ar_counts = (int*)PyArray_DATA(py_allocation_counts);

    size_t* out = brute_force_solver(mat, n_rows, n_cols, ar_counts);

    npy_intp dims[] = {n_rows};
    PyObject* py_out = PyArray_SimpleNewFromData(1, dims, NPY_UINTP, out);

    if (!py_out) {
        return nullptr;
    }
    PyArray_ENABLEFLAGS((PyArrayObject*)py_out, NPY_ARRAY_OWNDATA);

    return py_out;
}

static PyMethodDef methods[] = {
    {"solve", (PyCFunction)solve, METH_VARARGS, "Brute force solver"},
    {nullptr, nullptr, 0, nullptr}
};

static struct PyModuleDef module = {
    PyModuleDef_HEAD_INIT,
    "_brute_force_solver",
    nullptr,
    -1,
    methods
};

PyMODINIT_FUNC PyInit__brute_force_solver(void) {
    import_array();  // Must be called for NumPy support
    return PyModule_Create(&module);
}

} // extern "C"