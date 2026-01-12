# LRC Demo Script - 2 Minute Walkthrough

This script demonstrates Linux Reality Check for new users.

## Demo Flow (2 minutes)

### 1. Setup (10 seconds)
```bash
cd linux-reality-check
./setup.sh
# Output: Builds complete, system checks done
```

### 2. Check System (5 seconds)
```bash
./lrc check
```
**Shows:**
- CPU model and cores
- Kernel version
- CPU governor status (with warnings if needed)
- perf_event_paranoid status
- NUMA topology

### 3. List Experiments (5 seconds)
```bash
./lrc list
```
**Shows:**
- 10 experiments organized by category
- Clear descriptions
- Numbered for easy selection

### 4. Run Quick Test Suite (30 seconds)
```bash
./lrc quick
```
**Runs 3 experiments:**
1. null_baseline (measures overhead)
2. pinned (CPU affinity)
3. syscall_overhead (system call costs)

**Automatic output for each:**
- System configuration check
- Experiment execution
- Statistical summary
- Performance classification
- Distribution analysis
- Outlier detection

### 5. Explore Interactive Menu (10 seconds)
```bash
./lrc
```
**Shows:**
- Beautiful formatted menu
- System configuration
- All 10 experiments with descriptions
- Quick commands (quick, all, build, analyze, quit)

Type `3` to run null_baseline, or `quit` to exit.

### 6. View Results (5 seconds)
```bash
ls -lh data/
cat data/null_baseline.csv | head -5
```
**Shows:**
- CSV files for each experiment
- Raw measurement data

### 7. Advanced Analysis (20 seconds)
```bash
./lrc run cache_hierarchy
python3 analyze/correlate.py data/cache_hierarchy.csv
```
**Shows:**
- Correlation matrix between metrics
- Identifies relationships (e.g., cache misses vs runtime)

### 8. Documentation (5 seconds)
```bash
cat QUICKSTART.md
```
**Shows:**
- 5-minute tutorial
- Installation guide
- Experiment catalog
- Common workflows

---

## Key Points to Highlight

### 1. User-Friendly
- Single command for everything: `./lrc`
- Interactive menu (no memorization needed)
- Automatic analysis (no manual steps)
- Color-coded output (clear status)

### 2. Fast Setup
- One command: `./setup.sh`
- Builds everything automatically
- Checks system configuration
- Ready in <1 minute

### 3. Flexible Workflows

**Beginner:**
```bash
./lrc              # Interactive menu
# Select by number
```

**CLI User:**
```bash
./lrc run pinned   # Run specific experiment
./lrc quick        # Quick validation
```

**Power User:**
```bash
./lrc all          # Batch all experiments
for exp in pinned nice_levels; do
    ./lrc run $exp
    python3 analyze/timeseries.py data/$exp.csv
done
```

### 4. Research-Grade Quality
- Measurement-pure philosophy
- Raw kernel signals (/proc, clock_gettime)
- Hardware counters (perf_event_open)
- Statistical rigor (Welch's t-test, Cohen's d)
- No abstractions that interfere with measurement

### 5. Comprehensive Coverage
- **10 experiments**: CPU, memory, NUMA, locks, syscalls, mixed workloads
- **10 analysis tools**: Stats, classification, outliers, correlation, hypothesis testing
- **9 core modules**: CPU, memory (sequential/random), locks, mixed patterns

---

## Demo Script (Narration)

```
[0:00] "Let me show you Linux Reality Check, a research-grade performance tool."

[0:05] "First, one-command setup:"
$ ./setup.sh

[0:15] "Check your system configuration:"
$ ./lrc check

[0:20] "List all available experiments:"
$ ./lrc list

[0:25] "Run the quick test suite - 3 experiments in 30 seconds:"
$ ./lrc quick

[0:30] "Each experiment runs and analyzes automatically."
[0:35] "You get statistical summaries, classifications, and outlier detection."

[1:00] "All done! Results saved to CSV files:"
$ ls data/

[1:05] "For more control, use the interactive menu:"
$ ./lrc

[1:10] "Or run specific experiments:"
$ ./lrc run cache_hierarchy

[1:15] "Advanced users can use Python analysis tools directly:"
$ python3 analyze/correlate.py data/cache_hierarchy.csv

[1:20] "This shows correlations between metrics."

[1:25] "Documentation is comprehensive:"
$ cat QUICKSTART.md  # 5-minute tutorial
$ cat README.md      # Full docs

[1:35] "LRC covers everything from basic CPU affinity to NUMA locality,
        lock contention, and mixed workloads."

[1:45] "It's measurement-pure - no syscalls in hot paths, raw kernel signals,
        hardware performance counters."

[1:55] "From clone to first result in under 2 minutes. That's LRC."
```

---

## Terminal Recording Commands

If making an asciinema recording:

```bash
# Start recording
asciinema rec lrc-demo.cast

# Follow demo script above

# Stop recording
exit

# Upload (optional)
asciinema upload lrc-demo.cast
```

---

## One-Liner Demos

### Absolute Minimal Demo (10 seconds)
```bash
./lrc quick
```

### Beginner-Friendly Demo (30 seconds)
```bash
./setup.sh && ./lrc list && ./lrc run null_baseline
```

### Power User Demo (60 seconds)
```bash
./setup.sh && ./lrc all && ls data/*.csv
```

### Feature Showcase (90 seconds)
```bash
./setup.sh
./lrc check
./lrc list
./lrc quick
./lrc run cache_hierarchy
python3 analyze/correlate.py data/cache_hierarchy.csv
```

---

## What Users See

### Before (Complex)
```bash
cd core && make
cd ../scenarios && make
cd ../scenarios && ./pinned
cd ../analyze
python3 parse.py ../data/pinned.csv
python3 classify.py ../data/pinned.csv
python3 outliers.py ../data/pinned.csv
```
**8 commands, multiple directories, manual analysis**

### After (Simple)
```bash
./lrc run pinned
```
**1 command, automatic everything**

---

## Key Differentiators

| Feature | Traditional Tools | LRC |
|---------|------------------|-----|
| Setup | Multi-step, manual | `./setup.sh` |
| Running | Complex commands | `./lrc run <exp>` |
| Analysis | Manual, separate | Automatic |
| Discovery | Read docs | Interactive menu |
| Results | Raw output | Statistical + visual |
| Time to first result | 10+ minutes | <2 minutes |

---

## Closing Points

1. **User-friendly**: Single CLI, interactive menu, automatic analysis
2. **Fast**: Setup in 1 minute, first result in 2 minutes
3. **Flexible**: Works for beginners, CLI users, and power users
4. **Research-grade**: Measurement purity, statistical rigor
5. **Comprehensive**: 10 experiments, 10 analysis tools

**Try it: `./setup.sh && ./lrc quick`**
