/*
 * lrc.h - Linux Reality Check Main API
 * 
 * Unified header for all LRC functionality.
 * Include this file to access the complete API.
 */

#ifndef LRC_H
#define LRC_H

#define LRC_VERSION_MAJOR 2
#define LRC_VERSION_MINOR 1
#define LRC_VERSION_PATCH 0
#define LRC_VERSION_STRING "2.1.0"

/* Core APIs */
#include "workloads_api.h"
#include "numa_api.h"
#include "sched_api.h"
#include "metrics.h"
#include "perf_counters.h"

/**
 * @brief Get LRC version string
 * @return Version string (e.g., "2.1.0")
 */
static inline const char* lrc_version(void) {
    return LRC_VERSION_STRING;
}

/**
 * @brief Get major version number
 * @return Major version
 */
static inline int lrc_version_major(void) {
    return LRC_VERSION_MAJOR;
}

/**
 * @brief Get minor version number
 * @return Minor version
 */
static inline int lrc_version_minor(void) {
    return LRC_VERSION_MINOR;
}

/**
 * @brief Get patch version number
 * @return Patch version
 */
static inline int lrc_version_patch(void) {
    return LRC_VERSION_PATCH;
}

#endif /* LRC_H */
