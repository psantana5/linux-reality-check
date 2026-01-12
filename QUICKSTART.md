# Linux Reality Check - Quick Start Guide

Get started with LRC in under 5 minutes!

## Installation

### 1. Build Everything

```bash
cd linux-reality-check
./lrc build
```

This compiles all 10 experiments and analysis tools.

### 2. System Setup (Optional but Recommended)

For best measurement quality:

```bash
# Set CPU governor to performance mode
sudo cpupower frequency-set -g performance

# Allow perf hardware counters (optional)
sudo sysctl -w kernel.perf_event_paranoid=1

# Disable address space randomization (optional)
echo 0 | sudo tee /proc/sys/kernel/randomize_va_space
```

## Running Experiments

### Option 1: Interactive Menu (Recommended for Beginners)

```bash
./lrc
```

This launches a user-friendly menu where you can:
- Browse all 10 experiments with descriptions
- Select experiments by number
- View system configuration
- Automatically analyze results

### Option 2: Command Line

```bash
# Run a single experiment
./lrc run pinned

# Run quick test suite (3 fast experiments)
./lrc quick

# Run all experiments
./lrc all

# List available experiments
./lrc list

# Analyze existing results
./lrc analyze pinned
```

## Your First Experiment

Let's run the "null baseline" to measure measurement overhead:

```bash
./lrc run null_baseline
```

**Expected output:**
- Experiment runs 20 iterations
- CSV data saved to `data/null_baseline.csv`
- Automatic statistical analysis
- Performance classification
- Distribution histograms
- Outlier detection

**Results show:** The ~100-200μs overhead of metrics collection itself.

## Quick Test Suite

Run 3 fast experiments (~30 seconds):

```bash
./lrc quick
```

This runs:
1. **null_baseline** - Measurement overhead (20 iterations)
2. **pinned** - CPU affinity impact (40 iterations)
3. **syscall_overhead** - System call costs (20 iterations)

## Understanding Results

### Data Files

Results are saved in `data/`:
```
data/
├── pinned.csv              # Raw measurements
├── cache_hierarchy.csv
└── ...
```

### CSV Format

Each row contains:
```csv
name,iteration,workload_ns,context_switches,migrations,page_faults,...
pinned-cpu0,1,50123456,0,0,145,...
```

### Analysis Output

The `./lrc run` command automatically shows:

1. **Statistical Summary**
   - Mean, median, stddev
   - Min/max values
   - Coefficient of variation

2. **Performance Classification**
   - "Excellent" = CV < 1%
   - "Good" = CV < 5%
   - "Acceptable" = CV < 10%
   - "High Variance" = CV ≥ 10%

3. **Distribution Analysis**
   - ASCII histogram
   - Percentiles (p50, p95, p99)
   - Tail latency

4. **Outlier Detection**
   - IQR method
   - Highlights anomalous runs

## Experiment Catalog

### Basic Performance (Start Here)

| Experiment | Duration | Description |
|------------|----------|-------------|
| `null_baseline` | 5s | Measurement overhead |
| `pinned` | 15s | CPU affinity effects |
| `nice_levels` | 20s | Process priority impact |

### Memory Hierarchy

| Experiment | Duration | Description |
|------------|----------|-------------|
| `cache_hierarchy` | 20s | L1/L2/L3 cache latency |
| `cache_analysis` | 30s | Cache miss behavior with perf |
| `latency_vs_bandwidth` | 25s | Memory access patterns |

### Multi-Core & NUMA

| Experiment | Duration | Description |
|------------|----------|-------------|
| `numa_locality` | 30s | NUMA memory placement (⚠ single-socket systems: no effect) |
| `lock_scaling` | 45s | Lock contention (1,2,4,8 threads) |

### System Calls & Mixed

| Experiment | Duration | Description |
|------------|----------|-------------|
| `syscall_overhead` | 15s | getpid/getppid/read costs |
| `realistic_patterns` | 60s | 5 mixed CPU+memory workloads |

**Total runtime for all experiments:** ~5 minutes

## Common Workflows

### Workflow 1: Quick System Check
```bash
./lrc quick
# Review data/null_baseline.csv for overhead
# Review data/pinned.csv for stability
```

### Workflow 2: Cache Behavior Study
```bash
./lrc run cache_hierarchy
./lrc run cache_analysis
python3 analyze/correlate.py data/cache_analysis.csv
```

### Workflow 3: Lock Contention Analysis
```bash
./lrc run lock_scaling
# Compare spinlock vs mutex vs atomic across thread counts
python3 analyze/compare.py data/lock_scaling.csv
```

### Workflow 4: Statistical Comparison
```bash
./lrc run pinned
./lrc run nice_levels
python3 analyze/hypothesis_test.py data/pinned.csv data/nice_levels.csv
```

## Advanced Analysis

### Correlation Analysis
```bash
python3 analyze/correlate.py data/cache_hierarchy.csv
```
Shows relationships between metrics (e.g., cache misses vs workload time).

### Time-Series Trends
```bash
python3 analyze/timeseries.py data/pinned.csv
```
Detects performance drift over iterations.

### Statistical Significance
```bash
python3 analyze/hypothesis_test.py data/pinned.csv data/nice_levels.csv
```
Welch's t-test and Cohen's d effect size.

### Multi-Experiment Comparison
```bash
python3 analyze/compare.py data/*.csv
```
Side-by-side comparison of all experiments.

## Troubleshooting

### High Variance (CV > 10%)

**Symptoms:** Results vary wildly between runs

**Fixes:**
```bash
# Check CPU governor
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor

# Set to performance
sudo cpupower frequency-set -g performance

# Disable turbo boost (optional)
echo 1 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo
```

### Permission Errors

**Error:** `perf_event_open: Permission denied`

**Fix:**
```bash
sudo sysctl -w kernel.perf_event_paranoid=1
```

### CPU Migrations

**Error:** Too many CPU migrations reported

**Fix:** Use `taskset` to pin LRC to specific cores:
```bash
taskset -c 0-3 ./lrc run pinned
```

### NUMA Warnings

**Warning:** NUMA experiments show no effect

**Explanation:** Single-socket systems have uniform memory access (UMA). NUMA experiments need multi-socket hardware to show meaningful results.

## Next Steps

1. **Read methodology**: `docs/methodology.md` - Understand measurement principles
2. **Review limitations**: `docs/limitations.md` - Know what LRC can't measure
3. **Explore troubleshooting**: `docs/troubleshooting.md` - Comprehensive problem resolution
4. **Check examples**: `EXAMPLE.md` - Detailed walkthrough of pinned experiment

## Getting Help

- Check system configuration: `./lrc check`
- List all experiments: `./lrc list`
- View this guide: `cat QUICKSTART.md`
- Full documentation: `README.md`
- Troubleshooting: `docs/troubleshooting.md`

## TL;DR - 30 Second Start

```bash
cd linux-reality-check
./lrc build           # Build everything
./lrc quick           # Run 3 fast tests
ls data/*.csv         # See results
```

Done! You now have baseline performance data for your system.
