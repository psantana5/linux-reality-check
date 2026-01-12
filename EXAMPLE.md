# Example: Investigating CPU Pinning Hypothesis

This is a complete walkthrough of using LRC to test a performance hypothesis.

## The Question

**Does pinning a CPU-bound process to a specific core improve performance and reduce variance?**

## Common Assumption

"Pinning to a core is always better because it avoids migration overhead and maintains cache locality."

## Let's Test It

### Step 1: Build the Project

```bash
cd linux-reality-check/core
make

cd ../scenarios
make
```

### Step 2: Check System State

```bash
# Check CPU governor
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
# Should show: performance (or ondemand, powersave, etc.)

# Check system load
uptime
# Should show low load average (< 1.0 for idle system)

# Check CPU info
lscpu | grep "Model name"
nproc  # Number of cores
```

### Step 3: Run the Experiment

```bash
./run_experiment.sh pinned
```

This runs 30 iterations of the same CPU workload in three configurations:
1. **Unpinned** - Scheduler decides placement
2. **CPU 0** - Pinned to core 0
3. **CPU 1** - Pinned to core 1

### Step 4: Examine Raw Data

```bash
head ../data/pinned.csv
```

Output:
```csv
run,affinity,timestamp_ns,runtime_ns,voluntary_ctxt_switches,nonvoluntary_ctxt_switches,minor_page_faults,major_page_faults,start_cpu,end_cpu
0,unpinned,19618959762965,1635480111,0,43,0,0,4,2
1,unpinned,19620453732172,1493852043,0,17,0,0,2,2
```

**Observations:**
- Unpinned runs show `start_cpu != end_cpu` (migrations)
- High involuntary context switches
- Large runtime variance

### Step 5: Statistical Analysis

```bash
cd ../analyze
python3 parse.py ../data/pinned.csv
```

Output:
```
Group            Runs    Mean (ms)     StdDev     Median   Migr      Vol    Invol
------------------------------------------------------------------------------------------
cpu0               10      1526.59      21.87    1521.50      0        0      629
cpu1               10      1505.84      11.15    1500.41      0        0      100
unpinned           10      1592.00      96.50    1553.70      7        0      307
```

**Key Findings:**
- Unpinned: 96.5ms standard deviation (6% variance)
- CPU 1: 11.15ms standard deviation (0.7% variance)  
- Unpinned: 7 migrations in 10 runs (70% migration rate)
- Pinned: 0 migrations (as expected)

### Step 6: Bottleneck Classification

```bash
python3 classify.py ../data/pinned.csv
```

Output:
```
=== Comparative Analysis ===

cpu1:
  Runtime: 1505.84 ms (baseline +0.0%)
  Observations:
    · [Baseline] No significant interference detected

cpu0:
  Runtime: 1526.59 ms (baseline +1.4%)
  Observations:
    → [Scheduler] 63 involuntary context switches per run

unpinned:
  Runtime: 1592.00 ms (baseline +5.7%)
  Observations:
    ⚠ [Scheduler] 70.0% of runs migrated CPUs
    → [Scheduler] 31 involuntary context switches per run
    → [Variance] 6.1% coefficient of variation
```

**Interpretation:**
- CPU 1 is the cleanest (likely less system activity on that core)
- CPU 0 shows more preemption (may handle more interrupts)
- Unpinned shows migration overhead and high variance

### Step 7: Visualization

```bash
cd ../report
python3 visualize.py ../data/pinned.csv
```

Output:
```
Mean Runtime (ms)
============================================================
cpu1            ████████████████████████████  1505.84
cpu0            ████████████████████████████  1526.59
unpinned        ██████████████████████████████  1592.00

CPU Migration Rate (%)
============================================================
cpu0                 0.00
cpu1                 0.00
unpinned        ██████████████████████████████    70.00
```

## Conclusion

### Hypothesis: CONFIRMED

Pinning a CPU-bound process **does** improve performance when:
1. Runtime becomes more predictable (87% reduction in variance)
2. Migrations are eliminated completely
3. Mean runtime improves by 5-6%

### But There's More...

**Not all cores are equal:**
- CPU 1 outperformed CPU 0 by 1.4%
- CPU 0 had 6x more involuntary context switches

**Why?**
- Core 0 often handles more system interrupts
- Core 0 may have more background kernel tasks
- This is system-specific behavior

### Reality Check

The common assumption was **mostly correct**, but:
- The benefit is smaller than many expect (5-6%, not 50%)
- Core selection matters more than expected
- Without pinning, 30% of runs still didn't migrate

### Limitations

1. **Idle system:** Under load, benefits may be larger
2. **Synthetic workload:** Real applications have different cache behavior  
3. **No NUMA:** On multi-socket systems, effects are more dramatic
4. **No cache measurement:** We infer but don't measure cache effects

## What We Learned

1. **Pinning reduces variance** - The biggest win
2. **Migration has measurable cost** - But it's not catastrophic
3. **Core asymmetry exists** - Even on "identical" cores
4. **Measurements beat intuition** - Numbers over assumptions

## Next Experiments

Having established this baseline, we could now test:

1. **Under contention:**
   ```bash
   stress-ng --cpu 4 --timeout 60s &
   ./run_experiment.sh pinned
   ```
   Hypothesis: Pinning benefit increases under load

2. **With larger working set:**
   Modify iterations or add memory workload
   Hypothesis: Cache effects become dominant

3. **Different CPU governors:**
   ```bash
   sudo cpupower frequency-set -g powersave
   ./run_experiment.sh pinned
   ```
   Hypothesis: Frequency scaling adds variance

## Files Generated

```
data/pinned.csv              # Raw metrics (can be versioned)
PROJECT_STATUS.md            # This analysis (document findings)
```

## Reproducibility

To reproduce these results:
```bash
# System configuration
uname -r                     # Document kernel version
lscpu                        # Document CPU model  
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
uptime                       # Note system load

# Run experiment
./run_experiment.sh pinned

# Results will vary by system but patterns should hold
```

---

**This is what LRC is for:** Not benchmarking, but understanding. Not optimization, but observation. Not assumptions, but measurement.
