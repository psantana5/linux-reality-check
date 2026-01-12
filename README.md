# Linux Reality Check (LRC) v2.0

A research-grade, kernel-near Linux performance exploration tool that demonstrates—using controlled experiments—when common assumptions about CPU, memory, and scheduling behavior are wrong.

**This is not a benchmark suite. It is a measurement-pure experimental framework.**

---

## Quick Start (< 2 minutes)

```bash
# One-time setup (builds everything, ~30 seconds)
./setup.sh

# Run quick test suite (3 experiments, ~30 seconds)
./lrc quick

# Results displayed automatically!
```

**That's it! You now have performance data.**

---

## What's New in v2.0

- **Interrupt Safety** - Ctrl+C cleanly exits, no stray processes
- **Progress Indicators** - Spinners and progress bars
- **Enhanced Error Handling** - Clear messages with suggestions
- **Overwrite Protection** - Warns before overwriting results
- **Time Estimates** - Shows duration for each experiment
- ** Recent Results** - Displays recently run experiments
- **New Commands** - `version`, `clean`, `--no-color`

---

## Documentation

| Document | Audience | Time | Purpose |
|----------|----------|------|---------|
| **[QUICKSTART.md](QUICKSTART.md)** | Beginners | 5 min | Installation & first experiments |
| **[USER_GUIDE.md](USER_GUIDE.md)** | All users | 20 min | Complete reference |
| **[DEPLOYMENT.md](DEPLOYMENT.md)** | Ops/admins | 15 min | Workflows & integration |
| **[DEMO.md](DEMO.md)** | Presenters | 2 min | Demo script |

**New user? Start with [QUICKSTART.md](QUICKSTART.md)**

---

## Usage Modes

### Interactive (Beginner-Friendly)
```bash
./lrc              # Launch menu
# Select experiment by number
```

### Command-Line (Power Users)
```bash
./lrc run pinned              # Run specific experiment
./lrc analyze cache_hierarchy # Analyze results
./lrc quick                   # Quick validation
./lrc all                     # Run all 10 experiments
./lrc check                   # System configuration
./lrc list                    # List experiments
```

### Advanced (Researchers)
```bash
python3 analyze/correlate.py data/cache_hierarchy.csv
python3 analyze/hypothesis_test.py data/exp1.csv data/exp2.csv
```

---

## Core Philosophy

- Measurement must introduce minimal noise
- Change one variable at a time
- Prefer raw kernel signals over abstractions
- Favor reproducibility over convenience
- If the tool interferes with scheduling or cache behavior, it is wrong

## Features

### 10 Experiments (C)
1. **pinned** - CPU affinity impact on performance
2. **nice_levels** - Process priority effects on scheduling
3. **null_baseline** - Quantify measurement overhead
4. **cache_hierarchy** - L1/L2/L3/DRAM latency measurement
5. **cache_analysis** - Cache behavior with perf counters
6. **latency_vs_bandwidth** - Sequential vs random memory access
7. **numa_locality** - NUMA memory placement effects
8. **lock_scaling** - Lock contention (1,2,4,8 threads)
9. **syscall_overhead** - System call cost measurement
10. **realistic_patterns** - 5 mixed CPU+memory workloads

### 10 Analysis Tools (Python)
1. **parse.py** - Statistical summary (mean, median, stddev, CV)
2. **classify.py** - Performance classification & bottleneck detection
3. **outliers.py** - IQR-based outlier detection
4. **timeseries.py** - Warmup/throttling/drift detection
5. **compare.py** - Multi-experiment comparison
6. **distributions.py** - Histograms, percentiles, tail latency
7. **correlate.py** - Pearson correlation matrix
8. **hypothesis_test.py** - Statistical significance (Welch's t-test, Cohen's d)
9. **metadata.py** - System configuration tracking
10. **ebpf_tracer.py** - Kernel-level scheduler tracing (optional)

### Visualization (NEW!)
- **plot_all.py** - Automatic plot generation for all experiments
  - Smart visualization selection per experiment type
  - High-quality PNG output (150 DPI)
  - Summary dashboard with all results
  - Zero configuration needed
  
- **plot_advanced.py** - Advanced statistical analysis & plotting
  - Violin plots with confidence intervals
  - CDF and percentile analysis
  - Multi-method outlier detection
  - Time series decomposition
  - Cross-experiment correlation matrices
  - 9-panel comparison dashboard
  
```bash
python3 analyze/plot_all.py        # Basic plots
python3 analyze/plot_advanced.py   # Advanced statistical plots
make plots                          # Or use Makefile
make plots-advanced                 # Advanced plots
```

See [PLOTTING_GUIDE.md](PLOTTING_GUIDE.md) and [ADVANCED_PLOTTING_GUIDE.md](ADVANCED_PLOTTING_GUIDE.md) for details.

### Core Workloads (C)
- **cpu_spin** - Pure compute (integer arithmetic)
- **memory_stream** - Sequential bandwidth measurement
- **memory_random** - Pointer-chasing latency
- **lock_contention** - Multi-threaded spinlock/mutex/atomic operations
- **mixed_workload** - Realistic CPU+memory patterns

### Hardware Counters
- Instructions, cycles, IPC
- L1/LLC cache misses
- Branch predictions/mispredictions
- Requires: `kernel.perf_event_paranoid ≤ 1`

### Advanced Features
- **Statistical rigor**: Welch's t-test, effect size, correlation analysis
- **NUMA awareness**: Multi-socket topology detection
- **eBPF tracing**: Kernel-level visibility (optional)
- **CI/CD**: GitHub Actions pipeline
- **Docker**: Isolated testing environment

## Architecture

The project maintains strict separation between two layers:

### 1. Low-level execution & measurement (C only)
- Workloads
- Timing
- CPU pinning
- Scheduler interaction
- Raw metric collection

### 2. Analysis & reporting (Python only)
- Parsing raw output
- Deriving conclusions
- Presenting results clearly
- No influence on runtime behavior

**C produces facts. Python produces interpretation.**

## Repository Structure

```
linux-reality-check/
├── core/            # C: workloads + collectors
├── scenarios/       # C: execution configurations
├── data/            # Raw experiment output
├── analyze/         # Python: analysis logic
├── report/          # Python: CLI + ASCII graphs
└── docs/            # Methodology & limitations
```

## Quick Start

```bash
# Build core components
cd core
make

# Run an experiment
cd ../scenarios
make
./pinned

# Analyze results
cd ../analyze
python3 parse.py ../data/latest.csv
```

## Design Principles

1. **User-space only** - No kernel modules
2. **Minimal syscalls** - None in hot paths
3. **Explicit control** - No automatic tuning
4. **Reproducible** - Documented methods
5. **Honest** - Reports limitations clearly

## Documentation

See `docs/` for:
- `hypothesis.md` - Research questions
- `methodology.md` - Measurement techniques
- `limitations.md` - Known constraints

## Requirements

- Linux kernel 4.0+
- GCC with `-march=native` support
- Python 3.8+
- Root privileges (for CPU pinning only)

## License

MIT
