/*
 * null_baseline.c - Measurement overhead quantification
 *
 * Hypothesis:
 *   The measurement infrastructure itself has overhead.
 *   By measuring an empty workload, we can quantify this overhead
 *   and subtract it from other experiments.
 *
 * Method:
 *   Run metrics_init() → (empty loop) → metrics_finish()
 *   Measure:
 *   1. Pure timing overhead
 *   2. /proc read overhead
 *   3. sched_getcpu() overhead
 *
 * Variables:
 *   - Workload content (minimal - just volatile counter)
 *   - Measurement calls (standard)
 *
 * Expected outcome:
 *   - Total measurement overhead: ~100-200μs
 *   - Breakdown: /proc reads ~10-50μs each, timing ~25ns each
 *   - Negligible compared to ms-scale workloads
 *
 * Purpose:
 *   Establish confidence that measurement doesn't dominate results.
 *   Provide baseline to subtract from other experiments (optional).
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include "../core/metrics.h"

extern int pin_to_cpu(int cpu);

#define RUNS 100  // More runs for statistical significance

int main(void) {
    workload_metrics_t metrics;
    FILE *out = fopen("../data/null_baseline.csv", "w");
    
    if (!out) {
        perror("fopen");
        return 1;
    }
    
    pin_to_cpu(0);
    
    fprintf(out, "run,workload_type,");
    metrics_print_csv_header(out);
    
    printf("Running null baseline experiment...\n");
    printf("Quantifying pure measurement overhead.\n\n");
    
    // Null workload: absolutely minimal work
    printf("Null workload (minimal)...\n");
    for (int run = 0; run < RUNS; run++) {
        fprintf(out, "%d,null_minimal,", run);
        metrics_init(&metrics);
        
        // Minimal work: volatile to prevent optimization
        volatile uint64_t counter = 0;
        counter++;
        
        metrics_finish(&metrics);
        metrics_print_csv(out, &metrics);
    }
    
    // Empty loop baseline: typical "nothing" workload
    printf("Empty loop (typical nothing)...\n");
    for (int run = 0; run < RUNS; run++) {
        fprintf(out, "%d,empty_loop,", run);
        metrics_init(&metrics);
        
        volatile uint64_t sum = 0;
        for (int i = 0; i < 1000; i++) {
            sum += i;
        }
        
        metrics_finish(&metrics);
        metrics_print_csv(out, &metrics);
    }
    
    fclose(out);
    
    printf("\nResults saved to ../data/null_baseline.csv\n");
    printf("\nThis measures PURE measurement overhead.\n");
    printf("Expected: ~100-200μs total\n");
    printf("  - /proc reads: ~10-50μs each\n");
    printf("  - clock_gettime: ~25-40ns each\n");
    printf("  - sched_getcpu: ~10ns each\n\n");
    printf("Analyze with:\n");
    printf("  python3 ../analyze/parse.py ../data/null_baseline.csv\n");
    
    return 0;
}
