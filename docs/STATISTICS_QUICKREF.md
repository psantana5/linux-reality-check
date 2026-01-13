# Quick Reference: Robust vs Parametric Statistics

## One-Page Cheat Sheet

### Distribution Summary

| Statistic              | Parametric (❌)    | Non-Parametric (✅) | When to Use     |
|------------------------|--------------------|---------------------|-----------------|
| Central tendency       | Mean               | **Median**          | Always          |
| Spread                 | Std deviation      | **IQR** or **MAD**  | Always          |
| Variability ratio      | CV (std/mean)      | **MAD/median**      | Comparing spread|
| Percentiles            | Assuming normal    | **Direct quantile** | Always          |

### Visualization

| Plot Type              | Parametric (❌)         | Non-Parametric (✅)  | Purpose           |
|------------------------|-------------------------|---------------------|-------------------|
| Distribution shape     | Histogram (bins!)       | **ECDF**            | See full data     |
| Distribution density   | KDE (smoothing!)        | **Boxplot**         | Show quartiles    |
| Comparison             | Bar with error bars     | **Quantile plot**   | Compare p50-p99   |
| Overlay                | Normal fit curve        | **(none)**          | Don't assume      |

### Outliers

| Approach               | Parametric (❌)              | Non-Parametric (✅)           |
|------------------------|------------------------------|------------------------------|
| Detection              | Z-score > 3                  | **Tukey fences (IQR)**       |
| Action                 | Remove                       | **Retain & report**          |
| Interpretation         | Noise to clean               | **Tail behavior = the point**|

### Comparison (A/B Testing)

| Method                 | Parametric (❌)              | Non-Parametric (✅)           |
|------------------------|------------------------------|------------------------------|
| Test statistic         | T-test (means)               | **Quantile differences**     |
| Effect size            | Cohen's d                    | **Hodges-Lehmann**           |
| Uncertainty            | Parametric CI (t-dist)       | **Bootstrap CI**             |
| Report                 | "p < 0.05"                   | **"p99: Δ=-5ms [CI:-8,-2]"** |

### Confidence Intervals

| Parameter              | Parametric (❌)              | Non-Parametric (✅)           |
|------------------------|------------------------------|------------------------------|
| Mean                   | CI = mean ± t·SE             | **Bootstrap CI on median**   |
| Variance               | Chi-squared based            | **Bootstrap CI on IQR**      |
| Percentiles            | Assume normal                | **Bootstrap CI on quantile** |

---

## Code Quick Reference

```python
from analyze.robust_stats import *

# Summary statistics
stats = describe_robust(data)
stats['median']      # Central tendency (not mean)
stats['iqr']         # Spread (not std)
stats['mad']         # Alternative spread
stats['p99']         # Tail latency
stats['tail_ratio']  # p99/p50 (heaviness)

# Specific quantiles
median(data)         # p50
quantile(data, 0.99) # p99
iqr(data)            # Q3 - Q1
mad(data)            # Median absolute deviation

# Outlier flagging (retain!)
lower, upper, flagged = tukey_fences(data, k=1.5)
# DO NOT REMOVE flagged values

# Bootstrap CI
p99, lower, upper = bootstrap_ci_quantile(data, q=0.99, n_bootstrap=10000)
print(f"p99: {p99:.2f} [95% CI: {lower:.2f}, {upper:.2f}]")

# Compare two groups
diff, ci_low, ci_high = quantile_difference_ci(baseline, treatment, q=0.99)
print(f"Δp99: {diff:.2f} [95% CI: {ci_low:.2f}, {ci_high:.2f}]")

# Robust location shift
shift = hodges_lehmann_estimator(baseline, treatment)
```

---

## When to Use What

### ✅ Always Use Non-Parametric For:
- Latency measurements
- Cache miss counts
- Bandwidth/throughput
- Time-to-completion
- Any heavy-tailed data
- Small sample sizes
- Unknown distributions

### ❌ Parametric Might Be OK For:
- Extremely large samples (n > 10,000) where CLT applies
- Data that is provably normal (rare in systems!)
- Quick approximations (but note limitations)

### 🤔 When In Doubt:
**Use non-parametric.** It's always safe.

---

## Red Flags in Papers/Reports

If you see these, the analysis is probably wrong:

❌ "We removed outliers using z-score > 3"  
❌ "Mean latency ± standard deviation"  
❌ "T-test shows p < 0.05"  
❌ "Normal distribution overlay"  
❌ "We assume normal distribution"  
❌ "Histogram with arbitrary bins"  

✅ What you should see instead:

✅ "Median latency (IQR)"  
✅ "p99 latency with bootstrap CI"  
✅ "Quantile comparison at p50, p90, p99"  
✅ "ECDF visualization"  
✅ "Non-parametric methods (no distributional assumptions)"  
✅ "Outliers retained as meaningful tail behavior"  

---

## Emergency Decision Tree

```
Do you have systems performance data?
├─ YES → Use non-parametric methods (this guide)
└─ NO → Maybe parametric is OK (but still safer to use non-parametric)

Is your data heavy-tailed?
├─ YES → Definitely non-parametric
├─ NO → Are you sure? Check p99/p50 ratio
└─ Don't know → Use non-parametric to be safe

Do you care about tail latency (p99)?
├─ YES → Non-parametric, report quantiles
└─ NO → You should care (it matters for user experience)

Are reviewers likely to question assumptions?
├─ YES (academic paper) → Non-parametric mandatory
├─ MAYBE (tech report) → Non-parametric recommended
└─ NO (internal only) → Still use non-parametric (it's correct!)
```

---

## Common Mistakes to Avoid

### ❌ Mistake 1: "My data looks normal"
**Reality:** Visual inspection is unreliable. Tails often hidden in plots.  
**Fix:** Always check tail ratio (p99/p50). If > 1.5x, use non-parametric.

### ❌ Mistake 2: "I'll just remove outliers"
**Reality:** Outliers = the performance problem you're measuring.  
**Fix:** Flag but retain. Report p99 explicitly.

### ❌ Mistake 3: "T-test is standard"
**Reality:** T-test assumes normality. Systems data violates this.  
**Fix:** Use quantile differences with bootstrap CI.

### ❌ Mistake 4: "Mean is easier to interpret"
**Reality:** Mean is unstable in heavy tails.  
**Fix:** Report median. It's more stable and interpretable.

### ❌ Mistake 5: "I have a large sample"
**Reality:** Large n doesn't fix non-normality for inference.  
**Fix:** Use non-parametric. They scale to large n just fine.

---

## Final Rule

**When analyzing systems performance data:**

> Median, IQR, quantiles, ECDF, bootstrap.  
> No means, no stds, no normal fits, no t-tests.

Period.
