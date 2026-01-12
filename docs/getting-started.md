# Getting Started

## Prerequisites

```bash
# Check you have required tools
gcc --version        # GCC 5.0+
python3 --version    # Python 3.8+
uname -r             # Linux kernel 4.0+
```

## Build

```bash
# Build core library
cd core
make

# Build scenario executables
cd ../scenarios
make
```

## Run Your First Experiment

```bash
cd scenarios
./run_experiment.sh pinned
```

This will:
1. Run the CPU pinning experiment (30 runs)
2. Save raw metrics to `../data/pinned.csv`
3. Parse and analyze results
4. Print classification of bottlenecks

## Understanding the Output

### Parser Output
```
Group            Runs    Mean (ms)     StdDev     Median   Migr      Vol    Invol
------------------------------------------------------------------------------------------
cpu0               10      1526.59      21.87    1521.50      0        0      629
cpu1               10      1505.84      11.15    1500.41      0        0      100
unpinned           10      1592.00      96.50    1553.70      7        0      307
```

- **Runs:** Number of samples
- **Mean/StdDev/Median:** Runtime statistics (milliseconds)
- **Migr:** Total CPU migrations across all runs
- **Vol:** Total voluntary context switches
- **Invol:** Total involuntary context switches

### Classifier Output
```
cpu1:
  Runtime: 1505.84 ms (baseline +0.0%)
  Observations:
    · [Baseline] No significant interference detected
```

Severity indicators:
- `·` (low): Expected behavior
- `→` (medium): Measurable interference
- `⚠` (high): Significant interference

## Available Experiments

### 1. CPU Pinning (`pinned`)
Tests whether pinning eliminates scheduler migration overhead.

**Expected result:** Pinned runs show zero migrations and lower variance.

```bash
./run_experiment.sh pinned
```

### 2. Nice Levels (`nice_levels`)
Tests scheduling priority effects under contention.

**Expected result:** Without system load, all nice levels perform similarly.

```bash
./run_experiment.sh nice_levels
```

**Note:** For meaningful results, run with background CPU load:
```bash
# In another terminal
stress-ng --cpu 2 --timeout 60s &

# Then run experiment
./run_experiment.sh nice_levels
```

### 3. Cache Hierarchy (`cache_hierarchy`)
Tests memory access latency across cache levels.

**Expected result:** Runtime scales non-linearly with buffer size.

```bash
./run_experiment.sh cache_hierarchy
```

## Best Practices

### For Reproducible Results

1. **Run on idle system:**
   ```bash
   # Check system load
   uptime
   top -bn1 | head -20
   ```

2. **Disable CPU frequency scaling:**
   ```bash
   sudo cpupower frequency-set -g performance
   ```

3. **Check for thermal throttling:**
   ```bash
   sensors  # Install lm-sensors if needed
   ```

4. **Multiple runs:**
   Always run experiments multiple times. Look at variance, not just mean.

### Interpreting Results

**Low variance (<5%):** Reproducible behavior, scheduler not interfering much.

**High variance (>10%):** System interference, thermal throttling, or frequency scaling.

**Many migrations:** CPU not pinned or system very busy.

**Many involuntary switches:** Process being preempted frequently.

## Common Issues

### Permission Denied for Nice -10
```bash
# Run with sudo or set capability
sudo ./nice_levels

# Or permanently:
sudo setcap cap_sys_nice+ep ./nice_levels
```

### High Baseline Context Switches
This is normal on a busy system. LRC measures relative differences, not absolute perfection.

### Results Don't Match Expectations
Good! This is the point. Document what you expected vs. what happened.

## Next Steps

1. Read `docs/hypothesis.md` to understand what each experiment tests
2. Modify scenarios to test your own hypotheses
3. Add new workloads in `core/`
4. Create new scenarios in `scenarios/`

## Contributing Your Own Experiments

1. Write the workload in C (see `core/cpu_spin.c`)
2. Create a scenario that varies one variable (see `scenarios/pinned.c`)
3. Document hypothesis in `docs/hypothesis.md`
4. Run and analyze results
5. Document limitations

Remember: **Measurement purity over convenience.**
