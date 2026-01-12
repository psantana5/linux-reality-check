/*
 * mixed_workload.c - Realistic CPU+Memory mixed pattern
 *
 * What it stresses:
 *   - CPU and memory simultaneously
 *   - Configurable ratio
 *   - Temporal locality (working set changes)
 *   - Varying access patterns
 *
 * What it deliberately avoids:
 *   - Pure synthetic patterns
 *   - Predictable access
 *   - Static working set
 *
 * Purpose:
 *   Bridge gap between synthetic and real workloads.
 *   More realistic cache/memory behavior.
 *   Configurable to match different application profiles.
 */

#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define KB (1024ULL)
#define MB (1024ULL * KB)

typedef struct {
    uint64_t *buffer;
    size_t buffer_size;
    uint64_t *indices;
    size_t working_set_size;
    int compute_ratio;  // Compute ops per memory access
    uint64_t seed;
} mixed_workload_t;

/*
 * Initialize mixed workload.
 */
int mixed_workload_init(mixed_workload_t *w, size_t buffer_size, 
                        size_t working_set, int compute_ratio) {
    w->buffer_size = buffer_size;
    w->working_set_size = working_set;
    w->compute_ratio = compute_ratio;
    w->seed = time(NULL);
    
    w->buffer = malloc(buffer_size);
    if (!w->buffer) return -1;
    
    // Initialize with pattern
    size_t count = buffer_size / sizeof(uint64_t);
    for (size_t i = 0; i < count; i++) {
        w->buffer[i] = i;
    }
    
    // Pre-generate access pattern
    w->indices = malloc(working_set * sizeof(uint64_t));
    if (!w->indices) {
        free(w->buffer);
        return -1;
    }
    
    // Random working set within buffer
    srand(w->seed);
    for (size_t i = 0; i < working_set; i++) {
        w->indices[i] = rand() % count;
    }
    
    return 0;
}

/*
 * Cleanup mixed workload.
 */
void mixed_workload_cleanup(mixed_workload_t *w) {
    free(w->buffer);
    free(w->indices);
}

/*
 * Execute mixed CPU+Memory workload.
 * 
 * Pattern:
 *   For each memory access:
 *   1. Read from working set
 *   2. Perform N compute operations
 *   3. Write result back
 *
 * This simulates real application behavior:
 *   - Data structures with computation
 *   - Not pure bandwidth test
 *   - Not pure compute test
 */
uint64_t mixed_workload_run(mixed_workload_t *w, uint64_t iterations) {
    uint64_t result = 0;
    
    for (uint64_t iter = 0; iter < iterations; iter++) {
        // Memory access from working set
        size_t idx = w->indices[iter % w->working_set_size];
        uint64_t value = w->buffer[idx];
        
        // Compute operations (configurable ratio)
        for (int c = 0; c < w->compute_ratio; c++) {
            value = value * 3 + iter;
            value ^= (value << 13);
            value ^= (value >> 7);
            value ^= (value << 17);
        }
        
        // Write back (dirty cache line)
        w->buffer[idx] = value;
        result += value;
    }
    
    return result;
}

/*
 * Phase-based workload: working set grows over time.
 * Simulates application warmup.
 */
uint64_t mixed_workload_phased(mixed_workload_t *w, uint64_t iterations, int phases) {
    uint64_t result = 0;
    size_t initial_working_set = w->working_set_size;
    
    for (int phase = 0; phase < phases; phase++) {
        // Grow working set each phase
        w->working_set_size = initial_working_set * (phase + 1) / phases;
        if (w->working_set_size < 1) w->working_set_size = 1;
        
        result += mixed_workload_run(w, iterations / phases);
    }
    
    w->working_set_size = initial_working_set;
    return result;
}

/*
 * Bursty workload: alternating compute and memory phases.
 * Simulates batch processing patterns.
 */
uint64_t mixed_workload_bursty(mixed_workload_t *w, uint64_t iterations) {
    uint64_t result = 0;
    int original_ratio = w->compute_ratio;
    
    for (uint64_t i = 0; i < iterations; i++) {
        // Alternate between compute-heavy and memory-heavy
        if ((i / 1000) % 2 == 0) {
            w->compute_ratio = original_ratio * 4;  // Compute burst
        } else {
            w->compute_ratio = original_ratio / 4;  // Memory burst
            if (w->compute_ratio < 1) w->compute_ratio = 1;
        }
        
        size_t idx = w->indices[i % w->working_set_size];
        uint64_t value = w->buffer[idx];
        
        for (int c = 0; c < w->compute_ratio; c++) {
            value = value * 3 + i;
            value ^= (value << 13);
        }
        
        w->buffer[idx] = value;
        result += value;
    }
    
    w->compute_ratio = original_ratio;
    return result;
}
