/*
 * cpu_spin.c - Pure CPU compute workload
 *
 * What it stresses:
 *   - Integer ALU operations
 *   - Tight loop execution
 *   - Instruction cache
 *
 * What it deliberately avoids:
 *   - Memory allocation
 *   - System calls
 *   - Branch mispredictions (predictable loop)
 *   - I/O operations
 *
 * Purpose:
 *   Establish baseline CPU-bound behavior under different
 *   scheduling contexts. Any context switches or migrations
 *   indicate scheduler interference, not workload characteristics.
 */

#include <stdint.h>

/*
 * Perform fixed number of integer operations.
 * No syscalls, no allocations, no branches in hot path.
 *
 * Result accumulation prevents compiler from optimizing away the loop.
 */
uint64_t cpu_spin(uint64_t iterations) {
    uint64_t result = 0;
    
    for (uint64_t i = 0; i < iterations; i++) {
        result += i;
        result ^= (i << 1);
        result *= 3;
    }
    
    return result;
}

/*
 * Longer workload with multiple phases.
 * Used to study scheduler behavior over extended periods.
 */
uint64_t cpu_spin_long(uint64_t iterations, uint32_t phases) {
    uint64_t result = 0;
    
    for (uint32_t phase = 0; phase < phases; phase++) {
        for (uint64_t i = 0; i < iterations; i++) {
            result += i;
            result ^= (i << 1);
            result *= 3;
        }
    }
    
    return result;
}
