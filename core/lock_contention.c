/*
 * lock_contention.c - Multi-threaded lock contention workload
 *
 * What it stresses:
 *   - Spinlock contention
 *   - Mutex contention
 *   - Atomic operations
 *   - Cache coherency protocol (MESI)
 *
 * What it deliberately avoids:
 *   - Complex computation inside critical section
 *   - I/O operations
 *   - Memory allocation in hot path
 *
 * Purpose:
 *   Measure lock overhead and contention effects.
 *   Compare spinlock vs mutex vs atomic operations.
 *   Demonstrate scalability bottlenecks.
 */

#define _GNU_SOURCE
#include <pthread.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sched.h>

typedef struct {
    pthread_spinlock_t spinlock;
    pthread_mutex_t mutex;
    volatile uint64_t atomic_counter;
    uint64_t shared_counter;
    int iterations_per_thread;
    int thread_count;
} lock_workload_t;

/*
 * Spinlock contention: all threads compete for spinlock.
 * High contention, busy-wait.
 */
void* spinlock_worker(void* arg) {
    lock_workload_t* work = (lock_workload_t*)arg;
    
    for (int i = 0; i < work->iterations_per_thread; i++) {
        pthread_spin_lock(&work->spinlock);
        work->shared_counter++;
        pthread_spin_unlock(&work->spinlock);
    }
    
    return NULL;
}

/*
 * Mutex contention: all threads compete for mutex.
 * High contention, sleep-wait (scheduler involved).
 */
void* mutex_worker(void* arg) {
    lock_workload_t* work = (lock_workload_t*)arg;
    
    for (int i = 0; i < work->iterations_per_thread; i++) {
        pthread_mutex_lock(&work->mutex);
        work->shared_counter++;
        pthread_mutex_unlock(&work->mutex);
    }
    
    return NULL;
}

/*
 * Atomic operations: lock-free with hardware support.
 * Compare-and-swap, no actual lock.
 */
void* atomic_worker(void* arg) {
    lock_workload_t* work = (lock_workload_t*)arg;
    
    for (int i = 0; i < work->iterations_per_thread; i++) {
        __atomic_add_fetch(&work->atomic_counter, 1, __ATOMIC_SEQ_CST);
    }
    
    return NULL;
}

/*
 * Run lock contention experiment.
 * Returns elapsed time in nanoseconds.
 */
uint64_t run_lock_test(lock_workload_t* work, 
                        void* (*worker_func)(void*),
                        int pin_threads) {
    pthread_t* threads = malloc(work->thread_count * sizeof(pthread_t));
    cpu_set_t cpuset;
    
    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC_RAW, &start);
    
    // Create threads
    for (int i = 0; i < work->thread_count; i++) {
        pthread_create(&threads[i], NULL, worker_func, work);
        
        // Optionally pin each thread to specific CPU
        if (pin_threads) {
            CPU_ZERO(&cpuset);
            CPU_SET(i % sysconf(_SC_NPROCESSORS_ONLN), &cpuset);
            pthread_setaffinity_np(threads[i], sizeof(cpu_set_t), &cpuset);
        }
    }
    
    // Wait for all threads
    for (int i = 0; i < work->thread_count; i++) {
        pthread_join(threads[i], NULL);
    }
    
    clock_gettime(CLOCK_MONOTONIC_RAW, &end);
    
    free(threads);
    
    uint64_t elapsed_ns = (end.tv_sec - start.tv_sec) * 1000000000ULL +
                          (end.tv_nsec - start.tv_nsec);
    
    return elapsed_ns;
}

/*
 * Initialize lock workload.
 */
void lock_workload_init(lock_workload_t* work, int threads, int iterations) {
    pthread_spin_init(&work->spinlock, PTHREAD_PROCESS_PRIVATE);
    pthread_mutex_init(&work->mutex, NULL);
    work->atomic_counter = 0;
    work->shared_counter = 0;
    work->thread_count = threads;
    work->iterations_per_thread = iterations;
}

/*
 * Cleanup lock workload.
 */
void lock_workload_cleanup(lock_workload_t* work) {
    pthread_spin_destroy(&work->spinlock);
    pthread_mutex_destroy(&work->mutex);
}
