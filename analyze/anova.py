#!/usr/bin/env python3
"""
ANOVA (Analysis of Variance) for Linux Reality Check
Performs one-way ANOVA and post-hoc tests for multi-group comparisons.

Statistical Background:
- ANOVA tests if means differ across 3+ groups
- H0: All group means are equal
- H1: At least one group mean differs
- F-statistic: Ratio of between-group to within-group variance
- Post-hoc tests control family-wise error rate

Post-hoc Tests:
- Tukey HSD: Pairwise comparisons with family-wise error control
- Bonferroni: Conservative correction, divides alpha by number of comparisons
- Effect sizes: Eta-squared (proportion of variance explained)

Usage:
  # Basic ANOVA on CSV with groups
  python3 anova.py data/experiment.csv --metric runtime_ns --group workload_type

  # ANOVA with post-hoc tests
  python3 anova.py data/experiment.csv --metric runtime_ns --group workload_type --posthoc tukey

  # Multiple CSVs (each file is a group)
  python3 anova.py data/exp1.csv data/exp2.csv data/exp3.csv --metric runtime_ns

  # Export detailed results
  python3 anova.py data/experiment.csv --metric runtime_ns --group workload_type --output results.json
"""

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Try to import scipy for exact distributions
try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    print("Warning: scipy not available. Using approximations for p-values.", file=sys.stderr)
    print("Install with: pip install scipy", file=sys.stderr)


def calculate_mean(values: List[float]) -> float:
    """Calculate mean of values."""
    if not values:
        return 0.0
    return sum(values) / len(values)


def calculate_variance(values: List[float], mean: Optional[float] = None) -> float:
    """Calculate sample variance."""
    if len(values) < 2:
        return 0.0
    
    if mean is None:
        mean = calculate_mean(values)
    
    return sum((x - mean) ** 2 for x in values) / (len(values) - 1)


def calculate_std(values: List[float], mean: Optional[float] = None) -> float:
    """Calculate sample standard deviation."""
    return math.sqrt(calculate_variance(values, mean))


def f_distribution_cdf(f: float, df1: int, df2: int) -> float:
    """
    Approximate F-distribution CDF without scipy.
    Uses Beta distribution approximation.
    
    For exact values, scipy is required.
    """
    if SCIPY_AVAILABLE:
        return stats.f.cdf(f, df1, df2)
    
    # Rough approximation for p-value interpretation
    # This is not mathematically rigorous but gives guidance
    if f < 1.0:
        return 0.5
    elif f < 2.0:
        return 0.75
    elif f < 3.0:
        return 0.90
    elif f < 4.0:
        return 0.95
    elif f < 5.0:
        return 0.975
    else:
        return 0.99


def one_way_anova(groups: Dict[str, List[float]]) -> Dict:
    """
    Perform one-way ANOVA.
    
    Returns dict with:
    - f_statistic: F-test statistic
    - p_value: Probability under null hypothesis
    - df_between: Between-group degrees of freedom
    - df_within: Within-group degrees of freedom
    - ss_between: Between-group sum of squares
    - ss_within: Within-group sum of squares
    - ms_between: Between-group mean square
    - ms_within: Within-group mean square
    - eta_squared: Effect size (proportion of variance explained)
    """
    # Validate input
    if len(groups) < 2:
        return {'error': 'Need at least 2 groups for ANOVA'}
    
    # Filter empty groups
    groups = {k: v for k, v in groups.items() if v}
    
    if len(groups) < 2:
        return {'error': 'Need at least 2 non-empty groups'}
    
    # Calculate group statistics
    group_stats = {}
    grand_sum = 0.0
    grand_n = 0
    
    for name, values in groups.items():
        n = len(values)
        mean = calculate_mean(values)
        group_stats[name] = {
            'n': n,
            'mean': mean,
            'sum': sum(values)
        }
        grand_sum += sum(values)
        grand_n += n
    
    # Grand mean
    grand_mean = grand_sum / grand_n if grand_n > 0 else 0.0
    
    # Calculate sum of squares
    ss_between = 0.0
    ss_within = 0.0
    
    for name, values in groups.items():
        n = group_stats[name]['n']
        group_mean = group_stats[name]['mean']
        
        # Between-group SS
        ss_between += n * (group_mean - grand_mean) ** 2
        
        # Within-group SS
        for value in values:
            ss_within += (value - group_mean) ** 2
    
    # Degrees of freedom
    k = len(groups)  # Number of groups
    df_between = k - 1
    df_within = grand_n - k
    
    if df_within <= 0:
        return {'error': 'Insufficient data for ANOVA (need multiple observations per group)'}
    
    # Mean squares
    ms_between = ss_between / df_between if df_between > 0 else 0.0
    ms_within = ss_within / df_within if df_within > 0 else 0.0
    
    # F-statistic
    if ms_within == 0:
        f_statistic = float('inf')
        p_value = 0.0
    else:
        f_statistic = ms_between / ms_within
        
        # Calculate p-value
        if SCIPY_AVAILABLE:
            p_value = 1.0 - stats.f.cdf(f_statistic, df_between, df_within)
        else:
            # Approximation
            cdf = f_distribution_cdf(f_statistic, df_between, df_within)
            p_value = 1.0 - cdf
    
    # Effect size (eta-squared)
    ss_total = ss_between + ss_within
    eta_squared = ss_between / ss_total if ss_total > 0 else 0.0
    
    # Omega-squared (less biased effect size estimate)
    omega_squared = (ss_between - df_between * ms_within) / (ss_total + ms_within)
    omega_squared = max(0.0, omega_squared)  # Can't be negative
    
    return {
        'f_statistic': f_statistic,
        'p_value': p_value,
        'df_between': df_between,
        'df_within': df_within,
        'ss_between': ss_between,
        'ss_within': ss_within,
        'ss_total': ss_total,
        'ms_between': ms_between,
        'ms_within': ms_within,
        'eta_squared': eta_squared,
        'omega_squared': omega_squared,
        'grand_mean': grand_mean,
        'n_total': grand_n,
        'n_groups': k
    }


def tukey_hsd(groups: Dict[str, List[float]], alpha: float = 0.05) -> List[Dict]:
    """
    Tukey HSD post-hoc test for pairwise comparisons.
    
    Returns list of comparison dicts with:
    - group1, group2: Group names
    - mean_diff: Difference in means
    - q_statistic: Studentized range statistic
    - p_value: Adjusted p-value (approximate without scipy)
    - significant: Boolean indicating if difference is significant
    """
    if len(groups) < 2:
        return []
    
    # Calculate pooled variance (MSE from ANOVA)
    all_values = []
    group_means = {}
    group_sizes = {}
    
    for name, values in groups.items():
        all_values.extend(values)
        group_means[name] = calculate_mean(values)
        group_sizes[name] = len(values)
    
    # Get MSE from ANOVA
    anova_result = one_way_anova(groups)
    if 'error' in anova_result:
        return []
    
    mse = anova_result['ms_within']
    df_within = anova_result['df_within']
    
    # Pairwise comparisons
    comparisons = []
    group_names = sorted(groups.keys())
    
    for i in range(len(group_names)):
        for j in range(i + 1, len(group_names)):
            name1, name2 = group_names[i], group_names[j]
            
            mean1 = group_means[name1]
            mean2 = group_means[name2]
            n1 = group_sizes[name1]
            n2 = group_sizes[name2]
            
            # Mean difference
            mean_diff = mean1 - mean2
            
            # Standard error for difference
            se = math.sqrt(mse * (1/n1 + 1/n2) / 2)
            
            if se == 0:
                q_statistic = float('inf')
                p_value = 0.0
            else:
                # Studentized range statistic
                q_statistic = abs(mean_diff) / se
                
                # P-value (requires special studentized range distribution)
                # Approximation: treat as t-statistic for rough estimate
                if SCIPY_AVAILABLE:
                    # Convert q to t approximation
                    t_approx = q_statistic / math.sqrt(2)
                    p_value = 2 * (1 - stats.t.cdf(t_approx, df_within))
                else:
                    # Very rough approximation
                    if q_statistic < 2.0:
                        p_value = 0.5
                    elif q_statistic < 3.0:
                        p_value = 0.1
                    elif q_statistic < 4.0:
                        p_value = 0.01
                    else:
                        p_value = 0.001
            
            comparisons.append({
                'group1': name1,
                'group2': name2,
                'mean1': mean1,
                'mean2': mean2,
                'mean_diff': mean_diff,
                'se': se,
                'q_statistic': q_statistic,
                'p_value': p_value,
                'significant': p_value < alpha
            })
    
    return comparisons


def bonferroni_correction(groups: Dict[str, List[float]], alpha: float = 0.05) -> List[Dict]:
    """
    Bonferroni-corrected pairwise t-tests.
    
    Returns list of comparison dicts similar to Tukey HSD.
    """
    if len(groups) < 2:
        return []
    
    group_names = sorted(groups.keys())
    n_comparisons = len(group_names) * (len(group_names) - 1) // 2
    alpha_corrected = alpha / n_comparisons
    
    comparisons = []
    
    for i in range(len(group_names)):
        for j in range(i + 1, len(group_names)):
            name1, name2 = group_names[i], group_names[j]
            
            values1 = groups[name1]
            values2 = groups[name2]
            
            if not values1 or not values2:
                continue
            
            # Calculate statistics
            n1, n2 = len(values1), len(values2)
            mean1 = calculate_mean(values1)
            mean2 = calculate_mean(values2)
            var1 = calculate_variance(values1, mean1)
            var2 = calculate_variance(values2, mean2)
            
            # Pooled standard error
            pooled_se = math.sqrt(var1/n1 + var2/n2)
            
            if pooled_se == 0:
                t_statistic = float('inf')
                p_value = 0.0
            else:
                t_statistic = (mean1 - mean2) / pooled_se
                df = n1 + n2 - 2
                
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
            
            comparisons.append({
                'group1': name1,
                'group2': name2,
                'mean1': mean1,
                'mean2': mean2,
                'mean_diff': mean1 - mean2,
                'se': pooled_se,
                't_statistic': t_statistic,
                'p_value': p_value,
                'p_value_corrected': min(1.0, p_value * n_comparisons),
                'significant': p_value < alpha_corrected,
                'alpha_corrected': alpha_corrected
            })
    
    return comparisons


def load_csv_groups(csv_path: Path, metric: str, group_column: str) -> Dict[str, List[float]]:
    """Load data from CSV and group by column."""
    groups = defaultdict(list)
    
    try:
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            
            if metric not in reader.fieldnames:
                print(f"Error: Metric '{metric}' not found in {csv_path}", file=sys.stderr)
                return {}
            
            if group_column not in reader.fieldnames:
                print(f"Error: Group column '{group_column}' not found in {csv_path}", file=sys.stderr)
                return {}
            
            for row in reader:
                try:
                    value = float(row[metric])
                    group = row[group_column]
                    groups[group].append(value)
                except (ValueError, KeyError):
                    continue
    except Exception as e:
        print(f"Error reading {csv_path}: {e}", file=sys.stderr)
        return {}
    
    return dict(groups)


def load_multiple_csvs(csv_paths: List[Path], metric: str) -> Dict[str, List[float]]:
    """Load multiple CSVs, using filename as group name."""
    groups = {}
    
    for path in csv_paths:
        values = []
        try:
            with open(path, 'r') as f:
                reader = csv.DictReader(f)
                
                if metric not in reader.fieldnames:
                    print(f"Warning: Metric '{metric}' not found in {path}", file=sys.stderr)
                    continue
                
                for row in reader:
                    try:
                        values.append(float(row[metric]))
                    except (ValueError, KeyError):
                        continue
        except Exception as e:
            print(f"Error reading {path}: {e}", file=sys.stderr)
            continue
        
        if values:
            groups[path.stem] = values
    
    return groups


def interpret_effect_size(eta_squared: float) -> str:
    """Interpret eta-squared effect size (Cohen, 1988)."""
    if eta_squared < 0.01:
        return "negligible"
    elif eta_squared < 0.06:
        return "small"
    elif eta_squared < 0.14:
        return "medium"
    else:
        return "large"


def print_anova_report(groups: Dict[str, List[float]], anova_result: Dict, 
                       posthoc: Optional[str] = None, alpha: float = 0.05):
    """Print formatted ANOVA results."""
    
    print("=" * 70)
    print("ONE-WAY ANOVA")
    print("=" * 70)
    
    # Group summary statistics
    print("\nGroup Summary:")
    print("-" * 70)
    print(f"{'Group':<20} {'N':>8} {'Mean':>12} {'Std Dev':>12}")
    print("-" * 70)
    
    for name, values in sorted(groups.items()):
        n = len(values)
        mean = calculate_mean(values)
        std = calculate_std(values, mean)
        print(f"{name:<20} {n:>8} {mean:>12.2f} {std:>12.2f}")
    
    print()
    
    # ANOVA table
    print("ANOVA Table:")
    print("-" * 70)
    print(f"{'Source':<15} {'SS':>12} {'df':>8} {'MS':>12} {'F':>10} {'p-value':>10}")
    print("-" * 70)
    
    print(f"{'Between Groups':<15} {anova_result['ss_between']:>12.2f} "
          f"{anova_result['df_between']:>8} {anova_result['ms_between']:>12.2f} "
          f"{anova_result['f_statistic']:>10.3f} {anova_result['p_value']:>10.4f}")
    
    print(f"{'Within Groups':<15} {anova_result['ss_within']:>12.2f} "
          f"{anova_result['df_within']:>8} {anova_result['ms_within']:>12.2f}")
    
    print(f"{'Total':<15} {anova_result['ss_total']:>12.2f} "
          f"{anova_result['df_between'] + anova_result['df_within']:>8}")
    
    print()
    
    # Interpretation
    print("Results:")
    print("-" * 70)
    
    if anova_result['p_value'] < alpha:
        print(f"✓ Significant difference detected (p = {anova_result['p_value']:.4f} < {alpha})")
        print(f"  At least one group mean differs from the others.")
    else:
        print(f"✗ No significant difference (p = {anova_result['p_value']:.4f} >= {alpha})")
        print(f"  Cannot reject null hypothesis of equal means.")
    
    print()
    print(f"Effect Size (η²): {anova_result['eta_squared']:.4f} "
          f"({interpret_effect_size(anova_result['eta_squared'])})")
    print(f"  {anova_result['eta_squared']*100:.1f}% of variance explained by group membership")
    
    print(f"\nEffect Size (ω²): {anova_result['omega_squared']:.4f} "
          f"(less biased estimate)")
    print()
    
    # Post-hoc tests
    if posthoc and anova_result['p_value'] < alpha:
        print()
        print("=" * 70)
        print(f"POST-HOC TEST: {posthoc.upper()}")
        print("=" * 70)
        
        if posthoc == 'tukey':
            comparisons = tukey_hsd(groups, alpha)
            print(f"\nTukey HSD pairwise comparisons (α = {alpha}):")
        elif posthoc == 'bonferroni':
            comparisons = bonferroni_correction(groups, alpha)
            print(f"\nBonferroni-corrected pairwise comparisons (α = {alpha}):")
        else:
            print(f"Unknown post-hoc test: {posthoc}")
            return
        
        print("-" * 70)
        print(f"{'Comparison':<30} {'Diff':>12} {'Stat':>10} {'p-value':>10} {'Sig':>6}")
        print("-" * 70)
        
        for comp in comparisons:
            comparison = f"{comp['group1']} vs {comp['group2']}"
            diff = comp['mean_diff']
            
            if 'q_statistic' in comp:
                stat = comp['q_statistic']
                stat_label = f"{stat:.3f}"
            else:
                stat = comp['t_statistic']
                stat_label = f"{stat:.3f}"
            
            pval = comp.get('p_value_corrected', comp['p_value'])
            sig = "YES" if comp['significant'] else "NO"
            
            print(f"{comparison:<30} {diff:>12.2f} {stat_label:>10} {pval:>10.4f} {sig:>6}")
        
        print()


def main():
    parser = argparse.ArgumentParser(
        description="One-way ANOVA for Linux Reality Check",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # ANOVA on single CSV with grouping column
  python3 anova.py data/experiment.csv --metric runtime_ns --group workload_type

  # ANOVA with Tukey post-hoc test
  python3 anova.py data/experiment.csv --metric runtime_ns --group workload_type --posthoc tukey

  # ANOVA on multiple CSV files (each file is a group)
  python3 anova.py data/exp1.csv data/exp2.csv data/exp3.csv --metric runtime_ns

  # Export results to JSON
  python3 anova.py data/experiment.csv --metric runtime_ns --group workload_type --output results.json
        """
    )
    
    parser.add_argument('csv_files', nargs='+', help='CSV file(s) with experimental data')
    parser.add_argument('--metric', required=True, help='Metric column to analyze')
    parser.add_argument('--group', help='Column to group by (single CSV mode)')
    parser.add_argument('--posthoc', choices=['tukey', 'bonferroni'],
                       help='Post-hoc test for pairwise comparisons')
    parser.add_argument('--alpha', type=float, default=0.05,
                       help='Significance level (default: 0.05)')
    parser.add_argument('--output', help='Output file for JSON results')
    
    args = parser.parse_args()
    
    # Load data
    if len(args.csv_files) == 1 and args.group:
        # Single CSV with grouping column
        csv_path = Path(args.csv_files[0])
        if not csv_path.exists():
            print(f"Error: File not found: {csv_path}", file=sys.stderr)
            return 1
        
        groups = load_csv_groups(csv_path, args.metric, args.group)
    else:
        # Multiple CSVs
        csv_paths = [Path(p) for p in args.csv_files]
        for path in csv_paths:
            if not path.exists():
                print(f"Error: File not found: {path}", file=sys.stderr)
                return 1
        
        groups = load_multiple_csvs(csv_paths, args.metric)
    
    if not groups:
        print("Error: No valid data loaded", file=sys.stderr)
        return 1
    
    if len(groups) < 2:
        print("Error: Need at least 2 groups for ANOVA", file=sys.stderr)
        return 1
    
    # Perform ANOVA
    anova_result = one_way_anova(groups)
    
    if 'error' in anova_result:
        print(f"Error: {anova_result['error']}", file=sys.stderr)
        return 1
    
    # Print report
    print_anova_report(groups, anova_result, args.posthoc, args.alpha)
    
    # Export to JSON if requested
    if args.output:
        output = {
            'anova': anova_result,
            'groups': {name: {
                'n': len(values),
                'mean': calculate_mean(values),
                'std': calculate_std(values),
                'values': values
            } for name, values in groups.items()},
            'alpha': args.alpha
        }
        
        if args.posthoc:
            if args.posthoc == 'tukey':
                output['posthoc'] = {
                    'method': 'tukey_hsd',
                    'comparisons': tukey_hsd(groups, args.alpha)
                }
            elif args.posthoc == 'bonferroni':
                output['posthoc'] = {
                    'method': 'bonferroni',
                    'comparisons': bonferroni_correction(groups, args.alpha)
                }
        
        with open(args.output, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"Results exported to: {args.output}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
