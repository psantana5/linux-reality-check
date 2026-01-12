CC = gcc
CFLAGS = -O2 -march=native -Wall -Wextra -std=c11
LDFLAGS = -L../core -llrc -lrt

CORE_LIB = ../core/liblrc.a
SCENARIOS = pinned nice_levels cache_hierarchy latency_vs_bandwidth cache_analysis numa_locality syscall_overhead null_baseline lock_scaling realistic_patterns tlb_pressure huge_pages false_sharing branch_prediction atomic_operations simd_performance memory_bandwidth process_creation rwlock_scaling file_io_patterns

all: $(CORE_LIB) $(SCENARIOS)

$(CORE_LIB):
	$(MAKE) -C ../core

pinned: pinned.c $(CORE_LIB)
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

nice_levels: nice_levels.c $(CORE_LIB)
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

cache_hierarchy: cache_hierarchy.c $(CORE_LIB)
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

latency_vs_bandwidth: latency_vs_bandwidth.c $(CORE_LIB)
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

cache_analysis: cache_analysis.c $(CORE_LIB)
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

numa_locality: numa_locality.c $(CORE_LIB)
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

syscall_overhead: syscall_overhead.c $(CORE_LIB)
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

null_baseline: null_baseline.c $(CORE_LIB)
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

lock_scaling: lock_scaling.c $(CORE_LIB)
	$(CC) $(CFLAGS) -pthread -o $@ $< $(LDFLAGS)

realistic_patterns: realistic_patterns.c $(CORE_LIB)
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

tlb_pressure: tlb_pressure.c $(CORE_LIB)
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

huge_pages: huge_pages.c $(CORE_LIB)
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

false_sharing: false_sharing.c $(CORE_LIB)
	$(CC) $(CFLAGS) -pthread -o $@ $< $(LDFLAGS)

branch_prediction: branch_prediction.c $(CORE_LIB)
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

atomic_operations: atomic_operations.c $(CORE_LIB)
	$(CC) $(CFLAGS) -pthread -o $@ $< $(LDFLAGS)

simd_performance: simd_performance.c $(CORE_LIB)
	$(CC) $(CFLAGS) -mavx2 -o $@ $< $(LDFLAGS)

memory_bandwidth: memory_bandwidth.c $(CORE_LIB)
	$(CC) $(CFLAGS) -pthread -o $@ $< $(LDFLAGS)

process_creation: process_creation.c $(CORE_LIB)
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

rwlock_scaling: rwlock_scaling.c $(CORE_LIB)
	$(CC) $(CFLAGS) -pthread -o $@ $< $(LDFLAGS)

file_io_patterns: file_io_patterns.c $(CORE_LIB)
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

clean:
	rm -f $(SCENARIOS)

.PHONY: all clean
