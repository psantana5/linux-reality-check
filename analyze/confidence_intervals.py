#!/usr/bin/env python3
"""
Confidence Interval Calculator for LRC

Calculates confidence intervals using multiple methods:
- Normal approximation (for large samples)
- T-distribution (for smaller samples) - requires scipy
- Bootstrap (non-parametric, works for any distribution)
"""

import sys
import csv
import math

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    print("Warning: numpy not found, using pure Python (slower)", file=sys.stderr)

try:
    from scipy import stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    print("Warning: scipy not found, using bootstrap method only", file=sys.stderr)

def mean(data):
    """Calculate mean"""
    return sum(data) / len(data)

def variance(data, ddof=1):
    """Calculate variance"""
    m = mean(data)
    return sum((x - m) ** 2 for x in data) / (len(data) - ddof)

def std(data, ddof=1):
    """Calculate standard deviation"""
    return math.sqrt(variance(data, ddof))

def calculate_ci_t(data, confidence=0.95):
    """Calculate CI using t-distribution (requires scipy)"""
    if not HAS_SCIPY:
        return None, None
    
    if HAS_NUMPY:
        data_arr = np.array(data)
        n = len(data_arr)
        m = np.mean(data_arr)
        std_err = stats.sem(data_arr)
    else:
        n = len(data)
        m = mean(data)
        s = std(data)
        std_err = s / math.sqrt(n)
    
    df = n - 1
    t = stats.t.ppf((1 + confidence) / 2, df)
    
    margin = t * std_err
    return m - margin, m + margin

def calculate_ci_bootstrap(data, confidence=0.95, n_bootstrap=10000):
    """Calculate CI using bootstrap resampling (pure Python fallback)"""
    import random
    random.seed(42)  # Reproducibility
    
    n = len(data)
    bootstrap_means = []
    
    for _ in range(n_bootstrap):
        # Resample with replacement
        sample = [data[random.randint(0, n-1)] for _ in range(n)]
        bootstrap_means.append(mean(sample))
    
    # Sort and find percentiles
    bootstrap_means.sort()
    
    alpha = 1 - confidence
    lower_idx = int((alpha / 2) * n_bootstrap)
    upper_idx = int((1 - alpha / 2) * n_bootstrap)
    
    return bootstrap_means[lower_idx], bootstrap_means[upper_idx]

def calculate_all_cis(data, confidence_levels=[0.95, 0.99]):
    """Calculate confidence intervals using available methods"""
    m = mean(data)
    s = std(data)
    
    results = {
        'mean': m,
        'std': s,
        'n': len(data)
    }
    
    for conf in confidence_levels:
        conf_pct = int(conf * 100)
        
        # Try t-distribution first (if scipy available)
        if HAS_SCIPY:
            ci_lower_t, ci_upper_t = calculate_ci_t(data, conf)
            results[f'ci{conf_pct}_t_lower'] = ci_lower_t
            results[f'ci{conf_pct}_t_upper'] = ci_upper_t
            results[f'ci{conf_pct}_t_margin'] = ci_upper_t - m
        
        # Bootstrap (always available)
        ci_lower_boot, ci_upper_boot = calculate_ci_bootstrap(data, conf)
        results[f'ci{conf_pct}_bootstrap_lower'] = ci_lower_boot
        results[f'ci{conf_pct}_bootstrap_upper'] = ci_upper_boot
        results[f'ci{conf_pct}_bootstrap_margin'] = ci_upper_boot - m
    
    return results

def analyze_csv_with_ci(csv_file, metric='workload_ns', group_by='name'):
    """Analyze CSV file and add confidence intervals"""
    
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
    
    # Calculate CIs for each group
    results = {}
    for group, values in data.items():
        if len(values) < 2:
            continue
        
        results[group] = calculate_all_cis(values)
    
    return results

def print_ci_report(results, units='ms'):
    """Print formatted CI report"""
    print("=" * 80)
    print("CONFIDENCE INTERVALS")
    print("=" * 80)
    print()
    
    for group, stats in results.items():
        print(f"{group}:")
        print(f"  N = {stats['n']}")
        print()
        
        print("  Statistics:")
        print(f"    Mean: {stats['mean']:.3f} {units}")
        print(f"    Std:  {stats['std']:.3f} {units}")
        print()
        
        # T-distribution CIs (if available)
        if 'ci95_t_lower' in stats:
            print("  T-distribution confidence intervals:")
            if 'ci95_t_lower' in stats:
                print(f"    95% CI: [{stats['ci95_t_lower']:.3f}, {stats['ci95_t_upper']:.3f}] {units}")
                print(f"            {stats['mean']:.3f} ± {stats['ci95_t_margin']:.3f} {units}")
                print()
            
            if 'ci99_t_lower' in stats:
                print(f"    99% CI: [{stats['ci99_t_lower']:.3f}, {stats['ci99_t_upper']:.3f}] {units}")
                print(f"            {stats['mean']:.3f} ± {stats['ci99_t_margin']:.3f} {units}")
                print()
        
        # Bootstrap CIs
        print("  Bootstrap confidence intervals:")
        if 'ci95_bootstrap_lower' in stats:
            print(f"    95% CI: [{stats['ci95_bootstrap_lower']:.3f}, {stats['ci95_bootstrap_upper']:.3f}] {units}")
            print(f"            {stats['mean']:.3f} ± {stats['ci95_bootstrap_margin']:.3f} {units}")
        if 'ci99_bootstrap_lower' in stats:
            print(f"    99% CI: [{stats['ci99_bootstrap_lower']:.3f}, {stats['ci99_bootstrap_upper']:.3f}] {units}")
        print()

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Calculate confidence intervals for LRC results')
    parser.add_argument('csv_file', help='CSV file with results')
    parser.add_argument('--metric', '-m', default='workload_ns', help='Metric to analyze')
    parser.add_argument('--group', '-g', default='name', help='Column to group by')
    parser.add_argument('--confidence', '-c', type=float, nargs='+', default=[0.95, 0.99],
                       help='Confidence levels (e.g., 0.95 0.99)')
    
    args = parser.parse_args()
    
    try:
        results = analyze_csv_with_ci(args.csv_file, metric=args.metric, group_by=args.group)
        print_ci_report(results)
    except FileNotFoundError:
        print(f"Error: File '{args.csv_file}' not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error analyzing file: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Calculate confidence intervals for LRC results')
    parser.add_argument('csv_file', help='CSV file with results')
    parser.add_argument('--metric', '-m', default='workload_ns', help='Metric to analyze')
    parser.add_argument('--group', '-g', default='name', help='Column to group by')
    parser.add_argument('--confidence', '-c', type=float, nargs='+', default=[0.95, 0.99],
                       help='Confidence levels (e.g., 0.95 0.99)')
    
    args = parser.parse_args()
    
    try:
        results = analyze_csv_with_ci(args.csv_file, metric=args.metric, group_by=args.group)
        print_ci_report(results)
    except FileNotFoundError:
        print(f"Error: File '{args.csv_file}' not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error analyzing file: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
