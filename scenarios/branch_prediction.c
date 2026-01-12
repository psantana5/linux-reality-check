/*
 * Branch Prediction Impact Benchmark
 * 
 * Measures the cost of branch mispredictions on modern CPUs.
 * Modern CPUs use branch predictors to speculatively execute code.
 * Mispredictions cause pipeline flushes (10-20 cycle penalty).
 *
 * Expected Results:
 * - Predictable branches: ~1-2 cycles per iteration
 * - Unpredictable branches: ~10-20 cycles per iteration
 * - Sorted data: Perfect prediction
 * - Random data: 50% misprediction rate
 *
 * What This Tests:
 * - Branch predictor effectiveness
 * - Cost of pipeline flushes
 * - Data-dependent control flow overhead
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>

#define ARRAY_SIZE 1000000
#define ITERATIONS 10

static inline uint64_t get_time_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1000000000ULL + ts.tv_nsec;
}

// Test with predictable branches
uint64_t test_predictable(int *array, size_t size) {
    uint64_t sum = 0;
    uint64_t start = get_time_ns();
    
    for (size_t i = 0; i < size; i++) {
        if (array[i] < 128) {  // Predictable (all sorted)
            sum += array[i];
        } else {
            sum -= array[i];
        }
    }
    
    uint64_t end = get_time_ns();
    
    // Prevent optimization
    if (sum == 0xDEADBEEF) printf("!");
    
    return end - start;
}

// Test with unpredictable branches
uint64_t test_unpredictable(int *array, size_t size) {
    uint64_t sum = 0;
    uint64_t start = get_time_ns();
    
    for (size_t i = 0; i < size; i++) {
        if (array[i] < 128) {  // Unpredictable (random)
            sum += array[i];
        } else {
            sum -= array[i];
        }
    }
    
    uint64_t end = get_time_ns();
    
    if (sum == 0xDEADBEEF) printf("!");
    
    return end - start;
}

// Test without branches (branchless)
uint64_t test_branchless(int *array, size_t size) {
    uint64_t sum = 0;
    uint64_t start = get_time_ns();
    
    for (size_t i = 0; i < size; i++) {
        // Branchless: (array[i] < 128) ? add : subtract
        int mask = -((array[i] < 128));  // All 1s or all 0s
        sum += (array[i] & mask);
        sum -= (array[i] & ~mask);
    }
    
    uint64_t end = get_time_ns();
    
    if (sum == 0xDEADBEEF) printf("!");
    
    return end - start;
}

int compare_int(const void *a, const void *b) {
    return (*(int*)a - *(int*)b);
}

void run_experiment(FILE *csv) {
    int *array = malloc(ARRAY_SIZE * sizeof(int));
    if (!array) {
        perror("malloc");
        return;
    }
    
    int run = 0;
    
    // Test 1: Sorted array (predictable branches)
    printf("Test 1: Sorted array (predictable)...\n");
    for (size_t i = 0; i < ARRAY_SIZE; i++) {
        array[i] = i % 256;
    }
    qsort(array, ARRAY_SIZE, sizeof(int), compare_int);
    
    for (int iter = 0; iter < ITERATIONS; iter++) {
        uint64_t start_ts = get_time_ns();
        uint64_t runtime = test_predictable(array, ARRAY_SIZE);
        double ns_per_elem = (double)runtime / ARRAY_SIZE;
        
        fprintf(csv, "%d,sorted_predictable,%lu,%lu,0,0,0,0,-1,-1,%.2f\n",
               run++, start_ts, runtime, ns_per_elem);
    }
    
    // Test 2: Random array (unpredictable branches)
    printf("Test 2: Random array (unpredictable)...\n");
    srand(12345);
    for (size_t i = 0; i < ARRAY_SIZE; i++) {
        array[i] = rand() % 256;
    }
    
    for (int iter = 0; iter < ITERATIONS; iter++) {
        uint64_t start_ts = get_time_ns();
        uint64_t runtime = test_unpredictable(array, ARRAY_SIZE);
        double ns_per_elem = (double)runtime / ARRAY_SIZE;
        
        fprintf(csv, "%d,random_unpredictable,%lu,%lu,0,0,0,0,-1,-1,%.2f\n",
               run++, start_ts, runtime, ns_per_elem);
    }
    
    // Test 3: Random array with branchless code
    printf("Test 3: Random array (branchless)...\n");
    for (int iter = 0; iter < ITERATIONS; iter++) {
        uint64_t start_ts = get_time_ns();
        uint64_t runtime = test_branchless(array, ARRAY_SIZE);
        double ns_per_elem = (double)runtime / ARRAY_SIZE;
        
        fprintf(csv, "%d,random_branchless,%lu,%lu,0,0,0,0,-1,-1,%.2f\n",
               run++, start_ts, runtime, ns_per_elem);
    }
    
    // Test 4: Sorted array with branchless code (for comparison)
    printf("Test 4: Sorted array (branchless)...\n");
    qsort(array, ARRAY_SIZE, sizeof(int), compare_int);
    
    for (int iter = 0; iter < ITERATIONS; iter++) {
        uint64_t start_ts = get_time_ns();
        uint64_t runtime = test_branchless(array, ARRAY_SIZE);
        double ns_per_elem = (double)runtime / ARRAY_SIZE;
        
        fprintf(csv, "%d,sorted_branchless,%lu,%lu,0,0,0,0,-1,-1,%.2f\n",
               run++, start_ts, runtime, ns_per_elem);
    }
    
    free(array);
}

int main(void) {
    FILE *csv = fopen("data/branch_prediction.csv", "w");
    if (!csv) {
        perror("fopen");
        return 1;
    }
    
    fprintf(csv, "run,workload_type,timestamp_ns,runtime_ns,"
                 "voluntary_ctxt_switches,nonvoluntary_ctxt_switches,"
                 "minor_page_faults,major_page_faults,start_cpu,end_cpu,"
                 "ns_per_element\n");
    
    printf("Branch Prediction Impact Benchmark\n");
    printf("===================================\n\n");
    printf("Array size: %d elements\n", ARRAY_SIZE);
    printf("Iterations: %d\n\n", ITERATIONS);
    
    run_experiment(csv);
    
    fclose(csv);
    
    printf("\nResults saved to data/branch_prediction.csv\n");
    printf("\nExpected patterns:\n");
    printf("  Sorted + branches: ~1-2 ns/element (perfect prediction)\n");
    printf("  Random + branches: ~10-20 ns/element (50%% misprediction)\n");
    printf("  Branchless: ~3-5 ns/element (no mispredictions, more instructions)\n");
    printf("\nLesson: For unpredictable data, branchless code can be faster!\n");
    
    return 0;
}
