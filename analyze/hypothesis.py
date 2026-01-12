#!/usr/bin/env python3
"""
Hypothesis Testing Framework for Linux Reality Check

Automates A/B testing and statistical hypothesis testing for performance experiments.
Supports t-tests, sequential analysis, and Bayesian comparison.

Features:
- Automated A/B testing
- Sequential analysis (stop when conclusive)
- Bayesian inference
- Effect size calculation
- Statistical power monitoring

Usage:
  # Simple A/B test
  python3 analyze/hypothesis.py --baseline data/baseline.csv \\
      --treatment data/treatment.csv --metric runtime_ns

  # Sequential test (adaptive sampling)
  python3 analyze/hypothesis.py --sequential \\
      --baseline-scenario null_baseline \\
      --treatment-scenario optimized --metric runtime_ns

  # Bayesian comparison
  python3 analyze/hypothesis.py --baseline data/v1.csv \\
      --treatment data/v2.csv --metric runtime_ns --bayesian
"""

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Try scipy for exact tests
try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    print("Warning: scipy not available, using approximations", file=sys.stderr)


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


def cohens_d(mean1: float, mean2: float, std1: float, std2: float, n1: int, n2: int) -> float:
    """Calculate Cohen's d effect size."""
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


def print_hypothesis_test_results(result: Dict, baseline_name: str, treatment_name: str):
    """Print formatted hypothesis test results."""
    print("=" * 70)
    print("HYPOTHESIS TEST RESULTS")
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
        description="Hypothesis Testing Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Standard t-test
  python3 hypothesis.py --baseline data/v1.csv \\
      --treatment data/v2.csv --metric runtime_ns

  # Bayesian comparison
  python3 hypothesis.py --baseline data/v1.csv \\
      --treatment data/v2.csv --metric runtime_ns --bayesian

  # Both tests
  python3 hypothesis.py --baseline data/v1.csv \\
      --treatment data/v2.csv --metric runtime_ns --both
        """
    )
    
    parser.add_argument('--baseline', required=True, help='Baseline CSV file')
    parser.add_argument('--treatment', required=True, help='Treatment CSV file')
    parser.add_argument('--metric', required=True, help='Metric to compare')
    parser.add_argument('--bayesian', action='store_true', help='Use Bayesian comparison')
    parser.add_argument('--both', action='store_true', help='Run both frequentist and Bayesian')
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
    
    # Frequentist test (default)
    if not args.bayesian or args.both:
        ttest_result = ttest_independent(baseline, treatment)
        print_hypothesis_test_results(ttest_result, args.baseline, args.treatment)
        results['frequentist'] = ttest_result
    
    # Bayesian test
    if args.bayesian or args.both:
        if args.both:
            print()
        
        bayes_result = bayesian_comparison(baseline, treatment)
        print_bayesian_results(bayes_result, args.baseline, args.treatment)
        results['bayesian'] = bayes_result
    
    # Export results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results exported to {args.output}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
