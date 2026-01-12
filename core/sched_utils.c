/*
 * sched_utils.c - Scheduler interaction utilities
 *
 * Purpose:
 *   Explicit control over process scheduling context.
 *   All scheduling changes must be intentional and measurable.
 */

#define _GNU_SOURCE
#include <sched.h>
#include <unistd.h>
#include <sys/resource.h>
#include <errno.h>
#include <stdio.h>

/*
 * Pin calling thread to specific CPU core.
 * Returns 0 on success, -1 on failure.
 *
 * Justification for syscall:
 *   sched_setaffinity() is the only way to control CPU placement.
 *   Called once before workload, not in hot path.
 */
int pin_to_cpu(int cpu) {
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(cpu, &cpuset);
    
    if (sched_setaffinity(0, sizeof(cpu_set_t), &cpuset) == -1) {
        return -1;
    }
    
    return 0;
}

/*
 * Set process nice level.
 * Returns 0 on success, -1 on failure.
 *
 * Justification for syscall:
 *   setpriority() is the only way to modify scheduling priority.
 *   Called once before workload, not in hot path.
 */
int set_nice(int nice_value) {
    if (setpriority(PRIO_PROCESS, 0, nice_value) == -1) {
        return -1;
    }
    
    return 0;
}

/*
 * Get current CPU the thread is running on.
 * Returns CPU number, or -1 on error.
 *
 * Justification for syscall:
 *   sched_getcpu() is used only for verification, not in workload.
 */
int get_current_cpu(void) {
    return sched_getcpu();
}

/*
 * Yield CPU to scheduler once.
 * Used only in controlled experiments to study reschedule behavior.
 *
 * Justification for syscall:
 *   sched_yield() is the experiment subject itself.
 */
int yield_cpu(void) {
    return sched_yield();
}
