# Known Limitations

This document honestly reports what LRC **cannot** measure and what it deliberately **does not** attempt.

## Architectural Limitations

### 1. User-Space Only
**Limitation:** Cannot directly observe kernel internals.

**Impact:**
- Cannot see kernel-level lock contention
- Cannot measure time spent in kernel mode
- Cannot observe slab allocator behavior
- Cannot trace system call overhead in detail

**Mitigation:**
- Use indirect signals (context switches, page faults)
- Future: Integrate with eBPF for kernel visibility

---

### 2. No Direct Cache Measurement
**Limitation:** Hardware performance counters not yet integrated.

**Impact:**
- Cache miss rates are inferred, not measured
- Cannot distinguish L1/L2/L3 miss types
- Cannot measure memory bandwidth directly

**Mitigation:**
- Working set size experiments infer cache effects
- Future: `perf` integration planned

---

### 3. Coarse-Grained CPU Migration Tracking
**Limitation:** Only measure CPU at start and end.

**Impact:**
- Cannot detect mid-execution migrations
- Cannot measure migration frequency
- Cannot correlate migrations with performance drops

**Mitigation:**
- Accept as limitation for now
- Future: eBPF sched_migrate_task tracepoint

---

## Workload Limitations

### 4. Synthetic Workloads Only
**Limitation:** Workloads are intentionally simple and unrealistic.

**Impact:**
- Does not represent real application behavior
- Missing I/O, networking, complex logic
- Optimized by compiler in ways real code isn't

**Justification:**
- This is intentional. We isolate effects, not simulate reality.
- Complex workloads have too many confounds.

---

### 5. Single-Threaded
**Limitation:** No multi-threading experiments yet.

**Impact:**
- Cannot study inter-thread contention
- Cannot measure synchronization overhead
- Cannot test NUMA effects with thread migration

**Future Work:**
- Add multi-threaded scenarios carefully
- Control thread placement explicitly

---

## Environmental Limitations

### 6. Cannot Eliminate System Noise
**Limitation:** Other processes, kernel tasks, and interrupts exist.

**Impact:**
- Variance in measurements
- Occasional outliers
- Non-deterministic scheduling

**Mitigation:**
- Run on idle system
- Report variance metrics
- Use statistical aggregation (median, not mean)
- Document running processes

---

### 7. CPU Frequency Scaling
**Limitation:** Dynamic frequency affects absolute timing.

**Impact:**
- Runtime varies with CPU power state
- Thermal throttling affects results
- Turbo boost adds non-determinism

**Mitigation:**
- Document CPU governor in use
- Recommend `performance` governor for experiments
- Compare relative differences, not absolute times

---

## Measurement Limitations

### 8. Measurement Overhead
**Limitation:** Observation affects system state.

**Impact:**
- File I/O for `/proc` reads
- System calls for timing
- Potential cache pollution from instrumentation

**Mitigation:**
- All measurement outside hot paths
- Document overhead (~100µs per experiment)
- Overhead is constant across experiments (cancels out in comparisons)

---

### 9. Temporal Resolution
**Limitation:** Millisecond-scale measurements only.

**Impact:**
- Cannot study microsecond-scale effects
- Cannot measure individual context switch cost
- Cannot see fine-grained scheduler behavior

**Justification:**
- Workloads are designed for ms-scale duration
- Finer resolution requires kernel-level instrumentation

---

## Experimental Limitations

### 10. Single Machine
**Limitation:** Results are system-specific.

**Impact:**
- CPU microarchitecture matters
- Kernel version matters
- Configuration matters (preemption model, HZ, etc.)

**Mitigation:**
- Document system configuration
- Results are comparative, not absolute
- Principles generalize even if numbers don't

---

### 11. No NUMA Awareness
**Limitation:** Does not control NUMA node placement.

**Impact:**
- Memory may be on remote node
- Cannot study NUMA effects explicitly

**Future Work:**
- Add explicit NUMA placement experiments
- Use `numactl` for node pinning

---

### 12. No I/O Testing
**Limitation:** Deliberately avoids I/O workloads.

**Impact:**
- Cannot study disk latency
- Cannot study network effects
- Cannot study interrupt behavior

**Justification:**
- I/O introduces too many confounds
- Focus is CPU and memory subsystems

---

## What We Will NOT Add

### Automatic Tuning
**Reason:** Defeats the purpose. We observe, not optimize.

### High-Level Abstractions
**Reason:** Abstractions hide the behavior we're studying.

### Cross-Platform Support
**Reason:** Linux-specific is intentional. Other OSes behave differently.

### Machine Learning
**Reason:** Rule-based classification is explainable and verifiable.

---

## Reporting Limitations

When publishing results, you **must** include:
1. Kernel version (`uname -r`)
2. CPU model (`lscpu`)
3. CPU governor (`cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor`)
4. Running processes (`ps aux | wc -l`)
5. Memory pressure state (`free -h`)
6. Thermal state if relevant

Failure to document environment invalidates comparison with other results.
