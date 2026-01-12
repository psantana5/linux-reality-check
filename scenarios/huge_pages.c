/*
 * Huge Pages vs Normal Pages Benchmark
 * 
 * Compares performance of huge pages (2MB or 1GB) vs normal pages (4KB).
 * Huge pages reduce TLB pressure and page table overhead.
 *
 * Expected Results:
 * - Normal pages: Higher TLB misses on large working sets
 * - Huge pages (2MB): 512x fewer TLB entries needed
 * - Huge pages (1GB): 262144x fewer TLB entries needed
 * - Performance gain: 10-30% for memory-intensive workloads
 *
 * What This Tests:
 * - TLB efficiency with different page sizes
 * - Kernel huge page support
 * - Memory allocation overhead
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <sys/mman.h>
#include <unistd.h>

#define NORMAL_PAGE_SIZE (4 * 1024)           // 4 KB
#define HUGE_PAGE_SIZE (2 * 1024 * 1024)      // 2 MB
#define ITERATIONS 10000000

typedef enum {
    PAGE_TYPE_NORMAL,
    PAGE_TYPE_HUGE_2MB,
    PAGE_TYPE_TRANSPARENT_HUGE
} page_type_t;

static inline uint64_t get_time_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1000000000ULL + ts.tv_nsec;
}

static inline void compiler_barrier(void) {
    __asm__ __volatile__("" ::: "memory");
}

void* allocate_memory(size_t size, page_type_t page_type) {
    void *ptr;
    
    switch (page_type) {
        case PAGE_TYPE_NORMAL:
            // Standard allocation
            ptr = mmap(NULL, size,
                      PROT_READ | PROT_WRITE,
                      MAP_PRIVATE | MAP_ANONYMOUS,
                      -1, 0);
            break;
            
        case PAGE_TYPE_HUGE_2MB:
            // Explicit huge pages
            ptr = mmap(NULL, size,
                      PROT_READ | PROT_WRITE,
                      MAP_PRIVATE | MAP_ANONYMOUS | MAP_HUGETLB,
                      -1, 0);
            if (ptr == MAP_FAILED) {
                // Fallback to normal if huge pages not available
                fprintf(stderr, "Warning: Huge pages not available, using normal pages\n");
                ptr = mmap(NULL, size,
                          PROT_READ | PROT_WRITE,
                          MAP_PRIVATE | MAP_ANONYMOUS,
                          -1, 0);
            }
            break;
            
        case PAGE_TYPE_TRANSPARENT_HUGE:
            // Let kernel decide (Transparent Huge Pages)
            ptr = mmap(NULL, size,
                      PROT_READ | PROT_WRITE,
                      MAP_PRIVATE | MAP_ANONYMOUS,
                      -1, 0);
            if (ptr != MAP_FAILED) {
                // Advise kernel to use huge pages if possible
                madvise(ptr, size, MADV_HUGEPAGE);
            }
            break;
    }
    
    return ptr;
}

uint64_t measure_memory_access(char *buffer, size_t size) {
    uint64_t sum = 0;
    uint64_t start = get_time_ns();
    
    // Random-like access pattern to stress TLB
    size_t stride = 4096; // One page
    
    for (size_t i = 0; i < ITERATIONS; i++) {
        size_t offset = (i * stride) % size;
        sum += buffer[offset];
        compiler_barrier();
    }
    
    uint64_t end = get_time_ns();
    
    // Prevent optimization
    if (sum == 0xDEADBEEF) {
        printf("Impossible\n");
    }
    
    return end - start;
}

const char* page_type_name(page_type_t type) {
    switch (type) {
        case PAGE_TYPE_NORMAL: return "normal_4KB";
        case PAGE_TYPE_HUGE_2MB: return "huge_2MB";
        case PAGE_TYPE_TRANSPARENT_HUGE: return "transparent_huge";
        default: return "unknown";
    }
}

void run_experiment(FILE *csv) {
    // Test different working set sizes
    size_t sizes[] = {
        4 * 1024 * 1024,   // 4 MB
        16 * 1024 * 1024,  // 16 MB
        64 * 1024 * 1024,  // 64 MB
        256 * 1024 * 1024, // 256 MB
    };
    
    page_type_t page_types[] = {
        PAGE_TYPE_NORMAL,
        PAGE_TYPE_TRANSPARENT_HUGE,
        PAGE_TYPE_HUGE_2MB
    };
    
    int num_sizes = sizeof(sizes) / sizeof(sizes[0]);
    int num_types = sizeof(page_types) / sizeof(page_types[0]);
    int run = 0;
    
    for (int s = 0; s < num_sizes; s++) {
        size_t size = sizes[s];
        
        printf("Testing %zu MB working set...\n", size / (1024 * 1024));
        
        for (int t = 0; t < num_types; t++) {
            page_type_t page_type = page_types[t];
            
            // Allocate memory
            char *buffer = allocate_memory(size, page_type);
            if (buffer == MAP_FAILED) {
                fprintf(stderr, "Failed to allocate %zu MB with %s\n",
                       size / (1024 * 1024), page_type_name(page_type));
                continue;
            }
            
            // Touch all memory to ensure allocation
            memset(buffer, 0xAA, size);
            
            // Warm up
            measure_memory_access(buffer, size);
            
            // Actual measurement
            uint64_t start_ts = get_time_ns();
            uint64_t runtime = measure_memory_access(buffer, size);
            
            double ns_per_access = (double)runtime / ITERATIONS;
            
            fprintf(csv, "%d,%s_%zuMB,%lu,%lu,0,0,0,0,-1,-1,%.2f\n",
                   run++,
                   page_type_name(page_type),
                   size / (1024 * 1024),
                   start_ts,
                   runtime,
                   ns_per_access);
            
            munmap(buffer, size);
        }
    }
}

int main(void) {
    FILE *csv = fopen("data/huge_pages.csv", "w");
    if (!csv) {
        perror("fopen");
        return 1;
    }
    
    fprintf(csv, "run,workload_type,timestamp_ns,runtime_ns,"
                 "voluntary_ctxt_switches,nonvoluntary_ctxt_switches,"
                 "minor_page_faults,major_page_faults,start_cpu,end_cpu,"
                 "ns_per_access\n");
    
    printf("Huge Pages vs Normal Pages Benchmark\n");
    printf("====================================\n\n");
    printf("Comparing 4KB pages vs 2MB huge pages...\n");
    printf("Iterations per test: %d\n\n", ITERATIONS);
    
    run_experiment(csv);
    
    fclose(csv);
    
    printf("\nResults saved to data/huge_pages.csv\n");
    printf("\nExpected patterns:\n");
    printf("  Normal pages: Baseline performance\n");
    printf("  Huge pages: 10-30%% faster for large working sets\n");
    printf("  Transparent huge pages: Automatic optimization\n");
    printf("\nNote: Huge pages require kernel support and configuration\n");
    printf("      Check: cat /proc/meminfo | grep Huge\n");
    
    return 0;
}
