/*
 * numa_locality.c - NUMA local vs remote memory access
 *
 * Hypothesis:
 *   Remote NUMA node access has 2-3x higher latency than local.
 *   This dominates other cache effects on multi-socket systems.
 *
 * Method:
 *   Pin thread to node 0, allocate memory on:
 *   1. Local node (node 0)
 *   2. Remote node (node 1)
 *   
 *   Measure random access latency (pointer-chasing).
 *
 * Expected outcome:
 *   Remote access: 2-3x slower than local
 *   Even if both in "DRAM", locality matters more than cache
 *
 * Limitations:
 *   - Requires system with 2+ NUMA nodes
 *   - Simplified NUMA allocation (falls back to malloc)
 *   - Does not test all node combinations
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include "../core/metrics.h"

extern uint64_t memory_random_chase(uint64_t *buffer, size_t size, uint64_t iterations);
extern int pin_to_cpu(int cpu);
extern int numa_get_node_count(void);
extern uint64_t numa_node_to_cpus(int node);
extern void numa_print_topology(void);
extern void* numa_alloc_on_node(size_t size, int node);
extern int numa_free(void *ptr, size_t size);
extern int numa_is_available(void);

#define MB (1024ULL * 1024ULL)
#define BUFFER_SIZE (64 * MB)
#define ITERATIONS 1000000ULL
#define RUNS 10

int main(void) {
    workload_metrics_t metrics;
    
    printf("=== NUMA Locality Experiment ===\n\n");
    
    if (!numa_is_available()) {
        printf("⚠ NUMA not available on this system (single node or UMA)\n");
        printf("Running experiment anyway - will test malloc() behavior.\n");
        printf("Note: On single-node systems, both 'local' and 'remote' allocations\n");
        printf("      will be identical (no NUMA effect visible).\n\n");
    } else {
        numa_print_topology();
        printf("\n");
    }
    
    FILE *out = fopen("../data/numa_locality.csv", "w");
    if (!out) {
        perror("fopen");
        return 1;
    }
    
    fprintf(out, "run,locality,");
    metrics_print_csv_header(out);
    
    // Pin to first CPU of node 0 (if NUMA available)
    int cpu0 = 0; // Default to CPU 0
    if (numa_is_available()) {
        uint64_t node0_cpus = numa_node_to_cpus(0);
        for (int i = 0; i < 64; i++) {
            if (node0_cpus & (1ULL << i)) {
                cpu0 = i;
                break;
            }
        }
    }
    
    pin_to_cpu(cpu0);
    printf("Pinned to CPU %d\n\n", cpu0);
    
    // Test "local" memory (node 0 or default allocation)
    printf("Testing 'local' memory allocation...\n");
    uint64_t *local_buffer = numa_alloc_on_node(BUFFER_SIZE, 0);
    if (!local_buffer) {
        perror("malloc local");
        return 1;
    }
    memset(local_buffer, 0x42, BUFFER_SIZE);
    printf("  Allocated %llu MB\n", BUFFER_SIZE / MB);
    
    for (int run = 0; run < RUNS; run++) {
        fprintf(out, "%d,local,", run);
        metrics_init(&metrics);
        uint64_t result = memory_random_chase(local_buffer, BUFFER_SIZE, ITERATIONS);
        metrics_finish(&metrics);
        metrics_print_csv(out, &metrics);
        (void)result;
    }
    
    numa_free(local_buffer, BUFFER_SIZE);
    
    // Test "remote" memory (node 1 or another allocation)
    printf("Testing 'remote' memory allocation...\n");
    uint64_t *remote_buffer = numa_alloc_on_node(BUFFER_SIZE, 1);
    if (!remote_buffer) {
        perror("malloc remote");
        return 1;
    }
    memset(remote_buffer, 0x42, BUFFER_SIZE);
    printf("  Allocated %llu MB\n", BUFFER_SIZE / MB);
    
    for (int run = 0; run < RUNS; run++) {
        fprintf(out, "%d,remote,", run);
        metrics_init(&metrics);
        uint64_t result = memory_random_chase(remote_buffer, BUFFER_SIZE, ITERATIONS);
        metrics_finish(&metrics);
        metrics_print_csv(out, &metrics);
        (void)result;
    }
    
    numa_free(remote_buffer, BUFFER_SIZE);
    fclose(out);
    
    printf("\nResults saved to ../data/numa_locality.csv\n");
    
    if (!numa_is_available()) {
        printf("\n⚠ IMPORTANT: Single-node system detected!\n");
        printf("   Both 'local' and 'remote' used standard malloc().\n");
        printf("   No NUMA effect expected - results should be identical.\n");
        printf("   To see NUMA effects, run on a multi-socket system (e.g., dual Xeon).\n");
    } else {
        printf("\nNote: This is a simplified NUMA test.\n");
        printf("For production use, link with -lnuma and use numa_alloc_onnode().\n");
    }
    
    return 0;
}
