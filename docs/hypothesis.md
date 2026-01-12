# Research Hypotheses

This document lists testable hypotheses about Linux performance behavior that LRC is designed to investigate.

## H1: CPU Affinity and Migration

**Hypothesis:**
Pinning a compute-bound process to a specific CPU core eliminates migration overhead and reduces involuntary context switches compared to unpinned execution.

**Expected Signals:**
- Pinned: `start_cpu == end_cpu` in 100% of runs
- Pinned: Lower involuntary context switches
- Pinned: Lower runtime variance (coefficient of variation)

**Tested By:** `scenarios/pinned.c`

**Known Confounds:**
- System load from other processes
- CPU frequency scaling
- Interrupt handling on pinned CPU

---

## H2: Nice Priority Under Contention

**Hypothesis:**
Nice level affects scheduling quantum allocation. Under CPU contention, lower nice values (higher priority) receive more consistent scheduling and fewer preemptions.

**Expected Signals:**
- Nice -10: Fewest involuntary context switches under load
- Nice 19: Most involuntary context switches under load
- Without contention: Similar runtime across all nice levels

**Tested By:** `scenarios/nice_levels.c`

**Known Confounds:**
- CFS scheduling algorithm specifics
- Requires external load generator for meaningful results
- Other processes' nice values matter

---

## H3: Cache Hierarchy Latency

**Hypothesis:**
Memory access performance degrades non-linearly as working set size exceeds cache levels. Sequential streaming shows distinct performance tiers at L1/L2/L3/DRAM boundaries.

**Expected Signals:**
- L1 (8 KB): Lowest runtime per byte
- L2 (128 KB): ~3-4x slower than L1
- L3 (4 MB): ~10x slower than L1
- DRAM (64 MB): ~50x slower than L1

**Tested By:** `scenarios/cache_hierarchy.c`

**Known Confounds:**
- Hardware prefetcher masks sequential access penalties
- TLB effects at large buffer sizes
- Memory controller scheduling
- CPU frequency scaling

---

## H4: Context Switch Cost (Future)

**Hypothesis:**
Voluntary context switches (e.g., `sched_yield()`) are cheaper than involuntary switches because they don't require saving full CPU state and may not invalidate cache.

**Expected Signals:**
- TBD: Need to measure cache effects
- TBD: Need to distinguish switch types

**Status:** Not yet implemented

---

## H5: Memory Latency vs Bandwidth (Future)

**Hypothesis:**
Random access patterns are latency-bound (DRAM row activation), while sequential patterns are bandwidth-bound (memory controller throughput).

**Expected Signals:**
- TBD: Different bottleneck classification
- TBD: Different scaling with working set size

**Status:** Not yet implemented

---

## Adding New Hypotheses

New hypotheses must:
1. Be testable with kernel-exposed metrics
2. Involve one controlled variable
3. Have clear expected signals
4. Document known confounds
5. Be reproducible
