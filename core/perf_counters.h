#ifndef PERF_COUNTERS_H
#define PERF_COUNTERS_H

#include <stdint.h>
#include <stdio.h>

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

int perf_counters_init(perf_counters_t *pc);
void perf_counters_start(perf_counters_t *pc);
void perf_counters_stop(perf_counters_t *pc);
void perf_counters_close(perf_counters_t *pc);
void perf_counters_print_csv_header(FILE *out);
void perf_counters_print_csv(FILE *out, const perf_counters_t *pc);

#endif
