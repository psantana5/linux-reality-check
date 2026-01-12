/*
 * Atomic Operations Cost Benchmark
 * 
 * Measures the cost of atomic operations vs regular operations.
 * Atomic operations guarantee thread-safe access but have overhead.
 *
 * Expected Results:
 * - Regular increment: ~0.3-0.5 ns
 * - Atomic increment (single thread): ~5-10 ns (20x slower)
 * - Atomic increment (contended): ~50-200 ns (cache line bouncing)
 * - Compare-and-swap: ~10-20 ns
 *
 * What This Tests:
 * - Atomic operation overhead
 * - Lock-free algorithm costs
 * - Cache coherency protocol impact
 * - Contention effects
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdatomic.h>
#include <pthread.h>
#include <time.h>
#include <sched.h>
#include <unistd.h>

#define ITERATIONS 10000000
#define MAX_THREADS 8

static inline uint64_t get_time_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1000000000ULL + ts.tv_nsec;
}

typedef struct {
    int thread_id;
    uint64_t iterations;
    _Atomic uint64_t *shared_counter;
    uint64_t *local_counter;
    uint64_t runtime_ns;
} thread_arg_t;

// Test 1: Regular (non-atomic) increment
uint64_t test_regular_increment(void) {
    uint64_t counter = 0;
    uint64_t start = get_time_ns();
    
    for (uint64_t i = 0; i < ITERATIONS; i++) {
        counter++;
    }
    
    uint64_t end = get_time_ns();
    
    // Prevent optimization
    if (counter != ITERATIONS) {
        printf("Error: counter = %lu\n", counter);
    }
    
    return end - start;
}

// Test 2: Atomic increment (single thread)
uint64_t test_atomic_increment(void) {
    _Atomic uint64_t counter = 0;
    uint64_t start = get_time_ns();
    
    for (uint64_t i = 0; i < ITERATIONS; i++) {
        atomic_fetch_add_explicit(&counter, 1, memory_order_relaxed);
    }
    
    uint64_t end = get_time_ns();
    
    if (counter != ITERATIONS) {
        printf("Error: counter = %lu\n", counter);
    }
    
    return end - start;
}

// Test 3: Compare-and-swap
uint64_t test_compare_and_swap(void) {
    _Atomic uint64_t counter = 0;
    uint64_t start = get_time_ns();
    
    for (uint64_t i = 0; i < ITERATIONS; i++) {
        uint64_t expected = i;
        uint64_t desired = i + 1;
        atomic_compare_exchange_strong_explicit(&counter, &expected, desired,
                                               memory_order_relaxed,
                                               memory_order_relaxed);
    }
    
    uint64_t end = get_time_ns();
    
    if (counter != ITERATIONS) {
        printf("Error: counter = %lu\n", counter);
    }
    
    return end - start;
}

// Worker thread for contention test
void* worker_atomic_contention(void *arg) {
    thread_arg_t *params = (thread_arg_t*)arg;
    
    // Pin to specific CPU
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(params->thread_id, &cpuset);
    pthread_setaffinity_np(pthread_self(), sizeof(cpu_set_t), &cpuset);
    
    uint64_t start = get_time_ns();
    
    for (uint64_t i = 0; i < params->iterations; i++) {
        atomic_fetch_add_explicit(params->shared_counter, 1, memory_order_relaxed);
    }
    
    params->runtime_ns = get_time_ns() - start;
    
    return NULL;
}

// Worker thread for local (no contention) test
void* worker_local_increment(void *arg) {
    thread_arg_t *params = (thread_arg_t*)arg;
    
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(params->thread_id, &cpuset);
    pthread_setaffinity_np(pthread_self(), sizeof(cpu_set_t), &cpuset);
    
    uint64_t start = get_time_ns();
    
    for (uint64_t i = 0; i < params->iterations; i++) {
        (*params->local_counter)++;
    }
    
    params->runtime_ns = get_time_ns() - start;
    
    return NULL;
}

void run_contention_test(FILE *csv, int num_threads, int *run_number) {
    pthread_t threads[MAX_THREADS];
    thread_arg_t args[MAX_THREADS];
    _Atomic uint64_t shared_counter = 0;
    uint64_t local_counters[MAX_THREADS] = {0};
    
    // Test with contention (shared atomic)
    uint64_t start_ts = get_time_ns();
    
    for (int i = 0; i < num_threads; i++) {
        args[i].thread_id = i;
        args[i].iterations = ITERATIONS / num_threads;
        args[i].shared_counter = &shared_counter;
        pthread_create(&threads[i], NULL, worker_atomic_contention, &args[i]);
    }
    
    for (int i = 0; i < num_threads; i++) {
        pthread_join(threads[i], NULL);
    }
    
    uint64_t max_runtime = 0;
    for (int i = 0; i < num_threads; i++) {
        if (args[i].runtime_ns > max_runtime) {
            max_runtime = args[i].runtime_ns;
        }
    }
    
    double ns_per_op = (double)max_runtime / (ITERATIONS / num_threads);
    
    fprintf(csv, "%d,atomic_contended_%dthreads,%lu,%lu,0,0,0,0,-1,-1,%.2f\n",
           (*run_number)++, num_threads, start_ts, max_runtime, ns_per_op);
    
    // Test without contention (local counters)
    start_ts = get_time_ns();
    
    for (int i = 0; i < num_threads; i++) {
        args[i].thread_id = i;
        args[i].iterations = ITERATIONS / num_threads;
        args[i].local_counter = &local_counters[i];
        pthread_create(&threads[i], NULL, worker_local_increment, &args[i]);
    }
    
    for (int i = 0; i < num_threads; i++) {
        pthread_join(threads[i], NULL);
    }
    
    max_runtime = 0;
    for (int i = 0; i < num_threads; i++) {
        if (args[i].runtime_ns > max_runtime) {
            max_runtime = args[i].runtime_ns;
        }
    }
    
    ns_per_op = (double)max_runtime / (ITERATIONS / num_threads);
    
    fprintf(csv, "%d,local_no_contention_%dthreads,%lu,%lu,0,0,0,0,-1,-1,%.2f\n",
           (*run_number)++, num_threads, start_ts, max_runtime, ns_per_op);
}

void run_experiment(FILE *csv) {
    int run = 0;
    
    // Single-threaded tests
    printf("Single-threaded tests...\n");
    
    for (int i = 0; i < 5; i++) {
        uint64_t start_ts = get_time_ns();
        uint64_t runtime = test_regular_increment();
        double ns_per_op = (double)runtime / ITERATIONS;
        
        fprintf(csv, "%d,regular_increment,%lu,%lu,0,0,0,0,-1,-1,%.2f\n",
               run++, start_ts, runtime, ns_per_op);
    }
    
    for (int i = 0; i < 5; i++) {
        uint64_t start_ts = get_time_ns();
        uint64_t runtime = test_atomic_increment();
        double ns_per_op = (double)runtime / ITERATIONS;
        
        fprintf(csv, "%d,atomic_relaxed,%lu,%lu,0,0,0,0,-1,-1,%.2f\n",
               run++, start_ts, runtime, ns_per_op);
    }
    
    for (int i = 0; i < 5; i++) {
        uint64_t start_ts = get_time_ns();
        uint64_t runtime = test_compare_and_swap();
        double ns_per_op = (double)runtime / ITERATIONS;
        
        fprintf(csv, "%d,compare_and_swap,%lu,%lu,0,0,0,0,-1,-1,%.2f\n",
               run++, start_ts, runtime, ns_per_op);
    }
    
    // Multi-threaded contention tests
    int thread_counts[] = {2, 4, 8};
    for (int i = 0; i < 3; i++) {
        int num_threads = thread_counts[i];
        
        if (num_threads > sysconf(_SC_NPROCESSORS_ONLN)) {
            continue;
        }
        
        printf("Testing contention with %d threads...\n", num_threads);
        run_contention_test(csv, num_threads, &run);
    }
}

int main(void) {
    FILE *csv = fopen("data/atomic_operations.csv", "w");
    if (!csv) {
        perror("fopen");
        return 1;
    }
    
    fprintf(csv, "run,workload_type,timestamp_ns,runtime_ns,"
                 "voluntary_ctxt_switches,nonvoluntary_ctxt_switches,"
                 "minor_page_faults,major_page_faults,start_cpu,end_cpu,"
                 "ns_per_operation\n");
    
    printf("Atomic Operations Cost Benchmark\n");
    printf("=================================\n\n");
    printf("Iterations: %d\n", ITERATIONS);
    printf("Available CPUs: %ld\n\n", sysconf(_SC_NPROCESSORS_ONLN));
    
    run_experiment(csv);
    
    fclose(csv);
    
    printf("\nResults saved to data/atomic_operations.csv\n");
    printf("\nExpected patterns:\n");
    printf("  Regular: ~0.3-0.5 ns (baseline)\n");
    printf("  Atomic (no contention): ~5-10 ns (20x overhead)\n");
    printf("  Atomic (contended): ~50-200 ns (cache coherency)\n");
    printf("  CAS: ~10-20 ns (more complex than fetch_add)\n");
    
    return 0;
}
