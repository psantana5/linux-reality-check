/*
 * realistic_patterns.c - Realistic workload patterns experiment
 *
 * Hypothesis:
 *   Real applications exhibit mixed CPU+Memory patterns that
 *   differ significantly from pure synthetic workloads.
 *   
 *   Different compute:memory ratios lead to different bottlenecks:
 *   - High compute ratio: CPU-bound
 *   - Low compute ratio: Memory-bound
 *   - Phased access: Cache warming effects
 *
 * Method:
 *   Run mixed workload with different configurations:
 *   1. Compute-heavy (10:1 ratio)
 *   2. Balanced (3:1 ratio)
 *   3. Memory-heavy (1:1 ratio)
 *   4. Phased (growing working set)
 *   5. Bursty (alternating phases)
 *
 * Variables:
 *   - Compute:Memory ratio
 *   - Working set size
 *   - Access pattern (uniform, phased, bursty)
 *
 * Expected outcome:
 *   - Compute-heavy: High IPC, low cache misses
 *   - Memory-heavy: Low IPC, high cache misses
 *   - Phased: Warmup effects visible
 *   - Bursty: Variance in metrics
 *
 * Limitations:
 *   - Still synthetic (not real application)
 *   - Simplified compute (no branches, no calls)
 *   - Pre-generated access pattern
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include "../core/metrics.h"

extern int mixed_workload_init(void *w, size_t buffer_size, size_t working_set, int compute_ratio);
extern void mixed_workload_cleanup(void *w);
extern uint64_t mixed_workload_run(void *w, uint64_t iterations);
extern uint64_t mixed_workload_phased(void *w, uint64_t iterations, int phases);
extern uint64_t mixed_workload_bursty(void *w, uint64_t iterations);
extern int pin_to_cpu(int cpu);

typedef struct {
    uint64_t *buffer;
    size_t buffer_size;
    uint64_t *indices;
    size_t working_set_size;
    int compute_ratio;
    uint64_t seed;
} mixed_workload_t;

#define MB (1024ULL * 1024ULL)
#define BUFFER_SIZE (16 * MB)
#define WORKING_SET 10000
#define ITERATIONS 1000000ULL
#define RUNS 10

int main(void) {
    workload_metrics_t metrics;
    FILE *out = fopen("../data/realistic_patterns.csv", "w");
    
    if (!out) {
        perror("fopen");
        return 1;
    }
    
    pin_to_cpu(0);
    
    fprintf(out, "run,pattern,compute_ratio,");
    metrics_print_csv_header(out);
    
    printf("Running realistic workload patterns experiment...\n");
    printf("Testing different compute:memory ratios and patterns.\n\n");
    
    // Compute-heavy (10:1 ratio)
    printf("Compute-heavy pattern (10:1)...\n");
    for (int run = 0; run < RUNS; run++) {
        mixed_workload_t work;
        mixed_workload_init(&work, BUFFER_SIZE, WORKING_SET, 10);
        
        fprintf(out, "%d,compute_heavy,10,", run);
        metrics_init(&metrics);
        uint64_t result = mixed_workload_run(&work, ITERATIONS);
        metrics_finish(&metrics);
        metrics_print_csv(out, &metrics);
        
        mixed_workload_cleanup(&work);
        (void)result;
    }
    
    // Balanced (3:1 ratio)
    printf("Balanced pattern (3:1)...\n");
    for (int run = 0; run < RUNS; run++) {
        mixed_workload_t work;
        mixed_workload_init(&work, BUFFER_SIZE, WORKING_SET, 3);
        
        fprintf(out, "%d,balanced,3,", run);
        metrics_init(&metrics);
        uint64_t result = mixed_workload_run(&work, ITERATIONS);
        metrics_finish(&metrics);
        metrics_print_csv(out, &metrics);
        
        mixed_workload_cleanup(&work);
        (void)result;
    }
    
    // Memory-heavy (1:1 ratio)
    printf("Memory-heavy pattern (1:1)...\n");
    for (int run = 0; run < RUNS; run++) {
        mixed_workload_t work;
        mixed_workload_init(&work, BUFFER_SIZE, WORKING_SET, 1);
        
        fprintf(out, "%d,memory_heavy,1,", run);
        metrics_init(&metrics);
        uint64_t result = mixed_workload_run(&work, ITERATIONS);
        metrics_finish(&metrics);
        metrics_print_csv(out, &metrics);
        
        mixed_workload_cleanup(&work);
        (void)result;
    }
    
    // Phased (growing working set)
    printf("Phased pattern (warmup)...\n");
    for (int run = 0; run < RUNS; run++) {
        mixed_workload_t work;
        mixed_workload_init(&work, BUFFER_SIZE, WORKING_SET, 3);
        
        fprintf(out, "%d,phased,3,", run);
        metrics_init(&metrics);
        uint64_t result = mixed_workload_phased(&work, ITERATIONS, 5);
        metrics_finish(&metrics);
        metrics_print_csv(out, &metrics);
        
        mixed_workload_cleanup(&work);
        (void)result;
    }
    
    // Bursty (alternating compute/memory)
    printf("Bursty pattern (alternating)...\n");
    for (int run = 0; run < RUNS; run++) {
        mixed_workload_t work;
        mixed_workload_init(&work, BUFFER_SIZE, WORKING_SET, 3);
        
        fprintf(out, "%d,bursty,3,", run);
        metrics_init(&metrics);
        uint64_t result = mixed_workload_bursty(&work, ITERATIONS);
        metrics_finish(&metrics);
        metrics_print_csv(out, &metrics);
        
        mixed_workload_cleanup(&work);
        (void)result;
    }
    
    fclose(out);
    
    printf("\nResults saved to ../data/realistic_patterns.csv\n");
    printf("\nAnalyze with:\n");
    printf("  python3 ../analyze/parse.py ../data/realistic_patterns.csv\n");
    printf("  python3 ../analyze/distributions.py ../data/realistic_patterns.csv\n");
    
    return 0;
}
