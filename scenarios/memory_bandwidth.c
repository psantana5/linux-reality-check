/*
 * Memory Bandwidth Saturation Benchmark
 * 
 * Measures memory subsystem bandwidth limits. Tests sequential and
 * random access patterns with different operation sizes to find
 * the saturation point where adding more threads doesn't increase
 * total bandwidth.
 *
 * Expected Results:
 * - Single thread: 10-20 GB/s (L3/memory limited)
 * - Multiple threads: Linear scaling until bandwidth saturates
 * - Saturation point: ~50-100 GB/s (DDR4), ~200+ GB/s (DDR5)
 * - Random access: Much lower bandwidth due to cache misses
 *
 * What This Tests:
 * - Memory bandwidth limits
 * - Multi-channel memory scaling
 * - Sequential vs random access
 * - Copy, read, write bandwidth
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <pthread.h>
#include <sched.h>
#include <unistd.h>

#define BUFFER_SIZE (64 * 1024 * 1024)  // 64 MB per thread
#define ITERATIONS 5
#define MAX_THREADS 8

typedef struct {
    int thread_id;
    char *buffer;
    size_t size;
    uint64_t bytes_processed;
    uint64_t runtime_ns;
} thread_arg_t;

static inline uint64_t get_time_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1000000000ULL + ts.tv_nsec;
}

// Sequential read benchmark
void* sequential_read_thread(void *arg) {
    thread_arg_t *params = (thread_arg_t*)arg;
    
    // Pin to CPU
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(params->thread_id, &cpuset);
    pthread_setaffinity_np(pthread_self(), sizeof(cpu_set_t), &cpuset);
    
    uint64_t sum = 0;
    uint64_t start = get_time_ns();
    
    // Read entire buffer multiple times
    for (int iter = 0; iter < 10; iter++) {
        for (size_t i = 0; i < params->size; i += 64) {
            sum += params->buffer[i];
        }
    }
    
    params->runtime_ns = get_time_ns() - start;
    params->bytes_processed = params->size * 10;
    
    // Prevent optimization
    if (sum == 0xDEADBEEF) printf("!");
    
    return NULL;
}

// Sequential write benchmark
void* sequential_write_thread(void *arg) {
    thread_arg_t *params = (thread_arg_t*)arg;
    
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(params->thread_id, &cpuset);
    pthread_setaffinity_np(pthread_self(), sizeof(cpu_set_t), &cpuset);
    
    uint64_t start = get_time_ns();
    
    // Write entire buffer multiple times
    for (int iter = 0; iter < 10; iter++) {
        memset(params->buffer, 0xAA, params->size);
    }
    
    params->runtime_ns = get_time_ns() - start;
    params->bytes_processed = params->size * 10;
    
    return NULL;
}

// Sequential copy benchmark (read + write)
void* sequential_copy_thread(void *arg) {
    thread_arg_t *params = (thread_arg_t*)arg;
    
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(params->thread_id, &cpuset);
    pthread_setaffinity_np(pthread_self(), sizeof(cpu_set_t), &cpuset);
    
    char *temp = malloc(params->size);
    if (!temp) return NULL;
    
    uint64_t start = get_time_ns();
    
    // Copy buffer multiple times
    for (int iter = 0; iter < 10; iter++) {
        memcpy(temp, params->buffer, params->size);
    }
    
    params->runtime_ns = get_time_ns() - start;
    params->bytes_processed = params->size * 10 * 2;  // Read + Write
    
    free(temp);
    return NULL;
}

// Random read benchmark
void* random_read_thread(void *arg) {
    thread_arg_t *params = (thread_arg_t*)arg;
    
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(params->thread_id, &cpuset);
    pthread_setaffinity_np(pthread_self(), sizeof(cpu_set_t), &cpuset);
    
    uint64_t sum = 0;
    uint64_t start = get_time_ns();
    
    // Random access pattern
    unsigned int seed = params->thread_id;
    for (int iter = 0; iter < 10000000; iter++) {
        size_t offset = rand_r(&seed) % params->size;
        sum += params->buffer[offset];
    }
    
    params->runtime_ns = get_time_ns() - start;
    params->bytes_processed = 10000000;  // Number of accesses
    
    if (sum == 0xDEADBEEF) printf("!");
    
    return NULL;
}

typedef void* (*thread_func_t)(void*);

double run_bandwidth_test(thread_func_t func, int num_threads, const char *test_name) {
    pthread_t threads[MAX_THREADS];
    thread_arg_t args[MAX_THREADS];
    
    // Allocate buffers
    for (int i = 0; i < num_threads; i++) {
        args[i].thread_id = i;
        args[i].buffer = malloc(BUFFER_SIZE);
        args[i].size = BUFFER_SIZE;
        
        if (!args[i].buffer) {
            perror("malloc");
            return 0.0;
        }
        
        // Initialize buffer
        memset(args[i].buffer, 0xAA, BUFFER_SIZE);
    }
    
    // Run threads
    for (int i = 0; i < num_threads; i++) {
        pthread_create(&threads[i], NULL, func, &args[i]);
    }
    
    // Wait for completion
    for (int i = 0; i < num_threads; i++) {
        pthread_join(threads[i], NULL);
    }
    
    // Calculate total bandwidth
    uint64_t total_bytes = 0;
    uint64_t max_runtime = 0;
    
    for (int i = 0; i < num_threads; i++) {
        total_bytes += args[i].bytes_processed;
        if (args[i].runtime_ns > max_runtime) {
            max_runtime = args[i].runtime_ns;
        }
    }
    
    // Free buffers
    for (int i = 0; i < num_threads; i++) {
        free(args[i].buffer);
    }
    
    // Bandwidth in GB/s
    double bandwidth_gbs = (double)total_bytes / max_runtime;
    
    return bandwidth_gbs;
}

void run_experiment(FILE *csv) {
    int thread_counts[] = {1, 2, 4, 8};
    int num_counts = sizeof(thread_counts) / sizeof(thread_counts[0]);
    int run = 0;
    
    struct {
        const char *name;
        thread_func_t func;
    } tests[] = {
        {"sequential_read", sequential_read_thread},
        {"sequential_write", sequential_write_thread},
        {"sequential_copy", sequential_copy_thread},
        {"random_read", random_read_thread},
    };
    
    int num_tests = sizeof(tests) / sizeof(tests[0]);
    
    for (int t = 0; t < num_tests; t++) {
        printf("Testing %s...\n", tests[t].name);
        
        for (int i = 0; i < num_counts; i++) {
            int num_threads = thread_counts[i];
            
            if (num_threads > sysconf(_SC_NPROCESSORS_ONLN)) {
                continue;
            }
            
            printf("  %d thread(s)...\n", num_threads);
            
            uint64_t start_ts = get_time_ns();
            double bandwidth = run_bandwidth_test(tests[t].func, num_threads, tests[t].name);
            uint64_t runtime = get_time_ns() - start_ts;
            
            fprintf(csv, "%d,%s_%dthreads,%lu,%lu,0,0,0,0,-1,-1,%.2f\n",
                   run++, tests[t].name, num_threads, start_ts, runtime, bandwidth);
        }
    }
}

int main(void) {
    FILE *csv = fopen("data/memory_bandwidth.csv", "w");
    if (!csv) {
        perror("fopen");
        return 1;
    }
    
    fprintf(csv, "run,workload_type,timestamp_ns,runtime_ns,"
                 "voluntary_ctxt_switches,nonvoluntary_ctxt_switches,"
                 "minor_page_faults,major_page_faults,start_cpu,end_cpu,"
                 "bandwidth_gbs\n");
    
    printf("Memory Bandwidth Saturation Benchmark\n");
    printf("=====================================\n\n");
    printf("Buffer size per thread: %d MB\n", BUFFER_SIZE / (1024 * 1024));
    printf("Available CPUs: %ld\n\n", sysconf(_SC_NPROCESSORS_ONLN));
    
    run_experiment(csv);
    
    fclose(csv);
    
    printf("\nResults saved to data/memory_bandwidth.csv\n");
    printf("\nExpected patterns:\n");
    printf("  Sequential read: 10-20 GB/s (single thread)\n");
    printf("  Multi-threaded: Linear scaling until saturation\n");
    printf("  Saturation point: System-dependent (50-200 GB/s)\n");
    printf("  Random access: Much lower (cache miss dominated)\n");
    
    return 0;
}
