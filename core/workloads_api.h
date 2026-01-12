/*
 * workloads_api.h - Core workload functions
 * 
 * CPU and memory intensive workloads for performance testing.
 */

#ifndef LRC_WORKLOADS_API_H
#define LRC_WORKLOADS_API_H

#include <stddef.h>
#include <stdint.h>

/**
 * @brief Execute CPU-intensive spin workload
 * @param iterations Number of iterations to perform
 * @return Computed result (prevents optimization)
 */
uint64_t cpu_spin(uint64_t iterations);

/**
 * @brief Sequential memory streaming (measures bandwidth)
 * @param buffer Memory buffer to access
 * @param size Buffer size in bytes
 * @param iterations Number of passes through buffer
 * @return Computed result (prevents optimization)
 */
uint64_t memory_stream(uint64_t *buffer, size_t size, uint64_t iterations);

/**
 * @brief Random memory access via pointer chasing (measures latency)
 * @param buffer Memory buffer with pointer chain
 * @param size Buffer size in bytes
 * @param iterations Number of pointer hops
 * @return Computed result (prevents optimization)
 */
uint64_t memory_random_chase(uint64_t *buffer, size_t size, uint64_t iterations);

/**
 * @brief Multi-threaded lock contention workload
 * @param lock_type Type of lock (0=spinlock, 1=mutex, 2=atomic)
 * @param num_threads Number of threads
 * @param iterations Iterations per thread
 * @return Total operations completed
 */
uint64_t lock_contention(int lock_type, int num_threads, uint64_t iterations);

/**
 * @brief Mixed CPU+memory workload patterns
 * @param pattern Pattern ID (0-4 for different CPU/memory ratios)
 * @param size Working set size
 * @param iterations Number of iterations
 * @return Computed result
 */
uint64_t mixed_workload(int pattern, size_t size, uint64_t iterations);

#endif /* LRC_WORKLOADS_API_H */
