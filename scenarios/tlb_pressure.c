/*
 * TLB Pressure Benchmark
 * 
 * Measures the performance impact of TLB (Translation Lookaside Buffer) misses.
 * TLB caches virtual-to-physical address translations. When working set exceeds
 * TLB capacity, performance degrades due to page table walks.
 *
 * Expected Results:
 * - Small arrays (fits in TLB): ~2-3ns per access
 * - Large arrays (TLB thrashing): ~20-50ns per access
 * - Huge pages: Reduced TLB misses, better performance
 *
 * What This Tests:
 * - TLB capacity (typically 64-512 entries)
 * - Page table walk cost
 * - Memory access patterns vs TLB
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <sys/mman.h>
#include <unistd.h>

#define PAGE_SIZE 4096
#define ITERATIONS 1000000

typedef struct {
    uint64_t timestamp_ns;
    uint64_t runtime_ns;
    int voluntary_ctxt_switches;
    int nonvoluntary_ctxt_switches;
    size_t working_set_kb;
    int num_pages;
    int stride;
} measurement_t;

static inline uint64_t get_time_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1000000000ULL + ts.tv_nsec;
}

// Prevent compiler optimization
static inline void compiler_barrier(void) {
    __asm__ __volatile__("" ::: "memory");
}

uint64_t measure_tlb_pressure(char *buffer, size_t size, int stride) {
    uint64_t sum = 0;
    uint64_t start = get_time_ns();
    
    // Touch pages with given stride
    for (size_t i = 0; i < ITERATIONS; i++) {
        size_t offset = (i * stride * PAGE_SIZE) % size;
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

void run_experiment(FILE *csv) {
    // Test different working set sizes
    size_t sizes[] = {
        16 * 1024,        // 16 KB - fits in TLB (4 pages)
        64 * 1024,        // 64 KB - still ok (16 pages)
        256 * 1024,       // 256 KB - borderline (64 pages)
        1 * 1024 * 1024,  // 1 MB - TLB pressure (256 pages)
        4 * 1024 * 1024,  // 4 MB - heavy TLB misses (1024 pages)
        16 * 1024 * 1024, // 16 MB - severe TLB thrashing (4096 pages)
    };
    
    int num_sizes = sizeof(sizes) / sizeof(sizes[0]);
    
    // Test different stride patterns
    int strides[] = {1, 2, 4, 8, 16}; // Pages between accesses
    int num_strides = sizeof(strides) / sizeof(strides[0]);
    
    int run = 0;
    
    for (int s = 0; s < num_sizes; s++) {
        size_t size = sizes[s];
        
        // Allocate buffer
        char *buffer = mmap(NULL, size, 
                           PROT_READ | PROT_WRITE,
                           MAP_PRIVATE | MAP_ANONYMOUS,
                           -1, 0);
        
        if (buffer == MAP_FAILED) {
            perror("mmap");
            continue;
        }
        
        // Touch all pages to ensure allocation
        memset(buffer, 0xAA, size);
        
        for (int st = 0; st < num_strides; st++) {
            int stride = strides[st];
            
            uint64_t start_ts = get_time_ns();
            uint64_t runtime = measure_tlb_pressure(buffer, size, stride);
            
            // Calculate per-access time
            double ns_per_access = (double)runtime / ITERATIONS;
            
            fprintf(csv, "%d,tlb_pressure_%zuKB_stride%d,%lu,%lu,0,0,0,0,-1,-1,%.2f\n",
                   run++,
                   size / 1024,
                   stride,
                   start_ts,
                   runtime,
                   ns_per_access);
        }
        
        munmap(buffer, size);
    }
}

int main(void) {
    FILE *csv = fopen("data/tlb_pressure.csv", "w");
    if (!csv) {
        perror("fopen");
        return 1;
    }
    
    fprintf(csv, "run,workload_type,timestamp_ns,runtime_ns,"
                 "voluntary_ctxt_switches,nonvoluntary_ctxt_switches,"
                 "minor_page_faults,major_page_faults,start_cpu,end_cpu,"
                 "ns_per_access\n");
    
    printf("TLB Pressure Benchmark\n");
    printf("======================\n\n");
    printf("Testing TLB behavior with different working set sizes...\n");
    printf("Iterations per test: %d\n\n", ITERATIONS);
    
    run_experiment(csv);
    
    fclose(csv);
    
    printf("\nResults saved to data/tlb_pressure.csv\n");
    printf("\nExpected patterns:\n");
    printf("  Small working sets (16-64KB): Low TLB pressure, ~2-5 ns/access\n");
    printf("  Large working sets (1-16MB): High TLB misses, ~20-50 ns/access\n");
    printf("  Larger stride: More page table walks, higher latency\n");
    
    return 0;
}
