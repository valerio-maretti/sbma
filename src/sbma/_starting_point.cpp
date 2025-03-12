#include <cstdio>
#include <cfloat>
#include <immintrin.h>
#include "_util.hpp"

#ifdef _WIN32
    #include <intrin.h>
    #define cpuid(info, x) __cpuidex(info, x, 0)
#else
    #include <cpuid.h>
    void cpuid(int info[4], int x) {
        __cpuid_count(x, 0, info[0], info[1], info[2], info[3]);
    }
#endif

// ---------------------------- QUICKSORT
static void swap(int* a, int* b) {
    int temp = *a;
    *a = *b;
    *b = temp;
}

static int partition(const float* scores, int* indices, int low, int high) {
    float pivot = scores[indices[high]];
    int i = low - 1;

    for (int j = low; j < high; j++) {
        if (scores[indices[j]] > pivot) {
            i++;
            swap(&indices[i], &indices[j]);
        }
    }
    swap(&indices[i + 1], &indices[high]);
    return i + 1;
}

static void quicksort(const float* scores, int* indices, int low, int high) {
    if (low < high) {
        int pi = partition(scores, indices, low, high);
        quicksort(scores, indices, low, pi - 1);
        quicksort(scores, indices, pi + 1, high);
    }
}

static void sort_indices_descending(const float* scores, int* indices, int n) {
    for (int i = 0; i < n; i++) {
        indices[i] = i;
    }
    quicksort(scores, indices, 0, n - 1);
}

// ---------------------------- ROW SCORES
static void calculate_row_scores_scalar(const float* mat, float* scores, size_t n_rows, size_t n_cols) {
    for (size_t idx_row = 0; idx_row < n_rows; idx_row++) {
        const float* row = mat + idx_row * n_cols;
        float max_val = row[0];
        float second_max = -FLT_MAX;

        for (size_t idx_col = 1; idx_col < n_cols; idx_col++) {
            if (row[idx_col] > max_val) {
                second_max = max_val;
                max_val = row[idx_col];
            } else if (row[idx_col] > second_max) {
                second_max = row[idx_col];
            }
        }

        // Special case: if all elements are equal or n_cols == 1
        if (second_max == -FLT_MAX) {
            second_max = max_val;
        }

        scores[idx_row] = max_val + (max_val - second_max);  // best one
        // scores[idx_row] = max_val;
        // scores[idx_row] = max_val - second_max;
    }
}

static bool calculate_row_scores_avx2(const float* mat, float* scores, size_t n_rows, size_t n_cols) {
    const int simd_width = 8;

    float* max_array = (float*)malloc(simd_width * sizeof(float));
    float* second_max_array = (float*)malloc(simd_width * sizeof(float));

    if (!max_array || !second_max_array) {
        free(max_array);
        free(second_max_array);
        return false;
    }

    const int n_cols_32 = (int)n_cols;
    const int limit = n_cols_32 - (n_cols_32 % simd_width);

    for (size_t idx_row = 0; idx_row < n_rows; idx_row++) {
        const float* row = mat + idx_row * n_cols;
        float max_val = row[0];
        float second_max = -FLT_MAX;

//        if (n_cols_32 >= simd_width) {  // if I'm here I have more than 32 cols
        __m256 max_vec = _mm256_set1_ps(-FLT_MAX);
        __m256 second_max_vec = _mm256_set1_ps(-FLT_MAX);

        for (int idx_col = 0; idx_col < limit; idx_col += simd_width) {
            __m256 curr_vec = _mm256_loadu_ps(row + idx_col);

            // Update second_max_vec
            __m256 mask = _mm256_cmp_ps(curr_vec, max_vec, _CMP_GT_OQ);
            second_max_vec = _mm256_max_ps(
                second_max_vec,
                _mm256_blendv_ps(curr_vec, max_vec, mask)
            );

            // Update max_vec
            max_vec = _mm256_max_ps(max_vec, curr_vec);
        }

        _mm256_storeu_ps(max_array, max_vec);
        _mm256_storeu_ps(second_max_array, second_max_vec);

        for (int idx_col = 0; idx_col < simd_width; idx_col++) {
            if (max_array[idx_col] > max_val) {
                second_max = max_val;
                max_val = max_array[idx_col];
            } else if (max_array[idx_col] > second_max) {
                second_max = max_array[idx_col];
            }
        }
//        }

        for (int idx_col = limit; idx_col < n_cols_32; idx_col++) {
            if (row[idx_col] > max_val) {
                second_max = max_val;
                max_val = row[idx_col];
            } else if (row[idx_col] > second_max) {
                second_max = row[idx_col];
            }
        }

        // all elements are equal or n_cols == 1
        if (second_max == -FLT_MAX) {
            second_max = max_val;
        }

        scores[idx_row] = max_val + (max_val - second_max);  // best one
        // scores[idx_row] = max_val;
        // scores[idx_row] = second_max;
    }
    free(max_array);
    free(second_max_array);
    return true;
}

// ---------------------------- ENTRY POINT
static bool get_optimal_starting_point_scalar(
    const float* mat,
    const int* ar_counts,
    size_t* initial_assign,
    size_t n_rows,
    size_t n_cols
) {
    float* row_scores = (float*)malloc(n_rows * sizeof(float));
    int* sorted_indices = (int*)malloc(n_rows * sizeof(int));
    int* remaining_counts = (int*)malloc(n_cols * sizeof(int));
    char* taken_rows = (char*)calloc(n_rows, sizeof(char));

    if (!row_scores || !sorted_indices || !remaining_counts || !taken_rows) {
        free(row_scores);
        free(sorted_indices);
        free(remaining_counts);
        free(taken_rows);
        return false;
    }

    int n_cols_32 = (int)n_cols;

    calculate_row_scores_scalar(mat, row_scores, n_rows, n_cols);
    sort_indices_descending(row_scores, sorted_indices, (int)n_rows);

    remaining_counts = (int*)memcpy(remaining_counts, ar_counts, n_cols * sizeof(int));

    for (size_t idx_row = 0; idx_row < n_rows; idx_row++) {
        int row_best_idx = sorted_indices[idx_row];

        if (taken_rows[row_best_idx]) {
            continue;
        }

        int best_col = -1;
        float best_val = -FLT_MAX;
        const float* row = mat + row_best_idx * n_cols;

        for (int idx_col = 0; idx_col < n_cols_32; idx_col++) {
            if (remaining_counts[idx_col] > 0 && row[idx_col] > best_val) {
                best_val = row[idx_col];
                best_col = idx_col;
            }
        }

        if (best_col != -1) {
            initial_assign[row_best_idx] = (size_t)best_col;
            remaining_counts[best_col]--;
            taken_rows[row_best_idx] = 1;
        }
    }
    free(row_scores);
    free(sorted_indices);
    free(remaining_counts);
    free(taken_rows);
    return true;
}

static bool get_optimal_starting_point_avx2(
    const float* mat,
    const int* ar_counts,
    size_t* initial_assign,
    size_t n_rows,
    size_t n_cols
) {
    float* row_scores = (float*)malloc(n_rows * sizeof(float));
    int* sorted_indices = (int*)malloc(n_rows * sizeof(int));
    int* remaining_counts = (int*)malloc(n_cols * sizeof(int));
    char* taken_rows = (char*)calloc(n_rows, sizeof(char));

    if (!row_scores || !sorted_indices || !remaining_counts || !taken_rows) {
        free(row_scores);
        free(sorted_indices);
        free(remaining_counts);
        free(taken_rows);
        return false;
    }

    remaining_counts = (int*)memcpy(remaining_counts, ar_counts, n_cols * sizeof(int));

    if (!calculate_row_scores_avx2(mat, row_scores, n_rows, n_cols)) {
        return false;
    }
    sort_indices_descending(row_scores, sorted_indices, (int)n_rows);

    const int simd_width = 8;
    const size_t simd_width_64 = (size_t)simd_width;
    const int n_cols_32 = (int)n_cols;
    const int limit = n_cols_32 - (n_cols_32 % simd_width_64);

    __m256 min_vec = _mm256_set1_ps(-FLT_MAX);
    __m256i increment = _mm256_set_epi32(7, 6, 5, 4, 3, 2, 1, 0);

    for (size_t idx_row = 0; idx_row < n_rows; idx_row++) {
        int row_best_idx = sorted_indices[idx_row];
        if (taken_rows[row_best_idx]) continue;

        const float* row = mat + row_best_idx * n_cols;
        int best_col = -1;
        float best_val = -FLT_MAX;

        // SIMD processing
        for (int i = 0; i < limit; i += simd_width) {
            __m256 row_vec = _mm256_loadu_ps(row + i);
            __m256i counts_vec = _mm256_loadu_si256((__m256i*)(remaining_counts + i));
            __m256i col_indices = _mm256_add_epi32(_mm256_set1_epi32(i), increment);

            // Create mask for valid counts
            __m256i zero = _mm256_setzero_si256();
            __m256i valid_mask = _mm256_cmpgt_epi32(counts_vec, zero);

            __m256 masked_vals = _mm256_blendv_ps(min_vec, row_vec,
                _mm256_castsi256_ps(valid_mask));

            float vals[8];
            int indices[8];
            _mm256_storeu_ps(vals, masked_vals);
            _mm256_storeu_si256((__m256i*)indices, col_indices);

            // Process the 8 values
            for (int j = 0; j < 8; j++) {
                if (vals[j] > best_val) {
                    best_val = vals[j];
                    best_col = indices[j];
                }
            }
        }

        // Process remaining elements
        for (int i = limit; i < n_cols_32; i++) {
            if (remaining_counts[i] > 0 && row[i] > best_val) {
                best_val = row[i];
                best_col = i;
            }
        }

        if (best_col != -1) {
            initial_assign[row_best_idx] = (size_t)best_col;
            remaining_counts[best_col]--;
            taken_rows[row_best_idx] = 1;
        }
    }

    free(row_scores);
    free(sorted_indices);
    free(remaining_counts);
    free(taken_rows);
    return true;
}

static bool check_avx2() {
    int cpu_info[4];
    cpuid(cpu_info, 7);
    return (cpu_info[1] & (1 << 5)) != 0;
}

bool get_optimal_starting_point(
    float* mat,
    int* ar_counts,
    size_t* initial_assign,
    size_t n_rows,
    size_t n_cols,
    bool verbose
) {
    bool is_avx2_supported = check_avx2();
    if (verbose) {
        printf("AVX2 supported: %s\n", is_avx2_supported ? "true" : "false");
    }

    bool flag;

    // Use scalar version for small matrices (n_cols < 32)
    if (!is_avx2_supported || n_cols < 32) {
        flag = get_optimal_starting_point_scalar(mat, ar_counts, initial_assign, n_rows, n_cols);
    } else {
        flag = get_optimal_starting_point_avx2(mat, ar_counts, initial_assign, n_rows, n_cols);
    }

    return flag;
}


bool get_random_starting_point(
    int* ar_counts,
    size_t* initial_assign,
    size_t n_cols
 ) {
    size_t start = 0;
    size_t idx_col = 0;

    for (size_t idx_count = 0; idx_count < n_cols; idx_count++) {
        size_t count = (size_t)ar_counts[idx_count];
        size_t end = start + count;
        for (size_t i = start; i < end; i++) {
            initial_assign[i] = idx_col;
        }
        idx_col++;
        start += count;
    }

    return true;
}