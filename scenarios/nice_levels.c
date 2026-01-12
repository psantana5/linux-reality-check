/*
 * nice_levels.c - Scheduling priority experiment
 *
 * Hypothesis:
 *   Nice level affects scheduling quantum and preemption frequency.
 *   Lower nice (higher priority) should show fewer involuntary
 *   context switches under system load.
 *
 * Method:
 *   Run CPU workload at different nice levels:
 *   - Nice 0 (default)
 *   - Nice -10 (higher priority, requires privileges)
 *   - Nice 10 (lower priority)
 *   - Nice 19 (lowest priority)
 *
 * Variables:
 *   - Nice level (controlled)
 *   - Workload iterations (fixed)
 *
 * Expected outcome:
 *   Under no contention:
 *   - Similar runtime across nice levels
 *   - Low context switches regardless
 *
 *   Under contention:
 *   - Nice -10: fewest involuntary switches
 *   - Nice 19: most involuntary switches
 *
 * Limitations:
 *   - Requires other system load to show effect
 *   - Nice -10 requires CAP_SYS_NICE or root
 *   - Does not test real-time scheduling policies
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include "../core/metrics.h"

extern uint64_t cpu_spin(uint64_t iterations);
extern int set_nice(int nice_value);

#define ITERATIONS 500000000ULL
#define RUNS 10

static const int nice_levels[] = {0, -10, 10, 19};
static const char *nice_names[] = {"nice0", "nice-10", "nice10", "nice19"};

int main(void) {
    workload_metrics_t metrics;
    FILE *out = fopen("../data/nice_levels.csv", "w");
    
    if (!out) {
        perror("fopen");
        return 1;
    }
    
    fprintf(out, "run,nice_level,");
    metrics_print_csv_header(out);
    
    printf("Running nice level experiment...\n");
    printf("Note: nice -10 requires privileges, will skip if denied\n\n");
    
    for (size_t i = 0; i < sizeof(nice_levels) / sizeof(nice_levels[0]); i++) {
        int nice_val = nice_levels[i];
        const char *name = nice_names[i];
        
        if (set_nice(nice_val) == -1) {
            printf("Warning: Cannot set nice to %d (permission denied?)\n", nice_val);
            continue;
        }
        
        printf("Testing nice %d...\n", nice_val);
        
        for (int run = 0; run < RUNS; run++) {
            fprintf(out, "%d,%s,", run, name);
            metrics_init(&metrics);
            uint64_t result = cpu_spin(ITERATIONS);
            metrics_finish(&metrics);
            metrics_print_csv(out, &metrics);
            
            (void)result;
        }
    }
    
    fclose(out);
    printf("\nResults saved to ../data/nice_levels.csv\n");
    
    return 0;
}
