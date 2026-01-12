/*
 * metrics.c - Raw metric collection
 *
 * Purpose:
 *   Collect kernel-provided performance signals.
 *   No interpretation, no filtering, no aggregation.
 *   Pure data extraction.
 */

#define _GNU_SOURCE
#include <time.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <sched.h>

typedef struct {
    uint64_t timestamp_ns;
    uint64_t runtime_ns;
    uint64_t voluntary_ctxt_switches;
    uint64_t nonvoluntary_ctxt_switches;
    uint64_t minor_page_faults;
    uint64_t major_page_faults;
    int start_cpu;
    int end_cpu;
} workload_metrics_t;

/*
 * Get monotonic raw timestamp in nanoseconds.
 *
 * Justification for syscall:
 *   clock_gettime() is required for accurate timing.
 *   CLOCK_MONOTONIC_RAW is unaffected by NTP adjustments.
 *   Called only at workload boundaries, not in hot path.
 */
static uint64_t get_timestamp_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC_RAW, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + ts.tv_nsec;
}

/*
 * Read context switch counts from /proc/self/status.
 *
 * Justification for file I/O:
 *   /proc is the only interface to these kernel counters.
 *   Called only before/after workload, not in hot path.
 */
static void read_ctxt_switches(uint64_t *voluntary, uint64_t *nonvoluntary) {
    FILE *f = fopen("/proc/self/status", "r");
    if (!f) {
        *voluntary = 0;
        *nonvoluntary = 0;
        return;
    }
    
    char line[256];
    while (fgets(line, sizeof(line), f)) {
        if (strncmp(line, "voluntary_ctxt_switches:", 24) == 0) {
            sscanf(line + 24, "%lu", voluntary);
        } else if (strncmp(line, "nonvoluntary_ctxt_switches:", 27) == 0) {
            sscanf(line + 27, "%lu", nonvoluntary);
        }
    }
    
    fclose(f);
}

/*
 * Read page fault counts from /proc/self/stat.
 *
 * Justification for file I/O:
 *   /proc is the only interface to these kernel counters.
 *   Called only before/after workload, not in hot path.
 */
static void read_page_faults(uint64_t *minor, uint64_t *major) {
    FILE *f = fopen("/proc/self/stat", "r");
    if (!f) {
        *minor = 0;
        *major = 0;
        return;
    }
    
    // Read /proc/self/stat line
    char buf[1024];
    if (!fgets(buf, sizeof(buf), f)) {
        *minor = 0;
        *major = 0;
        fclose(f);
        return;
    }
    
    // Parse: skip 9 fields, read minflt (field 10), skip 1, read majflt (field 12)
    unsigned long minflt = 0, majflt = 0;
    char *p = buf;
    
    // Skip fields 1-9
    for (int i = 0; i < 9 && *p; i++) {
        while (*p && *p != ' ') p++;
        if (*p) p++;  // Skip space
    }
    
    // Read field 10 (minflt)
    if (*p) {
        minflt = strtoul(p, &p, 10);
        if (*p) p++;  // Skip space
        
        // Skip field 11
        while (*p && *p != ' ') p++;
        if (*p) p++;
        
        // Read field 12 (majflt)
        majflt = strtoul(p, NULL, 10);
    }
    
    *minor = minflt;
    *major = majflt;
    
    fclose(f);
}

/*
 * Initialize metrics collection before workload.
 */
void metrics_init(workload_metrics_t *m) {
    memset(m, 0, sizeof(workload_metrics_t));
    
    m->timestamp_ns = get_timestamp_ns();
    read_ctxt_switches(&m->voluntary_ctxt_switches, &m->nonvoluntary_ctxt_switches);
    read_page_faults(&m->minor_page_faults, &m->major_page_faults);
    m->start_cpu = sched_getcpu();
}

/*
 * Finalize metrics collection after workload.
 * Calculates deltas from initial values.
 */
void metrics_finish(workload_metrics_t *m) {
    uint64_t end_ts = get_timestamp_ns();
    uint64_t vol_ctxt, nonvol_ctxt;
    uint64_t minor_pf, major_pf;
    
    read_ctxt_switches(&vol_ctxt, &nonvol_ctxt);
    read_page_faults(&minor_pf, &major_pf);
    
    m->runtime_ns = end_ts - m->timestamp_ns;
    m->voluntary_ctxt_switches = vol_ctxt - m->voluntary_ctxt_switches;
    m->nonvoluntary_ctxt_switches = nonvol_ctxt - m->nonvoluntary_ctxt_switches;
    m->minor_page_faults = minor_pf - m->minor_page_faults;
    m->major_page_faults = major_pf - m->major_page_faults;
    m->end_cpu = sched_getcpu();
    m->timestamp_ns = end_ts;
}

/*
 * Output metrics in CSV format.
 * No interpretation, just raw numbers.
 */
void metrics_print_csv_header(FILE *out) {
    fprintf(out, "timestamp_ns,runtime_ns,voluntary_ctxt_switches,nonvoluntary_ctxt_switches,");
    fprintf(out, "minor_page_faults,major_page_faults,start_cpu,end_cpu\n");
}

void metrics_print_csv(FILE *out, const workload_metrics_t *m) {
    fprintf(out, "%lu,%lu,%lu,%lu,%lu,%lu,%d,%d\n",
            m->timestamp_ns,
            m->runtime_ns,
            m->voluntary_ctxt_switches,
            m->nonvoluntary_ctxt_switches,
            m->minor_page_faults,
            m->major_page_faults,
            m->start_cpu,
            m->end_cpu);
}
