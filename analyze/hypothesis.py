#!/usr/bin/env python3
"""
Hypothesis Testing Framework for Linux Reality Check

Academically rigorous statistical comparison using non-parametric methods
appropriate for heavy-tailed systems performance data.

Academic Rationale:
  Traditional t-tests assume:
  - Normal distributions
  - Independent observations
  - Equal variances
  
  Systems data violates all three assumptions. This module provides:
  - Quantile-based comparisons (not mean-based)
  - Bootstrap confidence intervals (non-parametric)
  - Hodges-Lehmann estimator (robust location shift)
  - Effect sizes on quantiles (not Cohen's d)

References:
  - Hodges & Lehmann (1963). Estimates of location based on rank tests
  - Efron & Tibshirani (1993). An Introduction to the Bootstrap
  - Doksum (1974). Empirical probability plots and statistical inference

Usage:
  # Quantile-based comparison
  python3 analyze/hypothesis.py --baseline data/baseline.csv \\
      --treatment data/treatment.csv --metric runtime_ns --quantile-compare

  # Bootstrap CI on specific quantile
  python3 analyze/hypothesis.py --baseline data/v1.csv \\
      --treatment data/v2.csv --metric runtime_ns --quantile 0.99
"""

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional

sys.path.insert(0, str(Path(__file__).parent))
from robust_stats import (
    quantile,
    median,
    iqr,
    mad,
    hodges_lehmann_estimator,
    bootstrap_ci_quantile,
    quantile_difference_ci,
    format_quantile_comparison,
    describe_robust
)

# Try scipy for compatibility with legacy code
try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    print("Warning: scipy not available, using bootstrap methods", file=sys.stderr)


def load_metric(csv_path: Path, metric: str) -> List[float]:
    """Load metric values from CSV."""
    values = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                values.append(float(row[metric]))
            except (ValueError, KeyError):
                continue
    return values


def calculate_statistics(values: List[float]) -> Dict:
    """Calculate basic statistics."""
    n = len(values)
    if n == 0:
        return {'n': 0, 'mean': 0, 'std': 0}
    
    mean = sum(values) / n
    
    if n < 2:
        return {'n': n, 'mean': mean, 'std': 0}
    
    variance = sum((x - mean) ** 2 for x in values) / (n - 1)
    std = math.sqrt(variance)
    
    return {'n': n, 'mean': mean, 'std': std}


def quantile_based_comparison(baseline: List[float], treatment: List[float],
                             quantiles: Optional[List[float]] = None) -> Dict:
    """
    Academically correct comparison using quantiles (not means).
    
    Reports differences at key percentiles (p50, p90, p95, p99) with
    bootstrap confidence intervals.
    
    This is the recommended method for systems research papers.
    """
    if quantiles is None:
        quantiles = [0.50, 0.90, 0.95, 0.99]
    
    results = {
        'quantiles': {},
        'hodges_lehmann': hodges_lehmann_estimator(baseline, treatment),
        'baseline_summary': describe_robust(baseline),
        'treatment_summary': describe_robust(treatment)
    }
    
    for q in quantiles:
        diff, lower_ci, upper_ci = quantile_difference_ci(
            baseline, treatment, q, n_bootstrap=5000
        )
        
        q_baseline = quantile(baseline, q)
        q_treatment = quantile(treatment, q)
        
        pct_change = (diff / q_baseline * 100) if q_baseline != 0 else 0.0
        
        # Check if CI excludes zero (significant difference)
        significant = (lower_ci > 0 and upper_ci > 0) or (lower_ci < 0 and upper_ci < 0)
        
        q_name = f"p{int(q * 100)}"
        
        results['quantiles'][q_name] = {
            'baseline': q_baseline,
            'treatment': q_treatment,
            'difference': diff,
            'percent_change': pct_change,
            'ci_lower': lower_ci,
            'ci_upper': upper_ci,
            'significant': significant
        }
    
    return results


def cohens_d(mean1: float, mean2: float, std1: float, std2: float, n1: int, n2: int) -> float:
    """Calculate Cohen's d effect size (legacy, for t-test)."""
    pooled_std = math.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return 0.0
    return (mean1 - mean2) / pooled_std


def ttest_independent(baseline: List[float], treatment: List[float]) -> Dict:
    """
    Perform independent samples t-test.
    
    Returns dict with t_statistic, p_value, significant
    """
    stats1 = calculate_statistics(baseline)
    stats2 = calculate_statistics(treatment)
    
    if stats1['n'] < 2 or stats2['n'] < 2:
        return {'error': 'Need at least 2 samples per group'}
    
    # Calculate t-statistic
    se = math.sqrt(stats1['std']**2/stats1['n'] + stats2['std']**2/stats2['n'])
    
    if se == 0:
        t_statistic = float('inf') if stats1['mean'] != stats2['mean'] else 0
    else:
        t_statistic = (stats1['mean'] - stats2['mean']) / se
    
    df = stats1['n'] + stats2['n'] - 2
    
    # Calculate p-value
    if SCIPY_AVAILABLE:
        p_value = 2 * (1 - stats.t.cdf(abs(t_statistic), df))
    else:
        # Rough approximation
        if abs(t_statistic) < 1.96:
            p_value = 0.05
        elif abs(t_statistic) < 2.576:
            p_value = 0.01
        else:
            p_value = 0.001
    
    effect_size = cohens_d(stats1['mean'], stats2['mean'], 
                          stats1['std'], stats2['std'],
                          stats1['n'], stats2['n'])
    
    return {
        't_statistic': t_statistic,
        'p_value': p_value,
        'df': df,
        'baseline_mean': stats1['mean'],
        'treatment_mean': stats2['mean'],
        'difference': stats1['mean'] - stats2['mean'],
        'percent_change': ((stats2['mean'] - stats1['mean']) / stats1['mean'] * 100) if stats1['mean'] != 0 else 0,
        'effect_size': effect_size,
        'significant': p_value < 0.05
    }


def print_quantile_comparison_results(result: Dict, baseline_name: str, treatment_name: str):
    """Print quantile-based comparison results (academically correct)."""
    print("=" * 80)
    print("QUANTILE-BASED COMPARISON (academically rigorous)")
    print("=" * 80)
    print()
    print(f"Baseline:  {baseline_name}")
    print(f"Treatment: {treatment_name}")
    print()
    
    print("Methodology:")
    print("  - Non-parametric quantile comparison (robust to heavy tails)")
    print("  - Bootstrap 95% confidence intervals (5000 resamples)")
    print("  - No parametric assumptions (no normality required)")
    print()
    
    # Robust summary statistics
    print("Summary Statistics:")
    print(f"  Baseline  - Median: {result['baseline_summary']['median']:.2f}, "
          f"IQR: {result['baseline_summary']['iqr']:.2f}, "
          f"Tail ratio: {result['baseline_summary']['tail_ratio']:.2f}x")
    print(f"  Treatment - Median: {result['treatment_summary']['median']:.2f}, "
          f"IQR: {result['treatment_summary']['iqr']:.2f}, "
          f"Tail ratio: {result['treatment_summary']['tail_ratio']:.2f}x")
    print()
    
    # Hodges-Lehmann estimator (robust location shift)
    hl = result['hodges_lehmann']
    print(f"Hodges-Lehmann Estimator (robust location shift):")
    print(f"  Estimated shift: {hl:.2f}")
    print()
    
    # Quantile differences with CIs
    print("Quantile Differences (with 95% bootstrap CI):")
    print()
    print("Percentile | Baseline | Treatment |   Diff   | % Change | 95% CI          | Sig?")
    print("-" * 85)
    
    for q_name, q_data in sorted(result['quantiles'].items()):
        sig_marker = "✓" if q_data['significant'] else "✗"
        
        print(f"{q_name:10s} | "
              f"{q_data['baseline']:8.2f} | "
              f"{q_data['treatment']:9.2f} | "
              f"{q_data['difference']:8.2f} | "
              f"{q_data['percent_change']:+7.1f}% | "
              f"[{q_data['ci_lower']:6.2f}, {q_data['ci_upper']:6.2f}] | "
              f"{sig_marker}")
    
    print()
    print("Interpretation:")
    print("  ✓ = CI excludes zero (significant difference)")
    print("  ✗ = CI includes zero (no significant difference)")
    print()
    
    # Overall conclusion
    p99_data = result['quantiles'].get('p99', {})
    p50_data = result['quantiles'].get('p50', {})
    
    if p99_data.get('significant'):
        direction = "lower" if p99_data['difference'] < 0 else "higher"
        print(f"Tail Latency (p99): Treatment is {abs(p99_data['percent_change']):.1f}% {direction}")
    
    if p50_data.get('significant'):
        direction = "faster" if p50_data['difference'] < 0 else "slower"
        print(f"Median Performance: Treatment is {abs(p50_data['percent_change']):.1f}% {direction}")
    
    print()
    print("Academic Note:")
    print("  This analysis uses non-parametric methods appropriate for")
    print("  heavy-tailed systems data. Quantile comparisons are preferred")
    print("  over mean-based tests (t-tests) in systems research.")
    print()


def print_ttest_results_legacy(result: Dict, baseline_name: str, treatment_name: str):
    """Print legacy t-test results (kept for backwards compatibility)."""
    print("=" * 70)
    print("LEGACY T-TEST RESULTS (Not Academically Sound for Systems Data)")
    print("=" * 70)
    print()
    print(f"Baseline:  {baseline_name}")
    print(f"Treatment: {treatment_name}")
    print()
    print("Descriptive Statistics:")
    print(f"  Baseline mean:  {result['baseline_mean']:.2f}")
    print(f"  Treatment mean: {result['treatment_mean']:.2f}")
    print(f"  Difference:     {result['difference']:.2f}")
    print(f"  Percent change: {result['percent_change']:.1f}%")
    print()
    print("Statistical Test:")
    print(f"  t-statistic: {result['t_statistic']:.3f}")
    print(f"  p-value:     {result['p_value']:.4f}")
    print(f"  df:          {result['df']}")
    print()
    print("Effect Size:")
    print(f"  Cohen's d:   {result['effect_size']:.3f}")
    
    if abs(result['effect_size']) < 0.2:
        effect_interp = "negligible"
    elif abs(result['effect_size']) < 0.5:
        effect_interp = "small"
    elif abs(result['effect_size']) < 0.8:
        effect_interp = "medium"
    else:
        effect_interp = "large"
    
    print(f"  Interpretation: {effect_interp}")
    print()
    print("Conclusion:")
    
    if result['significant']:
        direction = "faster" if result['difference'] > 0 else "slower"
        print(f"  ✓ Significant difference detected (p < 0.05)")
        print(f"  Treatment is {abs(result['percent_change']):.1f}% {direction} than baseline")
    else:
        print(f"  ✗ No significant difference (p >= 0.05)")
        print(f"  Cannot reject null hypothesis")
    print()


def bayesian_comparison(baseline: List[float], treatment: List[float]) -> Dict:
    """
    Simple Bayesian comparison using normal priors.
    
    Returns probability that treatment is better than baseline.
    """
    stats1 = calculate_statistics(baseline)
    stats2 = calculate_statistics(treatment)
    
    # Simplified: assume normal distributions
    # P(treatment > baseline) ≈ based on z-score
    
    diff_mean = stats2['mean'] - stats1['mean']
    diff_se = math.sqrt(stats1['std']**2/stats1['n'] + stats2['std']**2/stats2['n'])
    
    if diff_se == 0:
        prob_better = 1.0 if diff_mean > 0 else 0.0
    else:
        z = diff_mean / diff_se
        
        if SCIPY_AVAILABLE:
            prob_better = stats.norm.cdf(z)
        else:
            # Rough approximation
            prob_better = 0.5 + 0.4 * (z / (1 + abs(z)))
            prob_better = max(0.0, min(1.0, prob_better))
    
    return {
        'prob_treatment_better': prob_better,
        'prob_baseline_better': 1.0 - prob_better,
        'difference_mean': diff_mean,
        'difference_se': diff_se
    }


def print_bayesian_results(result: Dict, baseline_name: str, treatment_name: str):
    """Print Bayesian comparison results."""
    print("=" * 70)
    print("BAYESIAN COMPARISON")
    print("=" * 70)
    print()
    print(f"Baseline:  {baseline_name}")
    print(f"Treatment: {treatment_name}")
    print()
    print("Posterior Probabilities:")
    print(f"  P(Treatment > Baseline): {result['prob_treatment_better']:.1%}")
    print(f"  P(Baseline > Treatment): {result['prob_baseline_better']:.1%}")
    print()
    print("Expected Difference:")
    print(f"  Mean: {result['difference_mean']:.2f} ± {result['difference_se']:.2f}")
    print()
    print("Decision:")
    
    if result['prob_treatment_better'] > 0.95:
        print("  ✓ Strong evidence for treatment (>95% probability)")
    elif result['prob_treatment_better'] > 0.80:
        print("  ⚠ Moderate evidence for treatment (>80% probability)")
    elif result['prob_baseline_better'] > 0.80:
        print("  ⚠ Moderate evidence for baseline (>80% probability)")
    else:
        print("  ≈ Inconclusive (<80% probability either way)")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Hypothesis Testing Framework (Academically Rigorous)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quantile-based comparison (RECOMMENDED)
  python3 hypothesis.py --baseline data/v1.csv \\
      --treatment data/v2.csv --metric runtime_ns --quantile-compare

  # Legacy t-test (for reference only, not academically sound for systems data)
  python3 hypothesis.py --baseline data/v1.csv \\
      --treatment data/v2.csv --metric runtime_ns --legacy-ttest

Academic Note:
  The quantile-based comparison is the academically correct method for
  heavy-tailed systems data. T-tests assume normality and are unreliable
  for latency/cache/bandwidth measurements.
        """
    )
    
    parser.add_argument('--baseline', required=True, help='Baseline CSV file')
    parser.add_argument('--treatment', required=True, help='Treatment CSV file')
    parser.add_argument('--metric', required=True, help='Metric to compare')
    parser.add_argument('--quantile-compare', action='store_true',
                       help='Quantile-based comparison (RECOMMENDED)')
    parser.add_argument('--legacy-ttest', action='store_true',
                       help='Legacy t-test (not academically sound)')
    parser.add_argument('--output', help='Output JSON file')
    
    args = parser.parse_args()
    
    # Load data
    baseline_path = Path(args.baseline)
    treatment_path = Path(args.treatment)
    
    if not baseline_path.exists():
        print(f"Error: Baseline file not found: {baseline_path}", file=sys.stderr)
        return 1
    
    if not treatment_path.exists():
        print(f"Error: Treatment file not found: {treatment_path}", file=sys.stderr)
        return 1
    
    baseline = load_metric(baseline_path, args.metric)
    treatment = load_metric(treatment_path, args.metric)
    
    if not baseline:
        print(f"Error: No data for metric '{args.metric}' in baseline", file=sys.stderr)
        return 1
    
    if not treatment:
        print(f"Error: No data for metric '{args.metric}' in treatment", file=sys.stderr)
        return 1
    
    results = {}
    
    # Default to quantile comparison if nothing specified
    if not args.legacy_ttest and not args.quantile_compare:
        args.quantile_compare = True
    
    # Quantile-based comparison (RECOMMENDED)
    if args.quantile_compare:
        quantile_result = quantile_based_comparison(baseline, treatment)
        print_quantile_comparison_results(quantile_result, args.baseline, args.treatment)
        results['quantile_comparison'] = quantile_result
    
    # Legacy t-test (kept for backwards compatibility)
    if args.legacy_ttest:
        if args.quantile_compare:
            print("\n" + "=" * 80 + "\n")
        
        print("WARNING: T-test assumes normality (often violated in systems data)")
        print("         Results may be unreliable. Use quantile comparison instead.")
        print()
        
        ttest_result = ttest_independent(baseline, treatment)
        print_ttest_results_legacy(ttest_result, args.baseline, args.treatment)
        results['legacy_ttest'] = ttest_result
    
    # Export results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results exported to {args.output}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
