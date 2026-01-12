/*
 * numa_utils.c - NUMA awareness utilities
 *
 * Purpose:
 *   Control and measure NUMA node placement for workloads.
 *   Essential for multi-socket systems.
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/syscall.h>
#include <errno.h>

// NUMA constants
#define NUMA_MAXNODES 256
#define BITS_PER_LONG (sizeof(unsigned long) * 8)

// Cached node count for performance
static int cached_node_count = -2;  // -2 = not initialized, -1 = error, >=0 = count

// NUMA policy modes
#define MPOL_DEFAULT 0
#define MPOL_PREFERRED 1
#define MPOL_BIND 2
#define MPOL_INTERLEAVE 3

// mbind flags
#define MPOL_MF_STRICT (1<<0)
#define MPOL_MF_MOVE (1<<1)
#define MPOL_MF_MOVE_ALL (1<<2)

/*
 * Read NUMA topology from /sys.
 * Returns number of NUMA nodes, or -1 on error.
 */
int numa_get_node_count(void) {
    // Return cached value if available
    if (cached_node_count != -2) {
        return cached_node_count;
    }
    
    int count = 0;
    char path[256];
    
    for (int i = 0; i < NUMA_MAXNODES; i++) {
        snprintf(path, sizeof(path), "/sys/devices/system/node/node%d", i);
        if (access(path, F_OK) == 0) {
            count++;
        } else {
            break;
        }
    }
    
    cached_node_count = (count > 0) ? count : -1;
    return cached_node_count;
}

/*
 * Get CPUs belonging to a NUMA node.
 * Returns bitmask of CPUs (simplified - only supports up to 64 CPUs).
 */
uint64_t numa_node_to_cpus(int node) {
    char path[256];
    char buffer[256];
    FILE *f;
    
    snprintf(path, sizeof(path), 
             "/sys/devices/system/node/node%d/cpulist", node);
    
    f = fopen(path, "r");
    if (!f) return 0;
    
    if (!fgets(buffer, sizeof(buffer), f)) {
        fclose(f);
        return 0;
    }
    fclose(f);
    
    // Parse CPU list (e.g., "0-3,8-11")
    // Simplified: just return mask of first range
    int start, end;
    uint64_t mask = 0;
    
    if (sscanf(buffer, "%d-%d", &start, &end) == 2) {
        for (int i = start; i <= end && i < 64; i++) {
            mask |= (1ULL << i);
        }
    } else if (sscanf(buffer, "%d", &start) == 1) {
        if (start < 64) {
            mask |= (1ULL << start);
        }
    }
    
    return mask;
}

/*
 * Allocate memory on specific NUMA node.
 * Falls back to regular malloc if NUMA not available.
 *
 * Uses mbind() syscall directly to avoid libnuma dependency.
 */
void* numa_alloc_on_node(size_t size, int node) {
    // Check if NUMA is available
    int node_count = numa_get_node_count();
    if (node_count < 2) {
        return malloc(size);
    }
    
    // Validate node number
    if (node < 0 || node >= node_count) {
        return NULL;
    }
    
    // Allocate memory using mmap for page-aligned allocation
    // This is required for mbind() to work properly
    void *ptr = mmap(NULL, size, PROT_READ | PROT_WRITE,
                     MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    
    if (ptr == MAP_FAILED) {
        return NULL;
    }
    
    // Create nodemask with only the target node set
    unsigned long nodemask[((node_count + BITS_PER_LONG - 1) / BITS_PER_LONG)];
    memset(nodemask, 0, sizeof(nodemask));
    nodemask[node / BITS_PER_LONG] = 1UL << (node % BITS_PER_LONG);
    
    // Bind memory to the specified NUMA node
    long ret = syscall(SYS_mbind, ptr, size, MPOL_BIND, 
                       nodemask, node_count + 1, MPOL_MF_STRICT | MPOL_MF_MOVE);
    
    if (ret != 0) {
        // If mbind fails, still return the memory but it won't be NUMA-bound
        fprintf(stderr, "Warning: mbind() failed for node %d: %s\n", 
                node, strerror(errno));
    }
    
    return ptr;
}

/*
 * Free memory allocated with numa_alloc_on_node.
 * Must be used instead of free() for NUMA-allocated memory.
 * Returns 0 on success, -1 on error.
 */
int numa_free(void *ptr, size_t size) {
    if (!ptr) return 0;
    
    // If NUMA was available, memory was allocated with mmap
    if (numa_get_node_count() >= 2) {
        if (munmap(ptr, size) != 0) {
            return -1;
        }
    } else {
        // Fallback path used malloc
        free(ptr);
    }
    
    return 0;
}

/*
 * Allocate memory interleaved across all NUMA nodes.
 * Spreads pages across nodes for balanced memory bandwidth.
 * Returns pointer to allocated memory, or NULL on failure.
 */
void* numa_alloc_interleaved(size_t size) {
    int node_count = numa_get_node_count();
    
    // Fall back to malloc on single-node systems
    if (node_count < 2) {
        return malloc(size);
    }
    
    // Allocate memory using mmap
    void *ptr = mmap(NULL, size, PROT_READ | PROT_WRITE,
                     MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    
    if (ptr == MAP_FAILED) {
        return NULL;
    }
    
    // Create nodemask with all nodes set
    unsigned long nodemask[((node_count + BITS_PER_LONG - 1) / BITS_PER_LONG)];
    memset(nodemask, 0, sizeof(nodemask));
    
    for (int i = 0; i < node_count; i++) {
        nodemask[i / BITS_PER_LONG] |= 1UL << (i % BITS_PER_LONG);
    }
    
    // Use MPOL_INTERLEAVE to spread pages across nodes
    long ret = syscall(SYS_mbind, ptr, size, MPOL_INTERLEAVE,
                       nodemask, node_count + 1, MPOL_MF_MOVE);
    
    if (ret != 0) {
        fprintf(stderr, "Warning: mbind() interleave failed: %s\n", strerror(errno));
    }
    
    return ptr;
}

/*
 * Print NUMA topology information.
 */
void numa_print_topology(void) {
    int node_count = numa_get_node_count();
    
    printf("NUMA Configuration:\n");
    
    if (node_count < 0) {
        printf("  NUMA not available or not detected\n");
        return;
    }
    
    printf("  Nodes: %d\n", node_count);
    
    for (int node = 0; node < node_count; node++) {
        uint64_t cpus = numa_node_to_cpus(node);
        printf("  Node %d: CPUs ", node);
        
        int first = 1;
        for (int cpu = 0; cpu < 64; cpu++) {
            if (cpus & (1ULL << cpu)) {
                if (!first) printf(",");
                printf("%d", cpu);
                first = 0;
            }
        }
        printf("\n");
    }
}

/*
 * Check if system has multiple NUMA nodes.
 */
int numa_is_available(void) {
    return numa_get_node_count() > 1;
}
