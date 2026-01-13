#!/usr/bin/env python3
"""
hypothesis_test.py - Statistical hypothesis testing

Purpose:
  Determine if observed differences are statistically significant.
  Calculate effect sizes.
  Provide scientific rigor to claims.
"""

import sys
from pathlib import Path
from typing import List, Tuple
import statistics
import math
sys.path.insert(0, str(Path(__file__).parent))
from parse import parse_csv, RunGroup


def welch_t_test(group1: List[float], group2: List[float]) -> Tuple[float, float]:
    """
    Welch's t-test (unequal variances).
    Returns (t_statistic, degrees_of_freedom).
    """
    n1, n2 = len(group1), len(group2)
    
    if n1 < 2 or n2 < 2:
        return (0.0, 0.0)
    
    mean1 = statistics.mean(group1)
    mean2 = statistics.mean(group2)
    
    var1 = statistics.variance(group1)
    var2 = statistics.variance(group2)
    
    # Welch's t-statistic
    t_stat = (mean1 - mean2) / math.sqrt(var1/n1 + var2/n2)
    
    # Welch-Satterthwaite degrees of freedom
    numerator = (var1/n1 + var2/n2) ** 2
    denominator = (var1/n1)**2 / (n1-1) + (var2/n2)**2 / (n2-1)
    df = numerator / denominator if denominator > 0 else 0
    
    return (t_stat, df)


def cohens_d(group1: List[float], group2: List[float]) -> float:
    """
    Cohen's d effect size.
    
    Interpretation:
      0.2 = small
      0.5 = medium
      0.8 = large
    """
    if len(group1) < 2 or len(group2) < 2:
        return 0.0
    
    mean1 = statistics.mean(group1)
    mean2 = statistics.mean(group2)
    
    var1 = statistics.variance(group1)
    var2 = statistics.variance(group2)
    
    n1, n2 = len(group1), len(group2)
    
    # Pooled standard deviation
    pooled_std = math.sqrt(((n1-1)*var1 + (n2-1)*var2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0
    
    return (mean1 - mean2) / pooled_std


def t_to_p_value_approx(t: float, df: float) -> str:
    """
    Approximate p-value from t-statistic.
    Returns significance level as string.
    """
    abs_t = abs(t)
    
    # Rough approximations for common df ranges
    if df < 5:
        thresholds = [(4.604, 0.001), (2.776, 0.01), (2.015, 0.05), (1.476, 0.10)]
    elif df < 10:
        thresholds = [(3.499, 0.001), (2.634, 0.01), (1.812, 0.05), (1.372, 0.10)]
    elif df < 30:
        thresholds = [(3.250, 0.001), (2.462, 0.01), (1.701, 0.05), (1.310, 0.10)]
    else:
        thresholds = [(3.090, 0.001), (2.326, 0.01), (1.645, 0.05), (1.282, 0.10)]
    
    for threshold, p in thresholds:
        if abs_t >= threshold:
            return f"p < {p:.3f}"
    
    return "p > 0.10"


def interpret_effect_size(d: float) -> str:
    """Interpret Cohen's d."""
    abs_d = abs(d)
    
    if abs_d < 0.2:
        return "negligible"
    elif abs_d < 0.5:
        return "small"
    elif abs_d < 0.8:
        return "medium"
    else:
        return "large"


def compare_groups(name1: str, group1: RunGroup, 
                  name2: str, group2: RunGroup) -> None:
    """Compare two groups statistically."""
    print(f"\n{'='*70}")
    print(f"Comparing: {name1} vs {name2}")
    print(f"{'='*70}")
    
    runtimes1 = [m.runtime_ms for m in group1.runs]
    runtimes2 = [m.runtime_ms for m in group2.runs]
    
    # Descriptive statistics
    mean1 = statistics.mean(runtimes1)
    mean2 = statistics.mean(runtimes2)
    diff_pct = ((mean2 - mean1) / mean1) * 100
    
    print(f"\nDescriptive Statistics:")
    print(f"  {name1}:")
    print(f"    Mean: {mean1:.2f} ms")
    print(f"    SD:   {statistics.stdev(runtimes1):.2f} ms")
    print(f"    N:    {len(runtimes1)}")
    
    print(f"  {name2}:")
    print(f"    Mean: {mean2:.2f} ms")
    print(f"    SD:   {statistics.stdev(runtimes2):.2f} ms")
    print(f"    N:    {len(runtimes2)}")
    
    print(f"\n  Difference: {mean2 - mean1:+.2f} ms ({diff_pct:+.1f}%)")
    
    # Welch's t-test
    t_stat, df = welch_t_test(runtimes1, runtimes2)
    p_value_str = t_to_p_value_approx(t_stat, df)
    
    print(f"\nWelch's t-test:")
    print(f"  t-statistic: {t_stat:.3f}")
    print(f"  df:          {df:.1f}")
    print(f"  {p_value_str}")
    
    # Cohen's d
    d = cohens_d(runtimes1, runtimes2)
    effect = interpret_effect_size(d)
    
    print(f"\nEffect Size (Cohen's d):")
    print(f"  d = {d:.3f} ({effect})")
    
    # Conclusion
    print(f"\nConclusion:")
    
    if "p < 0.05" in p_value_str or "p < 0.01" in p_value_str or "p < 0.001" in p_value_str:
        print(f"  ✓ Difference is STATISTICALLY SIGNIFICANT")
        
        if abs(d) < 0.5:
            print(f"  ⚠ But effect size is {effect} - may not be practically important")
        else:
            print(f"  ✓ Effect size is {effect} - difference is meaningful")
    else:
        print(f"  ✗ Difference is NOT statistically significant")
        print(f"  → Cannot confidently say groups differ")
        print(f"  → May need more samples or larger effect")


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <data.csv>", file=sys.stderr)
        print(f"\nCompares all pairs of groups in the CSV.", file=sys.stderr)
        sys.exit(1)
    
    filepath = Path(sys.argv[1])
    groups = parse_csv(filepath)
    
    print(f"=== Hypothesis Testing: {filepath.name} ===")
    
    group_list = list(groups.items())
    
    if len(group_list) < 2:
        print("\nNeed at least 2 groups to compare")
        sys.exit(1)
    
    # Compare all pairs
    for i in range(len(group_list)):
        for j in range(i + 1, len(group_list)):
            name1, group1 = group_list[i]
            name2, group2 = group_list[j]
            compare_groups(name1, group1, name2, group2)
    
    print()


if __name__ == '__main__':
    main()
