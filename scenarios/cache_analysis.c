/*
 * cache_analysis.c - Cache behavior with hardware counters
 *
 * Hypothesis:
 *   Direct cache miss measurement reveals true bottlenecks
 *   better than runtime inference alone.
 *
 * Method:
 *   Same workloads as cache_hierarchy but with perf counters:
 *   - L1/L2/L3/DRAM buffer sizes
 *   - Measure: cache misses, IPC, branch prediction
 *
 * Expected outcome:
 *   - L1: High IPC (~3-4), low cache misses
 *   - L2: Medium IPC (~2), moderate L1 misses
 *   - L3: Low IPC (~1), high L1 misses, moderate LLC misses
 *   - DRAM: Very low IPC (<1), high LLC misses
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include "../core/metrics.h"
#include "../core/perf_counters.h"

extern uint64_t memory_stream_read(const uint64_t *buffer, size_t size);
extern int pin_to_cpu(int cpu);

#define KB (1024ULL)
#define MB (1024ULL * KB)
#define RUNS 10

static const size_t buffer_sizes[] = {
    8 * KB,
    128 * KB,
    4 * MB,
    64 * MB
};

static const char *size_names[] = {
    "8KB_L1",
    "128KB_L2",
    "4MB_L3",
    "64MB_DRAM"
};

int main(void) {
    workload_metrics_t metrics;
    perf_counters_t perf;
    
    FILE *out = fopen("../data/cache_analysis.csv", "w");
    if (!out) {
        perror("fopen");
        return 1;
    }
    
    // Initialize perf counters
    if (perf_counters_init(&perf) < 0) {
        fprintf(stderr, "Warning: perf counters not available\n");
        fprintf(stderr, "         Need: CAP_PERFMON or /proc/sys/kernel/perf_event_paranoid <= 2\n");
        fprintf(stderr, "         Continuing without hardware counters...\n");
        
        // Continue without perf - still useful data
        fprintf(out, "run,buffer_size,");
        metrics_print_csv_header(out);
    } else {
        fprintf(out, "run,buffer_size,");
        metrics_print_csv_header(out);
        fprintf(out, ",");
        perf_counters_print_csv_header(out);
    }
    
    pin_to_cpu(0);
    
    printf("Running cache analysis with hardware counters...\n\n");
    
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
            
            if (perf.fd_instructions >= 0) {
                perf_counters_start(&perf);
            }
            
            uint64_t result = memory_stream_read(buffer, size);
            
            if (perf.fd_instructions >= 0) {
                perf_counters_stop(&perf);
            }
            
            metrics_finish(&metrics);
            metrics_print_csv(out, &metrics);
            
            if (perf.fd_instructions >= 0) {
                fprintf(out, ",");
                perf_counters_print_csv(out, &perf);
            } else {
                fprintf(out, "\n");
            }
            
            (void)result;
        }
        
        free(buffer);
    }
    
    perf_counters_close(&perf);
    fclose(out);
    
    printf("\nResults saved to ../data/cache_analysis.csv\n");
    printf("\nAnalyze with:\n");
    printf("  python3 ../analyze/parse.py ../data/cache_analysis.csv\n");
    
    return 0;
}
