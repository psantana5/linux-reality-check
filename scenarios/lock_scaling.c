/*
 * lock_scaling.c - Lock contention scaling experiment
 *
 * Hypothesis:
 *   Lock contention overhead scales with thread count.
 *   Spinlocks: good for low contention, terrible for high contention.
 *   Mutexes: better for high contention (scheduler helps).
 *   Atomics: best scalability (lock-free).
 *
 * Method:
 *   Run same workload with 1, 2, 4, 8 threads:
 *   1. Spinlock contention
 *   2. Mutex contention
 *   3. Atomic operations
 *   
 *   Measure total runtime and throughput.
 *
 * Variables:
 *   - Thread count (1, 2, 4, 8)
 *   - Lock type (spinlock, mutex, atomic)
 *   - Work per thread (fixed)
 *
 * Expected outcome:
 *   - 1 thread: All similar (no contention)
 *   - 2-4 threads: Spinlock starts degrading
 *   - 8 threads: Spinlock terrible, mutex better, atomic best
 *   - Throughput: Atomic scales linearly, locks don't
 *
 * Limitations:
 *   - Synthetic workload (trivial critical section)
 *   - Does not test different contention patterns
 *   - CPU topology matters (SMT vs physical cores)
 *   - Does not measure fairness
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <pthread.h>

// Import from lock_contention.c
extern void lock_workload_init(void* work, int threads, int iterations);
extern void lock_workload_cleanup(void* work);
extern uint64_t run_lock_test(void* work, void* (*worker_func)(void*), int pin_threads);
extern void* spinlock_worker(void* arg);
extern void* mutex_worker(void* arg);
extern void* atomic_worker(void* arg);

// Use opaque pointer for lock_workload_t
typedef void* lock_workload_ptr;

#define ITERATIONS_PER_THREAD 1000000
#define RUNS 5

int main(void) {
    FILE *out = fopen("../data/lock_scaling.csv", "w");
    if (!out) {
        perror("fopen");
        return 1;
    }
    
    fprintf(out, "run,threads,lock_type,runtime_ns,ops_per_sec\n");
    
    printf("Running lock scaling experiment...\n");
    printf("Testing spinlock, mutex, and atomic operations.\n\n");
    
    int thread_counts[] = {1, 2, 4, 8};
    
    for (size_t t = 0; t < sizeof(thread_counts) / sizeof(thread_counts[0]); t++) {
        int threads = thread_counts[t];
        
        printf("Testing with %d thread(s)...\n", threads);
        
        for (int run = 0; run < RUNS; run++) {
            char work_buf[256];  // Opaque buffer for lock_workload_t
            
            // Spinlock test
            lock_workload_init(work_buf, threads, ITERATIONS_PER_THREAD);
            uint64_t spinlock_ns = run_lock_test(work_buf, spinlock_worker, 0);
            uint64_t total_ops = (uint64_t)threads * ITERATIONS_PER_THREAD;
            double ops_per_sec = (double)total_ops / (spinlock_ns / 1e9);
            fprintf(out, "%d,%d,spinlock,%lu,%.0f\n", run, threads, spinlock_ns, ops_per_sec);
            lock_workload_cleanup(work_buf);
            
            // Mutex test
            lock_workload_init(work_buf, threads, ITERATIONS_PER_THREAD);
            uint64_t mutex_ns = run_lock_test(work_buf, mutex_worker, 0);
            ops_per_sec = (double)total_ops / (mutex_ns / 1e9);
            fprintf(out, "%d,%d,mutex,%lu,%.0f\n", run, threads, mutex_ns, ops_per_sec);
            lock_workload_cleanup(work_buf);
            
            // Atomic test
            lock_workload_init(work_buf, threads, ITERATIONS_PER_THREAD);
            uint64_t atomic_ns = run_lock_test(work_buf, atomic_worker, 0);
            ops_per_sec = (double)total_ops / (atomic_ns / 1e9);
            fprintf(out, "%d,%d,atomic,%lu,%.0f\n", run, threads, atomic_ns, ops_per_sec);
            lock_workload_cleanup(work_buf);
        }
    }
    
    fclose(out);
    
    printf("\nResults saved to ../data/lock_scaling.csv\n");
    printf("\nAnalyze with:\n");
    printf("  python3 ../analyze/parse.py ../data/lock_scaling.csv\n");
    printf("  python3 ../analyze/classify.py ../data/lock_scaling.csv\n");
    printf("\nExpected results:\n");
    printf("  1 thread:  All similar (~1s)\n");
    printf("  2 threads: Spinlock starts degrading\n");
    printf("  4 threads: Mutex catches up\n");
    printf("  8 threads: Atomic best, spinlock worst\n");
    
    return 0;
}
