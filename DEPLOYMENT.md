# LRC Deployment Guide - User-Friendly Edition

This guide explains the new streamlined deployment system for Linux Reality Check.

## What's New? ✨

### 1. Single Command Interface (`./lrc`)

All functionality is now accessible through one unified CLI tool:

```bash
./lrc              # Interactive menu
./lrc run pinned   # Run specific experiment
./lrc quick        # Run 3 fast tests
./lrc all          # Run all 10 experiments
./lrc analyze pinned  # Analyze results
./lrc check        # System configuration
./lrc list         # List experiments
./lrc build        # Rebuild everything
```

### 2. Interactive Menu Mode

Running `./lrc` without arguments launches a beautiful interactive menu:

```
╔════════════════════════════════════════════════════════════╗
║          Linux Reality Check (LRC) v1.0                   ║
║          Research-Grade Performance Measurement           ║
╚════════════════════════════════════════════════════════════╝

Available Experiments:

  Basic Performance:
    1. pinned          - CPU affinity impact
    2. nice_levels     - Process priority
    3. null_baseline   - Measurement overhead

  Memory Hierarchy:
    4. cache_hierarchy - L1/L2/L3 latency
    ...

Select experiment number (1-10), command, or 'quit':
```

### 3. Automatic Setup Script (`./setup.sh`)

One-step setup with interactive configuration:

```bash
./setup.sh
```

This:
- ✅ Builds all 10 scenarios
- ✅ Builds all analysis tools
- ✅ Checks Python dependencies
- ✅ Verifies system configuration
- ❓ Optionally configures CPU governor
- ❓ Optionally enables perf counters

### 4. Quick Start Guide (`QUICKSTART.md`)

5-minute tutorial covering:
- Installation in 2 steps
- Your first experiment
- Quick test suite
- Understanding results
- Common workflows
- Troubleshooting

## File Structure

```
linux-reality-check/
├── lrc                  ⭐ Main CLI interface (NEW)
├── setup.sh             ⭐ One-step setup script (NEW)
├── QUICKSTART.md        ⭐ 5-minute tutorial (NEW)
├── DEPLOYMENT.md        ⭐ This file (NEW)
│
├── README.md            📚 Full documentation (UPDATED)
├── core/                🔧 Core measurement library
├── scenarios/           🧪 10 experiments
├── analyze/             📊 10 analysis tools
├── data/                💾 Results storage
└── docs/                📖 Detailed documentation
```

## User Journey

### For Complete Beginners

```bash
# Step 1: Setup (first time only)
./setup.sh

# Step 2: Read quick start
cat QUICKSTART.md

# Step 3: Run interactive menu
./lrc

# Step 4: Select experiment by number
# Select: 3 (null_baseline)
# Results displayed automatically!
```

**Time to first result: ~2 minutes**

### For Command-Line Users

```bash
# Setup once
./setup.sh

# Run quick tests
./lrc quick

# Run specific experiment
./lrc run cache_hierarchy

# Analyze old results
./lrc analyze pinned
```

### For Power Users

```bash
# Run all experiments in batch
./lrc all > full_results.txt

# Manually analyze with specific tools
python3 analyze/correlate.py data/cache_hierarchy.csv
python3 analyze/hypothesis_test.py data/pinned.csv data/nice_levels.csv

# Custom workflows
for exp in pinned nice_levels cache_hierarchy; do
    ./lrc run $exp
    python3 analyze/timeseries.py data/$exp.csv
done
```

## Feature Highlights

### 🎨 Color-Coded Output

- ✅ Green = Success
- ⚠️  Yellow = Warning
- ❌ Red = Error
- ℹ️  Blue = Info

### 🔍 System Configuration Checks

The `./lrc` tool automatically checks:
- CPU model and core count
- Kernel version
- CPU frequency governor
- perf_event_paranoid setting
- NUMA topology

And provides actionable warnings:
```
⚠ CPU governor is 'powersave' (recommend 'performance')
  Fix: sudo cpupower frequency-set -g performance
```

### 📊 Automatic Analysis

When you run an experiment, you automatically get:
1. **Statistical Summary** - Mean, median, stddev, CV
2. **Performance Classification** - Excellent/Good/Acceptable/Poor
3. **Distribution Analysis** - Histogram, percentiles
4. **Outlier Detection** - Anomalous data points

No need to remember analysis commands!

### ⚡ Quick Test Suite

`./lrc quick` runs 3 fast experiments (~30 seconds):
- **null_baseline** - Measures measurement overhead
- **pinned** - Tests CPU affinity
- **syscall_overhead** - Measures system call costs

Perfect for:
- Validating setup
- Quick system check
- CI/CD pipelines
- Before/after comparisons

### 🔄 Batch Operations

Run all 10 experiments:
```bash
./lrc all
```

Results saved to `data/*.csv` for later analysis.

## Configuration Management

### Recommended Setup (Manual)

For best measurement quality:

```bash
# CPU governor to performance
sudo cpupower frequency-set -g performance

# Enable perf counters
sudo sysctl -w kernel.perf_event_paranoid=1

# Disable ASLR (optional)
echo 0 | sudo tee /proc/sys/kernel/randomize_va_space

# Disable turbo boost (optional, for consistency)
echo 1 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo
```

### Automatic Setup (Interactive)

The `./setup.sh` script can apply these settings if run with sudo:
```bash
sudo ./setup.sh
```

It will ask before making each change.

### Verification

Check your configuration:
```bash
./lrc check
```

## Common Workflows

### Workflow 1: First-Time User
```bash
./setup.sh              # Build everything
cat QUICKSTART.md       # Read 5-min guide
./lrc                   # Launch menu
# Select: 3 (null_baseline)
```

### Workflow 2: Quick System Validation
```bash
./lrc quick             # 3 experiments in 30s
ls data/*.csv           # Verify output
```

### Workflow 3: Deep Cache Analysis
```bash
./lrc run cache_hierarchy
./lrc run cache_analysis
python3 analyze/correlate.py data/cache_analysis.csv
```

### Workflow 4: Lock Contention Study
```bash
./lrc run lock_scaling
python3 analyze/compare.py data/lock_scaling.csv
# Compare spinlock vs mutex vs atomic across thread counts
```

### Workflow 5: Statistical Comparison
```bash
./lrc run pinned
# Modify system (e.g., change CPU governor)
./lrc run pinned
# Compare results
python3 analyze/hypothesis_test.py data/pinned.csv data/pinned.csv
```

### Workflow 6: Batch Experimentation
```bash
./lrc all               # Run all 10 experiments
./lrc analyze pinned    # Analyze specific one
./lrc analyze cache_hierarchy
# ... etc
```

## Integration with CI/CD

### GitHub Actions

The `.github/workflows/ci.yml` pipeline:
1. Builds all components
2. Runs quick test suite
3. Validates CSV output
4. Archives results

### Docker

Build and run in container:
```bash
docker build -t lrc .
docker run --privileged lrc ./lrc quick
```

## Troubleshooting

### Problem: High Variance (CV > 10%)

**Solution:**
```bash
./lrc check  # See current config
sudo cpupower frequency-set -g performance
./lrc run <experiment>  # Re-run
```

### Problem: Permission Denied (perf counters)

**Solution:**
```bash
sudo sysctl -w kernel.perf_event_paranoid=1
```

### Problem: Experiment Not Found

**Solution:**
```bash
./lrc list              # List all experiments
./lrc build             # Rebuild if needed
```

### Problem: No Data Generated

**Check:**
```bash
ls -la data/            # Verify output
./lrc check             # Check system
cd scenarios && ./null_baseline  # Run directly
```

## Advanced Usage

### Custom Analysis Pipelines

```bash
# Run experiment
./lrc run realistic_patterns

# Multiple analysis tools
cd data
python3 ../analyze/parse.py realistic_patterns.csv
python3 ../analyze/distributions.py realistic_patterns.csv
python3 ../analyze/correlate.py realistic_patterns.csv
python3 ../analyze/timeseries.py realistic_patterns.csv
```

### Comparing Multiple Experiments

```bash
# Run several experiments
./lrc run pinned
./lrc run nice_levels
./lrc run cache_hierarchy

# Compare all
python3 analyze/compare.py data/*.csv

# Statistical significance
python3 analyze/hypothesis_test.py data/pinned.csv data/nice_levels.csv
```

### eBPF Tracing (Advanced)

```bash
# Requires BCC tools
sudo python3 analyze/ebpf_tracer.py <pid>
```

## Documentation Map

| Document | Purpose | Audience |
|----------|---------|----------|
| `QUICKSTART.md` | 5-minute tutorial | Beginners |
| `README.md` | Full documentation | All users |
| `DEPLOYMENT.md` | This file | Deployment/ops |
| `docs/methodology.md` | Measurement principles | Researchers |
| `docs/limitations.md` | What LRC can't do | All users |
| `docs/troubleshooting.md` | Problem resolution | Debugging |
| `EXAMPLE.md` | Detailed walkthrough | Learning |

## Summary

The new deployment system makes LRC:
- ✅ **Beginner-friendly** - Interactive menu with clear descriptions
- ✅ **Fast to setup** - One command builds everything
- ✅ **Guided** - Automatic system checks and warnings
- ✅ **Automated** - Experiments run and analyze in one command
- ✅ **Flexible** - Works for beginners and power users
- ✅ **Documented** - QUICKSTART for 5-min onboarding

**From clone to first result in under 3 minutes.**

## Next Steps

1. **Try it out**: `./setup.sh && ./lrc quick`
2. **Read quick start**: `cat QUICKSTART.md`
3. **Explore experiments**: `./lrc list`
4. **Deep dive**: `cat docs/methodology.md`
5. **Customize**: Modify scenarios in `scenarios/*.c`

Welcome to Linux Reality Check! 🚀
