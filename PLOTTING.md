# Advanced Plotting Guide

## 🎯 Overview

The advanced plotting system provides sophisticated statistical visualizations with professional-grade analysis tools for deep performance insights.

## 📊 What's New in Advanced Plotting

### Statistical Analysis
- ✅ **Violin Plots** with confidence intervals
- ✅ **CDF (Cumulative Distribution Function)** overlays
- ✅ **Outlier Detection** (IQR, Z-score, moving average)
- ✅ **Time Series Decomposition** (trend, seasonality, residuals)
- ✅ **Correlation Matrices** across experiments
- ✅ **Multi-Experiment Dashboards** with 9 comparison metrics

### Advanced Metrics
- Confidence intervals (95% CI)
- Kernel density estimation
- Percentile analysis (p50, p75, p90, p95, p99, p99.9)
- Coefficient of variation
- Rolling statistics
- Trend analysis with polynomial fitting
- Distribution fitting (normal, etc.)

## 🚀 Quick Start

```bash
# Generate all advanced plots
python3 analyze/plot_advanced.py

# Or use Makefile
make plots-advanced

# Plot specific experiments only
python3 analyze/plot_advanced.py --experiments pinned,cache_hierarchy

# Generate comparison plots
python3 analyze/plot_advanced.py --compare
```

## 📦 Dependencies

```bash
# Install required packages
sudo apt-get install python3-matplotlib python3-numpy python3-scipy

# Or with pip (in virtual environment)
pip3 install matplotlib numpy scipy
```

## 📂 Output Structure

```
data/plots/advanced/
├── null_baseline_violin_stats.png          # Violin plot with CI
├── null_baseline_cdf_percentiles.png       # CDF + percentile comparison
├── null_baseline_outlier_analysis.png      # 4-panel outlier detection
├── null_baseline_timeseries_decomposition.png  # Time series analysis
├── pinned_violin_stats.png
├── pinned_cdf_percentiles.png
├── ... (4 plots per experiment)
├── correlation_matrix.png                  # Cross-experiment correlations
└── comparison_dashboard.png                # 9-panel comparison
```

## 🎨 Plot Types Explained

### 1. Violin Plot with Statistics

**File**: `{experiment}_violin_stats.png`

**Features**:
- Kernel density estimation (width shows distribution)
- Embedded box plot
- 95% confidence intervals shown as error bars
- Statistical annotations (μ, σ, CI)

**Use Case**: Compare distributions across groups, see data spread and density

**Interpretation**:
- Wide sections = more data points
- Narrow sections = fewer data points
- CI bars = uncertainty in mean estimate

---

### 2. CDF and Percentiles

**File**: `{experiment}_cdf_percentiles.png`

**Left Panel - CDF**:
- Shows cumulative probability
- Marked percentiles (p50, p90, p95, p99)
- Multiple groups overlaid

**Right Panel - Percentile Bars**:
- Direct comparison of tail latencies
- Focus on high percentiles (p90-p99.9)

**Use Case**: Analyze tail latency, understand worst-case performance

**Interpretation**:
- Steeper CDF = more consistent performance
- Flat CDF regions = bimodal/multimodal behavior
- High p99 values = occasional slow outliers

---

### 3. Outlier Detection Analysis

**File**: `{experiment}_outlier_analysis.png`

**Four Detection Methods**:

1. **IQR Method** (top-left)
   - Box plot with outliers marked in red
   - Uses 1.5 × IQR rule

2. **Z-Score Method** (top-right)
   - Points beyond ±3σ marked as outliers
   - Mean and ±3σ boundaries shown

3. **Moving Average** (bottom-left)
   - Smoothed trend line
   - Deviations beyond 2σ highlighted

4. **Distribution Fit** (bottom-right)
   - Histogram with normal distribution overlay
   - Shows how well data fits normal distribution

**Use Case**: Identify anomalous runs, detect measurement errors

**Interpretation**:
- Multiple methods agree → strong outlier signal
- Methods disagree → borderline cases
- Many outliers → unstable experiment or external interference

---

### 4. Time Series Decomposition

**File**: `{experiment}_timeseries_decomposition.png`

**Four Components**:

1. **Original Series** (top-left)
   - Raw data over time
   - Identifies trends and patterns

2. **Trend Analysis** (top-right)
   - Polynomial fit (degree 3)
   - Shows long-term behavior

3. **Detrended (Residuals)** (bottom-left)
   - Data with trend removed
   - Reveals cyclical patterns

4. **Rolling Statistics** (bottom-right)
   - Moving average and standard deviation
   - Shows stability over time

**Use Case**: Detect performance degradation, warm-up effects, thermal throttling

**Interpretation**:
- Upward trend → performance degrading
- Downward trend → cache warming up
- Increasing std dev → stability decreasing
- Periodic patterns → external interference (cron jobs, etc.)

---

### 5. Correlation Matrix

**File**: `correlation_matrix.png`

**Features**:
- Heatmap showing correlations between all experiments
- Values from -1 (negative correlation) to +1 (positive correlation)
- Color coded: green (positive), red (negative)

**Use Case**: Find related experiments, detect common factors

**Interpretation**:
- High positive correlation (>0.7) → experiments affected by same factors
- High negative correlation (<-0.7) → inverse relationship
- Low correlation (~0) → independent experiments

---

### 6. Comparison Dashboard

**File**: `comparison_dashboard.png`

**Nine Analysis Panels**:

1. **Runtime Distribution** - Box plots side-by-side
2. **Mean Comparison** - Bar chart with error bars
3. **Coefficient of Variation** - Stability metric (lower = better)
4. **CDF Overlay** - All experiments on one plot
5. **Tail Latency** - Percentile comparison (p50, p90, p95, p99)
6. **Sample Size** - Number of runs per experiment
7. **Normalized Performance** - Relative to baseline (100% = baseline)
8. **Min-Max Range** - Spread of measurements
9. **Statistical Summary** - Table with mean, median, stddev, N

**Use Case**: Comprehensive cross-experiment comparison, identify best performers

**Interpretation**:
- Green bars in normalized panel → faster than baseline
- Red bars → slower than baseline
- High CV → inconsistent performance
- Large range → high variability

## 🔧 Command-Line Options

```bash
# Generate all plots for all experiments
python3 analyze/plot_advanced.py

# Plot specific experiments only
python3 analyze/plot_advanced.py --experiments null_baseline,pinned

# Skip comparison plots (faster)
python3 analyze/plot_advanced.py --no-compare

# Multiple experiments, with comparison
python3 analyze/plot_advanced.py --experiments "exp1,exp2,exp3" --compare
```

## 💡 Usage Examples

### Example 1: Detect Performance Regression

```bash
# Run experiment twice
./lrc run cache_hierarchy
mv data/cache_hierarchy.csv data/cache_hierarchy_v1.csv
# ... make code changes ...
./lrc run cache_hierarchy
mv data/cache_hierarchy.csv data/cache_hierarchy_v2.csv

# Compare with advanced plots
python3 analyze/plot_advanced.py \
  --experiments cache_hierarchy_v1,cache_hierarchy_v2 \
  --compare
```

Check:
- Comparison dashboard → normalized performance panel
- CDF overlay → shift in distribution
- Time series → trend changes

---

### Example 2: Analyze Outliers

```bash
./lrc run pinned
python3 analyze/plot_advanced.py --experiments pinned

# Check: pinned_outlier_analysis.png
# Look for: Agreement across detection methods
```

If outliers are consistent across methods → investigate system interference

---

### Example 3: Find Correlated Experiments

```bash
# Run all experiments
./lrc all

# Generate correlation matrix
python3 analyze/plot_advanced.py --compare

# Check: correlation_matrix.png
```

High correlation → experiments share common bottleneck

---

### Example 4: Detect Warm-Up Effects

```bash
./lrc run cache_hierarchy
python3 analyze/plot_advanced.py --experiments cache_hierarchy

# Check: cache_hierarchy_timeseries_decomposition.png
# Look at: Trend panel (top-right)
```

Downward trend at start → cache warming up

## 📈 Integration with Workflow

### Automated Analysis Pipeline

```bash
#!/bin/bash
# Full analysis workflow

# 1. Run experiments
./lrc all

# 2. Basic plots
make plots

# 3. Advanced statistical analysis
make plots-advanced

# 4. Generate report
echo "Results available in:"
echo "  - Basic: data/plots/"
echo "  - Advanced: data/plots/advanced/"
```

### CI/CD Integration

```yaml
# .github/workflows/performance.yml
- name: Run experiments
  run: ./lrc quick

- name: Generate advanced plots
  run: make plots-advanced

- name: Upload plots
  uses: actions/upload-artifact@v2
  with:
    name: performance-analysis
    path: data/plots/advanced/
```

## 🎓 Statistical Concepts

### Confidence Intervals (CI)
- **95% CI**: Range where true mean lies with 95% probability
- Narrower CI = more confident in estimate
- Larger sample size = narrower CI

### Coefficient of Variation (CV)
- **Formula**: (σ / μ) × 100
- **Low CV (<10%)**: Consistent performance
- **High CV (>20%)**: Highly variable performance

### Percentiles
- **p50 (median)**: Half of runs are faster
- **p90**: 90% of runs are faster (10% tail)
- **p99**: 99% of runs are faster (1% tail)
- **p99.9**: Focus on worst-case scenarios

### Z-Score
- **Formula**: (x - μ) / σ
- **|z| > 3**: Strong outlier (>99.7% confidence)

### Correlation Coefficient (r)
- **-1 to +1 scale**
- **|r| > 0.7**: Strong correlation
- **|r| < 0.3**: Weak correlation
- **r ≈ 0**: No linear relationship

## 🔍 Troubleshooting

### "No module named scipy"
```bash
sudo apt-get install python3-scipy
```

### Plots look crowded
Reduce number of experiments:
```bash
python3 analyze/plot_advanced.py --experiments exp1,exp2
```

### Memory error with large datasets
Process experiments individually:
```bash
for exp in *.csv; do
    python3 analyze/plot_advanced.py --experiments ${exp%.csv}
done
```

## 📊 Output Quality

- **Resolution**: 150 DPI (publication-ready)
- **Format**: PNG (for wide compatibility)
- **Size**: ~500KB - 2MB per plot
- **Dimensions**: Optimized for A4 printing and presentations

## 🎨 Customization

Edit `analyze/plot_advanced.py`:

```python
# Change confidence level
ci_low, ci_high = self._calculate_ci(data, confidence=0.99)  # 99% CI

# Change color scheme
COLORS = ['#YOUR', '#COLOR', '#SCHEME']

# Adjust resolution
plt.savefig(path, dpi=300)  # Higher resolution

# Change figure size
fig, ax = plt.subplots(figsize=(20, 12))  # Larger plots
```

## 📚 References

- **Violin Plots**: Hintze & Nelson (1998)
- **Outlier Detection**: Tukey (1977) - IQR method
- **Time Series**: Cleveland et al. (1990) - STL decomposition
- **Statistical Testing**: scipy.stats documentation

## 🎯 Best Practices

1. **Run enough samples** (≥30) for statistical significance
2. **Check outliers** before drawing conclusions
3. **Use CDF plots** for tail latency analysis
4. **Compare against baseline** for performance changes
5. **Look at trends** for warm-up/degradation effects
6. **Check correlation** for related experiments

---

**Advanced plotting elevates your analysis from basic metrics to deep statistical insights!** 📊✨
