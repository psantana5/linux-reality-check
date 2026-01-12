/*
 * numa_api.h - NUMA awareness API
 * 
 * Provides NUMA node detection, memory allocation, and topology queries.
 */

#ifndef LRC_NUMA_API_H
#define LRC_NUMA_API_H

#include <stddef.h>
#include <stdint.h>

/**
 * @brief Get the number of NUMA nodes in the system
 * @return Number of NUMA nodes, or -1 on error
 */
int numa_get_node_count(void);

/**
 * @brief Get CPUs belonging to a NUMA node
 * @param node NUMA node ID (0-based)
 * @return Bitmask of CPUs (up to 64 CPUs supported)
 */
uint64_t numa_node_to_cpus(int node);

/**
 * @brief Allocate memory on specific NUMA node
 * @param size Number of bytes to allocate (will be page-aligned)
 * @param node NUMA node ID (0-based)
 * @return Pointer to allocated memory, or NULL on failure
 * @note Memory must be freed with numa_free(), not free()
 * @note Falls back to malloc() on single-node systems
 */
void* numa_alloc_on_node(size_t size, int node);

/**
 * @brief Free memory allocated with numa_alloc_on_node
 * @param ptr Pointer to memory (can be NULL)
 * @param size Original allocation size in bytes
 * @return 0 on success, -1 on error
 */
int numa_free(void *ptr, size_t size);

/**
 * @brief Check if system has multiple NUMA nodes
 * @return 1 if NUMA available, 0 otherwise
 */
int numa_is_available(void);

/**
 * @brief Print NUMA topology information to stdout
 */
void numa_print_topology(void);

/**
 * @brief Allocate memory interleaved across all NUMA nodes
 * @param size Number of bytes to allocate
 * @return Pointer to allocated memory, or NULL on failure
 * @note Memory must be freed with numa_free()
 * @note Pages are distributed round-robin across all nodes
 */
void* numa_alloc_interleaved(size_t size);

#endif /* LRC_NUMA_API_H */
