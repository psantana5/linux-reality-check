#ifndef METRICS_H
#define METRICS_H

#include <stdint.h>
#include <stdio.h>

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

void metrics_init(workload_metrics_t *m);
void metrics_finish(workload_metrics_t *m);
void metrics_print_csv_header(FILE *out);
void metrics_print_csv(FILE *out, const workload_metrics_t *m);

#endif
