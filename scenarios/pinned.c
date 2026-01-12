/*
 * pinned.c - CPU pinning experiment
 *
 * Hypothesis:
 *   Pinning a CPU-bound task to a single core eliminates
 *   scheduler migration overhead and reduces context switches.
 *
 * Method:
 *   Run identical CPU workload on:
 *   1. Unpinned (scheduler chooses)
 *   2. Pinned to CPU 0
 *   3. Pinned to CPU 1
 *   
 *   Measure context switches and CPU migrations.
 *
 * Variables:
 *   - CPU affinity (controlled)
 *   - Workload iterations (fixed)
 *
 * Expected outcome:
 *   Pinned runs show:
 *   - Zero CPU migrations (start_cpu == end_cpu)
 *   - Fewer involuntary context switches
 *   - Lower runtime variance
 *
 * Limitations:
 *   - Does not account for other system load
 *   - Assumes CPUs are homogeneous
 *   - Does not test NUMA effects
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include "../core/metrics.h"

extern uint64_t cpu_spin(uint64_t iterations);
extern int pin_to_cpu(int cpu);

#define ITERATIONS 1000000000ULL
#define RUNS 10

int main(void) {
    workload_metrics_t metrics;
    FILE *out = fopen("../data/pinned.csv", "w");
    
    if (!out) {
        perror("fopen");
        return 1;
    }
    
    fprintf(out, "run,affinity,");
    metrics_print_csv_header(out);
    
    printf("Running pinned CPU experiment...\n");
    
    for (int run = 0; run < RUNS; run++) {
        fprintf(out, "%d,unpinned,", run);
        metrics_init(&metrics);
        uint64_t result = cpu_spin(ITERATIONS);
        metrics_finish(&metrics);
        metrics_print_csv(out, &metrics);
        
        (void)result;
    }
    
    for (int run = 0; run < RUNS; run++) {
        if (pin_to_cpu(0) == -1) {
            perror("pin_to_cpu(0)");
            continue;
        }
        
        fprintf(out, "%d,cpu0,", run);
        metrics_init(&metrics);
        uint64_t result = cpu_spin(ITERATIONS);
        metrics_finish(&metrics);
        metrics_print_csv(out, &metrics);
        
        (void)result;
    }
    
    for (int run = 0; run < RUNS; run++) {
        if (pin_to_cpu(1) == -1) {
            perror("pin_to_cpu(1)");
            continue;
        }
        
        fprintf(out, "%d,cpu1,", run);
        metrics_init(&metrics);
        uint64_t result = cpu_spin(ITERATIONS);
        metrics_finish(&metrics);
        metrics_print_csv(out, &metrics);
        
        (void)result;
    }
    
    fclose(out);
    printf("Results saved to ../data/pinned.csv\n");
    
    return 0;
}
