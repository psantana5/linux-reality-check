/*
 * memory_random.c - Random memory access workload
 *
 * What it stresses:
 *   - DRAM latency (not bandwidth)
 *   - TLB behavior
 *   - Last-level cache
 *
 * What it deliberately avoids:
 *   - Sequential access (defeats prefetcher)
 *   - Predictable patterns
 *   - Computation overhead
 *
 * Purpose:
 *   Measure true memory latency when cache-unfriendly.
 *   Pointer chasing ensures dependent loads - no ILP.
 */

#include <stdint.h>
#include <stdlib.h>
#include <string.h>

/*
 * Pre-shuffle array indices to create random access pattern.
 * Uses Fisher-Yates shuffle for uniform distribution.
 */
static void shuffle_indices(uint64_t *indices, size_t count) {
    for (size_t i = 0; i < count; i++) {
        indices[i] = i;
    }
    
    for (size_t i = count - 1; i > 0; i--) {
        size_t j = rand() % (i + 1);
        uint64_t tmp = indices[i];
        indices[i] = indices[j];
        indices[j] = tmp;
    }
}

/*
 * Pointer-chasing pattern: each element points to next in chain.
 * Creates dependent loads - CPU must wait for each access.
 * This measures true latency, not bandwidth.
 */
uint64_t memory_random_chase(uint64_t *buffer, size_t size, uint64_t iterations) {
    size_t count = size / sizeof(uint64_t);
    
    uint64_t *indices = malloc(count * sizeof(uint64_t));
    if (!indices) return 0;
    
    shuffle_indices(indices, count);
    
    for (size_t i = 0; i < count - 1; i++) {
        buffer[indices[i]] = indices[i + 1];
    }
    buffer[indices[count - 1]] = indices[0];
    
    free(indices);
    
    uint64_t index = 0;
    for (uint64_t i = 0; i < iterations; i++) {
        index = buffer[index];
    }
    
    return index;
}

/*
 * Random read with pre-shuffled indices.
 * Measures random access bandwidth (less latency-bound than pointer chase).
 */
uint64_t memory_random_read(const uint64_t *buffer, size_t size, const uint64_t *indices, size_t access_count) {
    uint64_t sum = 0;
    size_t count = size / sizeof(uint64_t);
    
    for (size_t i = 0; i < access_count; i++) {
        sum += buffer[indices[i] % count];
    }
    
    return sum;
}

/*
 * Generate random access indices (called before measurement).
 */
void memory_random_generate_indices(uint64_t *indices, size_t count, unsigned int seed) {
    srand(seed);
    shuffle_indices(indices, count);
}
