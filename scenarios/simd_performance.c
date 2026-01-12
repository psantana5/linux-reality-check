/*
 * SIMD vs Scalar Performance Benchmark
 * 
 * Compares SIMD (Single Instruction Multiple Data) vectorized operations
 * against scalar implementations. SIMD processes multiple data elements
 * in parallel using wide registers (128-bit, 256-bit, 512-bit).
 *
 * Expected Results:
 * - Scalar: Baseline performance
 * - SSE (128-bit): ~2-4x faster
 * - AVX2 (256-bit): ~4-8x faster
 * - Auto-vectorized: Compiler-dependent speedup
 *
 * What This Tests:
 * - SIMD instruction effectiveness
 * - Compiler auto-vectorization
 * - Memory alignment impact
 * - Data parallelism potential
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <immintrin.h>

#define ARRAY_SIZE (1024 * 1024)  // 1M elements
#define ITERATIONS 100

static inline uint64_t get_time_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1000000000ULL + ts.tv_nsec;
}

// Scalar implementation: add two arrays element by element
uint64_t add_scalar(float *a, float *b, float *result, size_t n) {
    uint64_t start = get_time_ns();
    
    for (size_t i = 0; i < n; i++) {
        result[i] = a[i] + b[i];
    }
    
    return get_time_ns() - start;
}

// Auto-vectorized (compiler decides)
uint64_t add_auto_vectorized(float *a, float *b, float *result, size_t n) {
    uint64_t start = get_time_ns();
    
    // Hint to compiler this can be vectorized
    #pragma GCC ivdep
    for (size_t i = 0; i < n; i++) {
        result[i] = a[i] + b[i];
    }
    
    return get_time_ns() - start;
}

// Explicit SSE (128-bit, 4 floats at once)
uint64_t add_sse(float *a, float *b, float *result, size_t n) {
    uint64_t start = get_time_ns();
    
    size_t i;
    for (i = 0; i < n - 3; i += 4) {
        __m128 va = _mm_load_ps(&a[i]);
        __m128 vb = _mm_load_ps(&b[i]);
        __m128 vr = _mm_add_ps(va, vb);
        _mm_store_ps(&result[i], vr);
    }
    
    // Handle remainder
    for (; i < n; i++) {
        result[i] = a[i] + b[i];
    }
    
    return get_time_ns() - start;
}

// AVX2 (256-bit, 8 floats at once)
uint64_t add_avx2(float *a, float *b, float *result, size_t n) {
    uint64_t start = get_time_ns();
    
    size_t i;
    for (i = 0; i < n - 7; i += 8) {
        __m256 va = _mm256_load_ps(&a[i]);
        __m256 vb = _mm256_load_ps(&b[i]);
        __m256 vr = _mm256_add_ps(va, vb);
        _mm256_store_ps(&result[i], vr);
    }
    
    // Handle remainder
    for (; i < n; i++) {
        result[i] = a[i] + b[i];
    }
    
    return get_time_ns() - start;
}

// Dot product: scalar
float dot_product_scalar(float *a, float *b, size_t n) {
    float sum = 0.0f;
    for (size_t i = 0; i < n; i++) {
        sum += a[i] * b[i];
    }
    return sum;
}

// Dot product: SSE
float dot_product_sse(float *a, float *b, size_t n) {
    __m128 sum = _mm_setzero_ps();
    
    size_t i;
    for (i = 0; i < n - 3; i += 4) {
        __m128 va = _mm_load_ps(&a[i]);
        __m128 vb = _mm_load_ps(&b[i]);
        sum = _mm_add_ps(sum, _mm_mul_ps(va, vb));
    }
    
    // Horizontal add to get final sum
    sum = _mm_hadd_ps(sum, sum);
    sum = _mm_hadd_ps(sum, sum);
    
    float result = _mm_cvtss_f32(sum);
    
    // Handle remainder
    for (; i < n; i++) {
        result += a[i] * b[i];
    }
    
    return result;
}

void run_experiment(FILE *csv) {
    // Allocate aligned memory for SIMD
    float *a = (float*)aligned_alloc(32, ARRAY_SIZE * sizeof(float));
    float *b = (float*)aligned_alloc(32, ARRAY_SIZE * sizeof(float));
    float *result = (float*)aligned_alloc(32, ARRAY_SIZE * sizeof(float));
    
    if (!a || !b || !result) {
        perror("aligned_alloc");
        return;
    }
    
    // Initialize with random data
    for (size_t i = 0; i < ARRAY_SIZE; i++) {
        a[i] = (float)i * 0.1f;
        b[i] = (float)i * 0.2f;
    }
    
    int run = 0;
    
    printf("Testing vector addition (%zu elements, %d iterations)...\n", 
           ARRAY_SIZE, ITERATIONS);
    
    // Test 1: Scalar
    printf("  Scalar implementation...\n");
    for (int iter = 0; iter < ITERATIONS; iter++) {
        uint64_t start_ts = get_time_ns();
        uint64_t runtime = add_scalar(a, b, result, ARRAY_SIZE);
        double throughput_gflops = (double)ARRAY_SIZE / runtime;  // GFLOP/s
        
        fprintf(csv, "%d,scalar_add,%lu,%lu,0,0,0,0,-1,-1,%.3f\n",
               run++, start_ts, runtime, throughput_gflops);
    }
    
    // Test 2: Auto-vectorized
    printf("  Auto-vectorized...\n");
    for (int iter = 0; iter < ITERATIONS; iter++) {
        uint64_t start_ts = get_time_ns();
        uint64_t runtime = add_auto_vectorized(a, b, result, ARRAY_SIZE);
        double throughput_gflops = (double)ARRAY_SIZE / runtime;
        
        fprintf(csv, "%d,auto_vectorized_add,%lu,%lu,0,0,0,0,-1,-1,%.3f\n",
               run++, start_ts, runtime, throughput_gflops);
    }
    
    // Test 3: Explicit SSE
    printf("  SSE (128-bit)...\n");
    for (int iter = 0; iter < ITERATIONS; iter++) {
        uint64_t start_ts = get_time_ns();
        uint64_t runtime = add_sse(a, b, result, ARRAY_SIZE);
        double throughput_gflops = (double)ARRAY_SIZE / runtime;
        
        fprintf(csv, "%d,sse_add,%lu,%lu,0,0,0,0,-1,-1,%.3f\n",
               run++, start_ts, runtime, throughput_gflops);
    }
    
    // Test 4: AVX2
    printf("  AVX2 (256-bit)...\n");
    for (int iter = 0; iter < ITERATIONS; iter++) {
        uint64_t start_ts = get_time_ns();
        uint64_t runtime = add_avx2(a, b, result, ARRAY_SIZE);
        double throughput_gflops = (double)ARRAY_SIZE / runtime;
        
        fprintf(csv, "%d,avx2_add,%lu,%lu,0,0,0,0,-1,-1,%.3f\n",
               run++, start_ts, runtime, throughput_gflops);
    }
    
    // Test 5: Dot product comparison
    printf("Testing dot product...\n");
    
    for (int iter = 0; iter < 10; iter++) {
        uint64_t start = get_time_ns();
        float result_scalar = dot_product_scalar(a, b, ARRAY_SIZE);
        uint64_t runtime_scalar = get_time_ns() - start;
        
        start = get_time_ns();
        float result_sse = dot_product_sse(a, b, ARRAY_SIZE);
        uint64_t runtime_sse = get_time_ns() - start;
        
        // Verify correctness
        float diff = result_scalar - result_sse;
        if (diff > 0.01f || diff < -0.01f) {
            printf("Warning: Results differ (scalar=%.2f, sse=%.2f)\n", 
                   result_scalar, result_sse);
        }
        
        fprintf(csv, "%d,dot_product_scalar,%lu,%lu,0,0,0,0,-1,-1,%.3f\n",
               run++, start, runtime_scalar, (double)ARRAY_SIZE / runtime_scalar);
        
        fprintf(csv, "%d,dot_product_sse,%lu,%lu,0,0,0,0,-1,-1,%.3f\n",
               run++, start, runtime_sse, (double)ARRAY_SIZE / runtime_sse);
    }
    
    free(a);
    free(b);
    free(result);
}

int main(void) {
    FILE *csv = fopen("data/simd_performance.csv", "w");
    if (!csv) {
        perror("fopen");
        return 1;
    }
    
    fprintf(csv, "run,workload_type,timestamp_ns,runtime_ns,"
                 "voluntary_ctxt_switches,nonvoluntary_ctxt_switches,"
                 "minor_page_faults,major_page_faults,start_cpu,end_cpu,"
                 "throughput_gflops\n");
    
    printf("SIMD vs Scalar Performance Benchmark\n");
    printf("====================================\n\n");
    printf("Array size: %d elements (%.1f MB)\n", 
           ARRAY_SIZE, (ARRAY_SIZE * sizeof(float)) / (1024.0 * 1024.0));
    printf("Iterations: %d\n\n", ITERATIONS);
    
    run_experiment(csv);
    
    fclose(csv);
    
    printf("\nResults saved to data/simd_performance.csv\n");
    printf("\nExpected patterns:\n");
    printf("  Scalar: Baseline throughput\n");
    printf("  SSE: ~4x faster (4 floats at once)\n");
    printf("  AVX2: ~8x faster (8 floats at once)\n");
    printf("  Auto-vectorized: Depends on compiler optimization\n");
    printf("\nNote: Requires CPU with SSE/AVX2 support\n");
    
    return 0;
}
