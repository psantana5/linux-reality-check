/*
 * sched_api.h - Scheduler and CPU affinity control
 * 
 * Functions for controlling thread placement and scheduling.
 */

#ifndef LRC_SCHED_API_H
#define LRC_SCHED_API_H

/**
 * @brief Pin calling thread to specific CPU
 * @param cpu CPU ID to pin to (0-based)
 * @return 0 on success, -1 on error
 */
int pin_to_cpu(int cpu);

/**
 * @brief Set scheduling priority (nice value)
 * @param nice_value Priority (-20 to 19, lower = higher priority)
 * @return 0 on success, -1 on error
 */
int set_nice(int nice_value);

/**
 * @brief Set real-time scheduling policy
 * @param policy Scheduling policy (SCHED_FIFO, SCHED_RR)
 * @param priority Priority (1-99)
 * @return 0 on success, -1 on error
 * @note Requires root privileges
 */
int set_realtime_policy(int policy, int priority);

#endif /* LRC_SCHED_API_H */
