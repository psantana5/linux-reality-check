/*
 * File I/O Patterns Benchmark
 * 
 * Measures file I/O performance with different access patterns.
 * Tests sequential, random, buffered, direct, and memory-mapped I/O.
 *
 * Expected Results:
 * - Sequential buffered: 1-5 GB/s (page cache)
 * - Random buffered: 10-100 MB/s (seeks + caching)
 * - Direct I/O: Similar to buffered for sequential, bypasses cache
 * - mmap: Fast for random access, lazy loading
 * - tmpfs: Near-memory speed (no disk)
 *
 * What This Tests:
 * - Page cache effectiveness
 * - Disk vs memory performance
 * - I/O buffering strategies
 * - Random vs sequential access
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/mman.h>

#define FILE_SIZE (64 * 1024 * 1024)  // 64 MB
#define BLOCK_SIZE 4096
#define ITERATIONS 100

static inline uint64_t get_time_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1000000000ULL + ts.tv_nsec;
}

// Sequential read with standard I/O
uint64_t test_sequential_read(const char *filename) {
    FILE *f = fopen(filename, "r");
    if (!f) {
        perror("fopen");
        return 0;
    }
    
    char buffer[BLOCK_SIZE];
    uint64_t bytes_read = 0;
    
    uint64_t start = get_time_ns();
    
    while (fread(buffer, 1, BLOCK_SIZE, f) > 0) {
        bytes_read += BLOCK_SIZE;
    }
    
    uint64_t runtime = get_time_ns() - start;
    
    fclose(f);
    return runtime;
}

// Sequential write
uint64_t test_sequential_write(const char *filename) {
    FILE *f = fopen(filename, "w");
    if (!f) {
        perror("fopen");
        return 0;
    }
    
    char buffer[BLOCK_SIZE];
    memset(buffer, 0xAA, BLOCK_SIZE);
    
    uint64_t start = get_time_ns();
    
    for (size_t i = 0; i < FILE_SIZE / BLOCK_SIZE; i++) {
        fwrite(buffer, 1, BLOCK_SIZE, f);
    }
    
    fflush(f);
    uint64_t runtime = get_time_ns() - start;
    
    fclose(f);
    return runtime;
}

// Random read with fseek
uint64_t test_random_read(const char *filename) {
    FILE *f = fopen(filename, "r");
    if (!f) {
        perror("fopen");
        return 0;
    }
    
    char buffer[BLOCK_SIZE];
    unsigned int seed = 12345;
    
    uint64_t start = get_time_ns();
    
    for (int i = 0; i < ITERATIONS; i++) {
        off_t offset = (rand_r(&seed) % (FILE_SIZE / BLOCK_SIZE)) * BLOCK_SIZE;
        fseek(f, offset, SEEK_SET);
        fread(buffer, 1, BLOCK_SIZE, f);
    }
    
    uint64_t runtime = get_time_ns() - start;
    
    fclose(f);
    return runtime;
}

// Direct I/O (bypasses page cache)
uint64_t test_direct_io_read(const char *filename) {
    int fd = open(filename, O_RDONLY | O_DIRECT);
    if (fd < 0) {
        perror("open O_DIRECT");
        return 0;
    }
    
    // Direct I/O requires aligned buffers
    void *buffer = aligned_alloc(BLOCK_SIZE, BLOCK_SIZE);
    if (!buffer) {
        close(fd);
        return 0;
    }
    
    uint64_t start = get_time_ns();
    
    size_t bytes_read = 0;
    while (bytes_read < FILE_SIZE) {
        ssize_t ret = read(fd, buffer, BLOCK_SIZE);
        if (ret <= 0) break;
        bytes_read += ret;
    }
    
    uint64_t runtime = get_time_ns() - start;
    
    free(buffer);
    close(fd);
    return runtime;
}

// Memory-mapped I/O
uint64_t test_mmap_read(const char *filename) {
    int fd = open(filename, O_RDONLY);
    if (fd < 0) {
        perror("open");
        return 0;
    }
    
    void *map = mmap(NULL, FILE_SIZE, PROT_READ, MAP_PRIVATE, fd, 0);
    if (map == MAP_FAILED) {
        perror("mmap");
        close(fd);
        return 0;
    }
    
    char buffer[BLOCK_SIZE];
    uint64_t sum = 0;
    
    uint64_t start = get_time_ns();
    
    // Sequential access through mmap
    char *ptr = (char*)map;
    for (size_t i = 0; i < FILE_SIZE; i += BLOCK_SIZE) {
        sum += ptr[i];
    }
    
    uint64_t runtime = get_time_ns() - start;
    
    // Prevent optimization
    if (sum == 0xDEADBEEF) printf("!");
    
    munmap(map, FILE_SIZE);
    close(fd);
    return runtime;
}

// Random access through mmap
uint64_t test_mmap_random(const char *filename) {
    int fd = open(filename, O_RDONLY);
    if (fd < 0) {
        perror("open");
        return 0;
    }
    
    void *map = mmap(NULL, FILE_SIZE, PROT_READ, MAP_PRIVATE, fd, 0);
    if (map == MAP_FAILED) {
        perror("mmap");
        close(fd);
        return 0;
    }
    
    unsigned int seed = 12345;
    uint64_t sum = 0;
    char *ptr = (char*)map;
    
    uint64_t start = get_time_ns();
    
    for (int i = 0; i < ITERATIONS * 100; i++) {
        size_t offset = rand_r(&seed) % FILE_SIZE;
        sum += ptr[offset];
    }
    
    uint64_t runtime = get_time_ns() - start;
    
    if (sum == 0xDEADBEEF) printf("!");
    
    munmap(map, FILE_SIZE);
    close(fd);
    return runtime;
}

void create_test_file(const char *filename) {
    printf("Creating test file (%d MB)...\n", FILE_SIZE / (1024 * 1024));
    
    FILE *f = fopen(filename, "w");
    if (!f) {
        perror("fopen");
        return;
    }
    
    char buffer[BLOCK_SIZE];
    memset(buffer, 0xAA, BLOCK_SIZE);
    
    for (size_t i = 0; i < FILE_SIZE / BLOCK_SIZE; i++) {
        fwrite(buffer, 1, BLOCK_SIZE, f);
    }
    
    fclose(f);
}

void run_experiment(FILE *csv) {
    const char *tmpfile = "/tmp/lrc_io_test.dat";
    
    create_test_file(tmpfile);
    
    int run = 0;
    
    struct {
        const char *name;
        uint64_t (*func)(const char*);
    } tests[] = {
        {"sequential_read", test_sequential_read},
        {"sequential_write", test_sequential_write},
        {"random_read", test_random_read},
        {"direct_io_read", test_direct_io_read},
        {"mmap_sequential", test_mmap_read},
        {"mmap_random", test_mmap_random},
    };
    
    int num_tests = sizeof(tests) / sizeof(tests[0]);
    
    for (int t = 0; t < num_tests; t++) {
        printf("Testing %s...\n", tests[t].name);
        
        uint64_t start_ts = get_time_ns();
        uint64_t runtime = tests[t].func(tmpfile);
        
        if (runtime > 0) {
            double throughput_mbs = (FILE_SIZE / (1024.0 * 1024.0)) / (runtime / 1e9);
            
            fprintf(csv, "%d,%s,%lu,%lu,0,0,0,0,-1,-1,%.2f\n",
                   run++, tests[t].name, start_ts, runtime, throughput_mbs);
        }
    }
    
    // Cleanup
    unlink(tmpfile);
}

int main(void) {
    FILE *csv = fopen("data/file_io_patterns.csv", "w");
    if (!csv) {
        perror("fopen");
        return 1;
    }
    
    fprintf(csv, "run,workload_type,timestamp_ns,runtime_ns,"
                 "voluntary_ctxt_switches,nonvoluntary_ctxt_switches,"
                 "minor_page_faults,major_page_faults,start_cpu,end_cpu,"
                 "throughput_mbs\n");
    
    printf("File I/O Patterns Benchmark\n");
    printf("===========================\n\n");
    printf("File size: %d MB\n", FILE_SIZE / (1024 * 1024));
    printf("Block size: %d bytes\n\n", BLOCK_SIZE);
    
    run_experiment(csv);
    
    fclose(csv);
    
    printf("\nResults saved to data/file_io_patterns.csv\n");
    printf("\nExpected patterns:\n");
    printf("  Sequential buffered: 1-5 GB/s (page cache)\n");
    printf("  Random buffered: 10-100 MB/s (seeks)\n");
    printf("  Direct I/O: Bypasses cache, disk speed\n");
    printf("  mmap sequential: Similar to buffered read\n");
    printf("  mmap random: Efficient for small random accesses\n");
    printf("\nNote: Using /tmp (tmpfs) for fastest results\n");
    
    return 0;
}
