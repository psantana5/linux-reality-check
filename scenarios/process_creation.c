/*
 * Process Creation Overhead Benchmark
 * 
 * Measures the cost of creating processes via fork(), vfork(), and clone().
 * Process creation is a fundamental operation with significant overhead.
 *
 * Expected Results:
 * - fork(): 50-200 microseconds (full copy-on-write setup)
 * - vfork(): 5-20 microseconds (minimal setup, shared address space)
 * - clone(CLONE_VM): 10-30 microseconds (thread-like)
 * - posix_spawn(): Similar to vfork()
 *
 * What This Tests:
 * - Process creation mechanisms
 * - Copy-on-write overhead
 * - Virtual memory setup cost
 * - Scheduler interaction
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include <unistd.h>
#include <sys/wait.h>
#include <sys/types.h>
#include <sched.h>
#include <spawn.h>

#define ITERATIONS 1000

extern char **environ;

static inline uint64_t get_time_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1000000000ULL + ts.tv_nsec;
}

// Child process does minimal work
static void child_minimal(void) {
    _exit(0);
}

// Test fork()
uint64_t test_fork(void) {
    uint64_t start = get_time_ns();
    
    pid_t pid = fork();
    
    if (pid == 0) {
        // Child
        child_minimal();
    } else if (pid > 0) {
        // Parent
        waitpid(pid, NULL, 0);
    } else {
        perror("fork");
        return 0;
    }
    
    return get_time_ns() - start;
}

// Test vfork()
uint64_t test_vfork(void) {
    uint64_t start = get_time_ns();
    
    pid_t pid = vfork();
    
    if (pid == 0) {
        // Child - must not modify parent's memory!
        _exit(0);
    } else if (pid > 0) {
        // Parent
        waitpid(pid, NULL, 0);
    } else {
        perror("vfork");
        return 0;
    }
    
    return get_time_ns() - start;
}

// Clone function for thread-like process
static int clone_child_func(void *arg) {
    (void)arg;
    return 0;
}

// Test clone() with CLONE_VM (thread-like)
uint64_t test_clone_vm(void) {
    // Allocate stack for child
    const size_t stack_size = 1024 * 1024;  // 1 MB
    void *stack = malloc(stack_size);
    if (!stack) {
        perror("malloc");
        return 0;
    }
    
    void *stack_top = (char*)stack + stack_size;
    
    uint64_t start = get_time_ns();
    
    pid_t pid = clone(clone_child_func, stack_top,
                     CLONE_VM | CLONE_FS | CLONE_FILES | CLONE_SIGHAND | SIGCHLD,
                     NULL);
    
    if (pid > 0) {
        waitpid(pid, NULL, 0);
    } else {
        perror("clone");
        free(stack);
        return 0;
    }
    
    uint64_t runtime = get_time_ns() - start;
    
    free(stack);
    return runtime;
}

// Test posix_spawn()
uint64_t test_posix_spawn(void) {
    uint64_t start = get_time_ns();
    
    pid_t pid;
    char *argv[] = {"/bin/true", NULL};
    
    int ret = posix_spawn(&pid, "/bin/true", NULL, NULL, argv, environ);
    
    if (ret == 0) {
        waitpid(pid, NULL, 0);
    } else {
        perror("posix_spawn");
        return 0;
    }
    
    return get_time_ns() - start;
}

void run_experiment(FILE *csv) {
    int run = 0;
    
    printf("Testing fork() (%d iterations)...\n", ITERATIONS);
    for (int i = 0; i < ITERATIONS; i++) {
        uint64_t start_ts = get_time_ns();
        uint64_t runtime = test_fork();
        
        if (runtime > 0) {
            double us = runtime / 1000.0;
            fprintf(csv, "%d,fork,%lu,%lu,0,0,0,0,-1,-1,%.2f\n",
                   run++, start_ts, runtime, us);
        }
    }
    
    printf("Testing vfork() (%d iterations)...\n", ITERATIONS);
    for (int i = 0; i < ITERATIONS; i++) {
        uint64_t start_ts = get_time_ns();
        uint64_t runtime = test_vfork();
        
        if (runtime > 0) {
            double us = runtime / 1000.0;
            fprintf(csv, "%d,vfork,%lu,%lu,0,0,0,0,-1,-1,%.2f\n",
                   run++, start_ts, runtime, us);
        }
    }
    
    printf("Testing clone(CLONE_VM) (%d iterations)...\n", ITERATIONS);
    for (int i = 0; i < ITERATIONS; i++) {
        uint64_t start_ts = get_time_ns();
        uint64_t runtime = test_clone_vm();
        
        if (runtime > 0) {
            double us = runtime / 1000.0;
            fprintf(csv, "%d,clone_vm,%lu,%lu,0,0,0,0,-1,-1,%.2f\n",
                   run++, start_ts, runtime, us);
        }
    }
    
    printf("Testing posix_spawn() (%d iterations)...\n", ITERATIONS / 10);
    for (int i = 0; i < ITERATIONS / 10; i++) {  // Fewer iterations (slower)
        uint64_t start_ts = get_time_ns();
        uint64_t runtime = test_posix_spawn();
        
        if (runtime > 0) {
            double us = runtime / 1000.0;
            fprintf(csv, "%d,posix_spawn,%lu,%lu,0,0,0,0,-1,-1,%.2f\n",
                   run++, start_ts, runtime, us);
        }
    }
}

int main(void) {
    FILE *csv = fopen("data/process_creation.csv", "w");
    if (!csv) {
        perror("fopen");
        return 1;
    }
    
    fprintf(csv, "run,workload_type,timestamp_ns,runtime_ns,"
                 "voluntary_ctxt_switches,nonvoluntary_ctxt_switches,"
                 "minor_page_faults,major_page_faults,start_cpu,end_cpu,"
                 "time_microseconds\n");
    
    printf("Process Creation Overhead Benchmark\n");
    printf("===================================\n\n");
    printf("Iterations: %d per test\n\n", ITERATIONS);
    
    run_experiment(csv);
    
    fclose(csv);
    
    printf("\nResults saved to data/process_creation.csv\n");
    printf("\nExpected patterns:\n");
    printf("  fork(): 50-200 us (full COW setup)\n");
    printf("  vfork(): 5-20 us (minimal, parent blocks)\n");
    printf("  clone(CLONE_VM): 10-30 us (thread-like)\n");
    printf("  posix_spawn(): Similar to vfork(), optimized for exec\n");
    printf("\nNote: Process creation is expensive compared to threads!\n");
    
    return 0;
}
