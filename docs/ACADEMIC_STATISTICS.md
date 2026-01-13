# Academic Statistics Guide

## Executive Summary

This document explains the **academically rigorous** statistical methods used in Linux Reality Check, contrasting them with common but inappropriate parametric methods.

**Key Point**: Systems performance data (latency, cache misses, bandwidth) violates the assumptions of traditional parametric statistics. Using mean, standard deviation, normal fits, and t-tests on such data is **academically unsound** and would be rejected by reviewers in peer-reviewed venues.

---

## The Problem with Parametric Statistics for Systems Data

### Assumptions of Parametric Methods (Mean, Std, T-tests, Normal Fits)

1. **Normality**: Data follows a Gaussian distribution
2. **Independence**: Observations are independent
3. **Homoscedasticity**: Equal variances across groups
4. **Light tails**: Extreme values are rare outliers to be removed

### Reality of Systems Performance Data

1. **Heavy-tailed**: Extreme values are meaningful (p99 latency matters!)
2. **Multimodal**: Multiple performance regimes (cache hit/miss, CPU states)
3. **Dependent**: Correlated observations (warmup, contention, memory state)
4. **Non-stationary**: Distribution changes over time (thermal effects, scheduling)

### Academic Consequence

> "The assumption of normality is violated, rendering the reported statistics unreliable."  
> — What a reviewer would write

---

## Academically Correct Methods (What We Use)

### 1. Distribution Summaries

| [WRONG] Wrong (Parametric)        | [OK] Correct (Non-parametric) | Why                                    |
|------------------------------|-----------------------------|-----------------------------------------|
| Mean                         | **Median**                  | Robust to outliers/heavy tails          |
| Standard deviation           | **IQR** or **MAD**          | Doesn't explode with tail events        |
| Histogram                    | **ECDF**                    | No binning artifacts                    |
| KDE / Violin (smoothed)      | **Boxplot / ECDF**          | No false smoothness                     |
| CV (std/mean)                | **MAD/median**              | Robust variability measure              |

**Code Example:**
```python
from analyze.robust_stats import describe_robust

stats = describe_robust(latency_data)
print(f"Median: {stats['median']:.2f} ms")
print(f"IQR: {stats['iqr']:.2f} ms")
print(f"p99: {stats['p99']:.2f} ms")
print(f"Tail ratio (p99/p50): {stats['tail_ratio']:.2f}x")
```

---

### 2. Outlier Handling

| [WRONG] Wrong                              | [OK] Correct                                    |
|---------------------------------------|-----------------------------------------------|
| Remove outliers (z-score > 3)         | **Retain outliers** (they are the problem!)   |
| Treat tails as noise                  | **Report p99, p99.9** explicitly              |
| Mean ± 3σ thresholds                  | **Tukey fences** (for flagging only)          |

**Academic Note:**  
In systems research, **outliers = tail latency = what we care about**. Removing them invalidates the analysis.

**Code Example:**
```python
from analyze.robust_stats import tukey_fences

lower, upper, flagged = tukey_fences(data, k=1.5)
print(f"Extreme values: {len(flagged)}/{len(data)}")
print("NOTE: These are RETAINED as meaningful tail behavior")
```

---

### 3. Hypothesis Testing / Comparisons

| [WRONG] Wrong (Parametric)              | [OK] Correct (Non-parametric)                   |
|------------------------------------|-----------------------------------------------|
| Independent t-test                 | **Quantile differences** (p50, p90, p99)      |
| Cohen's d (mean-based effect size) | **Hodges-Lehmann estimator**                  |
| Parametric CI (mean ± t·SE)        | **Bootstrap CI** on quantiles                 |
| P-value testing                    | **Estimation** with confidence intervals      |

**Why T-tests Fail:**
- They test "Are the **means** different?"
- But systems data cares about "Is the **p99 latency** different?"
- Mean is unstable in heavy tails

**Code Example:**
```python
from analyze.hypothesis import quantile_based_comparison

result = quantile_based_comparison(baseline, treatment)

# Reports differences at p50, p90, p95, p99 with bootstrap CIs
print(result['quantiles']['p99'])
# Output: {'difference': -15.3, 'ci_lower': -22.1, 'ci_upper': -8.7, 'significant': True}
```

---

### 4. Confidence Intervals

| [WRONG] Wrong                     | [OK] Correct                                  |
|------------------------------|---------------------------------------------|
| CI on mean (assuming normal) | **Bootstrap CI on median**                  |
| CI on std                    | **Bootstrap CI on IQR**                     |
| Parametric formulas          | **Bootstrap CI on p99**                     |

**Why Bootstrap?**
- No distributional assumptions
- Works for any statistic (median, p99, etc.)
- Academically accepted for non-normal data

**Code Example:**
```python
from analyze.robust_stats import bootstrap_ci_quantile

p99, lower, upper = bootstrap_ci_quantile(data, q=0.99, n_bootstrap=10000)
print(f"p99 latency: {p99:.2f} ms [95% CI: {lower:.2f}, {upper:.2f}]")
```

---

### 5. Time Series Analysis

| [WRONG] Wrong                          | [OK] Correct                                  |
|-----------------------------------|---------------------------------------------|
| Polynomial trend fitting          | **Change-point detection**                  |
| Rolling mean/std                  | **Regime segmentation**                     |
| Treating as stationary            | **State-based analysis**                    |

**Why?**  
Systems performance doesn't have smooth trends—it has **regime changes**:
- Cold start -> warmed up
- Low load -> high load
- Throttled -> un-throttled

**Code Example:**
```python
from analyze.timeseries import detect_warmup, detect_throttling

has_warmup, overhead_pct = detect_warmup(runs)
if has_warmup:
    print(f"Warmup effect: first runs {overhead_pct:+.1f}% slower")
```

---

## Visualization Best Practices

### Primary Plots (Always Include)

1. **ECDF (Empirical CDF)**
   - Shows full distribution without artifacts
   - No binning decisions needed
   - Clearly shows tail behavior

2. **Quantile plots** (p50, p90, p95, p99 over time or conditions)
   - Directly shows what matters
   - No parametric assumptions

3. **Boxplots** (Tukey style)
   - Shows median, IQR, and flagged extremes
   - Robust to outliers

### Secondary Plots (If Needed)

4. **Histograms** (if you must)
   - But state bin width explicitly
   - Never use for tail analysis

5. **Violin plots** (if you must)
   - **WITHOUT kernel density smoothing**
   - Or state bandwidth explicitly

### Never Use

[WRONG] Normal distribution overlays  
[WRONG] KDE with default bandwidth (hides tails)  
[WRONG] Mean ± std error bars (unstable for heavy tails)  

---

## How to Report Results in Papers

### [WRONG] Wrong Way
```
"We measured mean latency of 10.5 ± 2.3 ms (mean ± std).
T-test shows significant difference (p < 0.05).
We removed 5 outliers using z-score > 3."
```

**Reviewer response:**  
*"The assumption of normality is violated. Outlier removal is unjustified. Please use non-parametric methods."*

---

### [OK] Correct Way
```
"We analyzed performance using non-parametric methods.
Distributions are summarized via median and IQR:
  Baseline: median 10.2 ms (IQR 2.1 ms)
  Optimized: median 8.7 ms (IQR 1.8 ms)

Tail latency (p99) improved from 24.3 ms to 18.1 ms
(95% bootstrap CI: [-8.5, -3.9] ms, 5000 resamples).

All measurements are retained; extreme values represent
meaningful tail behavior rather than outliers to be removed."
```

**Reviewer response:**  
*"Statistical methodology is sound."* [OK]

---

## Summary: What Changed

| Component               | Old (Wrong)                   | New (Correct)                     |
|-------------------------|-------------------------------|-----------------------------------|
| `distributions.py`      | Histogram, mean, std          | ECDF, median, IQR, MAD            |
| `outliers.py`           | Flag and suggest removal      | Flag but RETAIN, explain tail     |
| `hypothesis.py`         | T-test, Cohen's d             | Quantile diff, Hodges-Lehmann     |
| `confidence_intervals.py`| Parametric CI on mean        | Bootstrap CI on quantiles         |
| `timeseries.py`         | Polynomial trends             | Change-point detection            |
| `plot_advanced.py`      | Normal fits, KDE smoothing    | ECDF, boxplots, raw quantiles     |

---

## References

### Academic Papers
- Hogg, McKean & Craig (2019). *Introduction to Mathematical Statistics*. 8th ed.
- Rousseeuw & Hubert (2011). *Robust statistics for outlier detection*. WIREs Data Mining.
- Efron & Tibshirani (1993). *An Introduction to the Bootstrap*. Chapman & Hall.
- Hodges & Lehmann (1963). *Estimates of location based on rank tests*. Ann. Math. Stat.

### Systems Research Best Practices
- Dean & Barroso (2013). *The Tail at Scale*. CACM.
- Ousterhout (2018). *Always Measure One Level Deeper*. CACM.

---

## Module Usage

### Quick Start

```python
# 1. Load your data
from analyze.parse import parse_csv
groups = parse_csv("data/experiment.csv")

# 2. Analyze with robust statistics
from analyze.distributions import analyze_distribution
for name, group in groups.items():
    analyze_distribution(group)  # Uses non-parametric methods

# 3. Compare treatments
from analyze.hypothesis import quantile_based_comparison
baseline = groups['baseline'].runs
treatment = groups['optimized'].runs

result = quantile_based_comparison(
    [r.runtime_ms for r in baseline],
    [r.runtime_ms for r in treatment]
)

# Reports quantile differences with bootstrap CIs
```

### Full Analysis Pipeline

```bash
# Distribution analysis (ECDF, quantiles, tail ratio)
python3 analyze/distributions.py data/results.csv

# Quantile-based comparison
python3 analyze/hypothesis.py \
    --baseline data/baseline.csv \
    --treatment data/optimized.csv \
    --metric runtime_ns \
    --quantile-compare

# Time series (warmup, throttling, regime changes)
python3 analyze/timeseries.py data/results.csv
```

---

## Frequently Asked Questions

### Q: Can I still use mean and standard deviation?

**A:** You can **report** them for reference, but:
1. Don't use them for inference (no t-tests)
2. Always report median and IQR alongside
3. Note that mean/std are "unreliable for heavy-tailed distributions"

### Q: What about small sample sizes?

**A:** Non-parametric methods work better than parametric with small samples!
- Bootstrap still works (but use more resamples)
- Quantiles are more stable than means
- No distributional assumptions to worry about

### Q: Is this overkill for internal analysis?

**A:** No. This is about **correctness**, not formality.
- Wrong methods give wrong conclusions
- "Optimized" system might actually be worse at p99
- Mean improvements can hide tail regressions

### Q: How do I convince my team/reviewer?

**A:** Show them this document and cite:
- *The Tail at Scale* (Dean & Barroso, CACM 2013)
- Modern statistics textbooks (Efron, Rousseeuw)
- Point out that mean-based methods assume normality (they don't have)

---

## Conclusion

**Key Takeaway:**  
Systems performance data requires non-parametric methods. Using mean, std, normal fits, and t-tests is academically unsound and can lead to wrong conclusions.

**This framework provides:**
- [OK] Academically rigorous methods
- [OK] Appropriate for heavy-tailed data
- [OK] Accepted in peer-reviewed venues
- [OK] Correct inference about tail behavior

**Use it for:**
- Academic papers
- Performance analysis reports
- A/B testing
- Regression detection
- Any scenario where correctness matters
