/*
 * memory_stream.c - Sequential memory streaming workload
 *
 * What it stresses:
 *   - Memory bandwidth
 *   - L1/L2/L3 cache hierarchy
 *   - Memory controller
 *   - TLB behavior
 *
 * What it deliberately avoids:
 *   - Random access patterns
 *   - Complex computation
 *   - System calls in loop
 *
 * Purpose:
 *   Isolate memory subsystem behavior. Cache misses and
 *   memory stalls should dominate, not CPU operations.
 */

#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#define CACHE_LINE_SIZE 64

/*
 * Sequential read and accumulate.
 * Pattern is cache-friendly but tests memory bandwidth
 * when buffer exceeds cache size.
 */
uint64_t memory_stream_read(const uint64_t *buffer, size_t size) {
    uint64_t sum = 0;
    size_t count = size / sizeof(uint64_t);
    
    for (size_t i = 0; i < count; i++) {
        sum += buffer[i];
    }
    
    return sum;
}

/*
 * Sequential write pattern.
 * Tests write bandwidth and cache write-back behavior.
 */
void memory_stream_write(uint64_t *buffer, size_t size) {
    size_t count = size / sizeof(uint64_t);
    
    for (size_t i = 0; i < count; i++) {
        buffer[i] = i;
    }
}

/*
 * Copy pattern: simultaneous read and write.
 * Maximum memory bandwidth stress.
 */
void memory_stream_copy(uint64_t *dst, const uint64_t *src, size_t size) {
    size_t count = size / sizeof(uint64_t);
    
    for (size_t i = 0; i < count; i++) {
        dst[i] = src[i];
    }
}

/*
 * Strided access pattern.
 * Deliberately miss cache lines to study cache hierarchy.
 *
 * stride: Number of cache lines to skip (1 = sequential, >1 = strided)
 */
uint64_t memory_stream_strided(const uint64_t *buffer, size_t size, size_t stride) {
    uint64_t sum = 0;
    size_t count = size / sizeof(uint64_t);
    size_t step = (stride * CACHE_LINE_SIZE) / sizeof(uint64_t);
    
    for (size_t i = 0; i < count; i += step) {
        sum += buffer[i];
    }
    
    return sum;
}
