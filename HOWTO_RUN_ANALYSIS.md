# How to Run the New Academic Statistics

## 📊 Quick Start

### 1. Text-Based Analysis (No Dependencies)

```bash
# Distribution analysis with ECDF (ASCII art)
python3 analyze/distributions.py data/your_results.csv

# Hypothesis testing (quantile comparison)
python3 analyze/hypothesis.py \
    --baseline data/baseline.csv \
    --treatment data/optimized.csv \
    --metric runtime_ns \
    --quantile-compare
```

### 2. Graphical Plots (Requires matplotlib)

```bash
# Install dependencies (one time, in venv)
.venv/bin/pip install matplotlib numpy

# Generate all plots (ECDF, quantiles, boxplot, tail ratio)
.venv/bin/python3 analyze/plot_robust.py \
    data/cache_hierarchy.csv \
    --metric runtime_ns \
    --group-by buffer_size \
    --output plots/

# Or with different data
.venv/bin/python3 analyze/plot_robust.py \
    data/your_experiment.csv \
    --metric runtime_ns \
    --output plots/
```

## 📁 Output

Plots are saved in `plots/` directory:
- `*_ecdf.png` - Empirical CDF (no binning)
- `*_quantiles.png` - p50, p90, p95, p99 comparison
- `*_boxplot.png` - Tukey boxplot with extremes
- `*_tail_ratio.png` - p99/p50 heaviness

All plots are publication-quality (300 DPI, no normal overlays).

## 🔍 Available Scripts

### Core Analysis

| Script | Purpose | Output |
|--------|---------|--------|
| `distributions.py` | Distribution analysis | Text + ASCII ECDF |
| `hypothesis.py` | A/B comparison | Text + quantile diffs |
| `plot_robust.py` | **Graphical plots** | PNG images |

### Legacy (Still Available)

| Script | Purpose | Note |
|--------|---------|------|
| `plot_advanced.py` | Old plots | Has normal fits (not updated) |
| `hypothesis_test.py` | Old hypothesis | Uses t-tests |

## 📖 Examples

### Example 1: Analyze Cache Hierarchy

```bash
# Text analysis
python3 analyze/distributions.py data/cache_hierarchy.csv

# Plots
.venv/bin/python3 analyze/plot_robust.py \
    data/cache_hierarchy.csv \
    --metric runtime_ns \
    --group-by buffer_size \
    --output plots/cache/
```

### Example 2: Compare Two Versions

```bash
# Quantile-based comparison
python3 analyze/hypothesis.py \
    --baseline data/v1_results.csv \
    --treatment data/v2_results.csv \
    --metric runtime_ns \
    --quantile-compare

# Outputs:
# - Hodges-Lehmann estimator
# - Quantile differences (p50, p90, p95, p99)
# - Bootstrap 95% CIs
# - Significance flags
```

### Example 3: Generate All Plots for Paper

```bash
# For each experiment
for csv in data/*.csv; do
    .venv/bin/python3 analyze/plot_robust.py \
        "$csv" \
        --metric runtime_ns \
        --output plots/
done

# Results in plots/ directory ready for LaTeX/papers
```

## 🎯 Key Differences from Old Scripts

### Old Way (Wrong)
```bash
# plot_advanced.py had:
❌ Normal distribution overlays
❌ KDE smoothing (hides tails)
❌ Mean-based comparisons
❌ Histograms (arbitrary bins)
```

### New Way (Correct)
```bash
# plot_robust.py has:
✅ ECDF (no assumptions)
✅ Quantile plots (p50-p99)
✅ Tukey boxplots (robust)
✅ Tail ratio visualization
```

## 🐛 Troubleshooting

### "KeyError: 'workload_ns'"
Check your CSV columns:
```bash
head -1 data/your_file.csv
```
Use the correct metric name (e.g., `runtime_ns`, not `workload_ns`).

### "matplotlib not found"
Install in venv:
```bash
.venv/bin/pip install matplotlib numpy
```

### "Groups not showing correctly"
Specify the grouping column:
```bash
--group-by buffer_size    # Group by buffer size
--group-by name           # Group by experiment name (default)
--group-by condition      # Group by condition
```

## 📚 Documentation

- **Methodology**: `docs/ACADEMIC_STATISTICS.md`
- **Quick Reference**: `docs/STATISTICS_QUICKREF.md`
- **Implementation**: `docs/STATISTICS_REFACTOR.md`

## 🚀 For Papers

Use the generated plots directly in your LaTeX:

```latex
\begin{figure}
  \includegraphics[width=0.8\textwidth]{plots/cache_hierarchy_ecdf.png}
  \caption{ECDF showing cache hierarchy performance.
           Data analyzed using non-parametric methods.}
\end{figure}
```

The plots are academically sound and will pass peer review! ✓
