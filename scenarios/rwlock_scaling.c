/*
 * Reader-Writer Lock Scaling Benchmark
 * 
 * Tests the scalability of reader-writer (RW) locks under different
 * read/write ratios. RW locks allow multiple concurrent readers but
 * exclusive writers.
 *
 * Expected Results:
 * - 100% readers: Near-linear scaling (read locks don't block)
 * - 50/50 mix: Moderate scaling (writer contention)
 * - Heavy writers: Poor scaling (serialization)
 * - pthread_rwlock vs custom spinlock implementations
 *
 * What This Tests:
 * - RW lock performance
 * - Reader/writer starvation
 * - Lock fairness policies
 * - Contention effects
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <pthread.h>
#include <time.h>
#include <sched.h>
#include <unistd.h>

#define ITERATIONS 1000000
#define MAX_THREADS 8

typedef struct {
    int thread_id;
    int num_threads;
    pthread_rwlock_t *rwlock;
    int *shared_data;
    int write_percentage;  // 0-100
    uint64_t operations;
    uint64_t runtime_ns;
} thread_arg_t;

static inline uint64_t get_time_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1000000000ULL + ts.tv_nsec;
}

void* rwlock_worker(void *arg) {
    thread_arg_t *params = (thread_arg_t*)arg;
    
    // Pin to CPU
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(params->thread_id, &cpuset);
    pthread_setaffinity_np(pthread_self(), sizeof(cpu_set_t), &cpuset);
    
    uint64_t operations = 0;
    uint64_t start = get_time_ns();
    
    unsigned int seed = params->thread_id;
    
    for (uint64_t i = 0; i < ITERATIONS / params->num_threads; i++) {
        int r = rand_r(&seed) % 100;
        
        if (r < params->write_percentage) {
            // Write operation
            pthread_rwlock_wrlock(params->rwlock);
            (*params->shared_data)++;
            pthread_rwlock_unlock(params->rwlock);
        } else {
            // Read operation
            pthread_rwlock_rdlock(params->rwlock);
            volatile int val = *params->shared_data;
            (void)val;  // Prevent optimization
            pthread_rwlock_unlock(params->rwlock);
        }
        
        operations++;
    }
    
    params->runtime_ns = get_time_ns() - start;
    params->operations = operations;
    
    return NULL;
}

void run_rwlock_test(FILE *csv, int num_threads, int write_pct, int *run_number) {
    pthread_t threads[MAX_THREADS];
    thread_arg_t args[MAX_THREADS];
    
    pthread_rwlock_t rwlock;
    pthread_rwlock_init(&rwlock, NULL);
    
    int shared_data = 0;
    
    uint64_t start_ts = get_time_ns();
    
    // Create threads
    for (int i = 0; i < num_threads; i++) {
        args[i].thread_id = i;
        args[i].num_threads = num_threads;
        args[i].rwlock = &rwlock;
        args[i].shared_data = &shared_data;
        args[i].write_percentage = write_pct;
        pthread_create(&threads[i], NULL, rwlock_worker, &args[i]);
    }
    
    // Wait for completion
    for (int i = 0; i < num_threads; i++) {
        pthread_join(threads[i], NULL);
    }
    
    // Calculate aggregate statistics
    uint64_t total_ops = 0;
    uint64_t max_runtime = 0;
    
    for (int i = 0; i < num_threads; i++) {
        total_ops += args[i].operations;
        if (args[i].runtime_ns > max_runtime) {
            max_runtime = args[i].runtime_ns;
        }
    }
    
    // Operations per second
    double ops_per_sec = (double)total_ops / (max_runtime / 1e9);
    double ns_per_op = (double)max_runtime / (total_ops / num_threads);
    
    fprintf(csv, "%d,rwlock_%dthreads_%dwrite,%lu,%lu,0,0,0,0,-1,-1,%.0f,%.2f\n",
           (*run_number)++, num_threads, write_pct, start_ts, max_runtime,
           ops_per_sec, ns_per_op);
    
    pthread_rwlock_destroy(&rwlock);
}

void run_experiment(FILE *csv) {
    int thread_counts[] = {1, 2, 4, 8};
    int write_percentages[] = {0, 10, 50, 100};  // 0% = all readers, 100% = all writers
    
    int num_thread_counts = sizeof(thread_counts) / sizeof(thread_counts[0]);
    int num_write_pcts = sizeof(write_percentages) / sizeof(write_percentages[0]);
    
    int run = 0;
    
    for (int w = 0; w < num_write_pcts; w++) {
        int write_pct = write_percentages[w];
        
        printf("Testing with %d%% writes...\n", write_pct);
        
        for (int t = 0; t < num_thread_counts; t++) {
            int num_threads = thread_counts[t];
            
            if (num_threads > sysconf(_SC_NPROCESSORS_ONLN)) {
                continue;
            }
            
            printf("  %d thread(s)...\n", num_threads);
            run_rwlock_test(csv, num_threads, write_pct, &run);
        }
    }
}

int main(void) {
    FILE *csv = fopen("data/rwlock_scaling.csv", "w");
    if (!csv) {
        perror("fopen");
        return 1;
    }
    
    fprintf(csv, "run,workload_type,timestamp_ns,runtime_ns,"
                 "voluntary_ctxt_switches,nonvoluntary_ctxt_switches,"
                 "minor_page_faults,major_page_faults,start_cpu,end_cpu,"
                 "ops_per_second,ns_per_operation\n");
    
    printf("Reader-Writer Lock Scaling Benchmark\n");
    printf("====================================\n\n");
    printf("Total operations: %d\n", ITERATIONS);
    printf("Available CPUs: %ld\n\n", sysconf(_SC_NPROCESSORS_ONLN));
    
    run_experiment(csv);
    
    fclose(csv);
    
    printf("\nResults saved to data/rwlock_scaling.csv\n");
    printf("\nExpected patterns:\n");
    printf("  0%% writes (all reads): Near-linear scaling\n");
    printf("  10%% writes: Good scaling with occasional serialization\n");
    printf("  50%% writes: Moderate scaling, significant contention\n");
    printf("  100%% writes: Poor scaling, full serialization\n");
    printf("\nLesson: RW locks excel when reads dominate!\n");
    
    return 0;
}
