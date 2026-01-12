/*
 * perf_counters.c - Hardware performance counter integration
 *
 * Purpose:
 *   Direct measurement of CPU hardware events using perf_event_open().
 *   Provides cache miss rates, instructions, cycles, etc.
 *
 * Justification for syscalls:
 *   perf_event_open() and read() are only way to access hardware counters.
 *   Called once before and once after workload - not in hot path.
 */

#define _GNU_SOURCE
#include <linux/perf_event.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <sys/syscall.h>

typedef struct {
    int fd_instructions;
    int fd_cycles;
    int fd_l1_dcache_misses;
    int fd_llc_misses;
    int fd_branches;
    int fd_branch_misses;
    
    uint64_t instructions_start;
    uint64_t cycles_start;
    uint64_t l1_misses_start;
    uint64_t llc_misses_start;
    uint64_t branches_start;
    uint64_t branch_misses_start;
    
    uint64_t instructions;
    uint64_t cycles;
    uint64_t l1_dcache_misses;
    uint64_t llc_misses;
    uint64_t branches;
    uint64_t branch_misses;
} perf_counters_t;

/*
 * Wrapper for perf_event_open syscall.
 */
static long perf_event_open(struct perf_event_attr *hw_event, pid_t pid,
                            int cpu, int group_fd, unsigned long flags) {
    return syscall(__NR_perf_event_open, hw_event, pid, cpu, group_fd, flags);
}

/*
 * Open a single performance counter.
 */
static int open_counter(uint32_t type, uint64_t config) {
    struct perf_event_attr pe;
    memset(&pe, 0, sizeof(struct perf_event_attr));
    
    pe.type = type;
    pe.size = sizeof(struct perf_event_attr);
    pe.config = config;
    pe.disabled = 1;
    pe.exclude_kernel = 0;  // Include kernel (we want full picture)
    pe.exclude_hv = 1;      // Exclude hypervisor
    
    int fd = perf_event_open(&pe, 0, -1, -1, 0);
    return fd;
}

/*
 * Initialize performance counters.
 * Returns 0 on success, -1 if perf not available.
 */
int perf_counters_init(perf_counters_t *pc) {
    memset(pc, 0, sizeof(perf_counters_t));
    
    // Open all counters
    pc->fd_instructions = open_counter(PERF_TYPE_HARDWARE, PERF_COUNT_HW_INSTRUCTIONS);
    pc->fd_cycles = open_counter(PERF_TYPE_HARDWARE, PERF_COUNT_HW_CPU_CYCLES);
    pc->fd_l1_dcache_misses = open_counter(PERF_TYPE_HW_CACHE, 
        (PERF_COUNT_HW_CACHE_L1D) | (PERF_COUNT_HW_CACHE_OP_READ << 8) | 
        (PERF_COUNT_HW_CACHE_RESULT_MISS << 16));
    pc->fd_llc_misses = open_counter(PERF_TYPE_HARDWARE, PERF_COUNT_HW_CACHE_MISSES);
    pc->fd_branches = open_counter(PERF_TYPE_HARDWARE, PERF_COUNT_HW_BRANCH_INSTRUCTIONS);
    pc->fd_branch_misses = open_counter(PERF_TYPE_HARDWARE, PERF_COUNT_HW_BRANCH_MISSES);
    
    // Check if at least basic counters work
    if (pc->fd_instructions < 0 || pc->fd_cycles < 0) {
        return -1;
    }
    
    return 0;
}

/*
 * Start counting (call before workload).
 */
void perf_counters_start(perf_counters_t *pc) {
    // Reset and enable all counters
    if (pc->fd_instructions >= 0) {
        ioctl(pc->fd_instructions, PERF_EVENT_IOC_RESET, 0);
        ioctl(pc->fd_instructions, PERF_EVENT_IOC_ENABLE, 0);
    }
    if (pc->fd_cycles >= 0) {
        ioctl(pc->fd_cycles, PERF_EVENT_IOC_RESET, 0);
        ioctl(pc->fd_cycles, PERF_EVENT_IOC_ENABLE, 0);
    }
    if (pc->fd_l1_dcache_misses >= 0) {
        ioctl(pc->fd_l1_dcache_misses, PERF_EVENT_IOC_RESET, 0);
        ioctl(pc->fd_l1_dcache_misses, PERF_EVENT_IOC_ENABLE, 0);
    }
    if (pc->fd_llc_misses >= 0) {
        ioctl(pc->fd_llc_misses, PERF_EVENT_IOC_RESET, 0);
        ioctl(pc->fd_llc_misses, PERF_EVENT_IOC_ENABLE, 0);
    }
    if (pc->fd_branches >= 0) {
        ioctl(pc->fd_branches, PERF_EVENT_IOC_RESET, 0);
        ioctl(pc->fd_branches, PERF_EVENT_IOC_ENABLE, 0);
    }
    if (pc->fd_branch_misses >= 0) {
        ioctl(pc->fd_branch_misses, PERF_EVENT_IOC_RESET, 0);
        ioctl(pc->fd_branch_misses, PERF_EVENT_IOC_ENABLE, 0);
    }
}

/*
 * Stop counting and read values (call after workload).
 */
void perf_counters_stop(perf_counters_t *pc) {
    ssize_t ret;
    
    // Disable and read all counters
    if (pc->fd_instructions >= 0) {
        ioctl(pc->fd_instructions, PERF_EVENT_IOC_DISABLE, 0);
        ret = read(pc->fd_instructions, &pc->instructions, sizeof(uint64_t));
        if (ret != sizeof(uint64_t)) pc->instructions = 0;
    }
    if (pc->fd_cycles >= 0) {
        ioctl(pc->fd_cycles, PERF_EVENT_IOC_DISABLE, 0);
        ret = read(pc->fd_cycles, &pc->cycles, sizeof(uint64_t));
        if (ret != sizeof(uint64_t)) pc->cycles = 0;
    }
    if (pc->fd_l1_dcache_misses >= 0) {
        ioctl(pc->fd_l1_dcache_misses, PERF_EVENT_IOC_DISABLE, 0);
        ret = read(pc->fd_l1_dcache_misses, &pc->l1_dcache_misses, sizeof(uint64_t));
        if (ret != sizeof(uint64_t)) pc->l1_dcache_misses = 0;
    }
    if (pc->fd_llc_misses >= 0) {
        ioctl(pc->fd_llc_misses, PERF_EVENT_IOC_DISABLE, 0);
        ret = read(pc->fd_llc_misses, &pc->llc_misses, sizeof(uint64_t));
        if (ret != sizeof(uint64_t)) pc->llc_misses = 0;
    }
    if (pc->fd_branches >= 0) {
        ioctl(pc->fd_branches, PERF_EVENT_IOC_DISABLE, 0);
        ret = read(pc->fd_branches, &pc->branches, sizeof(uint64_t));
        if (ret != sizeof(uint64_t)) pc->branches = 0;
    }
    if (pc->fd_branch_misses >= 0) {
        ioctl(pc->fd_branch_misses, PERF_EVENT_IOC_DISABLE, 0);
        ret = read(pc->fd_branch_misses, &pc->branch_misses, sizeof(uint64_t));
        if (ret != sizeof(uint64_t)) pc->branch_misses = 0;
    }
}

/*
 * Close all counter file descriptors.
 */
void perf_counters_close(perf_counters_t *pc) {
    if (pc->fd_instructions >= 0) close(pc->fd_instructions);
    if (pc->fd_cycles >= 0) close(pc->fd_cycles);
    if (pc->fd_l1_dcache_misses >= 0) close(pc->fd_l1_dcache_misses);
    if (pc->fd_llc_misses >= 0) close(pc->fd_llc_misses);
    if (pc->fd_branches >= 0) close(pc->fd_branches);
    if (pc->fd_branch_misses >= 0) close(pc->fd_branch_misses);
}

/*
 * Print CSV header for perf counters.
 */
void perf_counters_print_csv_header(FILE *out) {
    fprintf(out, "instructions,cycles,ipc,l1_dcache_misses,llc_misses,");
    fprintf(out, "branches,branch_misses,branch_miss_rate\n");
}

/*
 * Print perf counter values in CSV format.
 */
void perf_counters_print_csv(FILE *out, const perf_counters_t *pc) {
    double ipc = pc->cycles > 0 ? (double)pc->instructions / pc->cycles : 0.0;
    double branch_miss_rate = pc->branches > 0 ? 
        (double)pc->branch_misses / pc->branches : 0.0;
    
    fprintf(out, "%lu,%lu,%.3f,%lu,%lu,%lu,%lu,%.6f\n",
            pc->instructions,
            pc->cycles,
            ipc,
            pc->l1_dcache_misses,
            pc->llc_misses,
            pc->branches,
            pc->branch_misses,
            branch_miss_rate);
}
