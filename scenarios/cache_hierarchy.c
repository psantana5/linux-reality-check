/*
 * cache_hierarchy.c - Cache behavior experiment
 *
 * Hypothesis:
 *   Memory access patterns that fit in L1/L2/L3 cache show
 *   dramatically different performance characteristics than
 *   patterns that spill to main memory.
 *
 * Method:
 *   Sequential memory streaming across different buffer sizes:
 *   - 8 KB (fits in L1)
 *   - 128 KB (fits in L2)
 *   - 4 MB (fits in L3)
 *   - 64 MB (spills to main memory)
 *
 * Variables:
 *   - Buffer size (controlled)
 *   - Access pattern (sequential, fixed)
 *
 * Expected outcome:
 *   Runtime should increase non-linearly with buffer size:
 *   - L1: ~4 cycles/access
 *   - L2: ~12 cycles/access
 *   - L3: ~40 cycles/access
 *   - DRAM: ~200+ cycles/access
 *
 * Limitations:
 *   - Assumes cold cache at start
 *   - Hardware prefetcher may mask some effects
 *   - Does not measure cache associativity effects
 *   - CPU frequency scaling affects absolute numbers
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include "../core/metrics.h"

extern uint64_t memory_stream_read(const uint64_t *buffer, size_t size);
extern int pin_to_cpu(int cpu);

#define KB (1024ULL)
#define MB (1024ULL * KB)
#define RUNS 10

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
    FILE *out = fopen("../data/cache_hierarchy.csv", "w");
    
    if (!out) {
        perror("fopen");
        return 1;
    }
    
    pin_to_cpu(0);
    
    fprintf(out, "run,buffer_size,");
    metrics_print_csv_header(out);
    
    printf("Running cache hierarchy experiment...\n");
    printf("This will allocate up to 64 MB of memory.\n\n");
    
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
        
        for (int run = 0; run < RUNS; run++) {
            fprintf(out, "%d,%s,", run, name);
            metrics_init(&metrics);
            uint64_t result = memory_stream_read(buffer, size);
            metrics_finish(&metrics);
            metrics_print_csv(out, &metrics);
            
            (void)result;
        }
        
        free(buffer);
    }
    
    fclose(out);
    printf("\nResults saved to ../data/cache_hierarchy.csv\n");
    
    return 0;
}
