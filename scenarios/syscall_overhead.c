/*
 * syscall_overhead.c - System call overhead measurement
 *
 * Hypothesis:
 *   System calls have measurable overhead from user→kernel transition.
 *   Fast syscalls (getpid) should be <100ns.
 *   Moderate syscalls (read from /dev/null) should be <1μs.
 *   Complex syscalls (getrusage) should be <10μs.
 *
 * Method:
 *   Run tight loops calling different syscalls:
 *   1. getpid() - Fast path (vDSO accelerated on some systems)
 *   2. read(fd_devnull, buf, 1) - Simple kernel work
 *   3. getrusage(RUSAGE_SELF) - Moderate kernel work
 *   
 *   Compare against pure CPU loop baseline.
 *
 * Variables:
 *   - Syscall type (controlled)
 *   - Number of calls (fixed)
 *
 * Expected outcome:
 *   - getpid: 10-100ns per call (vDSO may be 10ns, real syscall 100ns)
 *   - read /dev/null: 200-500ns per call
 *   - getrusage: 500-2000ns per call
 *   - Baseline (no syscall): ~3-5ns per iteration
 *
 * Limitations:
 *   - Does not measure syscall variance under load
 *   - Some syscalls may be vDSO accelerated
 *   - Kernel version affects performance
 *   - Does not test all syscall types
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/resource.h>
#include <fcntl.h>
#include "../core/metrics.h"

extern int pin_to_cpu(int cpu);

#define ITERATIONS 1000000ULL
#define RUNS 10

int main(void) {
    workload_metrics_t metrics;
    FILE *out = fopen("../data/syscall_overhead.csv", "w");
    
    if (!out) {
        perror("fopen");
        return 1;
    }
    
    pin_to_cpu(0);
    
    fprintf(out, "run,syscall_type,");
    metrics_print_csv_header(out);
    
    printf("Running syscall overhead experiment...\n");
    printf("Measuring overhead of different system calls.\n\n");
    
    // Open /dev/null for read tests
    int fd_null = open("/dev/null", O_RDONLY);
    if (fd_null < 0) {
        perror("open /dev/null");
        return 1;
    }
    
    char dummy_buf[1];
    struct rusage dummy_rusage;
    
    // Baseline: empty loop (no syscall)
    printf("Baseline (no syscall)...\n");
    for (int run = 0; run < RUNS; run++) {
        fprintf(out, "%d,baseline,", run);
        metrics_init(&metrics);
        
        volatile uint64_t sum = 0;
        for (uint64_t i = 0; i < ITERATIONS; i++) {
            sum += i;
        }
        
        metrics_finish(&metrics);
        metrics_print_csv(out, &metrics);
        (void)sum;
    }
    
    // getpid() - fast syscall (may be vDSO)
    printf("getpid() - fast path...\n");
    for (int run = 0; run < RUNS; run++) {
        fprintf(out, "%d,getpid,", run);
        metrics_init(&metrics);
        
        for (uint64_t i = 0; i < ITERATIONS; i++) {
            (void)getpid();
        }
        
        metrics_finish(&metrics);
        metrics_print_csv(out, &metrics);
    }
    
    // read() from /dev/null - simple kernel work
    printf("read() from /dev/null - simple kernel work...\n");
    for (int run = 0; run < RUNS; run++) {
        fprintf(out, "%d,read_devnull,", run);
        metrics_init(&metrics);
        
        for (uint64_t i = 0; i < ITERATIONS; i++) {
            (void)read(fd_null, dummy_buf, 1);
        }
        
        metrics_finish(&metrics);
        metrics_print_csv(out, &metrics);
    }
    
    // getrusage() - moderate kernel work
    printf("getrusage() - moderate kernel work...\n");
    for (int run = 0; run < RUNS; run++) {
        fprintf(out, "%d,getrusage,", run);
        metrics_init(&metrics);
        
        for (uint64_t i = 0; i < ITERATIONS; i++) {
            (void)getrusage(RUSAGE_SELF, &dummy_rusage);
        }
        
        metrics_finish(&metrics);
        metrics_print_csv(out, &metrics);
    }
    
    close(fd_null);
    fclose(out);
    
    printf("\nResults saved to ../data/syscall_overhead.csv\n");
    printf("\nAnalyze with:\n");
    printf("  python3 ../analyze/parse.py ../data/syscall_overhead.csv\n");
    printf("\nExpected results:\n");
    printf("  baseline:      ~3-5 ns/call\n");
    printf("  getpid:        ~10-100 ns/call\n");
    printf("  read_devnull:  ~200-500 ns/call\n");
    printf("  getrusage:     ~500-2000 ns/call\n");
    
    return 0;
}
