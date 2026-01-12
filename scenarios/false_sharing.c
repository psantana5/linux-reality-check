/*
 * False Sharing Detection Benchmark
 * 
 * Demonstrates the performance impact of false sharing - when threads access
 * different variables that happen to share the same cache line.
 *
 * Expected Results:
 * - No sharing: ~100-200 cycles per operation
 * - False sharing: ~1000-2000 cycles per operation (10-20x slower!)
 * - Padded structures: Back to no-sharing performance
 *
 * What This Tests:
 * - Cache line contention (typically 64 bytes)
 * - Multi-core scaling problems
 * - Importance of data structure layout
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <pthread.h>
#include <time.h>
#include <sched.h>
#include <unistd.h>

#define CACHE_LINE_SIZE 64
#define ITERATIONS 10000000
#define MAX_THREADS 8

// Shared structure - false sharing
typedef struct {
    volatile uint64_t counter[MAX_THREADS];
} shared_counters_t;

// Padded structure - no false sharing
typedef struct {
    volatile uint64_t counter;
    char padding[CACHE_LINE_SIZE - sizeof(uint64_t)];
} __attribute__((aligned(CACHE_LINE_SIZE))) padded_counter_t;

typedef struct {
    int thread_id;
    int num_threads;
    uint64_t iterations;
    void *counters;
    int use_padding;
    uint64_t runtime_ns;
} thread_arg_t;

static inline uint64_t get_time_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1000000000ULL + ts.tv_nsec;
}

void* worker_thread(void *arg) {
    thread_arg_t *params = (thread_arg_t*)arg;
    
    // Pin to specific CPU to ensure different cores
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(params->thread_id, &cpuset);
    pthread_setaffinity_np(pthread_self(), sizeof(cpu_set_t), &cpuset);
    
    uint64_t start = get_time_ns();
    
    if (params->use_padding) {
        // Padded - no false sharing
        padded_counter_t *counters = (padded_counter_t*)params->counters;
        for (uint64_t i = 0; i < params->iterations; i++) {
            counters[params->thread_id].counter++;
        }
    } else {
        // Not padded - false sharing
        shared_counters_t *counters = (shared_counters_t*)params->counters;
        for (uint64_t i = 0; i < params->iterations; i++) {
            counters->counter[params->thread_id]++;
        }
    }
    
    params->runtime_ns = get_time_ns() - start;
    
    return NULL;
}

void run_test(FILE *csv, int num_threads, int use_padding, int run_number) {
    pthread_t threads[MAX_THREADS];
    thread_arg_t args[MAX_THREADS];
    
    // Allocate counter structures
    void *counters;
    if (use_padding) {
        counters = aligned_alloc(CACHE_LINE_SIZE, 
                                sizeof(padded_counter_t) * MAX_THREADS);
        memset(counters, 0, sizeof(padded_counter_t) * MAX_THREADS);
    } else {
        counters = calloc(1, sizeof(shared_counters_t));
    }
    
    if (!counters) {
        perror("allocation");
        return;
    }
    
    // Create threads
    uint64_t start_ts = get_time_ns();
    
    for (int i = 0; i < num_threads; i++) {
        args[i].thread_id = i;
        args[i].num_threads = num_threads;
        args[i].iterations = ITERATIONS;
        args[i].counters = counters;
        args[i].use_padding = use_padding;
        pthread_create(&threads[i], NULL, worker_thread, &args[i]);
    }
    
    // Wait for completion
    for (int i = 0; i < num_threads; i++) {
        pthread_join(threads[i], NULL);
    }
    
    // Calculate statistics
    uint64_t max_runtime = 0;
    uint64_t total_runtime = 0;
    
    for (int i = 0; i < num_threads; i++) {
        if (args[i].runtime_ns > max_runtime) {
            max_runtime = args[i].runtime_ns;
        }
        total_runtime += args[i].runtime_ns;
    }
    
    uint64_t avg_runtime = total_runtime / num_threads;
    double ns_per_op = (double)avg_runtime / ITERATIONS;
    
    const char *type = use_padding ? "padded" : "false_sharing";
    
    fprintf(csv, "%d,%s_%dthreads,%lu,%lu,0,0,0,0,-1,-1,%.2f,%lu\n",
           run_number,
           type,
           num_threads,
           start_ts,
           max_runtime,
           ns_per_op,
           max_runtime);
    
    free(counters);
}

void run_experiment(FILE *csv) {
    int thread_counts[] = {1, 2, 4, 8};
    int num_counts = sizeof(thread_counts) / sizeof(thread_counts[0]);
    int run = 0;
    
    printf("Testing false sharing effects...\n\n");
    
    for (int i = 0; i < num_counts; i++) {
        int num_threads = thread_counts[i];
        
        if (num_threads > sysconf(_SC_NPROCESSORS_ONLN)) {
            printf("Skipping %d threads (only %ld CPUs available)\n",
                   num_threads, sysconf(_SC_NPROCESSORS_ONLN));
            continue;
        }
        
        printf("Testing with %d thread(s)...\n", num_threads);
        
        // Test without padding (false sharing)
        run_test(csv, num_threads, 0, run++);
        
        // Test with padding (no false sharing)
        run_test(csv, num_threads, 1, run++);
    }
}

int main(void) {
    FILE *csv = fopen("data/false_sharing.csv", "w");
    if (!csv) {
        perror("fopen");
        return 1;
    }
    
    fprintf(csv, "run,workload_type,timestamp_ns,runtime_ns,"
                 "voluntary_ctxt_switches,nonvoluntary_ctxt_switches,"
                 "minor_page_faults,major_page_faults,start_cpu,end_cpu,"
                 "ns_per_op,max_thread_runtime\n");
    
    printf("False Sharing Detection Benchmark\n");
    printf("==================================\n\n");
    printf("Cache line size: %d bytes\n", CACHE_LINE_SIZE);
    printf("Iterations per thread: %d\n", ITERATIONS);
    printf("Available CPUs: %ld\n\n", sysconf(_SC_NPROCESSORS_ONLN));
    
    run_experiment(csv);
    
    fclose(csv);
    
    printf("\nResults saved to data/false_sharing.csv\n");
    printf("\nExpected patterns:\n");
    printf("  1 thread: No difference (no contention)\n");
    printf("  2+ threads with false sharing: 10-20x slower\n");
    printf("  2+ threads with padding: Near-linear scaling\n");
    printf("\nLesson: Always pad per-thread data to cache line boundaries!\n");
    
    return 0;
}
