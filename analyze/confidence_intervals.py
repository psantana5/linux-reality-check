#!/usr/bin/env python3
"""
Confidence Interval Calculator for LRC

Academically rigorous confidence intervals using bootstrap method
for quantiles (median, p90, p95, p99).

No parametric assumptions (no normal/t-distribution).
Appropriate for heavy-tailed systems performance data.
"""

import sys
import csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from robust_stats import (
    bootstrap_ci_quantile,
    quantile,
    median,
    iqr,
    mad,
    describe_robust
)


def calculate_quantile_cis(data, quantiles=None, confidence=0.95, n_bootstrap=10000):
    """
    Calculate bootstrap confidence intervals for quantiles.
    
    Args:
        data: Sample data
        quantiles: List of quantiles (e.g., [0.50, 0.90, 0.99])
        confidence: Confidence level (default 0.95)
        n_bootstrap: Number of bootstrap samples
    
    Returns:
        Dictionary with results for each quantile
    """
    if quantiles is None:
        quantiles = [0.50, 0.90, 0.95, 0.99]
    
    results = {}
    
    for q in quantiles:
        q_name = f'p{int(q * 100)}'
        point_est, ci_lower, ci_upper = bootstrap_ci_quantile(
            data, q, confidence=confidence, n_bootstrap=n_bootstrap
        )
        
        results[q_name] = {
            'quantile': q,
            'estimate': point_est,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'margin': ci_upper - point_est,
            'ci_width': ci_upper - ci_lower
        }
    
    return results


def analyze_csv_with_ci(csv_file, metric='runtime_ns', group_by='name', quantiles=None):
    """Analyze CSV file and calculate quantile CIs"""
    
    # Read data
    data = {}
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            group = row.get(group_by, 'default')
            if group not in data:
                data[group] = []
            
            # Convert nanoseconds to milliseconds if needed
            value = float(row[metric])
            if metric.endswith('_ns'):
                value = value / 1_000_000  # ns to ms
            
            data[group].append(value)
    
    # Calculate quantile CIs for each group
    results = {}
    for group, values in data.items():
        if len(values) < 2:
            continue
        
        # Robust summary
        summary = describe_robust(values)
        
        # Quantile CIs
        quantile_cis = calculate_quantile_cis(values, quantiles=quantiles)
        
        results[group] = {
            'summary': summary,
            'quantile_cis': quantile_cis
        }
    
    return results


def print_ci_report(results, units='ms'):
    """Print formatted CI report focusing on quantiles"""
    print("=" * 80)
    print("BOOTSTRAP CONFIDENCE INTERVALS FOR QUANTILES")
    print("=" * 80)
    print()
    print("Academic Note: Using bootstrap CIs on quantiles (non-parametric).")
    print("              No normality assumptions. Appropriate for heavy tails.")
    print()
    
    for group, data in results.items():
        summary = data['summary']
        quantile_cis = data['quantile_cis']
        
        print(f"{group}:")
        print(f"  N = {summary['n']}")
        print()
        
        print("  Robust Statistics:")
        print(f"    Median: {summary['median']:.3f} {units}")
        print(f"    IQR:    {summary['iqr']:.3f} {units}")
        print(f"    MAD:    {summary['mad']:.3f} {units}")
        print(f"    Tail ratio (p99/p50): {summary['tail_ratio']:.2f}x")
        print()
        
        print("  Bootstrap 95% Confidence Intervals:")
        print(f"    {'Quantile':<10} {'Estimate':<10} {'95% CI':<25} {'Width':<10}")
        print(f"    {'-'*10} {'-'*10} {'-'*25} {'-'*10}")
        
        for q_name, ci_data in sorted(quantile_cis.items()):
            ci_str = f"[{ci_data['ci_lower']:.3f}, {ci_data['ci_upper']:.3f}]"
            print(f"    {q_name:<10} "
                  f"{ci_data['estimate']:.3f} {units:<5} "
                  f"{ci_str:<25} "
                  f"{ci_data['ci_width']:.3f} {units}")
        
        print()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Calculate bootstrap confidence intervals for quantiles',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python3 confidence_intervals.py data/results.csv --metric runtime_ns

  # Custom quantiles
  python3 confidence_intervals.py data/cache.csv --metric workload_ns \\
      --quantiles 0.5 0.9 0.95 0.99 0.999

  # Different grouping
  python3 confidence_intervals.py data/exp.csv --metric latency_ns \\
      --group buffer_size

Academic Note:
  This script uses bootstrap confidence intervals for quantiles.
  No parametric assumptions (no mean/std, no t-distribution).
  Appropriate for heavy-tailed systems performance data.
        """
    )
    
    parser.add_argument('csv_file', help='CSV file with results')
    parser.add_argument('--metric', '-m', default='runtime_ns', 
                       help='Metric to analyze (default: runtime_ns)')
    parser.add_argument('--group', '-g', default='name', 
                       help='Column to group by (default: name)')
    parser.add_argument('--quantiles', '-q', type=float, nargs='+',
                       help='Quantiles to analyze (default: 0.5 0.9 0.95 0.99)')
    parser.add_argument('--bootstrap', '-b', type=int, default=10000,
                       help='Number of bootstrap samples (default: 10000)')
    
    args = parser.parse_args()
    
    try:
        results = analyze_csv_with_ci(
            args.csv_file, 
            metric=args.metric, 
            group_by=args.group,
            quantiles=args.quantiles
        )
        print_ci_report(results)
    except FileNotFoundError:
        print(f"Error: File '{args.csv_file}' not found", file=sys.stderr)
        sys.exit(1)
    except KeyError as e:
        print(f"Error: Column not found: {e}", file=sys.stderr)
        print(f"Check that metric '{args.metric}' and group '{args.group}' exist", 
              file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error analyzing file: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
