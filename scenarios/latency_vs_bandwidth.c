/*
 * latency_vs_bandwidth.c - Memory latency vs bandwidth experiment
 *
 * Hypothesis:
 *   Sequential memory access is bandwidth-bound (high throughput).
 *   Random memory access is latency-bound (dependent loads).
 *   Random access should be 10-50x slower at same buffer size.
 *
 * Method:
 *   Run both sequential and random access at multiple buffer sizes:
 *   - 8 KB (L1 cache)
 *   - 128 KB (L2 cache)
 *   - 4 MB (L3 cache)
 *   - 64 MB (DRAM)
 *
 * Variables:
 *   - Access pattern (sequential vs random)
 *   - Buffer size (controlled)
 *
 * Expected outcome:
 *   - Sequential: scales with buffer size (bandwidth-limited)
 *   - Random: much slower, less sensitive to size (latency-limited)
 *   - Random/Sequential ratio: 10-50x at DRAM sizes
 *
 * Limitations:
 *   - Hardware prefetcher helps sequential but not random
 *   - TLB effects at large sizes
 *   - Random uses pointer-chasing (worst case)
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include "../core/metrics.h"

extern uint64_t memory_stream_read(const uint64_t *buffer, size_t size);
extern uint64_t memory_random_chase(uint64_t *buffer, size_t size, uint64_t iterations);
extern int pin_to_cpu(int cpu);

#define KB (1024ULL)
#define MB (1024ULL * KB)
#define RUNS 10
#define RANDOM_ITERATIONS 100000ULL

static const size_t buffer_sizes[] = {
    8 * KB,      // L1
    128 * KB,    // L2
    4 * MB,      // L3
    64 * MB      // DRAM
};

static const char *size_names[] = {
    "8KB_L1",
    "128KB_L2",
    "4MB_L3",
    "64MB_DRAM"
};

int main(void) {
    workload_metrics_t metrics;
    FILE *out = fopen("../data/latency_vs_bandwidth.csv", "w");
    
    if (!out) {
        perror("fopen");
        return 1;
    }
    
    pin_to_cpu(0);
    
    fprintf(out, "run,buffer_size,access_pattern,");
    metrics_print_csv_header(out);
    
    printf("Running latency vs bandwidth experiment...\n");
    printf("This compares sequential (bandwidth) vs random (latency) access.\n\n");
    
    for (size_t i = 0; i < sizeof(buffer_sizes) / sizeof(buffer_sizes[0]); i++) {
        size_t size = buffer_sizes[i];
        const char *name = size_names[i];
        
        uint64_t *buffer = malloc(size);
        if (!buffer) {
            fprintf(stderr, "Failed to allocate %zu bytes\n", size);
            continue;
        }
        
        memset(buffer, 0x42, size);
        
        printf("Testing %s (%zu bytes)...\n", name, size);
        
        // Sequential access (bandwidth-bound)
        printf("  Sequential access...\n");
        for (int run = 0; run < RUNS; run++) {
            fprintf(out, "%d,%s,sequential,", run, name);
            metrics_init(&metrics);
            uint64_t result = memory_stream_read(buffer, size);
            metrics_finish(&metrics);
            metrics_print_csv(out, &metrics);
            
            (void)result;
        }
        
        // Random access (latency-bound)
        printf("  Random access (pointer-chasing)...\n");
        for (int run = 0; run < RUNS; run++) {
            fprintf(out, "%d,%s,random,", run, name);
            metrics_init(&metrics);
            uint64_t result = memory_random_chase(buffer, size, RANDOM_ITERATIONS);
            metrics_finish(&metrics);
            metrics_print_csv(out, &metrics);
            
            (void)result;
        }
        
        free(buffer);
        printf("\n");
    }
    
    fclose(out);
    printf("Results saved to ../data/latency_vs_bandwidth.csv\n");
    printf("\nAnalyze with:\n");
    printf("  python3 ../analyze/parse.py ../data/latency_vs_bandwidth.csv\n");
    printf("  python3 ../analyze/classify.py ../data/latency_vs_bandwidth.csv\n");
    
    return 0;
}
