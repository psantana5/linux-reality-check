# Measurement Methodology

This document describes the measurement techniques used by LRC and their limitations.

## Timing

### Clock Source
**Choice:** `CLOCK_MONOTONIC_RAW`

**Justification:**
- Not affected by NTP adjustments
- Monotonically increasing
- Nanosecond resolution
- Avoids VDSO overhead on modern kernels

**Limitations:**
- Does not account for CPU frequency scaling
- Subject to TSC synchronization issues on older systems
- Overhead: ~25-40ns per call on modern x86_64

**Alternative Rejected:** `CLOCK_MONOTONIC`
- Reason: Subject to NTP slew, introduces non-determinism

---

## Scheduler Metrics

### Context Switches
**Source:** `/proc/self/status`

**Fields:**
- `voluntary_ctxt_switches`: Task yielded CPU voluntarily
- `nonvoluntary_ctxt_switches`: Task was preempted

**Collection Method:**
- Read before workload
- Read after workload
- Report delta

**Limitations:**
- File I/O overhead (~10-50µs)
- Called outside hot path only
- Does not distinguish switch types (sleep vs yield)

---

### CPU Migration
**Source:** `sched_getcpu()`

**Method:**
- Record CPU at start
- Record CPU at end
- Flag migration if different

**Limitations:**
- Does not detect mid-execution migrations
- Provides coarse-grained view
- VDSO-accelerated, minimal overhead

---

## Memory Metrics

### Page Faults
**Source:** `/proc/self/stat`

**Fields:**
- Minor faults: Page was in memory, just not mapped
- Major faults: Disk I/O required

**Interpretation:**
- Minor faults: TLB misses, demand paging
- Major faults: Memory pressure, swapping

**Limitations:**
- Does not distinguish fault causes
- Cannot measure page-level access patterns

---

## Cache Behavior

### Current State
**Direct Measurement:** Not yet implemented

**Indirect Signals:**
- Runtime scaling with working set size
- Future: `perf` integration for hardware counters

**Limitations:**
- Hardware prefetcher obscures cache misses
- Cannot distinguish L1/L2/L3 misses without perf
- CPU microarchitecture specific

---

## Workload Design

### CPU Workload
**Implementation:** Integer arithmetic in tight loop

**Properties:**
- No memory allocation
- Predictable branches
- Fits in instruction cache
- Result accumulation prevents optimization

**Limitations:**
- Does not represent real workloads
- Compiler may optimize aggressively
- CPU frequency scaling affects results

---

### Memory Workload
**Implementation:** Sequential array traversal

**Properties:**
- Cache-friendly access pattern
- Minimal computation per access
- Controlled working set size

**Limitations:**
- Hardware prefetcher assists
- Does not test write-back behavior thoroughly
- TLB effects at large sizes

---

## Experimental Controls

### What We Control
- CPU affinity (explicit pinning)
- Nice level (explicit priority)
- Working set size (buffer allocation)
- Iteration count (fixed)

### What We Don't Control
- Other system processes
- Kernel background tasks
- Interrupt handling
- CPU frequency scaling
- NUMA placement (not yet)

---

## Reproducibility

### Required Steps
1. Run on idle system (minimize background load)
2. Disable CPU frequency scaling: `cpupower frequency-set -g performance`
3. Disable ASLR: `echo 0 > /proc/sys/kernel/randomize_va_space`
4. Pin unrelated tasks away from test CPUs
5. Run multiple iterations (10+)

### Reporting
- Always report standard deviation
- Report system configuration (CPU, kernel version)
- Document running processes during test
- Note thermal state if relevant

---

## Measurement Overhead

### Per-Experiment
- `/proc` reads: ~10-50µs each
- `clock_gettime()`: ~25-40ns each
- `sched_getcpu()`: ~10ns each

**Total overhead:** ~100µs per run (negligible for ms-scale workloads)

### Interference
- File I/O happens outside workload only
- No dynamic allocation in hot paths
- No logging during measurement

---

## Known Confounds

### Cannot Control
- Hardware interrupts
- RCU grace periods
- Kernel background tasks (kworker, etc.)
- Transparent hugepage behavior
- Memory compaction

### Future Work
- Isolate CPUs with `isolcpus` boot parameter
- Use real-time scheduling policies
- Add `perf` integration for hardware counters
- Test with different kernel configurations
